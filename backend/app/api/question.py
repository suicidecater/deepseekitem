"""
Question API蓝图 - 题库/练习/考试/错题本接口

所有端点需 JWT认证 + student角色校验。
与前端 Mock handlers 数据结构对齐。
"""
from flask import Blueprint, request, g

from app.extensions import db
from app.services.question_service import QuestionService
from app.models.question import ErrorQuestion
from app.middleware.auth import jwt_required_with_user
from app.middleware.rbac import role_required
from app.utils.response import success, error, paginated_response

question_bp = Blueprint('question', __name__)


def _source(subject):
    if subject == 1: return 'subject1'
    if subject == 4: return 'subject4'
    if subject == 5: return 'professional'
    return 'subject1'


# ========== 题目列表 ==========

@question_bp.route('/list', methods=['GET'])
@jwt_required_with_user()
@role_required('student')
def get_question_list():
    """
    GET /api/question/list
    获取题目列表（支持分页和筛选）
    Query params:
        page: 页码（默认1）
        page_size: 每页数量（默认20，最大100）
        subject: 科目 1科一/4科四
        type: 题型 1单选/2多选/3判断/4图片/5情景
        difficulty: 难度 1简单/2中等/3困难
        know_id: 知识点ID
        keyword: 题干关键词搜索
    """
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 20, type=int)
    subject = request.args.get('subject', type=int)
    q_type = request.args.get('type', type=int)
    difficulty = request.args.get('difficulty', type=int)
    know_id = request.args.get('know_id', type=int)
    keyword = request.args.get('keyword', '').strip() or None

    # 分页边界处理
    if page < 1:
        page = 1
    if page_size < 1:
        page_size = 20
    if page_size > 100:
        page_size = 100

    items, total, p, ps = QuestionService.get_question_list(
        page=page, page_size=page_size, subject=subject,
        q_type=q_type, difficulty=difficulty, know_id=know_id, keyword=keyword
    )

    return paginated_response(items, total, p, ps)


# ========== 开始练习 ==========

@question_bp.route('/practice/start', methods=['POST'])
@jwt_required_with_user()
@role_required('student')
def start_practice():
    """
    POST /api/question/practice/start
    开始练习：根据条件随机抽取题目（支持知识点筛选+艾宾浩斯自适应）
    Body: {
        "subject": 1,           // 科目 1科一/4科四
        "count": 20,            // 题目数量（默认20）
        "types": ["single", "multiple", "judge"],  // 题型筛选
        "difficulty": null,     // 难度筛选
        "knowId": null,         // 知识点ID筛选
        "adaptive": false       // 是否启用艾宾浩斯自适应
    }
    """
    data = request.get_json() or {}
    subject = data.get('subject', 1)
    count = data.get('count', 20)
    types = data.get('types', None)
    difficulty = data.get('difficulty', None)
    know_id = data.get('knowId', None)
    adaptive = data.get('adaptive', False)

    if count < 1:
        count = 20
    if count > 100:
        count = 100

    ok, msg, result = QuestionService.start_practice(
        student_id=g.user_id,
        subject=subject,
        count=count,
        types=types,
        difficulty=difficulty,
        know_id=know_id,
        adaptive=adaptive,
    )

    if not ok:
        return error(400, msg)

    return success(result, message=msg)


# ========== 提交练习答案 ==========

@question_bp.route('/practice/answer', methods=['POST'])
@jwt_required_with_user()
@role_required('student')
def answer_practice():
    """
    POST /api/question/practice/answer
    提交单题练习答案，返回正确答案和解析
    Body: {
        "practiceId": 1,
        "questionId": 1,
        "answer": "C"
    }
    """
    data = request.get_json() or {}
    practice_id = data.get('practiceId')
    question_id = data.get('questionId')
    user_answer = data.get('answer', '')

    if practice_id is None or question_id is None:
        return error(40001, '缺少必填参数：practiceId, questionId')

    ok, msg, result = QuestionService.answer_practice(
        student_id=g.user_id,
        practice_id=practice_id,
        question_id=question_id,
        user_answer=user_answer,
        source=data.get('source', 'subject1'),
    )

    if not ok:
        return error(400, msg)

    return success(result, message=msg)


# ========== 开始模拟考试 ==========

@question_bp.route('/exam/start', methods=['POST'])
@jwt_required_with_user()
@role_required('student')
def start_exam():
    """
    POST /api/question/exam/start
    开始模拟考试：按科目随机抽取题目
    Body: {
        "subject": 1,     // 科目 1科一/4科四
        "count": 100      // 题目数量（科一默认100，科四默认50）
    }
    """
    data = request.get_json() or {}
    subject = data.get('subject', 1)
    count = data.get('count', None)

    # 默认题数：科一100题，科四50题
    if count is None:
        count = 100 if subject == 1 else 50

    ok, msg, result = QuestionService.start_exam(
        student_id=g.user_id,
        subject=subject,
        count=count,
    )

    if not ok:
        return error(400, msg)

    return success(result, message=msg)


# ========== 考试答题缓存 ==========

