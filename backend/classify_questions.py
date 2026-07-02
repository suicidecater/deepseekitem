"""
AI 批量分类迁移脚本
遍历三张题库表，用 DeepSeek API 将每道题分为四维度之一：
交通标志 / 交通法规 / 安全常识 / 驾驶理论
含位置平滑校验，减少 AI 偶发错误。
"""

import json, re, ssl, http.client, time
from app import create_app
from app.extensions import db
from app.models.question import Subject1Question, Subject4Question, ProfessionalQuestion

CATEGORIES = ['交通标志', '交通法规', '安全常识', '驾驶理论']
BATCH_SIZE = 50
MAX_RETRIES = 3

app = create_app()
app.app_context().push()

# 查 API Key
from app.models.system_config import SystemConfig
API_KEY = SystemConfig.get_value('deepseek_api_key', '')
if not API_KEY:
    API_KEY = app.config.get('DEEPSEEK_API_KEY', '')
if not API_KEY:
    print('ERROR: DeepSeek API Key 未配置！请先在管理后台设置。')
    exit(1)

MODEL = app.config.get('DEEPSEEK_MODEL', 'deepseek-chat')


def call_deepseek(messages):
    """调用 DeepSeek API，返回 response content"""
    ctx = ssl.create_default_context()
    payload = json.dumps({
        'model': MODEL, 'messages': messages,
        'temperature': 0.3, 'stream': False,
    })
    for attempt in range(MAX_RETRIES):
        try:
            conn = http.client.HTTPSConnection('api.deepseek.com', timeout=60, context=ctx)
            conn.request('POST', '/v1/chat/completions', body=payload.encode('utf-8'), headers={
                'Authorization': f'Bearer {API_KEY}',
                'Content-Type': 'application/json',
            })
            resp = conn.getresponse()
            body = json.loads(resp.read().decode('utf-8'))
            conn.close()
            return body.get('choices', [{}])[0].get('message', {}).get('content', '')
        except Exception as e:
            print(f'  API 调用失败 (attempt {attempt+1}/{MAX_RETRIES}): {e}')
            if attempt < MAX_RETRIES - 1:
                time.sleep(3)
    return None


def smooth_categories(questions_with_cat):
    """
    位置平滑：如果某题前后各2题在同一类别，则修正该类题
    window_size=2, 需要 >=3/5 众数覆盖
    """
    n = len(questions_with_cat)
    if n < 5:
        return questions_with_cat

    for i in range(n):
        start = max(0, i - 2)
        end = min(n, i + 3)
        neighbors = [questions_with_cat[j][1] for j in range(start, end) if j != i]
        if not neighbors:
            continue
        # 找众数
        from collections import Counter
        c = Counter(neighbors)
        mode, count = c.most_common(1)[0]
        # 如果邻居中 >=3 个是同一类且当前不属于该类
        if count >= 3 and questions_with_cat[i][1] != mode:
            old = questions_with_cat[i][1]
            questions_with_cat[i] = (questions_with_cat[i][0], mode)
            print(f'  [平滑] 题号 {questions_with_cat[i][0].question_number}: {old} -> {mode}')


