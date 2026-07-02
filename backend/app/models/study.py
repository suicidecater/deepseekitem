"""
学习相关模型：StudyPlan（学习计划）、AiLearningPath（AI学习路径缓存）、AiChat（AI对话）
"""
from datetime import datetime, date
from app.extensions import db
from . import BaseModel


class StudyPlan(BaseModel):
    """学习计划表"""
    __tablename__ = 'study_plan'

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True, comment='计划ID')
    student_id = db.Column(db.BigInteger, db.ForeignKey('student.id'), nullable=False, index=True, comment='学员ID')
    study_subject = db.Column(db.SmallInteger, default=1, comment='学习方向: 1=科目一/4=科目四/5=专业人员')
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
            'study_subject': self.study_subject,
            'plan_type': self.plan_type,
            'content': self.content,
            'task_date': self.task_date.strftime('%Y-%m-%d') if self.task_date else None,
            'status': self.status,
        }


class AiLearningPath(BaseModel):
    """AI学习路径缓存表 — 测评结果不变则不重调DeepSeek"""
    __tablename__ = 'ai_learning_path'

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True, comment='路径ID')
    student_id = db.Column(db.BigInteger, db.ForeignKey('student.id'), nullable=False, comment='学员ID')
    study_subject = db.Column(db.SmallInteger, default=1, comment='学习方向: 1/4/5')
    evaluation_id = db.Column(db.BigInteger, nullable=True, comment='关联的测评记录ID')
    content = db.Column(db.Text, nullable=False, comment='AI生成的完整学习路径JSON')
    generated_at = db.Column(db.DateTime, default=datetime.now, comment='生成时间')
    __table_args__ = (
        db.Index('idx_student_subject_path', 'student_id', 'study_subject', unique=True),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'student_id': self.student_id,
            'study_subject': self.study_subject,
            'evaluation_id': self.evaluation_id,
            'content': self.content,
            'generated_at': self.generated_at.strftime('%Y-%m-%d %H:%M') if self.generated_at else None,
        }


class AiChat(BaseModel):
    """AI对话表"""
    __tablename__ = 'ai_chat'

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True, comment='对话ID')
    student_id = db.Column(db.BigInteger, db.ForeignKey('student.id'), nullable=False, index=True, comment='关联student.id')
    user_msg = db.Column(db.Text, nullable=False, comment='用户提问')
    ai_msg = db.Column(db.Text, nullable=False, comment='AI回复')
    is_collect = db.Column(db.SmallInteger, nullable=False, default=0, comment='1收藏 0未收藏')
    is_deleted = db.Column(db.SmallInteger, nullable=False, default=0, comment='1已删除 0正常')
    expire_time = db.Column(db.DateTime, nullable=True, comment='过期时间')
    create_time = db.Column(db.DateTime, default=datetime.now, comment='对话时间')

    def to_dict(self):
        return {
            'id': self.id,
            'studentId': self.student_id,
            'userMsg': self.user_msg,
            'aiMsg': self.ai_msg,
            'isCollect': self.is_collect,
            'isDeleted': self.is_deleted,
            'expireTime': self.expire_time.strftime('%Y-%m-%d %H:%M:%S') if self.expire_time else None,
            'createTime': self.create_time.strftime('%Y-%m-%d %H:%M:%S') if self.create_time else None,
        }
