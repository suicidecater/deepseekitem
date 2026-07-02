"""
Coach API蓝图 - 教练端接口

所有端点需 JWT认证 + coach角色校验。
"""
from datetime import datetime, timedelta
from io import BytesIO
import json

from flask import Blueprint, request, g, send_file

from app.extensions import db
from app.middleware.auth import jwt_required_with_user
from app.middleware.rbac import role_required
from app.utils.response import success, error
from app.models.user import Student
from app.models.exam import PracticeExam, Evaluation
from app.models.question import QuestionRecord, ErrorQuestion, SpecialTrainingSession

coach_bp = Blueprint('coach', __name__)


# ======================== 辅助函数 ========================

def _get_coach_student_ids(coach_id):
    """获取当前教练名下所有学员ID列表"""
    students = Student.query.filter_by(coach_id=coach_id).all()
    return [s.id for s in students], students


def _get_student_comprehensive_score(student_id):
    """从最近测评获取学员综合得分（雷达图四维度加权总分）"""
    latest_eval = Evaluation.query.filter_by(student_id=student_id)\
        .order_by(Evaluation.create_time.desc()).first()
    if latest_eval and latest_eval.total_score:
        return float(latest_eval.total_score)
    return 0.0


def _get_student_accuracy(student_id):
    """获取学员刷题总正确率（考试recoed平均值）"""
    from sqlalchemy import func
    result = db.session.query(
        func.avg(PracticeExam.correct_rate)
    ).filter(
        PracticeExam.student_id == student_id,
        PracticeExam.biz_type == 2,
        PracticeExam.status == 3,
    ).scalar()
    return round(float(result or 0), 1)


def _get_student_study_days(student_id):
    """统计学员有答题记录的不同日期数"""
    from sqlalchemy import func
    result = db.session.query(
        func.count(func.distinct(func.date(QuestionRecord.answer_time)))
    ).filter(
        QuestionRecord.student_id == student_id
    ).scalar()
    return result or 0


def _get_student_last_active(student_id):
    """获取学员最近活跃时间"""
    latest_record = QuestionRecord.query.filter_by(student_id=student_id)\
        .order_by(QuestionRecord.answer_time.desc()).first()
    if latest_record and latest_record.answer_time:
        return latest_record.answer_time
    student = Student.query.get(student_id)
    return student.update_time if student else None


def _build_student_item(s, include_computed=True):
    """构建学员列表项"""
    item = {
        'id': s.id,
        'name': s.name or '学员',
        'email': s.email or '',
        'carType': (s.car_type or 'C1') + ' 小型汽车',
        'status': s.status,
    }
    if include_computed:
        item['score'] = _get_student_comprehensive_score(s.id)
        item['accuracy'] = _get_student_accuracy(s.id)
        item['studyDays'] = _get_student_study_days(s.id)
        last_active = _get_student_last_active(s.id)
        item['lastActive'] = last_active.strftime('%Y-%m-%d %H:%M') if last_active else ''
    return item


def _get_student_trend(student_id):
    """获取学员近30天每日正确率趋势"""
    from sqlalchemy import func
    trend = []
    for i in range(29, -1, -1):
        day = datetime.now() - timedelta(days=i)
        day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)
        records = QuestionRecord.query.filter(
            QuestionRecord.student_id == student_id,
            QuestionRecord.answer_time >= day_start,
            QuestionRecord.answer_time < day_end,
        ).all()
        total_q = len(records)
        correct_q = sum(1 for r in records if r.is_correct)
        accuracy = round(correct_q / total_q * 100, 1) if total_q > 0 else 0
        trend.append({
            'date': day.strftime('%m-%d'),
            'accuracy': accuracy,
            'count': total_q,
        })
    return trend


# ======================== 统计接口 ========================

