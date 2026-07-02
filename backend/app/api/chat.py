"""
教练-学员对话 API + WebSocket 实时通信

REST API:
  GET    /api/chat/conversations                     - 获取会话列表
  POST   /api/chat/conversations                     - 创建/恢复会话
  GET    /api/chat/conversations/<id>/messages       - 获取消息
  POST   /api/chat/conversations/<id>/messages       - 发送消息
  PUT    /api/chat/conversations/<id>/read           - 标记已读
  PUT    /api/chat/conversations/<id>/archive        - 归档会话
  GET    /api/chat/unread-count                      - 获取总未读数

WebSocket 事件:
  connect / disconnect                               - 自动认证连接
  'join_conversation'   (room)                       - 加入会话房间
  'leave_conversation'  (room)                       - 离开会话房间
  'send_message'        (room, conversation_id, content)
  'new_message'         (broadcast)                  - 服务端推送新消息
  'typing'              (room, conversation_id)      - 正在输入
  'stop_typing'         (room, conversation_id)      - 停止输入
"""
from flask import Blueprint, request, g, current_app, session as flask_session
from flask_socketio import emit, join_room, leave_room, disconnect
from app.middleware.auth import jwt_required_with_user
from app.services.chat_service import ChatService
from app.extensions import socketio
from app.utils.response import success, error, paginated_response

chat_bp = Blueprint('chat', __name__)


# =========================== REST API ===========================


@chat_bp.route('/conversations', methods=['GET'])
@jwt_required_with_user()
def get_conversations():
    """
    获取当前用户的会话列表
    ?page=1&page_size=20
    """
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 20, type=int)
    if page < 1:
        page = 1
    if page_size < 1:
        page_size = 20
    if page_size > 100:
        page_size = 100

    try:
        conversations, total = ChatService.get_conversations(
            g.user_id, g.user_type, page, page_size
        )
        return paginated_response(conversations, total, page, page_size)
    except ValueError as e:
        return error(400, str(e))


@chat_bp.route('/conversations', methods=['POST'])
@jwt_required_with_user()
def create_conversation():
    """
    创建新会话或恢复已归档会话
    学员发起 ↔ 指定 coach_id; 教练发起 ↔ 指定 student_id
    Body: { coach_id?, student_id? }
    """
    data = request.get_json(silent=True) or {}
    coach_id = data.get('coach_id')
    student_id = data.get('student_id')

    try:
        if g.user_type == 'student':
            if not coach_id:
                return error(400, '请指定教练ID')
            conversation = ChatService.get_or_create_conversation(
                coach_id=coach_id, student_id=g.user_id
            )
        elif g.user_type == 'coach':
            if not student_id:
                return error(400, '请指定学员ID')
            conversation = ChatService.get_or_create_conversation(
                coach_id=g.user_id, student_id=student_id
            )
        else:
            return error(403, '当前角色不支持此操作')

        return success(conversation.to_dict(user_type=g.user_type), message='会话已创建')
    except ValueError as e:
        return error(400, str(e))


@chat_bp.route('/conversations/<int:conversation_id>/messages', methods=['GET'])
@jwt_required_with_user()
def get_messages(conversation_id):
    """
    获取指定会话的消息列表（按时间正序）
    ?page=1&page_size=50
    """
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 50, type=int)
    if page < 1:
        page = 1
    if page_size < 1:
        page_size = 50
    if page_size > 100:
        page_size = 100

    try:
        messages, total = ChatService.get_messages(conversation_id, page, page_size)
        return paginated_response(messages, total, page, page_size)
    except Exception as e:
        return error(400, str(e))


