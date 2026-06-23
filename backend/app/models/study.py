"""
学习相关模型：StudyPlan（学习计划）、AiChat（AI对话）
"""
from datetime import datetime, date
from app.extensions import db
from . import BaseModel


class StudyPlan(BaseModel):
    """学习计划表"""
    __tablename__ = 'study_plan'

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True, comment='计划ID')
    student_id = db.Column(db.BigInteger, db.ForeignKey('student.id'), nullable=False, index=True, comment='学员ID')
    plan_type = db.Column(db.SmallInteger, default=1, comment='计划类型: 1长期/2每日任务')
    content = db.Column(db.String(255), nullable=True, comment='计划内容')
    task_date = db.Column(db.Date, nullable=True, index=True, comment='任务日期')
    status = db.Column(db.SmallInteger, default=1, comment='状态: 1未开始/2进行中/3已完成/4逾期')
    create_time = db.Column(db.DateTime, default=datetime.now, comment='创建时间')
    update_time = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')

    def to_dict(self):
        return {
            'id': self.id,
            'student_id': self.student_id,
            'plan_type': self.plan_type,
            'content': self.content,
            'task_date': self.task_date.strftime('%Y-%m-%d') if self.task_date else None,
            'status': self.status,
        }


class AiChat(BaseModel):
    """AI对话表"""
    __tablename__ = 'ai_chat'

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True, comment='对话ID')
    student_id = db.Column(db.BigInteger, db.ForeignKey('student.id'), nullable=False, index=True, comment='学员ID')
    user_msg = db.Column(db.Text, nullable=True, comment='用户消息')
    ai_msg = db.Column(db.Text, nullable=True, comment='AI回复')
    is_collect = db.Column(db.SmallInteger, default=0, comment='是否收藏: 0否/1是')
    is_deleted = db.Column(db.SmallInteger, default=0, comment='是否删除: 0否/1是')
    expire_time = db.Column(db.DateTime, nullable=True, comment='过期时间')
    create_time = db.Column(db.DateTime, default=datetime.now, comment='创建时间')

    def to_dict(self):
        return {
            'id': self.id,
            'student_id': self.student_id,
            'user_msg': self.user_msg,
            'ai_msg': self.ai_msg,
            'is_collect': self.is_collect,
            'is_deleted': self.is_deleted,
            'create_time': self.create_time.strftime('%Y-%m-%d %H:%M:%S') if self.create_time else None,
        }
