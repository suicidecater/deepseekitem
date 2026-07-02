"""
通知系统API

管理端: /api/admin/notifications  (CRUD + 撤回)
教练端: /api/coach/notifications   (查看 + 标记已读)
学员端: /api/student/notifications (查看 + 标记已读)
"""
from datetime import datetime
from flask import Blueprint, request, g, current_app

from app.middleware.auth import jwt_required_with_user
from app.middleware.rbac import role_required
from app.utils.response import success, error, paginated_response
from app.models.notification import Notification, UserNotification
from app.models.user import Student, Coach
from app.extensions import db

notification_bp = Blueprint('notification', __name__)


# ===================== 管理员端 =====================

@notification_bp.route('/admin/notifications', methods=['GET'])
@jwt_required_with_user()
@role_required('admin')
def admin_list_notifications():
    """
    GET /api/admin/notifications
    管理员获取通知列表（分页+筛选）
    Query: page, page_size, type, status, target_role
    """
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 20, type=int)
    noti_type = request.args.get('type', type=int)
    status = request.args.get('status', type=int)
    target_role = request.args.get('target_role', type=int)

    if page < 1:
        page = 1
    if page_size < 1:
        page_size = 20
    if page_size > 100:
        page_size = 100

    query = Notification.query
    if noti_type is not None:
        query = query.filter(Notification.type == noti_type)
    if status is not None:
        query = query.filter(Notification.status == status)
    if target_role is not None:
        query = query.filter(Notification.target_role == target_role)

    query = query.order_by(Notification.id.desc())
    total = query.count()
    notifications = query.offset((page - 1) * page_size).limit(page_size).all()

    return paginated_response(
        [n.to_dict() for n in notifications],
        total, page, page_size,
    )


@notification_bp.route('/admin/notifications', methods=['POST'])
@jwt_required_with_user()
@role_required('admin')
def admin_create_notification():
    """
    POST /api/admin/notifications
    管理员发布通知
    Body: { title, content, type, target_role, status(可选, 默认2已发布) }
    发布时自动为所有目标用户创建 user_notification 记录
    """
    data = request.get_json() or {}
    title = (data.get('title') or '').strip()
    content = (data.get('content') or '').strip()
    noti_type = data.get('type', 1)
    target_role = data.get('target_role', 3)
    status = data.get('status', 2)  # 默认直接发布

    if not title:
        return error(40001, '标题不能为空')
    if not content:
        return error(40001, '内容不能为空')
    if noti_type not in (1, 2, 3):
        return error(40001, '无效的通知类型')
    if target_role not in (1, 2, 3):
        return error(40001, '无效的接收角色')

    notification = Notification(
        title=title,
        content=content,
        type=noti_type,
        target_role=target_role,
        publisher_id=g.user_id,
        status=status,
    )

    if status == 2:  # 已发布
        notification.publish_time = datetime.now()

    notification.save()

    # 发布后自动为所有目标用户创建 user_notification 记录
    if status == 2:
        _create_user_notifications(notification)

    return success(notification.to_dict(), message='通知发布成功')


@notification_bp.route('/admin/notifications/<int:noti_id>', methods=['PUT'])
@jwt_required_with_user()
@role_required('admin')
def admin_update_notification(noti_id):
    """
    PUT /api/admin/notifications/:id
    管理员编辑通知（仅草稿状态可编辑）
    Body: { title, content, type, target_role, status }
    如果状态改为"已发布"，自动为用户创建 user_notification 记录
    """
    notification = Notification.query.get(noti_id)
    if not notification:
        return error(404, '通知不存在')

    data = request.get_json() or {}

    if 'title' in data:
        title = (data['title'] or '').strip()
        if not title:
            return error(40001, '标题不能为空')
        notification.title = title

    if 'content' in data:
        content = (data['content'] or '').strip()
        if not content:
            return error(40001, '内容不能为空')
        notification.content = content

    if 'type' in data:
        if data['type'] not in (1, 2, 3):
            return error(40001, '无效的通知类型')
        notification.type = data['type']

    if 'target_role' in data:
        if data['target_role'] not in (1, 2, 3):
            return error(40001, '无效的接收角色')
        notification.target_role = data['target_role']

    if 'status' in data:
        new_status = data['status']
        if new_status not in (1, 2, 3):
            return error(40001, '无效的状态')
        # 从草稿变为已发布
        if notification.status == 1 and new_status == 2:
            notification.publish_time = datetime.now()
            notification.status = new_status
            notification.save()
            _create_user_notifications(notification)
            return success(notification.to_dict(), message='通知已发布')
        notification.status = new_status

    notification.save()
    return success(notification.to_dict(), message='更新成功')


@notification_bp.route('/admin/notifications/<int:noti_id>', methods=['DELETE'])
@jwt_required_with_user()
@role_required('admin')
def admin_delete_notification(noti_id):
    """DELETE /api/admin/notifications/:id  删除通知"""
    notification = Notification.query.get(noti_id)
    if not notification:
        return error(404, '通知不存在')

    notification.delete()
    return success(message='删除成功')


