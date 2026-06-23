"""
题库模型：Question（题目）、ErrorQuestion（错题本）
"""
from datetime import datetime
from app.extensions import db
from . import BaseModel


class Question(BaseModel):
    """题目表"""
    __tablename__ = 'question'

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True, comment='题目ID')
    know_id = db.Column(db.BigInteger, db.ForeignKey('knowledge.id'), nullable=True, index=True, comment='知识点ID')
    type = db.Column(db.SmallInteger, nullable=False, comment='题型: 1单选/2多选/3判断/4图片/5情景')
    difficulty = db.Column(db.SmallInteger, default=1, comment='难度: 1简单/2中等/3困难')
    train_type = db.Column(db.SmallInteger, default=1, comment='培训类型')
    subject = db.Column(db.SmallInteger, nullable=False, index=True, comment='科目: 1科一/4科四')
    content = db.Column(db.Text, nullable=False, comment='题干')
    image = db.Column(db.String(255), nullable=True, comment='题目图片URL')
    answer = db.Column(db.String(64), nullable=False, comment='正确答案')
    analysis = db.Column(db.Text, nullable=True, comment='解析')
    law = db.Column(db.Text, nullable=True, comment='法规原文')
    status = db.Column(db.SmallInteger, default=1, comment='状态: 1草稿/2待审核/3已上线/4作废')
    version = db.Column(db.Integer, default=1, comment='版本号')
    tags = db.Column(db.String(255), nullable=True, comment='标签(逗号分隔)')
    variant_ids = db.Column(db.String(255), nullable=True, comment='变体题目ID(逗号分隔)')
    create_time = db.Column(db.DateTime, default=datetime.now, comment='创建时间')
    update_time = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')

    # 关系
    error_questions = db.relationship('ErrorQuestion', backref='question', lazy='dynamic')

    def to_dict(self, include_answer=False):
        data = {
            'id': self.id,
            'know_id': self.know_id,
            'type': self.type,
            'difficulty': self.difficulty,
            'train_type': self.train_type,
            'subject': self.subject,
            'content': self.content,
            'image': self.image,
            'analysis': self.analysis,
            'law': self.law,
            'status': self.status,
            'version': self.version,
            'tags': self.tags.split(',') if self.tags else [],
        }
        if include_answer:
            data['answer'] = self.answer
        return data

    def to_practice_dict(self):
        """练习/考试用：不返回答案，但返回解析标记"""
        return {
            'id': self.id,
            'know_id': self.know_id,
            'type': self.type,
            'difficulty': self.difficulty,
            'subject': self.subject,
            'content': self.content,
            'image': self.image,
            'status': self.status,
            'tags': self.tags.split(',') if self.tags else [],
        }


class ErrorQuestion(BaseModel):
    """错题本表"""
    __tablename__ = 'error_question'

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True, comment='记录ID')
    student_id = db.Column(db.BigInteger, db.ForeignKey('student.id'), nullable=False, index=True, comment='学员ID')
    question_id = db.Column(db.BigInteger, db.ForeignKey('question.id'), nullable=False, index=True, comment='题目ID')
    error_type = db.Column(db.SmallInteger, default=4, comment='错因: 1概念不清/2审题失误/3混淆记忆/4其他')
    error_count = db.Column(db.Integer, default=1, comment='错误次数')
    update_time = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    create_time = db.Column(db.DateTime, default=datetime.now, comment='创建时间')

    __table_args__ = (
        db.UniqueConstraint('student_id', 'question_id', name='uk_student_question'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'student_id': self.student_id,
            'question_id': self.question_id,
            'error_type': self.error_type,
            'error_count': self.error_count,
            'update_time': self.update_time.strftime('%Y-%m-%d %H:%M:%S') if self.update_time else None,
        }