def classify_table(model_class, table_name):
    """对单张表批量分类"""
    print(f'\n{"="*60}')
    print(f'开始分类: {table_name}')
    print(f'{"="*60}')

    questions = model_class.query.order_by(model_class.question_number).all()
    total = len(questions)
    print(f'共 {total} 题')

    all_results = []  # [(question, category), ...]
    batch_count = 0

    for offset in range(0, total, BATCH_SIZE):
        batch = questions[offset:offset + BATCH_SIZE]
        batch_count += 1
        current_end = min(offset + BATCH_SIZE, total)

        # 构建 prompt
        lines = []
        for q in batch:
            qid = q.question_number
            text = q.question_text[:80]  # 取前80字足够分类
            lines.append(f'[{qid}] {text}')
        body = '\n'.join(lines)

        prompt = (
            '你是一个交通知识题库分类专家。请将以下50道驾考题按四维度严格分类：\n\n'
            '- 交通标志：涉及标志标线、信号灯、交警手势、道路交通标线、警告/禁令/指示/指路标志\n'
            '- 交通法规：涉及法律法规条文、罚款金额、记分规定、扣留/吊销驾驶证、行政/刑事处罚、事故责任认定\n'
            '- 安全常识：涉及安全驾驶操作、危险情况处置、恶劣天气驾驶、伤员急救、避险方法、行车安全检查\n'
            '- 驾驶理论：涉及车辆构造原理、仪表指示灯含义、车辆维护保养、驾驶证申领使用、车辆年检登记\n\n'
            '判断规则：\n'
            '1. 题干提到"标志""标线""信号灯""交警手势""指示/警告/禁令"中的任一关键词 → 交通标志\n'
            '2. 题干提到"罚款""记分""吊销""拘留""处罚""违法""事故责任"中的任一关键词 → 交通法规\n'
            '3. 题干提到"安全""危险""避险""爆胎""制动""车速""疲劳""灯光使用""伤员"中的任一关键词 → 安全常识\n'
            '4. 题干提到"发动机""仪表""变速器""离合器""保养""年检""证件申领""车辆装置"中的任一关键词 → 驾驶理论\n'
            '5. 注意优先级：交通标志 > 交通法规 > 安全常识 > 驾驶理论\n\n'
            f'请输出纯JSON数组（不要```json```标记，不要任何其他内容），格式如下：\n'
            '[{"id":题号,"category":"交通标志","confidence":0.95}, ...]\n'
            '每题都要包含id和category，confidence为0.0-1.0的置信度。\n\n'
            f'题目列表：\n{body}'
        )

        messages = [
            {'role': 'system', 'content': '你是一个交通题库分类专家，只输出JSON数组，不要其他内容。'},
            {'role': 'user', 'content': prompt},
        ]

        print(f'\n  批次 {batch_count}: 题号 {batch[0].question_number}-{batch[-1].question_number} ({len(batch)}题)... ', end='', flush=True)
        result = call_deepseek(messages)
        if not result:
            print('API 失败，跳过此批次')
            continue

        # 解析结果
        try:
            # 清洗：去掉可能的markdown包裹
            cleaned = result.strip()
            if cleaned.startswith('```'):
                cleaned = re.sub(r'^```\w*\n?', '', cleaned)
                cleaned = re.sub(r'\n?```$', '', cleaned)
            batch_results = json.loads(cleaned)
        except json.JSONDecodeError as e:
            print(f'JSON 解析失败: {e}')
            print(f'  原始返回前200字: {result[:200]}')
            continue

        # 构建 id -> category 映射
        cat_map = {}
        for item in batch_results:
            qid = item.get('id')
            cat = item.get('category', '').strip()
            # 标准化类别名
            for c in CATEGORIES:
                if c in cat:
                    cat = c
                    break
            else:
                cat = None  # 无法识别的类别
            if qid is not None and cat in CATEGORIES:
                cat_map[qid] = cat

        matched = len(cat_map)
        print(f'成功 {matched}/{len(batch)}')

        for q in batch:
            cat = cat_map.get(q.question_number, None)
            all_results.append((q, cat))

    # 位置平滑
    print(f'\n  位置平滑校验...')
    smooth_categories(all_results)

    # 写入数据库
    update_count = 0
    null_count = 0
    for q, cat in all_results:
        if cat and cat in CATEGORIES:
            q.category = cat
            update_count += 1
        else:
            null_count += 1
    db.session.commit()

    # 统计
    from collections import Counter
    cat_counts = Counter(r[1] for r in all_results if r[1] in CATEGORIES)
    print(f'\n  分类完成: 更新 {update_count} 题, 未分类 {null_count} 题')
    for c in CATEGORIES:
        print(f'    {c}: {cat_counts.get(c, 0)} 题')

    return update_count, null_count


# ========== 主流程 ==========
if __name__ == '__main__':
    tables = [
        (Subject1Question, '科目一 (subject1_question)'),
        (Subject4Question, '科目四 (subject4_question)'),
        (ProfessionalQuestion, '专业人员 (professional_question)'),
    ]

    total_updates = 0
    total_nulls = 0

    for model_class, name in tables:
        u, n = classify_table(model_class, name)
        total_updates += u
        total_nulls += n

    print(f'\n{"="*60}')
    print(f'全部完成！总计: {total_updates} 题已分类, {total_nulls} 题待人工补标')
    print(f'{"="*60}')