@chat_bp.route('/conversations/<int:conversation_id>/messages', methods=['POST'])
@jwt_required_with_user()
def send_message(conversation_id):
    """
    发送消息（REST方式）
    Body: { content: "消息内容", message_type?: 1=文本/2=图片/3=文件 }
    发送成功后通过 WebSocket 广播给房间内所有客户端
    """
    data = request.get_json(silent=True) or {}
    content = (data.get('content') or '').strip()
    message_type = data.get('message_type', 1)

    if not content:
        return error(400, '消息内容不能为空')
    if len(content) > 5000:
        return error(400, '消息内容过长，最多5000字')

    try:
        message = ChatService.send_message(
            conversation_id=conversation_id,
            sender_type=g.user_type,
            sender_id=g.user_id,
            content=content,
            message_type=message_type
        )

        msg_dict = message.to_dict()

        # WebSocket 广播新消息到会话房间
        room = f'conversation_{conversation_id}'
        socketio.emit('new_message', msg_dict, room=room)

        # 推送未读计数更新给接收方
        conversation = message.conversation
        receiver_type = 'coach' if g.user_type == 'student' else 'student'
        receiver_id = conversation.coach_id if g.user_type == 'student' else conversation.student_id
        total_unread = ChatService.get_unread_count(receiver_id, receiver_type)
        socketio.emit('unread_count_updated', {
            'conversation_id': conversation_id,
            'conversation_unread': conversation.unread_coach if receiver_type == 'coach' else conversation.unread_student,
            'total_unread': total_unread
        }, room=f'user_{receiver_type}_{receiver_id}')

        return success(msg_dict, message='消息发送成功')
    except ValueError as e:
        return error(400, str(e))
    except Exception as e:
        return error(500, str(e))


@chat_bp.route('/conversations/<int:conversation_id>/read', methods=['PUT'])
@jwt_required_with_user()
def mark_read(conversation_id):
    """标记会话所有消息为已读"""
    try:
        ChatService.mark_read(conversation_id, g.user_type)

        # 通知房间对方已读
        room = f'conversation_{conversation_id}'
        socketio.emit('messages_read', {
            'conversation_id': conversation_id,
            'reader_type': g.user_type
        }, room=room)

        # 推送清零后的未读数给当前用户（红点实时消失）
        total_unread = ChatService.get_unread_count(g.user_id, g.user_type)
        socketio.emit('unread_count_updated', {
            'conversation_id': conversation_id,
            'conversation_unread': 0,
            'total_unread': total_unread
        }, room=f'user_{g.user_type}_{g.user_id}')

        return success(message='已标记为已读')
    except ValueError as e:
        return error(400, str(e))


@chat_bp.route('/conversations/<int:conversation_id>/archive', methods=['PUT'])
@jwt_required_with_user()
def archive_conversation(conversation_id):
    """归档会话"""
    try:
        ChatService.archive_conversation(conversation_id)
        return success(message='会话已归档')
    except Exception as e:
        return error(400, str(e))


@chat_bp.route('/unread-count', methods=['GET'])
@jwt_required_with_user()
def get_unread_count():
    """获取当前用户的总未读消息数"""
    count = ChatService.get_unread_count(g.user_id, g.user_type)
    return success({'unread_count': count})


# =========================== WebSocket 事件 ===========================


@socketio.on('connect')
def handle_connect():
    """客户端连接时进行JWT认证"""
    token = request.args.get('token') or (
        request.headers.get('Authorization', '').replace('Bearer ', '')
    )
    if not token:
        token = request.cookies.get('token')

    if not token:
        emit('auth_error', {'message': '缺少认证Token'})
        disconnect()
        return False

    try:
        from flask_jwt_extended import decode_token
        decoded = decode_token(token)
        # JWT identity 格式: {'user_type': 'student'/'coach', 'user_id': <int>}
        identity = decoded.get('sub', {})
        if isinstance(identity, str):
            import json
            identity = json.loads(identity)

        user_type = identity.get('user_type')
        user_id = identity.get('user_id')

        if not user_type or not user_id:
            emit('auth_error', {'message': 'Token格式无效'})
            disconnect()
            return False

        # 挂载用户信息到 flask session
        flask_session['user_type'] = user_type
        flask_session['user_id'] = user_id
        flask_session['ws_authenticated'] = True

        # 加入用户专属房间（用于单播通知）
        join_room(f'user_{user_type}_{user_id}')
        emit('connected', {
            'message': 'WebSocket连接成功',
            'user_type': user_type,
            'user_id': user_id
        })
    except Exception as e:
        emit('auth_error', {'message': f'认证失败: {str(e)}'})
        disconnect()
        return False


