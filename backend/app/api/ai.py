"""
AI API蓝图 - DeepSeek AI相关接口（含题库检索增强）

所有端点需 JWT认证 + student角色校验。
"""
import json
import re
import time

from flask import Blueprint, request, g, Response, stream_with_context, current_app

from app.middleware.auth import jwt_required_with_user
from app.middleware.rbac import role_required
from app.utils.response import success, error
from app.models.system_config import SystemConfig
from app.models.question import Subject1Question, Subject4Question, ProfessionalQuestion

ai_bp = Blueprint('ai', __name__)


def _get_api_key():
    """获取 DeepSeek API Key：优先从 system_config 表读取，回退到环境变量"""
    key = SystemConfig.get_value('deepseek_api_key', '')
    if not key:
        key = current_app.config.get('DEEPSEEK_API_KEY', '')
    return key


def _call_deepseek_api(messages, stream=False, temperature=0.7):
    """
    调用 DeepSeek API（使用 urllib 避免 requests SSL 兼容问题）
    返回: (success: bool, data: str or None, error: str or None)
    """
    api_key = _get_api_key()
    if not api_key:
        return False, None, '管理员尚未配置AI服务'

    import ssl, http.client

    base_url = current_app.config.get('DEEPSEEK_BASE_URL', 'https://api.deepseek.com/v1')
    model = current_app.config.get('DEEPSEEK_MODEL', 'deepseek-chat')
    timeout = current_app.config.get('DEEPSEEK_TIMEOUT', 30)
    max_retries = current_app.config.get('DEEPSEEK_MAX_RETRIES', 2)

    payload = json.dumps({
        'model': model, 'messages': messages,
        'temperature': temperature, 'stream': stream,
    })

    ctx = ssl.create_default_context()

    for attempt in range(max_retries):
        try:
            conn = http.client.HTTPSConnection('api.deepseek.com', timeout=timeout, context=ctx)
            conn.request('POST', '/v1/chat/completions', body=payload.encode('utf-8'), headers={
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json',
            })
            resp = conn.getresponse()
            body = resp.read().decode('utf-8')
            if resp.status == 200:
                resp_data = json.loads(body)
                return True, resp_data, None
            elif resp.status == 401:
                return False, None, 'API Key无效'
            elif resp.status == 429:
                return False, None, '请求过于频繁'
            else:
                err = json.loads(body).get('error', {}).get('message', f'HTTP {resp.status}')
                return False, None, err
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(1)
                continue
            return False, None, f'调用异常: {str(e)}'
        finally:
            try: conn.close()
            except: pass

    return False, None, '已达最大重试次数'


# ========== 意图识别 & 关键词提取 ==========

import re as _re_module  # noqa: E402 (已在顶部导入，此处为类型安全)

# 干扰词列表（这些词不携带检索价值）
_STOP_WORDS = {
    '这个', '那个', '哪题', '啊', '是', '的', '吗', '对', '不对', '对不对',
    '正确', '错误', '判断', '想知道', '我想', '知道', '项目', '原问题',
    '是什么呢', '什么', '请问', '帮忙', '帮', '谢谢', '你好',
}

# 意图识别正则
_BROWSE_PATTERN = _re_module.compile(
    r'(科目|科|subject)\s*[一二三四1-4]?\s*.*?前\s*(\d+)\s*(题|道)'
)
_QUIZ_VERIFY_PATTERN = _re_module.compile(
    r'(对\s*的?\s*吗|对吗|对不对|是对|正确|错误|判断\s*题|是否)'
)
_QUIZ_LOCATE_PATTERN = _re_module.compile(
    r'(哪\s*题|哪个\s*题|编号|题号|在哪|帮\s*我\s*找)'
)
_SOURCE_PATTERN = _re_module.compile(
    r'(科目\s*一?|科\s*一?|subject\s*1)|(科目\s*四?|科\s*四?|subject\s*4)|(专业|从业|危险品)'
)