@question_bp.route('/exam/answer', methods=['POST'])
@jwt_required_with_user()
@role_required('student')
def cache_exam_answer():
    """
    POST /api/question/exam/answer
    考试答题缓存：保存用户答案
    Body: {
        "examId": 1,
        "questionId": 1,
        "answer": "C"
    }
    """
    data = request.get_json() or {}
    exam_id = data.get('examId')
    question_id = data.get('questionId')
    user_answer = data.get('answer', '')

    if exam_id is None or question_id is None:
        return error(40001, '缺少必填参数：examId, questionId')

    ok, msg, result = QuestionService.cache_exam_answer(
        student_id=g.user_id,
        exam_id=exam_id,
        question_id=question_id,
        user_answer=user_answer,
    )

    if not ok:
        return error(400, msg)

    return success(result, message=msg)


# ========== 交卷评分 ==========

@question_bp.route('/exam/submit', methods=['POST'])
@jwt_required_with_user()
@role_required('student')
def submit_exam():
    """
    POST /api/question/exam/submit
    交卷评分：计算得分、正确率，返回详细分析
    Body: {
        "examId": 1,
        "totalTime": 1800   // 总用时（秒），可选
    }
    """
    data = request.get_json() or {}
    exam_id = data.get('examId')
    total_time = data.get('totalTime', None)

    if exam_id is None:
        return error(40001, '缺少必填参数：examId')

    ok, msg, result = QuestionService.submit_exam(
        student_id=g.user_id,
        exam_id=exam_id,
        total_time=total_time,
        source=data.get('source', 'subject1'),
    )

    if not ok:
        return error(400, msg)

    return success(result, message=msg)


# ========== 错题本列表 ==========

@question_bp.route('/error-book', methods=['GET'])
@jwt_required_with_user()
@role_required('student')
def get_error_book():
    """
    GET /api/question/error-book
    获取错题本列表（支持分页和科目筛选）
    Query params:
        page: 页码（默认1）
        page_size: 每页数量（默认20）
        subject: 科目 1科一/4科四（可选）
    """
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 20, type=int)
    subject = request.args.get('subject', type=int)

    # 分页边界处理
    if page < 1:
        page = 1
    if page_size < 1:
        page_size = 20
    if page_size > 100:
        page_size = 100

    ok, msg, result = QuestionService.get_error_book(
        student_id=g.user_id,
        page=page,
        page_size=page_size,
        subject=subject,
    )

    if not ok:
        return error(400, msg)

    return success(result, message=msg)


# ========== 错题复习 ==========

@question_bp.route('/error-book/review', methods=['POST'])
@jwt_required_with_user()
@role_required('student')
def review_error_question():
    """
    POST /api/question/error-book/review
    错题复习：查看错题详情或提交复习答案
    Body: {
        "errorId": 1,
        "answer": "C"   // 可选，提供则为提交复习答案；不提供则为查看错题详情
    }
    """
    data = request.get_json() or {}
    error_id = data.get('errorId')
    user_answer = data.get('answer', None)

    if error_id is None:
        return error(40001, '缺少必填参数：errorId')

    ok, msg, result = QuestionService.review_error_question(
        student_id=g.user_id,
        error_id=error_id,
        user_answer=user_answer,
    )

    if not ok:
        return error(400, msg)

    return success(result, message=msg)


# ========== 错题删除 ==========

@question_bp.route('/error-book/<int:error_id>', methods=['DELETE'])
@jwt_required_with_user()
@role_required('student')
def delete_error_question(error_id):
    """
    DELETE /api/question/error-book/<error_id>
    从错题本中删除一条错题记录（仅限当前用户）
    """
    eq = ErrorQuestion.query.filter_by(id=error_id, student_id=g.user_id).first()
    if not eq:
        return error(404, '错题记录不存在')
    db.session.delete(eq)
    db.session.commit()
    return success(None, message='已从错题本移除')


# ========== 顺序刷题 ==========

# ========== 专项训练 ==========

