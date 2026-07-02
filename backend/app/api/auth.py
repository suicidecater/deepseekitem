"""
Auth API蓝图 - 认证相关接口

三种用户分开注册/登录（仅邮箱）：
- 学员: /api/auth/student/register, /api/auth/student/login
- 教练: /api/auth/coach/register, /api/auth/coach/login
- 管理员: /api/auth/admin/register, /api/auth/admin/login
- 兼容旧接口: /api/auth/register, /api/auth/login
"""
from flask import Blueprint, request, g
from flask_jwt_extended import (
    jwt_required, get_jwt_identity, get_jwt,
    create_access_token
)
import json

from app.services.auth_service import AuthService
from app.middleware.auth import jwt_required_with_user
from app.utils.response import success, error
from app.utils.validators import validate_email

auth_bp = Blueprint('auth', __name__)


# ========== 发送验证码 ==========

@auth_bp.route('/send-code', methods=['POST'])
def send_code():
    """
    POST /api/auth/send-code
    发送邮箱验证码（Redis存储5分钟 + 60秒限频）
    Body: { "email": "xxx@qq.com", "type": "register" }
    """
    data = request.get_json() or {}
    # 兼容 account 和 email 两种传参方式
    email = (data.get('email') or data.get('account') or '').strip()
    code_type = data.get('type', 'register')

    if not email:
        return error(40001, '邮箱不能为空')
    if not validate_email(email):
        return error(40001, '邮箱格式不正确')

    ok, msg = AuthService.send_verify_code(email, code_type)
    if not ok:
        if '频繁' in msg or '秒后再试' in msg:
            return error(42900, msg)
        return error(40001, msg)

    return success(message=msg)


# ============================================================
# 学员 - 注册/登录
# ============================================================

@auth_bp.route('/student/register', methods=['POST'])
def student_register():
    """
    POST /api/auth/student/register
    学员注册
    Body: {
        "email": "xxx@qq.com",
        "password": "abc123",
        "name": "张三",
        "trainType": 1,      // 1驾考/2客运/3货运/4危险品
        "carType": "C1",     // 可选：C1/C2/A1/A2
        "code": "123456"
    }
    """
    data = request.get_json() or {}
    email = (data.get('email') or '').strip()
    password = data.get('password', '')
    name = (data.get('name') or '').strip()
    train_type = data.get('trainType', 1)
    car_type = data.get('carType') or None
    code = data.get('code')

    if not email or not password:
        return error(40001, '邮箱和密码不能为空')

    ok, msg, result = AuthService.register_student(
        email, password, name, train_type, car_type, code
    )
    if not ok:
        return error(40001, msg)

    return success(result, message=msg)


@auth_bp.route('/student/login', methods=['POST'])
def student_login():
    """
    POST /api/auth/student/login
    学员登录（密码或验证码）
    Body: {
        "email": "xxx@qq.com",
        "password": "abc123",   // 密码登录
        "code": "123456"        // 验证码登录
    }
    """
    data = request.get_json() or {}
    email = (data.get('email') or '').strip()
    password = data.get('password', '')
    code = data.get('code', '')

    if not email:
        return error(40001, '请输入邮箱')
    if not password and not code:
        return error(40001, '请输入密码或验证码')

    ok, msg, result = AuthService.login_student(email, password, code)
    if not ok:
        return error(40100, msg)

    return success(result, message=msg)


# ============================================================
# 教练 - 注册/登录
# ============================================================

@auth_bp.route('/coach/register', methods=['POST'])
def coach_register():
    """
    POST /api/auth/coach/register
    教练注册
    Body: {
        "email": "xxx@qq.com",
        "password": "abc123",
        "schoolName": "XX驾校",
        "trainType": 1,         // 1驾考/2客运/3货运/4危险品
        "schoolAddress": "...", // 可选
        "schoolPhone": "...",   // 可选
        "code": "123456"
    }
    """
    data = request.get_json() or {}
    email = (data.get('email') or '').strip()
    password = data.get('password', '')
    school_name = (data.get('schoolName') or '').strip()
    train_type = data.get('trainType', 1)
    school_address = data.get('schoolAddress')
    school_phone = data.get('schoolPhone')
    code = data.get('code')

    if not email or not password:
        return error(40001, '邮箱和密码不能为空')

    ok, msg, result = AuthService.register_coach(
        email, password, school_name, train_type,
        school_address, school_phone, code
    )
    if not ok:
        return error(40001, msg)

    return success(result, message=msg)


