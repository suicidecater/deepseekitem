"""
考试测评模型：Evaluation（能力测评）、PracticeExam（练习考试一体化）
"""
from datetime import datetime
from app.extensions import db
from . import BaseModel


class Evaluation(BaseModel):
    """能力测评表"""
    __tablename__ = 'evaluation'

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True, comment='测评ID')
    student_id = db.Column(db.BigInteger, db.ForeignKey('student.id'), nullable=False, index=True, comment='学员ID')
    total_score = db.Column(db.Integer, default=0, comment='总分')
    sign_score = db.Column(db.Integer, default=0, comment='标志标线得分')
    law_score = db.Column(db.Integer, default=0, comment='法律法规得分')
    safe_score = db.Column(db.Integer, default=0, comment='安全文明得分')
    drive_score = db.Column(db.Integer, default=0, comment='驾驶操作得分')
    level = db.Column(db.String(16), nullable=True, comment='能力等级: 入门/基础/进阶/冲刺')
    weak_know = db.Column(db.Text, nullable=True, comment='薄弱知识点(JSON)')
    create_time = db.Column(db.DateTime, default=datetime.now, comment='测评时间')

    def to_dict(self):
        return {
            'id': self.id,
            'student_id': self.student_id,
            'total_score': self.total_score,
            'sign_score': self.sign_score,
            'law_score': self.law_score,
            'safe_score': self.safe_score,
            'drive_score': self.drive_score,
            'level': self.level,
            'weak_know': self.weak_know,
            'create_time': self.create_time.strftime('%Y-%m-%d %H:%M:%S') if self.create_time else None,
        }


class PracticeExam(BaseModel):
    """练习考试一体化表"""
    __tablename__ = 'practice_exam'

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True, comment='记录ID')
    student_id = db.Column(db.BigInteger, db.ForeignKey('student.id'), nullable=False, index=True, comment='学员ID')
    biz_type = db.Column(db.SmallInteger, nullable=False, comment='业务类型: 1练习/2考试')
    subject = db.Column(db.SmallInteger, nullable=False, comment='科目: 1科一/4科四')
    question_ids = db.Column(db.String(1024), nullable=True, comment='题目ID列表(逗号分隔)')
    user_answers = db.Column(db.Text, nullable=True, comment='用户答案(JSON)')
    total_time = db.Column(db.Integer, default=0, comment='总用时(秒)')
    score = db.Column(db.Integer, default=0, comment='得分')
    correct_rate = db.Column(db.Numeric(5, 2), default=0.00, comment='正确率(%)')
    status = db.Column(db.SmallInteger, default=1, comment='状态: 1进行中/2已完成/3已交卷')
    create_time = db.Column(db.DateTime, default=datetime.now, comment='开始时间')
    end_time = db.Column(db.DateTime, nullable=True, comment='结束时间')

    def to_dict(self):
        return {
            'id': self.id,
            'student_id': self.student_id,
            'biz_type': self.biz_type,
            'subject': self.subject,
            'question_ids': self.question_ids,
            'user_answers': self.user_answers,
            'total_time': self.total_time,
            'score': self.score,
            'correct_rate': float(self.correct_rate) if self.correct_rate else 0,
            'status': self.status,
            'create_time': self.create_time.strftime('%Y-%m-%d %H:%M:%S') if self.create_time else None,
            'end_time': self.end_time.strftime('%Y-%m-%d %H:%M:%S') if self.end_time else None,
        }
