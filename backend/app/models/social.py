"""
社交/互动模型：Message（消息通知）、Note（笔记互动）、Feedback（用户反馈）
系统日志：SysLog
"""
from datetime import datetime
from app.extensions import db
from . import BaseModel


class Message(BaseModel):
    """消息通知表"""
    __tablename__ = 'message'

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True, comment='消息ID')
    receive_type = db.Column(db.SmallInteger, nullable=False, index=True, comment='接收者类型: 1学员/2教练/3管理员')
    receive_id = db.Column(db.BigInteger, nullable=False, index=True, comment='接收者ID')
    title = db.Column(db.String(64), nullable=False, comment='消息标题')
    content = db.Column(db.Text, nullable=True, comment='消息内容')
    type = db.Column(db.SmallInteger, default=1, comment='消息类型: 1提醒/2公告/3成绩/4任务')
    channel = db.Column(db.SmallInteger, default=1, comment='渠道: 1站内/2邮箱')
    status = db.Column(db.SmallInteger, default=1, comment='状态: 1未读/2已读/3删除')
    create_time = db.Column(db.DateTime, default=datetime.now, comment='创建时间')

    def to_dict(self):
        return {
            'id': self.id,
            'receive_type': self.receive_type,
            'receive_id': self.receive_id,
            'title': self.title,
            'content': self.content,
            'type': self.type,
            'channel': self.channel,
            'status': self.status,
            'create_time': self.create_time.strftime('%Y-%m-%d %H:%M:%S') if self.create_time else None,
        }


class Note(BaseModel):
    """笔记互动表"""
    __tablename__ = 'note'

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True, comment='笔记ID')
    student_id = db.Column(db.BigInteger, db.ForeignKey('student.id'), nullable=False, index=True, comment='学员ID')
    content = db.Column(db.Text, nullable=True, comment='笔记内容')
    status = db.Column(db.SmallInteger, default=1, comment='状态: 1待审核/2已上线/3驳回')
    like_count = db.Column(db.Integer, default=0, comment='点赞数')
    collect_count = db.Column(db.Integer, default=0, comment='收藏数')
    comment = db.Column(db.Text, nullable=True, comment='评论(JSON)')
    create_time = db.Column(db.DateTime, default=datetime.now, comment='创建时间')
    update_time = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')

    def to_dict(self):
        return {
            'id': self.id,
            'student_id': self.student_id,
            'content': self.content,
            'status': self.status,
            'like_count': self.like_count,
            'collect_count': self.collect_count,
            'comment': self.comment,
            'create_time': self.create_time.strftime('%Y-%m-%d %H:%M:%S') if self.create_time else None,
        }


class Feedback(BaseModel):
    """用户反馈表"""
    __tablename__ = 'feedback'

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True, comment='反馈ID')
    user_type = db.Column(db.SmallInteger, nullable=False, comment='用户类型: 1学员/2教练')
    user_id = db.Column(db.BigInteger, nullable=False, index=True, comment='用户ID')
    type = db.Column(db.SmallInteger, default=3, comment='反馈类型: 1故障/2学习/3建议/4投诉')
    content = db.Column(db.Text, nullable=True, comment='反馈内容')
    handler_id = db.Column(db.BigInteger, db.ForeignKey('admin.id'), nullable=True, comment='处理人ID')
    reply = db.Column(db.Text, nullable=True, comment='回复内容')
    status = db.Column(db.SmallInteger, default=1, comment='状态: 1待处理/2处理中/3已办结')
    create_time = db.Column(db.DateTime, default=datetime.now, comment='创建时间')
    update_time = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')

    # 关系
    handler = db.relationship('PlatformAdmin', backref=db.backref('feedbacks', lazy='dynamic'))

    def to_dict(self):
        return {
            'id': self.id,
            'user_type': self.user_type,
            'user_id': self.user_id,
            'type': self.type,
            'content': self.content,
            'handler_id': self.handler_id,
            'reply': self.reply,
            'status': self.status,
            'create_time': self.create_time.strftime('%Y-%m-%d %H:%M:%S') if self.create_time else None,
        }


class SysLog(BaseModel):
    """系统日志表"""
    __tablename__ = 'sys_log'

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True, comment='日志ID')
    user_type = db.Column(db.SmallInteger, nullable=False, comment='用户类型: 1学员 2教练 3管理员')
    user_id = db.Column(db.BigInteger, nullable=False, index=True, comment='用户ID')
    log_type = db.Column(db.SmallInteger, nullable=False, comment='日志类型: 1登录 2操作')
    module = db.Column(db.String(64), nullable=True, comment='操作模块')
    content = db.Column(db.String(255), nullable=False, comment='日志内容')
    ip = db.Column(db.String(32), nullable=True, comment='登录IP')
    device = db.Column(db.String(64), nullable=True, comment='设备信息')
    oper_time = db.Column(db.DateTime, default=datetime.now, comment='操作时间')

    def to_dict(self):
        return {
            'id': self.id,
            'userType': self.user_type,
            'userId': self.user_id,
            'logType': self.log_type,
            'module': self.module,
            'content': self.content,
            'ip': self.ip,
            'device': self.device,
            'operTime': self.oper_time.strftime('%Y-%m-%d %H:%M:%S') if self.oper_time else None,
        }
