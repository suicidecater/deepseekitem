"""
通知系统模型：Notification（通知表）、UserNotification（用户已读状态表）
"""
from datetime import datetime
from app.extensions import db
from . import BaseModel


class Notification(BaseModel):
    """通知表"""
    __tablename__ = 'notification'

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True, comment='通知ID')
    title = db.Column(db.String(128), nullable=False, comment='通知标题')
    content = db.Column(db.Text, nullable=False, comment='通知内容')
    type = db.Column(db.SmallInteger, nullable=False, default=1, comment='类型: 1系统公告/2培训通知/3其他')
    target_role = db.Column(db.SmallInteger, nullable=False, default=3, comment='接收角色: 1教练/2学员/3全部')
    publisher_id = db.Column(db.BigInteger, nullable=False, comment='发布者(管理员)ID')
    status = db.Column(db.SmallInteger, nullable=False, default=1, comment='状态: 1草稿/2已发布/3已撤回')
    create_time = db.Column(db.DateTime, default=datetime.now, comment='创建时间')
    publish_time = db.Column(db.DateTime, nullable=True, comment='发布时间')

    # 关系
    user_notifications = db.relationship('UserNotification', backref='notification', lazy='dynamic',
                                          cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'type': self.type,
            'target_role': self.target_role,
            'publisher_id': self.publisher_id,
            'status': self.status,
            'create_time': self.create_time.strftime('%Y-%m-%d %H:%M:%S') if self.create_time else None,
            'publish_time': self.publish_time.strftime('%Y-%m-%d %H:%M:%S') if self.publish_time else None,
        }


class UserNotification(BaseModel):
    """用户通知关联表（记录已读状态）"""
    __tablename__ = 'user_notification'

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True, comment='记录ID')
    notification_id = db.Column(db.BigInteger, db.ForeignKey('notification.id', ondelete='CASCADE'),
                                  nullable=False, index=True, comment='通知ID')
    user_id = db.Column(db.BigInteger, nullable=False, index=True, comment='用户ID')
    user_role = db.Column(db.SmallInteger, nullable=False, comment='用户角色: 1教练/2学员')
    is_read = db.Column(db.SmallInteger, nullable=False, default=0, comment='是否已读: 0未读/1已读')
    read_time = db.Column(db.DateTime, nullable=True, comment='阅读时间')

    def to_dict(self):
        return {
            'id': self.id,
            'notification_id': self.notification_id,
            'user_id': self.user_id,
            'user_role': self.user_role,
            'is_read': self.is_read,
            'read_time': self.read_time.strftime('%Y-%m-%d %H:%M:%S') if self.read_time else None,
        }
