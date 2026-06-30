"""
统一响应格式
"""
from flask import jsonify


def success(data=None, message='success'):
    """成功响应"""
    return jsonify({
        'code': 0,
        'message': message,
        'data': data if data is not None else {}
    })


def error(code, message):
    """
    错误响应
    自动将业务错误码映射为标准 HTTP 状态码：
    4xxxx → 首三位作为 HTTP 状态码
    """
    if code >= 1000:
        http_code = code // 100
        if http_code < 100:
            http_code = 400
    else:
        http_code = code
    return jsonify({
        'code': code,
        'message': message,
        'data': None
    }), http_code


def paginated_response(items, total, page, page_size):
    """分页响应"""
    return success({
        'list': items,
        'pagination': {
            'total': total,
            'page': page,
            'page_size': page_size,
            'total_pages': (total + page_size - 1) // page_size if page_size > 0 else 0,
        }
    })
