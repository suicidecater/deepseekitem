"""
Admin API蓝图 - 管理端接口

所有端点需 JWT认证 + admin角色校验。
"""
from flask import Blueprint, request, g

from app.middleware.auth import jwt_required_with_user
from app.middleware.rbac import role_required
from app.utils.response import success, error, paginated_response
from app.models.system_config import SystemConfig
from app.models.user import Student, Coach, PlatformAdmin
from app.extensions import db
import bcrypt

admin_bp = Blueprint('admin', __name__)


# ========== 系统配置管理 ==========

# 管理员可管理的配置项白名单
MANAGEABLE_CONFIG_KEYS = ['deepseek_api_key', 'qq_email_address']


@admin_bp.route('/config', methods=['GET'])
@jwt_required_with_user()
@role_required('admin')
def get_config():
    """
    GET /api/admin/config
    获取系统配置（管理员专属）
    返回所有可管理配置项的列表
    """
    configs = {}
    for key in MANAGEABLE_CONFIG_KEYS:
        value = SystemConfig.get_value(key, '')
        configs[key] = {
            'key': key,
            'value': value,
            'is_set': bool(value),
        }

    return success({
        'configs': configs,
        'editable_keys': MANAGEABLE_CONFIG_KEYS,
    })


@admin_bp.route('/config', methods=['PUT'])
@jwt_required_with_user()
@role_required('admin')
def update_config():
    """
    PUT /api/admin/config
    更新系统配置项（管理员专属）
    Body: {
        "configs": {
            "deepseek_api_key": "sk-xxx",
            "qq_email_address": "xxx@qq.com"
        }
    }
    只允许更新白名单中的配置项
    """
    data = request.get_json() or {}
    configs = data.get('configs', {})

    if not configs or not isinstance(configs, dict):
        return error(40001, '请提供有效的配置项')

    updated = []
    for key, value in configs.items():
        if key not in MANAGEABLE_CONFIG_KEYS:
            continue

        description_map = {
            'deepseek_api_key': 'DeepSeek API密钥',
            'qq_email_address': 'QQ邮箱发件地址',
        }
        SystemConfig.set_value(
            key=key,
            value=str(value) if value else '',
            description=description_map.get(key, ''),
            updated_by=g.user_id,
        )
        updated.append(key)

    if not updated:
        return error(40001, '未提供有效的配置项，可配置项: ' + ', '.join(MANAGEABLE_CONFIG_KEYS))

    return success({'updated': updated}, message='配置更新成功')


@admin_bp.route('/config/status', methods=['GET'])
@jwt_required_with_user()
@role_required('admin')
def get_config_status():
    """
    GET /api/admin/config/status
    查看配置状态：哪些配置项已填写
    返回: { configs: { key: { is_set: bool, has_value: bool } } }
    """
    status = {}
    for key in MANAGEABLE_CONFIG_KEYS:
        value = SystemConfig.get_value(key, '')
        status[key] = {
            'key': key,
            'is_set': bool(value),
            'has_value': bool(value),
        }

    # 也检查环境变量中的 fallback
    from flask import current_app
    if not status.get('deepseek_api_key', {}).get('is_set'):
        env_key = current_app.config.get('DEEPSEEK_API_KEY', '')
        if env_key:
            status['deepseek_api_key']['is_set'] = True
            status['deepseek_api_key']['source'] = 'env'

    if not status.get('qq_email_address', {}).get('is_set'):
        env_email = current_app.config.get('SMTP_USER', '')
        if env_email:
            status['qq_email_address']['is_set'] = True
            status['qq_email_address']['source'] = 'env'

    return success({
        'configs': status,
        'ai_ready': status.get('deepseek_api_key', {}).get('is_set', False),
        'email_ready': status.get('qq_email_address', {}).get('is_set', False),
    })


# ========== 驾校管理仪表盘 ==========

