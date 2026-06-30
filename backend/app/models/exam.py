"""
考试测评模型：Evaluation（能力测评）、PracticeExam（练习考试一体化）
"""
from datetime import datetime
from app.extensions import db
from . import BaseModel


class Evaluation(BaseModel):
    """能力测评表（每人每方向仅一条记录）"""
    __tablename__ = 'evaluation'
    __table_args__ = (
        db.UniqueConstraint('student_id', 'study_subject', name='uq_student_subject_eval'),
    )

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True, comment='测评ID')
    student_id = db.Column(db.BigInteger, db.ForeignKey('student.id'), nullable=False, index=True, comment='学员ID')
    study_subject = db.Column(db.SmallInteger, default=1, nullable=False, comment='学习方向: 1科目一/4科目四/5专业人员')
    total_score = db.Column(db.Integer, default=0, comment='总分')
    sign_score = db.Column(db.Integer, default=0, comment='标志标线得分')
    law_score = db.Column(db.Integer, default=0, comment='法律法规得分')
    safe_score = db.Column(db.Integer, default=0, comment='安全文明得分')
    drive_score = db.Column(db.Integer, default=0, comment='驾驶操作得分')
    level = db.Column(db.String(16), nullable=True, comment='能力等级: 入门/基础/进阶/冲刺')
    weak_know = db.Column(db.Text, nullable=True, comment='薄弱知识点(JSON)')
    simple_rate = db.Column(db.Integer, default=0, comment='简单题全局正确率(%)')
    mid_rate = db.Column(db.Integer, default=0, comment='中等题全局正确率(%)')
    diff_detail = db.Column(db.Text, nullable=True, comment='难度分层详情(JSON: 四维度×两难度)')
    create_time = db.Column(db.DateTime, default=datetime.now, comment='测评时间')

    def to_dict(self):
        return {
            'id': self.id,
            'student_id': self.student_id,
            'study_subject': self.study_subject,
            'total_score': self.total_score,
            'sign_score': self.sign_score,
            'law_score': self.law_score,
            'safe_score': self.safe_score,
            'drive_score': self.drive_score,
            'level': self.level,
            'weak_know': self.weak_know,
            'simple_rate': self.simple_rate,
            'mid_rate': self.mid_rate,
            'diff_detail': self.diff_detail,
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


class AbilityAssessment(BaseModel):
    """能力测评表"""
    __tablename__ = 'ability_assessment'

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True, comment='测评ID')
    student_id = db.Column(db.BigInteger, nullable=False, index=True, comment='关联student.id')
    total_score = db.Column(db.Integer, nullable=False, comment='总分')
    sign_score = db.Column(db.Integer, nullable=False, comment='交通标志得分')
    law_score = db.Column(db.Integer, nullable=False, comment='交通法规得分')
    safe_score = db.Column(db.Integer, nullable=False, comment='安全常识得分')
    drive_score = db.Column(db.Integer, nullable=False, comment='驾驶理论得分')
    level = db.Column(db.String(16), nullable=True, comment='能力等级')
    weak_know = db.Column(db.Text, nullable=True, comment='薄弱方面')
    create_time = db.Column(db.DateTime, default=datetime.now, comment='测评时间')

    def to_dict(self):
        return {
            'id': self.id,
            'studentId': self.student_id,
            'totalScore': self.total_score,
            'signScore': self.sign_score,
            'lawScore': self.law_score,
            'safeScore': self.safe_score,
            'driveScore': self.drive_score,
            'level': self.level,
            'weakKnow': self.weak_know,
            'createTime': self.create_time.strftime('%Y-%m-%d %H:%M:%S') if self.create_time else None,
        }
