"""
RBAC角色校验中间件
"""
from functools import wraps
from flask import g
from app.utils.response import error


def role_required(*roles):
    """
    RBAC角色校验装饰器
    限制API只能由特定角色访问

    用法:
        @role_required('student')       # 仅学员
        @role_required('coach', 'admin') # 教练或管理员

    参数:
        roles: 允许的角色列表，可选值: 'student', 'coach', 'admin'
    """
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            # 确保已通过JWT认证，g.current_user已挂载
            if not hasattr(g, 'user_type'):
                return error(401, '请先登录')

            user_type = g.user_type
            if user_type not in roles:
                return error(403, '权限不足，无法访问该资源')

            return f(*args, **kwargs)
        return decorated
    return decorator