@coach_bp.route('/student-stat', methods=['GET'])
@jwt_required_with_user()
@role_required('coach')
def student_stat():
    """
    GET /api/coach/student-stat
    返回：总学员、近7天活跃、综合平均分、平均正确率、待辅导学员、未完成考试、错题总量、薄弱题型TOP1
    """
    student_ids, all_students = _get_coach_student_ids(g.user_id)
    total_count = len(all_students)

    # 近7天活跃学员（有答题记录）
    seven_days_ago = datetime.now() - timedelta(days=7)
    three_days_ago = datetime.now() - timedelta(days=3)
    active_ids_set = set()
    if student_ids:
        from sqlalchemy import func
        rows = db.session.query(
            func.distinct(QuestionRecord.student_id)
        ).filter(
            QuestionRecord.student_id.in_(student_ids),
            QuestionRecord.answer_time >= seven_days_ago,
        ).all()
        active_ids_set = {r[0] for r in rows}
    active_count = len(active_ids_set)

    # 学员综合平均分（从Evaluation表）
    avg_score = 0.0
    if student_ids:
        from sqlalchemy import func
        result = db.session.query(
            func.avg(Evaluation.total_score)
        ).filter(
            Evaluation.student_id.in_(student_ids)
        ).scalar()
        avg_score = round(float(result or 0), 1)

    # 全员平均刷题正确率
    avg_accuracy = 0.0
    if student_ids:
        from sqlalchemy import func
        result = db.session.query(
            func.avg(PracticeExam.correct_rate)
        ).filter(
            PracticeExam.student_id.in_(student_ids),
            PracticeExam.biz_type == 2,
            PracticeExam.status == 3,
        ).scalar()
        avg_accuracy = round(float(result or 0), 1)

    # ---- 新增指标 ----
    # 待辅导学员：近3天无刷题 且 正确率<60
    pending_tutor_count = 0
    unfinished_exam_count = 0
    total_errors = 0
    top_weak_dimension = '暂无'

    if student_ids:
        from sqlalchemy import func
        # 活跃学员ID
        recent_active_rows = db.session.query(
            func.distinct(QuestionRecord.student_id)
        ).filter(
            QuestionRecord.student_id.in_(student_ids),
            QuestionRecord.answer_time >= three_days_ago,
        ).all()
        recent_active_set = {r[0] for r in recent_active_rows}

        # 总错题量
        error_result = db.session.query(
            func.count(ErrorQuestion.id)
        ).filter(
            ErrorQuestion.student_id.in_(student_ids)
        ).scalar()
        total_errors = error_result or 0

        # 未完成考试（分配了模考但未交卷）
        unfinished = PracticeExam.query.filter(
            PracticeExam.student_id.in_(student_ids),
            PracticeExam.biz_type == 2,
            PracticeExam.status.in_([0, 1]),
        ).count()
        unfinished_exam_count = unfinished

        # 待辅导学员统计
        for s in all_students:
            if s.id not in recent_active_set:
                acc = _get_student_accuracy(s.id)
                if acc < 60:
                    pending_tutor_count += 1

        # 薄弱题型 TOP1：统计所有学员错误最多的维度
        dim_count = {'交通标志': 0, '交通法规': 0, '安全常识': 0, '驾驶理论': 0}
        evals = Evaluation.query.filter(
            Evaluation.student_id.in_(student_ids)
        ).all()
        for ev in evals:
            scores = {
                '交通标志': ev.sign_score or 0,
                '交通法规': ev.law_score or 0,
                '安全常识': ev.safe_score or 0,
                '驾驶理论': ev.drive_score or 0,
            }
            min_dim = min(scores, key=scores.get)
            dim_count[min_dim] = dim_count.get(min_dim, 0) + 1
        if dim_count:
            top_weak_dimension = max(dim_count, key=dim_count.get)

    return success({
        'total': total_count,
        'active': active_count,
        'avgScore': avg_score,
        'avgAccuracy': avg_accuracy,
        'pendingTutorCount': pending_tutor_count,
        'unfinishedExamCount': unfinished_exam_count,
        'totalErrors': total_errors,
        'topWeakDimension': top_weak_dimension,
    })


# ======================== 学员列表分页接口 ========================