BANK_MODELS = [
    ('科目一', Subject1Question),
    ('科目四', Subject4Question),
    ('专业人员', ProfessionalQuestion),
]


def _detect_intent(text):
    """
    检测用户意图，返回 (intent, extra)
    intent: 'browse' | 'quiz' | 'chat'
    extra: dict, e.g. {'limit': 100} for browse; {'verify': True, 'locate': True} for quiz
    """
    result = {'intent': 'chat', 'extra': {}}

    # 浏览模式：科目一前100题
    m = _BROWSE_PATTERN.search(text)
    if m:
        result['intent'] = 'browse'
        result['extra']['limit'] = int(m.group(2))
        return result

    # 查题模式：验证 + 定位
    has_verify = bool(_QUIZ_VERIFY_PATTERN.search(text))
    has_locate = bool(_QUIZ_LOCATE_PATTERN.search(text))
    if has_verify or has_locate:
        result['intent'] = 'quiz'
        result['extra']['verify'] = has_verify
        result['extra']['locate'] = has_locate
        return result

    return result


def _extract_source(text):
    """从文本中提取题目来源：'subject1' / 'subject4' / 'professional' / None"""
    m = _SOURCE_PATTERN.search(text)
    if not m:
        return None
    if m.group(1):
        return 'subject1'
    if m.group(2):
        return 'subject4'
    if m.group(3):
        return 'professional'
    return None


def _extract_keywords(text):
    """
    从用户消息中提取检索关键词。
    1. 去掉干扰词
    2. 按常见分隔符切分
    3. 保留 ≥2 字符的片段
    4. 附加长片段的首部作为短关键词
    """
    # 去掉干扰词
    cleaned = text
    for sw in sorted(_STOP_WORDS, key=len, reverse=True):
        cleaned = cleaned.replace(sw, ' ')
    # 去掉标点
    cleaned = _re_module.sub(r'[，。！？、；：""''「」【】《》（）\s,\.!\?;:]+', ' ', cleaned)
    # 切词
    raw_kw = [w.strip() for w in cleaned.split(' ') if len(w.strip()) >= 2]
    # 去重 + 附加复合词
    keywords = list(dict.fromkeys(raw_kw))  # 保序去重
    # 对 ≥4 字的词，追加其前 2 字作为短关键词
    extra = []
    for kw in keywords:
        if len(kw) >= 4:
            extra.append(kw[:2])
    keywords.extend(extra)
    return list(dict.fromkeys(keywords))  # 最终去重


def _search_or(keywords, source_filter=None, max_per_bank=5):
    """
    多关键词 OR 检索，返回按匹配度排序的 [(label, question, hit_count), ...]
    source_filter: None 搜全部，或 'subject1'/'subject4'/'professional' 限定
    """
    from collections import Counter
    scored = {}  # (label, q.id) → (label, question, hit_count)

    banks = BANK_MODELS
    if source_filter:
        label_map = {'subject1': '科目一', 'subject4': '科目四', 'professional': '专业人员'}
        label = label_map.get(source_filter)
        model_map = {'subject1': Subject1Question, 'subject4': Subject4Question, 'professional': ProfessionalQuestion}
        banks = [(label, model_map[source_filter])] if label else banks

    for kw in keywords:
        if len(kw) < 2:
            continue
        for label, Model in banks:
            try:
                qs = Model.query.filter(Model.question_text.contains(kw)).limit(max_per_bank * 2).all()
                for q in qs:
                    key = (label, q.id)
                    if key not in scored:
                        scored[key] = (label, q, 0)
                    scored[key] = (label, q, scored[key][2] + 1)
            except Exception as e:
                current_app.logger.warning(f'检索异常[{label}][{kw}]: {e}')

    # 按命中关键词数降序，同分按题号升序
    results = sorted(scored.values(), key=lambda x: (-x[2], x[1].question_number))
    return results[:max_per_bank]


