"""
JWT认证中间件
"""
from functools import wraps
from flask import g
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from app.models.user import Student, Coach, PlatformAdmin
from app.utils.response import error


def jwt_required_with_user():
    """
    JWT认证装饰器
    验证JWT Token，解析用户身份后将当前用户对象挂载到 g.current_user
    """
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            import traceback, logging
            try:
                # 验证JWT Token
                verify_jwt_in_request()

                # 从JWT中获取用户身份信息
                identity = get_jwt_identity()
                if isinstance(identity, str):
                    import json
                    identity = json.loads(identity)

                user_type = identity.get('user_type')
                user_id = identity.get('user_id')

                # 根据用户类型查找用户
                user = None
                if user_type == 'student':
                    user = Student.query.get(user_id)
                elif user_type == 'coach':
                    user = Coach.query.get(user_id)
                elif user_type == 'admin':
                    user = PlatformAdmin.query.get(user_id)

                if user is None:
                    return error(401, '用户不存在或已被禁用')

                g.current_user = user
                g.user_type = user_type
                g.user_id = user_id

                return f(*args, **kwargs)
            except Exception as e:
                logging.getLogger(__name__).error(f'JWT middleware error: {e}\n{traceback.format_exc()}')
                return error(500, f'认证服务异常: {str(e)}')
        return decorated
    return decorator