@admin_bp.route('/school/dashboard', methods=['GET'])
@jwt_required_with_user()
@role_required('admin')
def school_dashboard():
    """
    GET /api/admin/school/dashboard
    驾校管理仪表盘（聚合统计数据）
    """
    from app.models.user import Student
    from app.models.exam import PracticeExam

    total_students = Student.query.filter_by(status=1).count()
    avg_score = 0
    pass_rate = 0
    active_rate = 0

    # 统计平均分和通过率
    exams = PracticeExam.query.filter_by(biz_type=2, status=3).all()
    if exams:
        avg_score = round(sum(e.score for e in exams) / len(exams), 1)
        passed = sum(1 for e in exams if e.score >= 90)
        pass_rate = round((passed / len(exams)) * 100, 1) if exams else 0

    # 活跃率（有练习记录的学员占比）
    active_students = db.session.query(PracticeExam.student_id).distinct().count()
    if total_students > 0:
        active_rate = round((active_students / total_students) * 100, 1)

    return success({
        'totalStudents': total_students,
        'avgScore': avg_score,
        'passRate': pass_rate,
        'activeRate': active_rate,
    })


# ========== 运营数据仪表盘 ==========

@admin_bp.route('/operation/dashboard', methods=['GET'])
@jwt_required_with_user()
@role_required('admin')
def operation_dashboard():
    """
    GET /api/admin/operation/dashboard
    运营数据仪表盘
    """
    from app.models.user import Student, Coach
    from app.extensions import db

    total_users = Student.query.count() + Coach.query.count()
    dau = 0
    mau = 0
    retention = 0

    # Mock数据（后续接入真实统计）
    import random
    dau = random.randint(300, 600)
    mau = random.randint(1200, 2500)
    retention = random.randint(55, 75)

    return success({
        'totalUsers': total_users,
        'dau': dau,
        'mau': mau,
        'retention': retention,
    })


# ========== 驾校任务列表 ==========

@admin_bp.route('/school/tasks', methods=['GET'])
@jwt_required_with_user()
@role_required('admin')
def school_tasks():
    """
    GET /api/admin/school/tasks
    驾校管理任务列表
    """
    return success({
        'list': [
            {
                'id': 1,
                'title': '新增科目一题库',
                'assignee': '管理员A',
                'status': '进行中',
                'dueDate': '2026-06-15',
            },
            {
                'id': 2,
                'title': '审核学员注册申请',
                'assignee': '管理员B',
                'status': '待处理',
                'dueDate': '2026-06-20',
            },
        ]
    })


# ========== 人员管理（学生/教练/管理员） ==========

USER_MODELS = {
    'student': Student,
    'coach': Coach,
    'admin': PlatformAdmin,
}

USER_LABELS = {'student': '学员', 'coach': '教练', 'admin': '管理员'}

def _get_user_model(role):
    return USER_MODELS.get(role)

def _user_to_dict(u, role):
    d = {
        'id': u.id,
        'role': role,
        'email': u.email,
        'status': u.status,
    }
    if role == 'student':
        d['name'] = u.name or ''
        d['trainType'] = u.train_type
        d['carType'] = u.car_type or ''
    elif role == 'coach':
        d['name'] = u.school_name or ''
        d['trainType'] = u.train_type
        d['phone'] = u.school_phone or ''
    elif role == 'admin':
        d['adminType'] = u.admin_type
    return d


@admin_bp.route('/users/<role>', methods=['GET'])
@jwt_required_with_user()
@role_required('admin')
def get_users(role):
    """GET /api/admin/users/{role}?page=1&page_size=20&keyword=&status="""
    Model = _get_user_model(role)
    if not Model:
        return error(40001, '无效角色，可选: student/coach/admin')

    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 20, type=int)
    keyword = request.args.get('keyword', '').strip()
    status = request.args.get('status', type=int)

    if page < 1: page = 1
    if page_size < 1: page_size = 20
    if page_size > 100: page_size = 100

    query = Model.query
    if status is not None:
        query = query.filter(Model.status == status)
    if keyword:
        if role == 'student':
            query = query.filter((Model.email.contains(keyword)) | (Model.name.contains(keyword)))
        elif role == 'coach':
            query = query.filter((Model.email.contains(keyword)) | (Model.school_name.contains(keyword)))
        else:
            query = query.filter(Model.email.contains(keyword))

    query = query.order_by(Model.id.desc())

    total = query.count()
    users = query.offset((page - 1) * page_size).limit(page_size).all()

    return paginated_response(
        [_user_to_dict(u, role) for u in users],
        total, page, page_size,
    )