@notification_bp.route('/admin/notifications/<int:noti_id>/recall', methods=['PUT'])
@jwt_required_with_user()
@role_required('admin')
def admin_recall_notification(noti_id):
    """PUT /api/admin/notifications/:id/recall  撤回通知"""
    notification = Notification.query.get(noti_id)
    if not notification:
        return error(404, '通知不存在')
    if notification.status != 2:
        return error(40001, '只有已发布的通知才可以撤回')

    notification.status = 3
    notification.save()
    return success(notification.to_dict(), message='通知已撤回')


# ===================== 教练端 =====================

@notification_bp.route('/coach/notifications', methods=['GET'])
@jwt_required_with_user()
@role_required('coach')
def coach_list_notifications():
    """
    GET /api/coach/notifications
    教练获取通知列表（只显示已发布且未撤回的通知）
    Query: page, page_size
    """
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 20, type=int)
    if page < 1:
        page = 1
    if page_size < 1:
        page_size = 20
    if page_size > 100:
        page_size = 100

    user_id = g.user_id

    # 查询该教练关联的 user_notification，联表获取通知信息
    query = db.session.query(UserNotification, Notification).join(
        Notification, UserNotification.notification_id == Notification.id
    ).filter(
        UserNotification.user_id == user_id,
        UserNotification.user_role == 1,
        Notification.status == 2,  # 只显示已发布
    ).order_by(Notification.publish_time.desc())

    total = query.count()
    rows = query.offset((page - 1) * page_size).limit(page_size).all()

    items = []
    for un, noti in rows:
        item = noti.to_dict()
        item['is_read'] = un.is_read
        item['read_time'] = un.read_time.strftime('%Y-%m-%d %H:%M:%S') if un.read_time else None
        items.append(item)

    return paginated_response(items, total, page, page_size)


@notification_bp.route('/coach/notifications/unread-count', methods=['GET'])
@jwt_required_with_user()
@role_required('coach')
def coach_unread_count():
    """GET /api/coach/notifications/unread-count  获取未读数量"""
    user_id = g.user_id
    count = db.session.query(UserNotification).join(
        Notification, UserNotification.notification_id == Notification.id
    ).filter(
        UserNotification.user_id == user_id,
        UserNotification.user_role == 1,
        UserNotification.is_read == 0,
        Notification.status == 2,
    ).count()

    return success({'count': count})


@notification_bp.route('/coach/notifications/read-all', methods=['PUT'])
@jwt_required_with_user()
@role_required('coach')
def coach_read_all():
    """
    PUT /api/coach/notifications/read-all  全部标记已读
    字面路由必须排在 <int:noti_id>/read 之前，否则会被 int 转换器拦截
    """
    # 校验当前登录用户 ID
    user_id = g.user_id
    if not user_id:
        current_app.logger.warning('[coach_read_all] g.user_id 为空，用户未登录')
        return error(401, '用户未登录，请重新登录')

    current_app.logger.info(f'[coach_read_all] 开始批量标记已读，user_id={user_id}')
    now = datetime.now()

    try:
        # 第一步：查出所有需要更新的 user_notification 记录 ID
        # 不能用 JOIN + UPDATE，SQLAlchemy 不支持，改用子查询
        un_ids_query = db.session.query(UserNotification.id).join(
            Notification, UserNotification.notification_id == Notification.id
        ).filter(
            UserNotification.user_id == user_id,
            UserNotification.user_role == 1,
            UserNotification.is_read == 0,
            Notification.status == 2,
        )
        un_ids = [row[0] for row in un_ids_query.all()]
        current_app.logger.info(f'[coach_read_all] 查出待更新记录数: {len(un_ids)}')

        if not un_ids:
            current_app.logger.info('[coach_read_all] 无未读记录，直接返回')
            return success({'updated_count': 0}, message='已全部标记为已读')

        # 第二步：批量更新（用 IN 子查询，避免 JOIN + UPDATE 的 SQL 语法问题）
        updated = UserNotification.query.filter(
            UserNotification.id.in_(un_ids)
        ).update(
            {'is_read': 1, 'read_time': now},
            synchronize_session=False
        )
        db.session.commit()
        current_app.logger.info(f'[coach_read_all] 批量更新成功，updated={updated}')

        return success({'updated_count': updated}, message='已全部标记为已读')

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'[coach_read_all] 批量标记已读失败: {str(e)}', exc_info=True)
        return error(500, f'服务器内部错误: {str(e)}')


@notification_bp.route('/coach/notifications/<int:noti_id>/read', methods=['PUT'])
@jwt_required_with_user()
@role_required('coach')
def coach_read_notification(noti_id):
    """PUT /api/coach/notifications/:id/read  标记单条已读"""
    user_id = g.user_id
    un = UserNotification.query.filter_by(
        notification_id=noti_id, user_id=user_id, user_role=1
    ).first()
    if not un:
        return error(404, '通知记录不存在')

    if un.is_read == 0:
        un.is_read = 1
        un.read_time = datetime.now()
        un.save()

    return success({'is_read': 1}, message='已标记为已读')


# ===================== 学员端 =====================

