"""
教练-学员对话数据模型
"""
from datetime import datetime
from app.extensions import db
from . import BaseModel


class Conversation(BaseModel):
    """教练-学员会话表"""
    __tablename__ = 'conversation'

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True, comment='会话ID')
    coach_id = db.Column(db.BigInteger, db.ForeignKey('coach.id', ondelete='CASCADE'),
                         nullable=False, comment='教练ID')
    student_id = db.Column(db.BigInteger, db.ForeignKey('student.id', ondelete='CASCADE'),
                           nullable=False, comment='学员ID')
    last_message = db.Column(db.String(500), nullable=True, comment='最后一条消息摘要')
    last_message_time = db.Column(db.DateTime, default=datetime.now, comment='最后消息时间')
    unread_coach = db.Column(db.Integer, default=0, comment='教练未读数')
    unread_student = db.Column(db.Integer, default=0, comment='学员未读数')
    status = db.Column(db.SmallInteger, default=1, comment='状态: 1正常/2已归档')
    create_time = db.Column(db.DateTime, default=datetime.now, comment='创建时间')

    # 关系
    coach = db.relationship('Coach', backref=db.backref('conversations', lazy='dynamic'))
    student = db.relationship('Student', backref=db.backref('conversations', lazy='dynamic'))
    messages = db.relationship('ChatMessage', backref='conversation', lazy='dynamic',
                               cascade='all, delete-orphan',
                               order_by='ChatMessage.create_time')

    def to_dict(self, user_type=None):
        """序列化为字典，user_type='coach'/'student'用于判断当前用户的未读数"""
        data = {
            'id': self.id,
            'coach_id': self.coach_id,
            'student_id': self.student_id,
            'last_message': self.last_message,
            'last_message_time': self.last_message_time.strftime('%Y-%m-%d %H:%M:%S')
                if self.last_message_time else None,
            'unread_count': self.unread_coach if user_type == 'coach' else self.unread_student,
            'status': self.status,
            'create_time': self.create_time.strftime('%Y-%m-%d %H:%M:%S')
                if self.create_time else None,
        }
        # 携带对方信息 - 使用 try/except 防止延迟加载异常
        try:
            if self.coach:
                data['coach_name'] = self.coach.name or f'教练 #{self.coach_id}'
        except Exception:
            data['coach_name'] = f'教练 #{self.coach_id}'
        try:
            if self.student:
                data['student_name'] = self.student.name or f'学员 #{self.student_id}'
        except Exception:
            data['student_name'] = f'学员 #{self.student_id}'
        return data


class ChatMessage(BaseModel):
    """聊天消息表"""
    __tablename__ = 'chat_message'

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True, comment='消息ID')
    conversation_id = db.Column(db.BigInteger, db.ForeignKey('conversation.id', ondelete='CASCADE'),
                                nullable=False, comment='会话ID')
    sender_type = db.Column(db.String(20), nullable=False,
                            comment='发送者类型: student/coach')
    sender_id = db.Column(db.BigInteger, nullable=False, comment='发送者ID')
    content = db.Column(db.Text, nullable=False, comment='消息内容')
    message_type = db.Column(db.SmallInteger, default=1,
                             comment='消息类型: 1文本/2图片/3文件')
    status = db.Column(db.SmallInteger, default=1,
                       comment='状态: 1已发送/2已读/3已撤回')
    create_time = db.Column(db.DateTime, default=datetime.now, comment='创建时间')

    def to_dict(self):
        return {
            'id': self.id,
            'conversation_id': self.conversation_id,
            'sender_type': self.sender_type,
            'sender_id': self.sender_id,
            'content': self.content,
            'message_type': self.message_type,
            'status': self.status,
            'create_time': self.create_time.strftime('%Y-%m-%d %H:%M:%S')
                if self.create_time else None,
        }