def _format_question_context(matches):
    """将匹配到的题目格式化为 AI 上下文文本"""
    if not matches:
        return ''

    lines = ['以下是与用户问题相关的题库数据，请基于这些数据回答：', '']
    for label, q, hit in matches:
        options = []
        for opt_letter in ['A', 'B', 'C', 'D']:
            val = getattr(q, f'option_{opt_letter.lower()}', '')
            if val:
                options.append(f'{opt_letter}. {val}')

        lines.append(f'【{label}】题号 {q.question_number}  |  匹配度: {hit}个关键词')
        lines.append(f'题目：{q.question_text}')
        if options:
            lines.append(f'选项：{"  ".join(options)}')
        lines.append(f'正确答案：{q.correct_answer}')
        lines.append(f'题型：{q.question_type or "未知"}  |  难度：{q.difficulty}/5')
        lines.append('')

    return '\n'.join(lines)


def _format_questions_list(questions, label, limit):
    """将 DB 查询结果格式化为可读文本（浏览模式）"""
    lines = [
        f'以下是【{label}】题库前 {limit} 道题目：',
        '',
    ]
    for q in questions:
        line = f'#{q.question_number}  [{q.question_type or "?"}] {q.question_text[:60]}{"..." if len(q.question_text or "") > 60 else ""}'
        if q.question_type in ('单选题', '多选题'):
            opts = []
            for o in ['A', 'B', 'C', 'D']:
                v = getattr(q, f'option_{o.lower()}', '')
                if v:
                    opts.append(f'{o}.{v}')
            if opts:
                line += f'  |  {"  ".join(opts)}'
        line += f'  |  答案: {q.correct_answer}'
        lines.append(line)
    return '\n'.join(lines)


def _sse_response(text):
    """将文本包装为 SSE 流式响应"""
    chunk_size = 15
    def generate():
        for i in range(0, len(text), chunk_size):
            chunk = text[i:i+chunk_size]
            yield f"data: {json.dumps({'content': chunk}, ensure_ascii=False)}\n\n"
        yield f"data: {json.dumps({'type': 'end'})}\n\n"
    return Response(
        stream_with_context(generate()),
        mimetype='text/event-stream',
        headers={'Cache-Control': 'no-cache', 'Connection': 'keep-alive', 'X-Accel-Buffering': 'no'}
    )


# ========== SSE流式AI问答 ==========