@socketio.on('disconnect')
def handle_disconnect():
    """客户端断开连接"""
    user_type = flask_session.get('user_type')
    user_id = flask_session.get('user_id')
    if user_type and user_id:
        leave_room(f'user_{user_type}_{user_id}')


@socketio.on('join_conversation')
def handle_join_conversation(data):
    """
    加入指定会话房间
    data: { conversation_id: int }
    """
    if not flask_session.get('ws_authenticated'):
        emit('auth_error', {'message': '请先认证'})
        return

    conversation_id = data.get('conversation_id')
    if not conversation_id:
        emit('error', {'message': '缺少conversation_id'})
        return

    room = f'conversation_{conversation_id}'
    join_room(room)

    # 加入时自动标记已读
    try:
        user_type = flask_session.get('user_type')
        user_id = flask_session.get('user_id')
        ChatService.mark_read(conversation_id, user_type)
        # 推送清零后的未读数给当前用户
        total_unread = ChatService.get_unread_count(user_id, user_type)
        socketio.emit('unread_count_updated', {
            'conversation_id': conversation_id,
            'conversation_unread': 0,
            'total_unread': total_unread
        }, room=f'user_{user_type}_{user_id}')
    except Exception:
        pass

    emit('joined_conversation', {
        'conversation_id': conversation_id,
        'message': '已加入会话'
    })


@socketio.on('leave_conversation')
def handle_leave_conversation(data):
    """离开指定会话房间"""
    conversation_id = data.get('conversation_id')
    if conversation_id:
        room = f'conversation_{conversation_id}'
        leave_room(room)


@socketio.on('send_message')
def handle_ws_send_message(data):
    """
    通过 WebSocket 发送消息
    data: { conversation_id: int, content: str, message_type?: int }

    优势：延迟更低，无需HTTP往返
    """
    if not flask_session.get('ws_authenticated'):
        emit('auth_error', {'message': '请先认证'})
        return

    conversation_id = data.get('conversation_id')
    content = (data.get('content') or '').strip()
    message_type = data.get('message_type', 1)
    user_type = flask_session.get('user_type')
    user_id = flask_session.get('user_id')

    if not conversation_id or not content:
        emit('error', {'message': '缺少conversation_id或消息内容'})
        return
    if len(content) > 5000:
        emit('error', {'message': '消息内容过长'})
        return

    try:
        message = ChatService.send_message(
            conversation_id=conversation_id,
            sender_type=user_type,
            sender_id=user_id,
            content=content,
            message_type=message_type
        )
        msg_dict = message.to_dict()

        # 广播到会话房间
        room = f'conversation_{conversation_id}'
        socketio.emit('new_message', msg_dict, room=room)

        # 发送确认给发送者
        emit('message_sent', msg_dict)

        # 推送未读计数更新给接收方
        conversation = message.conversation
        receiver_type = 'coach' if user_type == 'student' else 'student'
        receiver_id = conversation.coach_id if user_type == 'student' else conversation.student_id
        total_unread = ChatService.get_unread_count(receiver_id, receiver_type)
        socketio.emit('unread_count_updated', {
            'conversation_id': conversation_id,
            'conversation_unread': conversation.unread_coach if receiver_type == 'coach' else conversation.unread_student,
            'total_unread': total_unread
        }, room=f'user_{receiver_type}_{receiver_id}')
    except Exception as e:
        emit('error', {'message': str(e)})


@socketio.on('typing')
def handle_typing(data):
    """正在输入提示"""
    conversation_id = data.get('conversation_id')
    if not conversation_id or not flask_session.get('ws_authenticated'):
        return

    room = f'conversation_{conversation_id}'
    socketio.emit('user_typing', {
        'conversation_id': conversation_id,
        'user_type': flask_session.get('user_type'),
        'user_id': flask_session.get('user_id')
    }, room=room, include_sender=False)


@socketio.on('stop_typing')
def handle_stop_typing(data):
    """停止输入提示"""
    conversation_id = data.get('conversation_id')
    if not conversation_id or not flask_session.get('ws_authenticated'):
        return

    room = f'conversation_{conversation_id}'
    socketio.emit('user_stop_typing', {
        'conversation_id': conversation_id,
        'user_type': flask_session.get('user_type')
    }, room=room, include_sender=False)