@coach_bp.route('/student-list', methods=['GET'])
@jwt_required_with_user()
@role_required('coach')
def student_list():
    """
    GET /api/coach/student-list
    学员列表分页接口
    Query: ?page=1&page_size=20&keyword=&car_type=&accuracy_range=&active_days=&pending_only=
    返回字段：姓名、邮箱、车型、综合得分、正确率、学习天数、最近活跃、薄弱维度、待处理提醒
    """
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 20, type=int)
    keyword = request.args.get('keyword', '').strip()
    car_type = request.args.get('car_type', '').strip()
    accuracy_range = request.args.get('accuracy_range', '').strip()
    active_days = request.args.get('active_days', type=int, default=0)
    pending_only = request.args.get('pending_only', '').strip()

    if page < 1:
        page = 1
    if page_size < 1:
        page_size = 20
    if page_size > 100:
        page_size = 100

    query = Student.query.filter_by(coach_id=g.user_id)

    if keyword:
        query = query.filter(
            db.or_(
                Student.name.like(f'%{keyword}%'),
                Student.email.like(f'%{keyword}%'),
            )
        )

    if car_type:
        query = query.filter(Student.car_type.like(f'%{car_type}%'))

    query = query.order_by(Student.create_time.desc())

    total = query.count()
    all_students = query.all()

    # 筛选：正确率区间、活跃天数、待辅导
    three_days_ago = datetime.now() - timedelta(days=3)
    student_ids = [s.id for s in all_students]
    from sqlalchemy import func

    if active_days > 0:
        active_since = datetime.now() - timedelta(days=active_days)
        active_rows = db.session.query(
            func.distinct(QuestionRecord.student_id)
        ).filter(
            QuestionRecord.student_id.in_(student_ids),
            QuestionRecord.answer_time >= active_since,
        ).all()
        active_set = {r[0] for r in active_rows}
        all_students = [s for s in all_students if s.id in active_set]

    if accuracy_range or pending_only:
        filtered = []
        for s in all_students:
            acc = _get_student_accuracy(s.id)
            if accuracy_range:
                if accuracy_range == '0-60' and acc >= 60:
                    continue
                if accuracy_range == '60-80' and (acc < 60 or acc >= 80):
                    continue
                if accuracy_range == '80-100' and acc < 80:
                    continue

            if pending_only == '1':
                recent = QuestionRecord.query.filter(
                    QuestionRecord.student_id == s.id,
                    QuestionRecord.answer_time >= three_days_ago,
                ).first()
                # 待辅导：近3天未刷题 或 正确率<60%
                is_pending = (recent is None) or (acc < 60)
                if not is_pending:
                    continue
            filtered.append(s)
        all_students = filtered

    # 分页
    total_filtered = len(all_students)
    start = (page - 1) * page_size
    paged = all_students[start:start + page_size]

    # 构建列表项（含新增字段）
    # three_days_ago 已在上面定义
    student_list_data = []
    for s in paged:
        item = _build_student_item(s, include_computed=True)
        # 薄弱维度
        latest_eval = Evaluation.query.filter_by(student_id=s.id)\
            .order_by(Evaluation.create_time.desc()).first()
        dim_map = {
            '交通标志': latest_eval.sign_score or 0,
            '交通法规': latest_eval.law_score or 0,
            '安全常识': latest_eval.safe_score or 0,
            '驾驶理论': latest_eval.drive_score or 0,
        } if latest_eval else {
            '交通标志': 0, '交通法规': 0, '安全常识': 0, '驾驶理论': 0,
        }
        min_dim = min(dim_map, key=dim_map.get)
        item['weakDimension'] = min_dim
        item['weakDimensionScore'] = dim_map[min_dim]

        # 待处理提醒标签
        tags = []
        acc = item.get('accuracy', 0)
        recent = QuestionRecord.query.filter(
            QuestionRecord.student_id == s.id,
            QuestionRecord.answer_time >= three_days_ago,
        ).first()
        if not recent and acc < 60:
            tags.append('待辅导')
        unfin_exam = PracticeExam.query.filter(
            PracticeExam.student_id == s.id,
            PracticeExam.biz_type == 2,
            PracticeExam.status.in_([0, 1]),
        ).first()
        if unfin_exam:
            tags.append('未交卷')
        item['pendingTags'] = tags

        student_list_data.append(item)

    return success({
        'list': student_list_data,
        'pagination': {
            'total': total_filtered,
            'page': page,
            'page_size': page_size,
        },
    })


# ======================== Excel导出接口 ========================

