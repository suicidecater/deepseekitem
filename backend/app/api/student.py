"""
Student API蓝图 - 学员端接口

所有端点需 JWT认证 + student角色校验。
与前端 Mock handlers 数据结构对齐。
"""
from flask import Blueprint, request, g

from app.services.student_service import StudentService
from app.middleware.auth import jwt_required_with_user
from app.middleware.rbac import role_required
from app.utils.response import success, error, paginated_response
from app.models.user import Coach

student_bp = Blueprint('student', __name__)


# ========== 能力雷达图动态分值 ==========

@student_bp.route('/ability-radar', methods=['GET'])
@jwt_required_with_user()
@role_required('student')
def get_ability_radar():
    """
    GET /api/student/ability-radar
    获取学员能力雷达图四维度动态分数
    返回: { traffic_sign, traffic_law, safety_common, driving_theory }
    四维度分数基于学员答题记录动态加权计算
    """
    data = StudentService.get_ability_radar(g.user_id)
    return success(data)


# ========== 首页统计数据 ==========

@student_bp.route('/home-stat', methods=['GET'])
@jwt_required_with_user()
@role_required('student')
def get_home_stat():
    """
    GET /api/student/home-stat
    获取学员首页统计数据（动态）
    返回: {
        student_name, continue_study_days,
        today_study_minutes, total_done_questions
    }
    """
    data = StudentService.get_home_stat(g.user_id)
    if data is None:
        return error(404, '学员不存在')
    return success(data)


# ========== 仪表盘 ==========

@student_bp.route('/dashboard', methods=['GET'])
@jwt_required_with_user()
@role_required('student')
def dashboard():
    """
    GET /api/student/dashboard
    获取学员仪表盘聚合数据（profile + 能力评分 + 今日任务 + 知识树等）
    """
    data = StudentService.get_dashboard(g.user_id)
    if data is None:
        return error(404, '学员不存在')
    return success(data)


# ========== 个人档案 ==========

@student_bp.route('/profile', methods=['GET'])
@jwt_required_with_user()
@role_required('student')
def get_profile():
    """
    GET /api/student/profile
    获取学员个人档案
    """
    data = StudentService.get_profile(g.user_id)
    if data is None:
        return error(404, '学员不存在')
    return success(data)


@student_bp.route('/profile', methods=['PUT'])
@jwt_required_with_user()
@role_required('student')
def update_profile():
    """
    PUT /api/student/profile
    更新学员个人档案
    Body: { "name": "", "phone": "", "car_type": "C1", "train_type": 1 }
    """
    data = request.get_json() or {}
    ok, msg, result = StudentService.update_profile(g.user_id, data)
    if not ok:
        return error(400, msg)
    return success(result, message=msg)


# ========== 能力测评 ==========

@student_bp.route('/evaluation/start', methods=['POST'])
@jwt_required_with_user()
@role_required('student')
def start_evaluation():
    """
    POST /api/student/evaluation/start
    开始能力测评：随机抽取40道题（不返回正确答案）
    """
    ok, msg, result = StudentService.start_evaluation(g.user_id)
    if not ok:
        return error(400, msg)
    return success(result, message=msg)


@student_bp.route('/evaluation/submit', methods=['POST'])
@jwt_required_with_user()
@role_required('student')
def submit_evaluation():
    """
    POST /api/student/evaluation/submit
    提交能力测评答案，返回四维度雷达图 + 薄弱点 + 建议
    Body: {
        "answers": [
            { "questionId": 1, "answer": "C", "correct": true },
            ...
        ],
        "totalTime": 1200
    }
    """
    data = request.get_json() or {}
    answers = data.get('answers', [])

    ok, msg, result = StudentService.submit_evaluation(g.user_id, answers)
    if not ok:
        return error(400, msg)
    return success(result, message=msg)


# ========== 学习方向 ==========