@question_bp.route('/special-training/start', methods=['POST'])
@jwt_required_with_user()
@role_required('student')
def start_special_training():
    """
    POST /api/question/special-training/start
    根据用户学习方向，从对应题库中随机抽取指定分类的20道题目
    Body: { "category": "交通标志" }
    """
    import random
    from app.models.question import Subject1Question, Subject4Question, ProfessionalQuestion
    from app.models.user import Student

    data = request.get_json() or {}
    category = (data.get('category') or '').strip()

    VALID_CATEGORIES = ['交通标志', '交通法规', '安全常识', '驾驶理论']
    if category not in VALID_CATEGORIES:
        return error(40001, f'无效分类，可选: {", ".join(VALID_CATEGORIES)}')

    # 获取用户学习方向
    student = Student.query.get(g.user_id)
    if not student:
        return error(40001, '学员不存在')

    direction = student.study_subject or 1
    model_map = {1: Subject1Question, 4: Subject4Question, 5: ProfessionalQuestion}
    primary_model = model_map.get(direction, Subject1Question)
    fallback_model = Subject1Question

    PER_COUNT = 20

    # 从主题库抽取
    pool = primary_model.query.filter(primary_model.category == category).all()
    import random
    picked = random.sample(pool, min(PER_COUNT, len(pool))) if pool else []

    # 不足时从科目一补充
    shortfall = PER_COUNT - len(picked)
    if shortfall > 0 and primary_model != fallback_model:
        exclude_ids = [q.id for q in picked]
        fb_pool = fallback_model.query.filter(
            fallback_model.category == category
        ).filter(~fallback_model.id.in_(exclude_ids)).all() if exclude_ids else fallback_model.query.filter(
            fallback_model.category == category
        ).all()
        extra = random.sample(fb_pool, min(shortfall, len(fb_pool))) if fb_pool else []
        picked.extend(extra)

    random.shuffle(picked)

    questions = []
    for q in picked:
        questions.append({
            'id': q.id,
            'source': q.source_table,
            'type': {'判断题': 'judge', '单选题': 'single', '多选题': 'multiple'}.get(q.question_type, 'single'),
            'category': q.category,
            'content': q.question_text,
            'options': q.get_options_list(),
            'image': q.image_file,
            'difficulty': q.difficulty,
        })

    subject_names = {1: '科目一', 4: '科目四', 5: '专业人员'}
    return success({
        'questions': questions,
        'total': len(questions),
        'category': category,
        'subject': subject_names.get(direction, '科目一'),
    })


@question_bp.route('/special-training/submit', methods=['POST'])
@jwt_required_with_user()
@role_required('student')
def submit_special_training():
    """
    POST /api/question/special-training/submit
    提交专项训练答案，返回判题结果
    Body: {
        "answers": [{"questionId": 1, "answer": "A"}, ...],
        "category": "交通标志"
    }
    """
    from app.models.question import Subject1Question, Subject4Question, ProfessionalQuestion

    data = request.get_json() or {}
    answers = data.get('answers', [])
    category = (data.get('category') or '').strip()

    if not answers:
        return error(40001, '缺少答案数据')

    # 收集所有 questionId 及对应的 source
    qid_source_map = {a.get('questionId'): a.get('source', 'subject1') for a in answers if a.get('questionId')}

    question_ids = list(qid_source_map.keys())
    if not question_ids:
        return error(40001, '答案数据为空')

    # 从三张表中查找题目（专项训练题目可能来自任意表）
    all_models = [Subject1Question, Subject4Question, ProfessionalQuestion]
    qmap = {}
    for model in all_models:
        try:
            qs = model.query.filter(model.id.in_(question_ids)).all()
            for q in qs:
                qmap[q.id] = q
        except Exception:
            continue

    correct_count = 0
    answer_map = {}

    for a in answers:
        qid = a.get('questionId')
        user_ans = str(a.get('answer', '') or '').strip().upper()
        q = qmap.get(qid)
        if q:
            correct_ans = str(q.correct_answer or '').strip().upper()
            is_correct = (user_ans == correct_ans)
            if is_correct:
                correct_count += 1
            else:
                # 收集到错题本
                q_source = qid_source_map.get(qid, 'subject1')
                QuestionService._add_error(g.user_id, qid, q_source)
            answer_map[str(qid)] = {
                'userAnswer': user_ans,
                'correctAnswer': correct_ans,
                'isCorrect': is_correct,
            }
        else:
            answer_map[str(qid)] = {
                'userAnswer': user_ans,
                'correctAnswer': '',
                'isCorrect': False,
            }

    total = len(answers)
    correct_rate = round(correct_count / total * 100, 1) if total > 0 else 0

    return success({
        'correctRate': correct_rate,
        'correctCount': correct_count,
        'wrongCount': total - correct_count,
        'totalCount': total,
        'category': category,
        'answerMap': answer_map,
    })


@question_bp.route('/sequential', methods=['GET'])
@jwt_required_with_user()
@role_required('student')
def get_sequential_questions():
    """
    GET /api/question/sequential?source=subject1
    返回指定题库的全部题目，按题号升序（不含正确答案）
    source: subject1 / subject4 / professional
    """
    source = request.args.get('source', 'subject1').strip()
    ok, msg, result = QuestionService.get_sequential_questions(source=source)
    if not ok:
        return error(400, msg)
    return success(result, message=msg)


@question_bp.route('/check-answer', methods=['POST'])
@jwt_required_with_user()
@role_required('student')
def check_sequential_answer():
    """
    POST /api/question/check-answer
    校验单题答案（顺序刷题用）
    Body: { "questionId": 1, "source": "subject1", "answer": "C" }
    返回: { correct: bool, correctAnswer: "B" }
    """
    data = request.get_json() or {}
    question_id = data.get('questionId')
    source = data.get('source', 'subject1')
    user_answer = data.get('answer', '')

    if question_id is None:
        return error(40001, '缺少必填参数：questionId')

    ok, msg, result = QuestionService.check_sequential_answer(
        question_id=question_id, source=source, user_answer=user_answer
    )
    if not ok:
        return error(400, msg)
    return success(result, message=msg)