@coach_bp.route('/export-student', methods=['GET'])
@jwt_required_with_user()
@role_required('coach')
def export_student():
    """
    GET /api/coach/export-student
    Excel导出：姓名、邮箱、车型、综合得分、正确率(%)、学习天数、最近活跃
    Query: ?keyword=（可选筛选）
    """
    keyword = request.args.get('keyword', '').strip()

    query = Student.query.filter_by(coach_id=g.user_id)
    if keyword:
        query = query.filter(
            db.or_(
                Student.name.like(f'%{keyword}%'),
                Student.email.like(f'%{keyword}%'),
            )
        )
    students = query.order_by(Student.create_time.desc()).all()

    try:
        from openpyxl import Workbook
        from openpyxl.styles import Font, Alignment, Border, Side, PatternFill

        wb = Workbook()
        ws = wb.active
        ws.title = '学情管理'

        # 表头样式
        header_font = Font(name='微软雅黑', bold=True, size=11, color='FFFFFF')
        header_fill = PatternFill(start_color='1677FF', end_color='1677FF', fill_type='solid')
        header_alignment = Alignment(horizontal='center', vertical='center')
        thin_border = Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin'),
        )

        headers = ['姓名', '邮箱', '车型', '综合得分', '正确率(%)', '学习天数', '最近活跃']
        for col_idx, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col_idx, value=header)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = header_alignment
            cell.border = thin_border

        # 数据行
        data_font = Font(name='微软雅黑', size=10)
        data_alignment = Alignment(horizontal='center', vertical='center')

        for row_idx, s in enumerate(students, 2):
            item = _build_student_item(s)
            row_data = [
                item['name'],
                item['email'],
                item['carType'],
                item['score'],
                item['accuracy'],
                item['studyDays'],
                item['lastActive'],
            ]
            for col_idx, value in enumerate(row_data, 1):
                cell = ws.cell(row=row_idx, column=col_idx, value=value)
                cell.font = data_font
                cell.alignment = data_alignment
                cell.border = thin_border

        # 列宽自适应
        col_widths = [12, 28, 14, 10, 12, 10, 18]
        for idx, width in enumerate(col_widths, 1):
            ws.column_dimensions[ws.cell(row=1, column=idx).column_letter].width = width

        # 输出到内存
        output = BytesIO()
        wb.save(output)
        output.seek(0)

        filename = f'学情管理_{datetime.now().strftime("%Y%m%d%H%M%S")}.xlsx'
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=filename,
        )
    except ImportError:
        return error(500, 'Excel导出依赖未安装，请安装openpyxl: pip install openpyxl')


# ======================== 学员详情 ========================

@coach_bp.route('/students/<int:student_id>', methods=['GET'])
@jwt_required_with_user()
@role_required('coach')
def get_student_detail(student_id):
    """
    GET /api/coach/students/{id}
    获取学员详情（含能力雷达图四维度得分、薄弱知识点、模考记录）
    """
    student = Student.query.filter_by(id=student_id, coach_id=g.user_id).first()
    if not student:
        return error(404, '学员不存在或不属于当前教练')

    # 考试历史
    exams = PracticeExam.query.filter_by(
        student_id=student_id, biz_type=2, status=3
    ).order_by(PracticeExam.create_time.desc()).limit(10).all()
    exam_history = [e.to_dict() for e in exams]

    # 最新测评 – 四维度得分
    latest_eval = Evaluation.query.filter_by(student_id=student_id)\
        .order_by(Evaluation.create_time.desc()).first()

    dimensions = []
    weak_points = []
    if latest_eval:
        dimensions = [
            {'name': '交通标志', 'score': latest_eval.sign_score or 0},
            {'name': '交通法规', 'score': latest_eval.law_score or 0},
            {'name': '安全常识', 'score': latest_eval.safe_score or 0},
            {'name': '驾驶理论', 'score': latest_eval.drive_score or 0},
        ]
        if latest_eval.weak_know:
            import json
            try:
                weak_points = json.loads(latest_eval.weak_know)
            except (json.JSONDecodeError, TypeError):
                pass

    return success({
        'student': student.to_dict(),
        'dimensions': dimensions,
        'examHistory': exam_history,
        'weakPoints': weak_points,
        'latestEvaluation': latest_eval.to_dict() if latest_eval else None,
        # 新增：总练习次数（专项训练提交次数）
        'totalPracticeCount': SpecialTrainingSession.query.filter_by(student_id=student_id).count(),
        # 新增：总错题数
        'totalErrorCount': ErrorQuestion.query.filter_by(student_id=student_id).count(),
        # 新增：近30天正确率趋势（每日正确率）
        'trendData': _get_student_trend(student_id),
    })


# ======================== 全局分析图表数据 ========================