@student_bp.route('/study-direction', methods=['PUT'])
@jwt_required_with_user()
@role_required('student')
def update_study_direction():
    """
    PUT /api/student/study-direction
    切换学习方向
    Body: { "study_subject": 1 }  // 1=科目一/4=科目四/5=专业人员
    """
    data = request.get_json() or {}
    study_subject = data.get('study_subject', 1)
    ok, msg, result = StudentService.update_study_direction(g.user_id, study_subject)
    if not ok:
        return error(400, msg)
    return success(result, message=msg)


@student_bp.route('/evaluation/status', methods=['GET'])
@jwt_required_with_user()
@role_required('student')
def evaluation_status():
    """
    GET /api/student/evaluation/status
    查询测评状态
    """
    data = StudentService.get_evaluation_status(g.user_id)
    if data is None:
        return error(404, '学员不存在')
    return success(data)


# ========== 学习计划 ==========

@student_bp.route('/study-plan', methods=['GET'])
@jwt_required_with_user()
@role_required('student')
def get_study_plan():
    """
    GET /api/student/study-plan?direction=1
    获取学员AI学习路径（缓存版：测评不变不重调DeepSeek）
    direction: 可选，1=科目一/4=科目四/5=专业人员，不传则使用当前方向
    返回: { evaluationSummary, plan, cached, generatedAt }
    """
    direction = request.args.get('direction', type=int)
    data = StudentService.get_learning_path(g.user_id, direction=direction)
    if data is None:
        return error(404, '学员不存在')
    return success(data)


@student_bp.route('/study-plan/generate', methods=['POST'])
@jwt_required_with_user()
@role_required('student')
def generate_study_plan():
    """
    POST /api/student/study-plan/generate
    触发AI生成学习计划
    Body: { "study_subject": 4, "exam_date": "2026-07-01" } (均可选)
    study_subject: 1=科目一/4=科目四/5=专业人员，不传则使用当前方向
    """
    data = request.get_json() or {}
    exam_date = data.get('exam_date', None)
    direction = data.get('study_subject', None)

    ok, msg, result = StudentService.generate_study_plan(g.user_id, exam_date, direction=direction)
    if not ok:
        return error(400, msg)
    return success(result, message=msg)


# ========== 学习进度 ==========

@student_bp.route('/progress', methods=['GET'])
@jwt_required_with_user()
@role_required('student')
def get_progress():
    """
    GET /api/student/progress?direction=1
    direction: 可选，1/4/5，不传则使用当前方向
    """
    direction = request.args.get('direction', type=int)
    data = StudentService.get_progress(g.user_id, direction=direction)
    if data is None:
        return error(404, '学员不存在')
    return success(data)


# ========== 评估报告 ==========

@student_bp.route('/report', methods=['GET'])
@jwt_required_with_user()
@role_required('student')
def get_report():
    """
    GET /api/student/report
    获取学员评估报告（总分 + 等级 + 成长曲线 + 考试历史 + AI建议）
    Query: ?direction=1 (可选，1=科目一/4=科目四/5=专业人员)
    """
    direction = request.args.get('direction', type=int)
    data = StudentService.get_report(g.user_id, direction=direction)
    if data is None:
        return error(404, '学员不存在')
    return success(data)


# ========== 消息列表 ==========

@student_bp.route('/messages', methods=['GET'])
@jwt_required_with_user()
@role_required('student')
def get_messages():
    """
    GET /api/student/messages
    获取学员消息列表（支持分页）
    Query: ?page=1&page_size=20
    """
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 20, type=int)

    # 分页边界处理：page≤0 修正为1，page_size>100 限制为100
    if page < 1:
        page = 1
    if page_size < 1:
        page_size = 20
    if page_size > 100:
        page_size = 100

    messages, total = StudentService.get_messages(g.user_id, page, page_size)
    return paginated_response(messages, total, page, page_size)


# ========== 可选教练列表 ==========

@student_bp.route('/coaches', methods=['GET'])
@jwt_required_with_user()
@role_required('student')
def get_available_coaches():
    """
    GET /api/student/coaches
    获取可选的教练列表（用于学员发起对话时选择教练）
    """
    coaches = Coach.query.filter_by(status=1).order_by(Coach.create_time.desc()).all()
    coach_list = [c.to_dict() for c in coaches]
    return success({'list': coach_list, 'total': len(coach_list)})
