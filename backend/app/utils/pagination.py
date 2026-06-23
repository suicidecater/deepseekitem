"""
分页工具
"""
from flask import request


def get_pagination_params():
    """从请求中提取分页参数"""
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 20, type=int)

    # 限制最大分页数
    if page < 1:
        page = 1
    if page_size < 1:
        page_size = 20
    if page_size > 100:
        page_size = 100

    return page, page_size


def paginate_query(query, page=None, page_size=None):
    """对查询进行分页"""
    if page is None or page_size is None:
        page, page_size = get_pagination_params()

    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()

    return items, total, page, page_size
