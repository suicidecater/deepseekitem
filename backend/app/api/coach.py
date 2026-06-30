"""
Coach API蓝图 - 教练端接口

所有端点需 JWT认证 + coach角色校验。
"""
from flask import Blueprint, request, g

from app.middleware.auth import jwt_required_with_user
from app.middleware.rbac import role_required
from app.utils.response import success, error, paginated_response
from app.models.user import Student
from app.models.exam import PracticeExam

coach_bp = Blueprint('coach', __name__)


# ========== 学员列表 ==========

@coach_bp.route('/students', methods=['GET'])
@jwt_required_with_user()
@role_required('coach')
def get_students():
    """
    GET /api/coach/students
    获取教练名下学员列表
    Query: ?page=1&page_size=20&keyword=&status=
    """
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 20, type=int)
    keyword = request.args.get('keyword', '').strip()
    status = request.args.get('status', type=int)

    if page < 1:
        page = 1
    if page_size < 1:
        page_size = 20
    if page_size > 100:
        page_size = 100

    query = Student.query.filter_by(coach_id=g.user_id)

    if status is not None:
        query = query.filter_by(status=status)
    if keyword:
        query = query.filter(
            db.or_(
                Student.name.like(f'%{keyword}%'),
                Student.email.like(f'%{keyword}%'),
                Student.phone.like(f'%{keyword}%'),
            )
        )

    query = query.order_by(Student.create_time.desc())

    total = query.count()
    students = query.offset((page - 1) * page_size).limit(page_size).all()

    # 统计数据
    all_students = Student.query.filter_by(coach_id=g.user_id).all()
    total_count = len(all_students)
    active_count = sum(1 for s in all_students if s.status == 1)

    # 平均分和正确率
    student_ids = [s.id for s in all_students]
    if student_ids:
        from sqlalchemy import func
        avg_stats = db.session.query(
            func.avg(PracticeExam.score).label('avg_score'),
            func.avg(PracticeExam.correct_rate).label('avg_accuracy'),
        ).filter(
            PracticeExam.student_id.in_(student_ids),
            PracticeExam.biz_type == 2,
            PracticeExam.status == 3,
        ).first()
        avg_score = round(float(avg_stats.avg_score or 0), 1)
        avg_accuracy = round(float(avg_stats.avg_accuracy or 0), 1)
    else:
        avg_score = 0
        avg_accuracy = 0

    student_list = []
    for s in students:
        phone = s.phone or ''
        if phone and len(phone) >= 11:
            phone = phone[:3] + '****' + phone[-4:]

        # 最近练习统计
        latest_practice = PracticeExam.query.filter_by(
            student_id=s.id, biz_type=2, status=3
        ).order_by(PracticeExam.create_time.desc()).first()

        student_list.append({
            'id': s.id,
            'name': s.name or '学员',
            'phone': phone,
            'carType': (s.car_type or 'C1') + ' 小型汽车',
            'score': latest_practice.score if latest_practice else 0,
            'accuracy': float(latest_practice.correct_rate) if latest_practice else 0,
            'studyDays': 0,  # TODO: 统计学习天数
            'lastActive': s.update_time.strftime('%Y-%m-%d') if s.update_time else '',
            'status': s.status,
        })

    return success({
        'stats': {
            'total': total_count,
            'active': active_count,
            'avgScore': avg_score,
            'avgAccuracy': avg_accuracy,
        },
        'list': student_list,
        'pagination': {
            'total': total,
            'page': page,
            'page_size': page_size,
        },
    })


# ========== 学员详情 ==========

@coach_bp.route('/students/<int:student_id>', methods=['GET'])
@jwt_required_with_user()
@role_required('coach')
def get_student_detail(student_id):
    """
    GET /api/coach/students/{id}
    获取学员详情
    """
    student = Student.query.filter_by(id=student_id, coach_id=g.user_id).first()
    if not student:
        return error(404, '学员不存在或不属于当前教练')

    # 考试历史
    exams = PracticeExam.query.filter_by(
        student_id=student_id, biz_type=2, status=3
    ).order_by(PracticeExam.create_time.desc()).limit(10).all()

    exam_history = [e.to_dict() for e in exams]

    # 薄弱知识点（从最近测评获取）
    from app.models.exam import Evaluation
    latest_eval = Evaluation.query.filter_by(student_id=student_id)\
        .order_by(Evaluation.create_time.desc()).first()

    weak_points = []
    if latest_eval and latest_eval.weak_know:
        try:
            weak_points = json.loads(latest_eval.weak_know)
        except (json.JSONDecodeError, TypeError):
            pass

    return success({
        'student': student.to_dict(),
        'examHistory': exam_history,
        'weakPoints': weak_points,
        'latestEvaluation': latest_eval.to_dict() if latest_eval else None,
    })


# ========== AI辅导建议 ==========

@coach_bp.route('/ai-advice', methods=['GET'])
@jwt_required_with_user()
@role_required('coach')
def get_ai_advice():
    """
    GET /api/coach/ai-advice
    获取AI辅导建议（基于学员整体学情）
    Query: ?student_id=1 (可选，指定学员)
    """
    student_id = request.args.get('student_id', type=int)

    # Mock AI辅导建议
    return success({
        'weaknesses': ['驾驶理论薄弱', '扣分标准混淆'],
        'aiSuggestions': [
            {'type': '重点', 'content': '本周重点攻克驾驶理论，尤其是交通法规中的扣分标准'},
            {'type': '方法', 'content': '使用对比记忆法，将相似扣分项进行对比学习'},
            {'type': '方案', 'content': '制定5天专项辅导计划，每天45分钟理论+15道练习题'},
        ],
        'plan': [
            {'day': '第1天', 'task': '驾驶理论精讲：扣分标准梳理', 'duration': '45分钟'},
            {'day': '第2天', 'task': '理论精讲续：罚款金额对比', 'duration': '45分钟'},
            {'day': '第3天', 'task': '专项练习：扣分罚款50题', 'duration': '30分钟'},
            {'day': '第4天', 'task': '错题回顾+知识点强化', 'duration': '45分钟'},
            {'day': '第5天', 'task': '模拟考试+薄弱点分析', 'duration': '60分钟'},
        ],
    })


from app.extensions import db
import json