@notification_bp.route('/student/notifications', methods=['GET'])
@jwt_required_with_user()
@role_required('student')
def student_list_notifications():
    """
    GET /api/student/notifications
    学员获取通知列表（只显示已发布且未撤回的通知）
    Query: page, page_size
    """
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 20, type=int)
    if page < 1:
        page = 1
    if page_size < 1:
        page_size = 20
    if page_size > 100:
        page_size = 100

    user_id = g.user_id

    query = db.session.query(UserNotification, Notification).join(
        Notification, UserNotification.notification_id == Notification.id
    ).filter(
        UserNotification.user_id == user_id,
        UserNotification.user_role == 2,
        Notification.status == 2,
    ).order_by(Notification.publish_time.desc())

    total = query.count()
    rows = query.offset((page - 1) * page_size).limit(page_size).all()

    items = []
    for un, noti in rows:
        item = noti.to_dict()
        item['is_read'] = un.is_read
        item['read_time'] = un.read_time.strftime('%Y-%m-%d %H:%M:%S') if un.read_time else None
        items.append(item)

    return paginated_response(items, total, page, page_size)


@notification_bp.route('/student/notifications/unread-count', methods=['GET'])
@jwt_required_with_user()
@role_required('student')
def student_unread_count():
    """GET /api/student/notifications/unread-count  获取未读数量"""
    user_id = g.user_id
    count = db.session.query(UserNotification).join(
        Notification, UserNotification.notification_id == Notification.id
    ).filter(
        UserNotification.user_id == user_id,
        UserNotification.user_role == 2,
        UserNotification.is_read == 0,
        Notification.status == 2,
    ).count()

    return success({'count': count})


@notification_bp.route('/student/notifications/read-all', methods=['PUT'])
@jwt_required_with_user()
@role_required('student')
def student_read_all():
    """
    PUT /api/student/notifications/read-all  全部标记已读
    字面路由必须排在 <int:noti_id>/read 之前，否则会被 int 转换器拦截
    """
    # 校验当前登录用户 ID
    user_id = g.user_id
    if not user_id:
        current_app.logger.warning('[student_read_all] g.user_id 为空，用户未登录')
        return error(401, '用户未登录，请重新登录')

    current_app.logger.info(f'[student_read_all] 开始批量标记已读，user_id={user_id}')
    now = datetime.now()

    try:
        # 第一步：查出所有需要更新的 user_notification 记录 ID
        un_ids_query = db.session.query(UserNotification.id).join(
            Notification, UserNotification.notification_id == Notification.id
        ).filter(
            UserNotification.user_id == user_id,
            UserNotification.user_role == 2,
            UserNotification.is_read == 0,
            Notification.status == 2,
        )
        un_ids = [row[0] for row in un_ids_query.all()]
        current_app.logger.info(f'[student_read_all] 查出待更新记录数: {len(un_ids)}')

        if not un_ids:
            current_app.logger.info('[student_read_all] 无未读记录，直接返回')
            return success({'updated_count': 0}, message='已全部标记为已读')

        # 第二步：批量更新
        updated = UserNotification.query.filter(
            UserNotification.id.in_(un_ids)
        ).update(
            {'is_read': 1, 'read_time': now},
            synchronize_session=False
        )
        db.session.commit()
        current_app.logger.info(f'[student_read_all] 批量更新成功，updated={updated}')

        return success({'updated_count': updated}, message='已全部标记为已读')

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'[student_read_all] 批量标记已读失败: {str(e)}', exc_info=True)
        return error(500, f'服务器内部错误: {str(e)}')


@notification_bp.route('/student/notifications/<int:noti_id>/read', methods=['PUT'])
@jwt_required_with_user()
@role_required('student')
def student_read_notification(noti_id):
    """PUT /api/student/notifications/:id/read  标记单条已读"""
    user_id = g.user_id
    un = UserNotification.query.filter_by(
        notification_id=noti_id, user_id=user_id, user_role=2
    ).first()
    if not un:
        return error(404, '通知记录不存在')

    if un.is_read == 0:
        un.is_read = 1
        un.read_time = datetime.now()
        un.save()

    return success({'is_read': 1}, message='已标记为已读')


# ===================== 辅助函数 =====================

def _create_user_notifications(notification):
    """
    根据通知的 target_role，为所有符合条件的目标用户创建 UserNotification 记录
    target_role: 1=教练, 2=学员, 3=全部
    """
    target_role = notification.target_role
    noti_id = notification.id

    records = []

    if target_role in (1, 3):  # 教练 或 全部
        coach_ids = [row[0] for row in db.session.query(Coach.id).all()]
        for cid in coach_ids:
            records.append(UserNotification(
                notification_id=noti_id,
                user_id=cid,
                user_role=1,
                is_read=0,
            ))

    if target_role in (2, 3):  # 学员 或 全部
        student_ids = [row[0] for row in db.session.query(Student.id).all()]
        for sid in student_ids:
            records.append(UserNotification(
                notification_id=noti_id,
                user_id=sid,
                user_role=2,
                is_read=0,
            ))

    if records:
        db.session.bulk_save_objects(records)
        db.session.commit()
