"""
教练-学员对话服务层

user_type 使用字符串: 'student' | 'coach'
sender_type 使用字符串: 'student' | 'coach'
"""
from datetime import datetime
from app.extensions import db
from app.models.chat import Conversation, ChatMessage
from app.models.user import Student, Coach


class ChatService:
    """对话服务"""

    # 角色常量
    ROLE_STUDENT = 'student'
    ROLE_COACH = 'coach'

    @staticmethod
    def get_or_create_conversation(coach_id, student_id):
        """获取或创建会话"""
        conversation = Conversation.query.filter_by(
            coach_id=coach_id,
            student_id=student_id,
            status=1
        ).first()

        if not conversation:
            coach = Coach.get_by_id(coach_id)
            student = Student.get_by_id(student_id)
            if not coach:
                raise ValueError('教练不存在')
            if not student:
                raise ValueError('学员不存在')

            conversation = Conversation(
                coach_id=coach_id,
                student_id=student_id
            )
            db.session.add(conversation)
            db.session.commit()
            # 刷新对象以加载关系（coach, student），避免 to_dict() 延迟加载出错
            db.session.refresh(conversation)
        elif conversation.status == 2:
            conversation.status = 1
            db.session.commit()
            # 刷新对象以加载关系
            db.session.refresh(conversation)

        return conversation

    @staticmethod
    def send_message(conversation_id, sender_type, sender_id, content, message_type=1):
        """发送消息"""
        conversation = Conversation.get_or_404(conversation_id)
        if conversation.status != 1:
            raise ValueError('会话已归档')

        message = ChatMessage(
            conversation_id=conversation_id,
            sender_type=sender_type,
            sender_id=sender_id,
            content=content,
            message_type=message_type
        )
        db.session.add(message)

        conversation.last_message = content[:100]
        conversation.last_message_time = datetime.now()

        if sender_type == ChatService.ROLE_STUDENT:
            conversation.unread_coach = (conversation.unread_coach or 0) + 1
        elif sender_type == ChatService.ROLE_COACH:
            conversation.unread_student = (conversation.unread_student or 0) + 1

        db.session.commit()
        return message

    @staticmethod
    def mark_read(conversation_id, user_type):
        """将某用户在该会话中的消息标记为已读"""
        conversation = Conversation.get_or_404(conversation_id)

        if user_type == ChatService.ROLE_STUDENT:
            conversation.unread_student = 0
        elif user_type == ChatService.ROLE_COACH:
            conversation.unread_coach = 0
        else:
            raise ValueError('无效的用户类型')

        db.session.commit()

    @staticmethod
    def get_messages(conversation_id, page=1, page_size=50):
        """获取会话消息列表（按时间正序）"""
        query = ChatMessage.query.filter_by(
            conversation_id=conversation_id
        ).order_by(ChatMessage.create_time.asc())

        total = query.count()
        messages = query.offset((page - 1) * page_size).limit(page_size).all()

        return [m.to_dict() for m in messages], total

    @staticmethod
    def get_conversations(user_id, user_type, page=1, page_size=20):
        """获取用户的会话列表"""
        # 使用 COALESCE 处理 last_message_time 为 NULL 的情况，避免 nullslast() 兼容性问题
        from sqlalchemy import desc, func
        order_expr = desc(func.coalesce(Conversation.last_message_time, Conversation.create_time))
        
        if user_type == ChatService.ROLE_STUDENT:
            query = Conversation.query.filter_by(
                student_id=user_id
            ).filter(Conversation.status.in_([1, 2])).order_by(order_expr)
        elif user_type == ChatService.ROLE_COACH:
            query = Conversation.query.filter_by(
                coach_id=user_id
            ).filter(Conversation.status.in_([1, 2])).order_by(order_expr)
        else:
            raise ValueError('无效的用户类型')

        total = query.count()
        conversations = query.offset((page - 1) * page_size).limit(page_size).all()

        return [c.to_dict(user_type=user_type) for c in conversations], total

    @staticmethod
    def get_unread_count(user_id, user_type):
        """获取用户总未读消息数"""
        if user_type == ChatService.ROLE_STUDENT:
            result = db.session.query(
                db.func.coalesce(db.func.sum(Conversation.unread_student), 0)
            ).filter(
                Conversation.student_id == user_id,
                Conversation.status == 1
            ).scalar()
        elif user_type == ChatService.ROLE_COACH:
            result = db.session.query(
                db.func.coalesce(db.func.sum(Conversation.unread_coach), 0)
            ).filter(
                Conversation.coach_id == user_id,
                Conversation.status == 1
            ).scalar()
        else:
            return 0
        return int(result)

    @staticmethod
    def archive_conversation(conversation_id):
        """归档会话"""
        conversation = Conversation.get_or_404(conversation_id)
        conversation.status = 2
        db.session.commit()
