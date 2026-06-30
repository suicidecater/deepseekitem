"""
题库模型：三张独立题库表（科目一/科目四/专业人员）
"""
from datetime import datetime
from app.extensions import db
from . import BaseModel

SOURCE_TABLES = {
    'subject1': 'subject1_question',
    'subject4': 'subject4_question',
    'professional': 'professional_question',
}


class BaseQuestionModel(BaseModel):
    """题库基类（抽象）"""
    __abstract__ = True

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True, comment='记录ID')
    question_number = db.Column(db.Integer, nullable=False, comment='题号')
    question_type = db.Column(db.String(16), nullable=False, comment='题型: 判断题/单选题/多选题')
    question_text = db.Column(db.Text, nullable=False, comment='题干')
    option_a = db.Column(db.String(255), nullable=True, comment='A选项')
    option_b = db.Column(db.String(255), nullable=True, comment='B选项')
    option_c = db.Column(db.String(255), nullable=True, comment='C选项')
    option_d = db.Column(db.String(255), nullable=True, comment='D选项')
    correct_answer = db.Column(db.String(16), nullable=False, comment='正确答案')
    image_file = db.Column(db.String(255), nullable=True, comment='附图文件名')
    category = db.Column(db.String(20), nullable=True, comment='分类: 交通标志/交通法规/安全常识/驾驶理论')
    difficulty = db.Column(db.Integer, default=1, comment='难度: 1-5')
    create_time = db.Column(db.DateTime, default=datetime.now, comment='创建时间')
    update_time = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')

    @property
    def source_table(self):
        """子类需覆盖"""
        return 'subject1'

    def get_options_list(self):
        """将 option_a/b/c/d 转为列表"""
        opts = []
        if self.option_a: opts.append('A. ' + self.option_a)
        if self.option_b: opts.append('B. ' + self.option_b)
        if self.option_c: opts.append('C. ' + self.option_c)
        if self.option_d: opts.append('D. ' + self.option_d)
        return opts

    def to_dict(self, include_answer=False):
        data = {
            'id': self.id,
            'source': self.source_table,
            'questionNumber': self.question_number,
            'questionType': self.question_type,
            'questionText': self.question_text,
            'optionA': self.option_a,
            'optionB': self.option_b,
            'optionC': self.option_c,
            'optionD': self.option_d,
            'imageFile': self.image_file,
            'category': self.category,
            'difficulty': self.difficulty,
        }
        if include_answer:
            data['correctAnswer'] = self.correct_answer
        return data

    def to_practice_dict(self):
        """练习/考试用：不返回答案，返回前端格式"""
        return {
            'id': self.id,
            'source': self.source_table,
            'type': QuestionService.map_type(self.question_type),
            'category': self.category,
            'difficulty': self.difficulty,
            'content': self.question_text,
            'image': self.image_file,
            'options': self.get_options_list(),
        }


class Subject1Question(BaseQuestionModel):
    __tablename__ = 'subject1_question'
    source_table = 'subject1'

class Subject4Question(BaseQuestionModel):
    __tablename__ = 'subject4_question'
    source_table = 'subject4'

class ProfessionalQuestion(BaseQuestionModel):
    __tablename__ = 'professional_question'
    source_table = 'professional'


# 向下兼容别名
Question = Subject1Question   # 旧代码引用 Question 时使用科目一表

# 延迟导入（避免循环依赖）
class QuestionService:
    @staticmethod
    def map_type(type_str):
        """将中文题型映射为英文"""
        return {'判断题': 'judge', '单选题': 'single', '多选题': 'multiple'}.get(type_str, 'single')

    @staticmethod
    def map_type_int(type_str):
        return {'判断题': 3, '单选题': 1, '多选题': 2}.get(type_str, 1)

    @staticmethod
    def get_table(source):
        """根据 source 获取对应的模型类"""
        return {'subject1': Subject1Question, 'subject4': Subject4Question, 'professional': ProfessionalQuestion}.get(source)


# 错题本
class ErrorQuestion(BaseModel):
    __tablename__ = 'error_question'

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True, comment='记录ID')
    student_id = db.Column(db.BigInteger, db.ForeignKey('student.id'), nullable=False, index=True, comment='学员ID')
    question_id = db.Column(db.BigInteger, nullable=False, index=True, comment='题目ID')
    source = db.Column(db.String(20), nullable=False, default='subject1', comment='来源: subject1/subject4/professional')
    error_type = db.Column(db.SmallInteger, default=4, comment='错因')
    error_count = db.Column(db.Integer, default=1, comment='错误次数')
    update_time = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    create_time = db.Column(db.DateTime, default=datetime.now)

    __table_args__ = (db.UniqueConstraint('student_id', 'question_id', 'source', name='uk_student_question'),)

    def to_dict(self):
        return {
            'id': self.id,
            'studentId': self.student_id,
            'questionId': self.question_id,
            'source': self.source,
            'errorType': {1: '概念不清', 2: '审题失误', 3: '混淆记忆', 4: '其他'}.get(self.error_type, '其他'),
            'errorCount': self.error_count,
        }


# 学员记忆曲线
class StudentQuestionMemory(BaseModel):
    __tablename__ = 'student_question_memory'

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    student_id = db.Column(db.BigInteger, db.ForeignKey('student.id'), nullable=False, index=True)
    question_id = db.Column(db.BigInteger, nullable=False, index=True)
    source = db.Column(db.String(20), nullable=False, default='subject1')
    memory_strength = db.Column(db.Float, default=1.0)
    review_count = db.Column(db.Integer, default=0)
    last_review_time = db.Column(db.DateTime, nullable=True)
    next_review_time = db.Column(db.DateTime, nullable=True)

    __table_args__ = (db.UniqueConstraint('student_id', 'question_id', 'source', name='uk_student_question_mem'),)

    def to_dict(self):
        return {
            'id': self.id,
            'questionId': self.question_id,
            'source': self.source,
            'memoryStrength': self.memory_strength,
            'reviewCount': self.review_count,
        }