@coach_bp.route('/student-analytics', methods=['GET'])
@jwt_required_with_user()
@role_required('coach')
def student_analytics():
    """
    GET /api/coach/student-analytics
    返回全局分析图表数据：
    - 近30天活跃趋势（每天刷题人数）
    - 四维能力平均得分
    - 正确率分层分布（0-60 / 60-80 / 80-100）
    """
    student_ids, all_students = _get_coach_student_ids(g.user_id)
    from sqlalchemy import func

    # 近30天活跃趋势
    active_trend = []
    for i in range(29, -1, -1):
        day = datetime.now() - timedelta(days=i)
        day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)
        count = 0
        if student_ids:
            count = db.session.query(
                func.count(func.distinct(QuestionRecord.student_id))
            ).filter(
                QuestionRecord.student_id.in_(student_ids),
                QuestionRecord.answer_time >= day_start,
                QuestionRecord.answer_time < day_end,
            ).scalar() or 0
        active_trend.append({
            'date': day.strftime('%m-%d'),
            'count': count,
        })

    # 四维能力平均得分
    dimension_avg = []
    if student_ids:
        result = db.session.query(
            func.avg(Evaluation.sign_score),
            func.avg(Evaluation.law_score),
            func.avg(Evaluation.safe_score),
            func.avg(Evaluation.drive_score),
        ).filter(
            Evaluation.student_id.in_(student_ids)
        ).first()
        if result:
            dimension_avg = [
                {'name': '交通标志', 'score': round(float(result[0] or 0), 1)},
                {'name': '交通法规', 'score': round(float(result[1] or 0), 1)},
                {'name': '安全常识', 'score': round(float(result[2] or 0), 1)},
                {'name': '驾驶理论', 'score': round(float(result[3] or 0), 1)},
            ]

    # 正确率分层分布
    distribution = {'0-60': 0, '60-80': 0, '80-100': 0}
    for s in all_students:
        acc = _get_student_accuracy(s.id)
        if acc < 60:
            distribution['0-60'] += 1
        elif acc < 80:
            distribution['60-80'] += 1
        else:
            distribution['80-100'] += 1

    accuracy_distribution = [
        {'range': '0-60分', 'count': distribution['0-60']},
        {'range': '60-80分', 'count': distribution['60-80']},
        {'range': '80-100分', 'count': distribution['80-100']},
    ]

    return success({
        'activeTrend': active_trend,
        'dimensionAvg': dimension_avg,
        'accuracyDistribution': accuracy_distribution,
    })


# ======================== 待辅导学员列表 ========================

@coach_bp.route('/pending-coaching', methods=['GET'])
@jwt_required_with_user()
@role_required('coach')
def pending_coaching():
    """
    GET /api/coach/pending-coaching
    获取待辅导学员列表：正确率<60% 或 近3天未刷题
    """
    student_ids, all_students = _get_coach_student_ids(g.user_id)
    three_days_ago = datetime.now() - timedelta(days=3)
    from sqlalchemy import func

    recent_active_rows = db.session.query(
        func.distinct(QuestionRecord.student_id)
    ).filter(
        QuestionRecord.student_id.in_(student_ids),
        QuestionRecord.answer_time >= three_days_ago,
    ).all()
    recent_active_set = {r[0] for r in recent_active_rows}

    pending_list = []
    for s in all_students:
        acc = _get_student_accuracy(s.id)
        is_inactive = s.id not in recent_active_set
        reason = ''
        if is_inactive and acc < 60:
            reason = '长期未刷题且正确率低'
        elif is_inactive:
            reason = '近3天未刷题'
        elif acc < 60:
            reason = '正确率过低（<60%）'
        else:
            continue

        # 薄弱维度
        weak_dim = '暂无'
        latest_eval = Evaluation.query.filter_by(student_id=s.id)\
            .order_by(Evaluation.create_time.desc()).first()
        if latest_eval:
            dim_map = {
                '交通标志': latest_eval.sign_score or 0,
                '交通法规': latest_eval.law_score or 0,
                '安全常识': latest_eval.safe_score or 0,
                '驾驶理论': latest_eval.drive_score or 0,
            }
            weak_dim = min(dim_map, key=dim_map.get)

        last_active = _get_student_last_active(s.id)
        days_since = 0
        if last_active:
            days_since = (datetime.now() - last_active).days

        pending_list.append({
            'id': s.id,
            'name': s.name or '学员',
            'email': s.email or '',
            'carType': (s.car_type or 'C1'),
            'weakDimension': weak_dim,
            'accuracy': acc,
            'lastActive': last_active.strftime('%Y-%m-%d %H:%M') if last_active else '',
            'daysSinceActive': days_since,
            'reason': reason,
        })

    return success(pending_list)


# ======================== 单学员导出 ========================

