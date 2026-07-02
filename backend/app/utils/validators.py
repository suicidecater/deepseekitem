"""
参数校验工具
"""
import re
from functools import wraps
from flask import request, jsonify


# 正则校验
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
PHONE_REGEX = re.compile(r'^1[3-9]\d{9}$')
PASSWORD_REGEX = re.compile(r'^(?=.*[a-zA-Z])(?=.*\d).{6,}$')


def validate_email(email):
    """校验邮箱格式"""
    if not email or not EMAIL_REGEX.match(email):
        return False
    return True


def validate_phone(phone):
    """校验手机号格式"""
    if not phone or not PHONE_REGEX.match(phone):
        return False
    return True


def validate_password(password):
    """校验密码强度：至少6位，包含字母和数字"""
    if not password or not PASSWORD_REGEX.match(password):
        return False
    return True


def require_params(*required_fields):
    """装饰器：校验必填参数"""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            data = request.get_json(silent=True) or {}
            missing = [f for f in required_fields if f not in data or data[f] is None or data[f] == '']
            if missing:
                return jsonify({
                    'code': 400,
                    'message': f'缺少必填参数: {", ".join(missing)}',
                    'data': None
                }), 400
            return f(*args, **kwargs)
        return decorated
    return decorator


def sanitize_string(value, max_length=None):
    """字符串清洗：去除首尾空格，限制长度"""
    if value is None:
        return None
    value = str(value).strip()
    if max_length and len(value) > max_length:
        value = value[:max_length]
    return value


def validate_pagination(page, page_size):
    """校验分页参数"""
    if page < 1:
        return 1
    if page_size < 1:
        return 20
    if page_size > 100:
        return 100
    return page, page_size