@ai_bp.route('/chat/stream', methods=['POST'])
@jwt_required_with_user()
@role_required('student')
def chat_stream():
    """
    POST /api/ai/chat/stream
    SSE流式AI问答（意图路由 + 关键词检索 + 题库增强）

    支持三种模式：
    - browse: "科目一前100题" → 直接查库返回，不调AI
    - quiz:   "XX是对的吗？哪题？" → 关键词提取 → 检索 → AI分析
    - chat:   "为什么XX？" → 关键词检索 → AI自由回答
    """
    data = request.get_json() or {}
    question = (data.get('question') or '').strip()

    if not question:
        return error(40001, '请输入问题')

    # ---- 意图识别 ----
    intent_info = _detect_intent(question)
    intent = intent_info['intent']
    source_filter = _extract_source(question)
    current_app.logger.info(f'AI意图: {intent}, source: {source_filter}')

    # ---- 浏览模式：直接查库，不调 AI ----
    if intent == 'browse':
        limit = min(intent_info['extra'].get('limit', 100), 500)
        banks_to_search = BANK_MODELS
        if source_filter:
            label_map = {'subject1': '科目一', 'subject4': '科目四', 'professional': '专业人员'}
            model_map = {'subject1': Subject1Question, 'subject4': Subject4Question, 'professional': ProfessionalQuestion}
            banks_to_search = [(label_map.get(source_filter, '未知'), model_map[source_filter])] if source_filter in model_map else BANK_MODELS

        all_parts = []
        for label, Model in banks_to_search:
            try:
                qs = Model.query.order_by(Model.question_number).limit(limit).all()
                if qs:
                    all_parts.append(_format_questions_list(qs, label, limit))
            except Exception as e:
                current_app.logger.warning(f'浏览模式查询异常[{label}]: {e}')

        if not all_parts:
            full_response = '未找到题目数据，请检查题库是否已导入。'
        else:
            full_response = '\n\n'.join(all_parts)

        try:
            from app.models.study import AiChat
            AiChat(student_id=g.user_id, user_msg=question, ai_msg=full_response).save()
        except Exception:
            pass
        return _sse_response(full_response)

    # ---- 提取关键词并检索 ----
    keywords = _extract_keywords(question)
    current_app.logger.info(f'提取关键词: {keywords}')

    matched = _search_or(keywords, source_filter=source_filter, max_per_bank=5)
    current_app.logger.info(f'检索到 {len(matched)} 条匹配题目')

    # ---- 查题模式：必须找到匹配才分析 ----
    if intent == 'quiz':
        if not matched:
            full_response = (
                '在三个题库中未检索到与该题目匹配的数据。\n\n'
                '可能原因：\n'
                '1. 题目描述与题库原文差异较大，建议使用题干中的关键词重新提问\n'
                '2. 该题目暂未录入题库\n\n'
                '你可以尝试复制题干中的关键短语（如"危险货物"、"包装标志"）重新提问。'
            )
            try:
                from app.models.study import AiChat
                AiChat(student_id=g.user_id, user_msg=question, ai_msg=full_response).save()
            except Exception:
                pass
            return _sse_response(full_response)

        # 找到匹配 → 调 AI 做分析
        question_context = _format_question_context(matched)
        verify = intent_info['extra'].get('verify', False)
        locate = intent_info['extra'].get('locate', False)

        system_prompt = (
            '你是专业的交通知识培训助手。\n\n'
            f'{question_context}\n'
            '请严格基于以上题库数据回答：\n'
            '1. 首先明确给出该题在题库中的位置（哪个科目、第几题）\n'
        )
        if verify:
            system_prompt += (
                '2. 判断用户引述的题干是否正确，如果用户引述与题库原文有出入请指出\n'
                '3. 给出正确答案，并判断"对/错"\n'
            )
        if locate:
            system_prompt += '4. 明确标注题号来源\n'
        system_prompt += (
            '5. 深度解析答案（为什么选这个，其他选项错在哪）\n'
            '6. 知识点拓展（法规依据、记忆口诀）\n\n'
            '重要：必须使用题库的正确答案，不要自行判断。使用中文，简洁准确。'
        )

        api_key = _get_api_key()
        if not api_key:
            full_response = (
                _format_response_without_ai(matched, verify, locate)
            )
            try:
                from app.models.study import AiChat
                AiChat(student_id=g.user_id, user_msg=question, ai_msg=full_response).save()
            except Exception:
                pass
            return _sse_response(full_response)

        messages = [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': question},
        ]
        success_flag, resp_data, error_msg = _call_deepseek_api(messages, stream=False)
        if not success_flag:
            full_response = _format_response_without_ai(matched, verify, locate) + f'\n（AI服务暂不可用：{error_msg}，以下为题库直接查询结果）'
        else:
            full_response = resp_data.get('choices', [{}])[0].get('message', {}).get('content', '')

        try:
            from app.models.study import AiChat
            AiChat(student_id=g.user_id, user_msg=question, ai_msg=full_response).save()
        except Exception:
            pass
        return _sse_response(full_response)

    # ---- 聊天模式：关键词检索作为上下文，AI 自由回答 ----
    question_context = _format_question_context(matched) if matched else ''

    api_key = _get_api_key()
    if not api_key:
        if matched:
            full_response = (
                '（AI服务未配置，以下为题库检索结果）\n\n'
                + _format_response_without_ai(matched, verify=False, locate=False)
            )
        else:
            full_response = '请在管理后台配置 DeepSeek API Key 以使用 AI 问答功能。'
        try:
            from app.models.study import AiChat
            AiChat(student_id=g.user_id, user_msg=question, ai_msg=full_response).save()
        except Exception:
            pass
        return _sse_response(full_response)

    if question_context:
        system_prompt = (
            '你是专业的交通知识培训助手，专注于中国交通法规、驾驶理论、'
            '交通标志标线、安全文明驾驶等领域的教学。\n\n'
            f'{question_context}\n'
            '请基于以上题库数据回答用户问题，回答需包含：\n'
            '1. 正确答案（如题库中有匹配题目，必须使用题库的正确答案）\n'
            '2. 深度解析\n'
            '3. 知识点拓展\n'
            '如果题库中没有匹配的题目，请基于交通法规知识回答并注明。使用中文，简洁准确。'
        )
    else:
        system_prompt = (
            '你是一个专业的交通知识培训助手，专注于中国交通法规、驾驶理论、'
            '交通标志标线、安全文明驾驶等领域的教学。请用中文回答，'
            '回答应包含以下结构：\n'
            '1. 知识点讲解\n'
            '2. 法规引用（如有）\n'
            '3. 案例分析（如有）\n'
            '回答应简洁准确，适合驾考学员学习。'
        )

    messages = [
        {'role': 'system', 'content': system_prompt},
        {'role': 'user', 'content': question},
    ]

    success_flag, resp_data, error_msg = _call_deepseek_api(messages, stream=False)
    if not success_flag:
        return error(500, f'AI调用失败: {error_msg}')

    full_response = resp_data.get('choices', [{}])[0].get('message', {}).get('content', '')

    try:
        from app.models.study import AiChat
        AiChat(student_id=g.user_id, user_msg=question, ai_msg=full_response).save()
    except Exception:
        pass

    return _sse_response(full_response)