@admin_bp.route('/users/<role>/<int:user_id>', methods=['GET'])
@jwt_required_with_user()
@role_required('admin')
def get_user_detail(role, user_id):
    """GET /api/admin/users/{role}/{id}"""
    Model = _get_user_model(role)
    if not Model:
        return error(40001, '无效角色')
    user = Model.query.get(user_id)
    if not user:
        return error(404, '用户不存在')
    return success(_user_to_dict(user, role))


@admin_bp.route('/users/<role>', methods=['POST'])
@jwt_required_with_user()
@role_required('admin')
def create_user(role):
    """POST /api/admin/users/{role}"""
    Model = _get_user_model(role)
    if not Model:
        return error(40001, '无效角色')

    data = request.get_json() or {}
    email = (data.get('email') or '').strip()
    password = (data.get('password') or '').strip()

    if not email or not password:
        return error(40001, '邮箱和密码不能为空')

    if Model.query.filter_by(email=email).first():
        return error(40001, f'该邮箱已注册{USER_LABELS.get(role, "")}账号')

    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    if role == 'student':
        user = Student(email=email, password=hashed,
                       name=data.get('name', ''), train_type=data.get('trainType', 1),
                       car_type=data.get('carType', ''), status=data.get('status', 1))
    elif role == 'coach':
        user = Coach(email=email, password=hashed,
                     school_name=data.get('name', ''),
                     school_phone=data.get('phone', ''),
                     train_type=data.get('trainType', 1),
                     status=data.get('status', 1))
    elif role == 'admin':
        user = PlatformAdmin(email=email, password=hashed,
                             admin_type=data.get('adminType', 2),
                             status=data.get('status', 1))

    user.save()
    return success(_user_to_dict(user, role), message='创建成功')


@admin_bp.route('/users/<role>/<int:user_id>', methods=['PUT'])
@jwt_required_with_user()
@role_required('admin')
def update_user(role, user_id):
    """PUT /api/admin/users/{role}/{id}"""
    Model = _get_user_model(role)
    if not Model:
        return error(40001, '无效角色')

    user = Model.query.get(user_id)
    if not user:
        return error(404, '用户不存在')

    data = request.get_json() or {}

    if 'email' in data:
        email = data['email'].strip()
        if email != user.email:
            if Model.query.filter_by(email=email).first():
                return error(40001, '该邮箱已被使用')
            user.email = email
    if 'password' in data and data['password']:
        user.password = bcrypt.hashpw(data['password'].encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    if 'status' in data:
        user.status = data['status']

    if role == 'student':
        if 'name' in data: user.name = data['name']
        if 'trainType' in data: user.train_type = data['trainType']
        if 'carType' in data: user.car_type = data['carType']
    elif role == 'coach':
        if 'name' in data: user.school_name = data['name']
        if 'phone' in data: user.school_phone = data['phone']
        if 'trainType' in data: user.train_type = data['trainType']
    elif role == 'admin':
        if 'adminType' in data: user.admin_type = data['adminType']

    user.save()
    return success(_user_to_dict(user, role), message='更新成功')


@admin_bp.route('/users/<role>/<int:user_id>', methods=['DELETE'])
@jwt_required_with_user()
@role_required('admin')
def delete_user(role, user_id):
    """DELETE /api/admin/users/{role}/{id}"""
    Model = _get_user_model(role)
    if not Model:
        return error(40001, '无效角色')

    user = Model.query.get(user_id)
    if not user:
        return error(404, '用户不存在')

    user.delete()
    return success(message='删除成功')