@coach_bp.route('/export-student/<int:student_id>', methods=['GET'])
@jwt_required_with_user()
@role_required('coach')
def export_single_student(student_id):
    """
    GET /api/coach/export-student/<id>
    导出单个学员完整学情Excel（含个人刷题记录、考试记录、错题明细）
    """
    student = Student.query.filter_by(id=student_id, coach_id=g.user_id).first()
    if not student:
        return error(404, '学员不存在或不属于当前教练')

    try:
        from openpyxl import Workbook
        from openpyxl.styles import Font, Alignment, Border, Side, PatternFill

        wb = Workbook()
        header_font = Font(name='微软雅黑', bold=True, size=11, color='FFFFFF')
        header_fill = PatternFill(start_color='1677FF', end_color='1677FF', fill_type='solid')
        center_align = Alignment(horizontal='center', vertical='center')
        thin_border = Border(
            left=Side(style='thin'), right=Side(style='thin'),
            top=Side(style='thin'), bottom=Side(style='thin'),
        )
        data_font = Font(name='微软雅黑', size=10)

        def style_header(ws, headers, row=1):
            for col, h in enumerate(headers, 1):
                cell = ws.cell(row=row, column=col, value=h)
                cell.font = header_font
                cell.fill = header_fill
                cell.alignment = center_align
                cell.border = thin_border

        def style_row(ws, row, values):
            for col, v in enumerate(values, 1):
                cell = ws.cell(row=row, column=col, value=v)
                cell.font = data_font
                cell.alignment = center_align
                cell.border = thin_border

        # Sheet1: 基本信息
        ws1 = wb.active
        ws1.title = '基本信息'
        basic = _build_student_item(student)
        headers1 = ['姓名', '邮箱', '车型', '综合得分', '正确率(%)', '学习天数', '最近活跃']
        style_header(ws1, headers1)
        style_row(ws1, 2, [basic[k] for k in ['name', 'email', 'carType', 'score', 'accuracy', 'studyDays', 'lastActive']])

        # 四维度
        latest_eval = Evaluation.query.filter_by(student_id=student_id)\
            .order_by(Evaluation.create_time.desc()).first()
        dim_row = 4
        ws1.cell(row=dim_row, column=1, value='四维能力').font = header_font
        dim_headers = ['交通标志', '交通法规', '安全常识', '驾驶理论']
        if latest_eval:
            for col, name in enumerate(dim_headers, 2):
                ws1.cell(row=dim_row, column=col, value=name).font = header_font
            scores = [latest_eval.sign_score, latest_eval.law_score, latest_eval.safe_score, latest_eval.drive_score]
            for col, s in enumerate(scores, 2):
                ws1.cell(row=dim_row+1, column=col, value=s).font = data_font

        # Sheet2: 考试记录
        ws2 = wb.create_sheet('考试记录')
        exams = PracticeExam.query.filter_by(
            student_id=student_id, biz_type=2, status=3
        ).order_by(PracticeExam.create_time.desc()).all()
        headers2 = ['时间', '得分', '正确率(%)', '科目', '用时(分钟)']
        style_header(ws2, headers2)
        subject_map = {1: '科一', 4: '科四'}
        for i, e in enumerate(exams, 2):
            style_row(ws2, i, [
                e.create_time.strftime('%Y-%m-%d %H:%M') if e.create_time else '',
                e.score or 0,
                float(e.correct_rate or 0),
                subject_map.get(e.subject, f'科目{e.subject}') if e.subject else '',
                round((e.total_time or 0) / 60, 1),
            ])

        # Sheet3: 错题明细
        ws3 = wb.create_sheet('错题明细')
        errors = ErrorQuestion.query.filter_by(student_id=student_id)\
            .order_by(ErrorQuestion.create_time.desc()).limit(200).all()
        headers3 = ['时间', '题库来源', '题目ID', '错因类型', '错误次数']
        style_header(ws3, headers3)
        error_type_map = {1: '概念不清', 2: '审题失误', 3: '混淆记忆', 4: '其他'}
        for i, err in enumerate(errors, 2):
            style_row(ws3, i, [
                err.create_time.strftime('%Y-%m-%d %H:%M') if err.create_time else '',
                err.source or '',
                err.question_id or '',
                error_type_map.get(err.error_type, '其他') if err.error_type else '',
                err.error_count or 0,
            ])

        output = BytesIO()
        wb.save(output)
        output.seek(0)

        filename = f'{student.name or "学员"}_学情报告_{datetime.now().strftime("%Y%m%d")}.xlsx'
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=filename,
        )
    except ImportError:
        return error(500, 'Excel导出依赖未安装，请安装openpyxl')


# ======================== AI辅导建议 ========================

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