def _format_response_without_ai(matched, verify, locate):
    """无 AI 时的降级回答，直接用数据库结果格式化"""
    lines = ['（以下为题库直接查询结果）\n']
    for label, q, hit in matched:
        lines.append(f'【{label}】第 {q.question_number} 题')
        lines.append(f'题干：{q.question_text}')
        opts = []
        for o in ['A', 'B', 'C', 'D']:
            v = getattr(q, f'option_{o.lower()}', '')
            if v:
                opts.append(f'{o}. {v}')
        if opts:
            lines.append(f'选项：{"  ".join(opts)}')
        lines.append(f'正确答案：{q.correct_answer}')
        if verify:
            lines.append('请自行对比你的引述与上述题库原文是否一致。')
        lines.append('')
    return '\n'.join(lines)


# ========== AI生成交通场景 ==========

@ai_bp.route('/generate-scene', methods=['POST'])
@jwt_required_with_user()
@role_required('student')
def generate_scene():
    """
    POST /api/ai/generate-scene
    AI生成交通场景（场景描述 + 题目）
    Body: {
        "topic": "高速公路安全车距",
        "difficulty": 2
    }
    """
    data = request.get_json() or {}
    topic = (data.get('topic') or '交通标志').strip()
    difficulty = data.get('difficulty', 1)

    api_key = _get_api_key()
    if not api_key:
        return error(40001, '管理员尚未配置AI服务，请联系管理员设置DeepSeek API Key')

    prompt = (
        f'请生成一个关于"{topic}"的交通场景模拟题，难度等级{difficulty}（1简单/2中等/3困难）。\n'
        '请按以下JSON格式返回（只返回JSON，不要其他内容）：\n'
        '{\n'
        '  "scene": {"title": "场景标题", "description": "场景描述（50字以内）"},\n'
        '  "question": {\n'
        '    "content": "题目内容",\n'
        '    "options": ["A. 选项一", "B. 选项二", "C. 选项三", "D. 选项四"],\n'
        '    "answer": "C",\n'
        '    "analysis": "解析说明"\n'
        '  }\n'
        '}'
    )

    messages = [
        {'role': 'system', 'content': '你是一个交通场景生成器，只输出JSON格式，不要其他内容。'},
        {'role': 'user', 'content': prompt},
    ]

    success_flag, resp, error_msg = _call_deepseek_api(messages, stream=False, temperature=0.8)

    if not success_flag:
        # 返回Mock数据作为降级
        return success({
            'scene': {
                'title': topic,
                'description': f'模拟{topic}相关交通场景，请根据题目作答',
            },
            'question': {
                'content': f'关于{topic}，以下说法正确的是？',
                'options': ['A. 选项一', 'B. 选项二', 'C. 选项三', 'D. 选项四'],
                'answer': 'C',
                'analysis': '请参考交通法规相关条款',
            },
            'note': f'AI服务暂不可用（{error_msg}），显示为Mock数据',
        })

    try:
        content = resp.json().get('choices', [{}])[0].get('message', {}).get('content', '{}')
        # 尝试提取JSON
        if '```json' in content:
            content = content.split('```json')[1].split('```')[0].strip()
        elif '```' in content:
            content = content.split('```')[1].split('```')[0].strip()
        result = json.loads(content)
        return success(result)
    except (json.JSONDecodeError, KeyError, IndexError) as e:
        current_app.logger.error(f'AI场景生成解析失败: {e}, content: {content if isinstance(content, str) else "N/A"}')
        return success({
            'scene': {'title': topic, 'description': f'关于{topic}的交通场景'},
            'question': {
                'content': f'关于{topic}，以下说法正确的是？',
                'options': ['A. 选项一', 'B. 选项二', 'C. 选项三', 'D. 选项四'],
                'answer': 'C',
                'analysis': 'AI解析失败，请参考相关法规',
            },
            'note': 'AI返回格式异常，已降级为Mock数据',
        })