@auth_bp.route('/coach/login', methods=['POST'])
def coach_login():
    """
    POST /api/auth/coach/login
    教练登录（密码或验证码）
    Body: {
        "email": "xxx@qq.com",
        "password": "abc123",
        "code": "123456"
    }
    """
    data = request.get_json() or {}
    email = (data.get('email') or '').strip()
    password = data.get('password', '')
    code = data.get('code', '')

    if not email:
        return error(40001, '请输入邮箱')
    if not password and not code:
        return error(40001, '请输入密码或验证码')

    ok, msg, result = AuthService.login_coach(email, password, code)
    if not ok:
        return error(40100, msg)

    return success(result, message=msg)


# ============================================================
# 平台管理员 - 注册/登录
# ============================================================

@auth_bp.route('/admin/register', methods=['POST'])
def admin_register():
    """
    POST /api/auth/admin/register
    平台管理员注册
    Body: {
        "email": "xxx@qq.com",
        "password": "abc123",
        "adminType": 2,     // 1超级/2内容/3运营
        "code": "123456"
    }
    """
    data = request.get_json() or {}
    email = (data.get('email') or '').strip()
    password = data.get('password', '')
    admin_type = data.get('adminType', 2)
    code = data.get('code')

    if not email or not password:
        return error(40001, '邮箱和密码不能为空')

    ok, msg, result = AuthService.register_admin(email, password, admin_type, code)
    if not ok:
        return error(40001, msg)

    return success(result, message=msg)


@auth_bp.route('/admin/login', methods=['POST'])
def admin_login():
    """
    POST /api/auth/admin/login
    平台管理员登录（密码或验证码）
    Body: {
        "email": "xxx@qq.com",
        "password": "abc123",
        "code": "123456"
    }
    """
    data = request.get_json() or {}
    email = (data.get('email') or '').strip()
    password = data.get('password', '')
    code = data.get('code', '')

    if not email:
        return error(40001, '请输入邮箱')
    if not password and not code:
        return error(40001, '请输入密码或验证码')

    ok, msg, result = AuthService.login_admin(email, password, code)
    if not ok:
        return error(40100, msg)

    return success(result, message=msg)


# ============================================================
# 向下兼容：旧版统一登录/注册
# ============================================================

@auth_bp.route('/register', methods=['POST'])
def register():
    """
    POST /api/auth/register（向下兼容）
    学员注册
    Body: {
        "email": "xxx@qq.com",
        "password": "abc123",
        "name": "张三",
        "code": "123456"
    }
    """
    data = request.get_json() or {}
    email = (data.get('email') or data.get('account') or '').strip()
    password = data.get('password', '')
    name = (data.get('name') or '').strip()
    code = data.get('code')

    if not email or not password:
        return error(40001, '邮箱和密码不能为空')

    ok, msg, result = AuthService.register(email, password, name, code)
    if not ok:
        return error(40001, msg)

    return success(result, message=msg)


@auth_bp.route('/login', methods=['POST'])
def login():
    """
    POST /api/auth/login（向下兼容）
    统一登录（遍历三张表）
    Body: {
        "email": "xxx@qq.com",
        "password": "abc123",
        "code": "123456"
    }
    """
    data = request.get_json() or {}
    email = (data.get('email') or data.get('account') or '').strip()
    password = data.get('password', '')
    code = data.get('code', '')

    if not email:
        return error(40001, '请输入邮箱')
    if not password and not code:
        return error(40001, '请输入密码或验证码')

    ok, msg, result = AuthService.login(email, password, code)
    if not ok:
        return error(40100, msg)

    return success(result, message=msg)


# ============================================================
# Token管理（不变）
# ============================================================

@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """
    POST /api/auth/refresh
    使用Refresh Token刷新Access Token
    支持两种方式携带 refresh_token:
      1. Header: Authorization: Bearer <refresh_token>
      2. Body: { "refresh_token": "<refresh_token>" }
    """
    identity = get_jwt_identity()
    if isinstance(identity, str):
        identity = json.loads(identity)

    new_access_token = create_access_token(identity=json.dumps(identity))

    original_refresh_token = None
    auth_header = request.headers.get('Authorization', '')
    if auth_header.startswith('Bearer '):
        original_refresh_token = auth_header[7:]

    if not original_refresh_token:
        data = request.get_json(silent=True) or {}
        original_refresh_token = data.get('refresh_token', None)

    return success({
        'token': new_access_token,
        'refresh_token': original_refresh_token,
    }, message='Token刷新成功')


@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """
    POST /api/auth/logout
    退出登录：将当前JWT加入Redis黑名单
    """
    jti = get_jwt().get('jti')
    AuthService.logout(jti)
    return success(message='登出成功')


@auth_bp.route('/me', methods=['GET'])
@jwt_required_with_user()
def me():
    """
    GET /api/auth/me
    获取当前登录用户信息
    """
    user = g.current_user
    user_type = g.user_type
    data = AuthService.get_current_user_info(user, user_type)
    return success(data)