# ========== 对话历史管理 ==========

@ai_bp.route('/chat/history', methods=['GET'])
@jwt_required_with_user()
@role_required('student')
def get_chat_history():
    """
    GET /api/ai/chat/history
    获取当前学员的对话历史（最近50条，未删除的）
    """
    from app.models.study import AiChat
    records = AiChat.query.filter_by(
        student_id=g.user_id, is_deleted=False
    ).order_by(AiChat.create_time.asc()).limit(50).all()

    history = []
    for r in records:
        history.append({
            'id': r.id,
            'user_msg': r.user_msg,
            'ai_msg': r.ai_msg,
            'is_collect': r.is_collect or False,
            'create_time': r.create_time.strftime('%Y-%m-%d %H:%M') if r.create_time else '',
        })
    return success(history)


@ai_bp.route('/chat/history', methods=['DELETE'])
@jwt_required_with_user()
@role_required('student')
def clear_chat_history():
    """
    DELETE /api/ai/chat/history
    清空当前学员的对话历史（软删除）
    """
    from app.models.study import AiChat
    count = AiChat.query.filter_by(
        student_id=g.user_id, is_deleted=False
    ).update({'is_deleted': True})

    from app.extensions import db
    db.session.commit()
    return success({'cleared': count}, message=f'已清空 {count} 条对话记录')


# ========== 语音转文字 ==========

@ai_bp.route('/speech-to-text', methods=['POST'])
@jwt_required_with_user()
@role_required('student')
def speech_to_text():
    """
    POST /api/ai/speech-to-text
    语音转文字（当前返回Mock）
    Body: { "audio": "base64编码的音频数据" }
    返回: { text: "识别的文字" }
    """
    data = request.get_json() or {}
    audio = data.get('audio', '')

    if not audio:
        return error(40001, '请提供音频数据')

    # TODO: 接入腾讯云ASR或其他语音识别服务
    # 当前返回Mock，提示用户手动输入
    return success({
        'text': '',
        'note': '语音识别功能暂未接入，请手动输入问题',
        'status': 'not_implemented',
    })
