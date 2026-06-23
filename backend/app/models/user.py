"""
用户体系模型：Student（学员）、Coach（教练）、PlatformAdmin（平台管理员）
"""
from datetime import datetime
from app.extensions import db
from . import BaseModel


class Student(BaseModel):
    """学员表"""
    __tablename__ = 'student'

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True, comment='学员ID')
    email = db.Column(db.String(64), unique=True, nullable=False, index=True, comment='邮箱')
    password = db.Column(db.String(64), nullable=False, comment='密码(bcrypt加密)')
    phone = db.Column(db.String(64), unique=True, nullable=True, index=True, comment='手机号')
    name = db.Column(db.String(32), nullable=True, comment='姓名')
    coach_id = db.Column(db.BigInteger, db.ForeignKey('coach.id'), nullable=True, index=True, comment='教练ID')
    train_type = db.Column(db.SmallInteger, default=1, comment='培训类型: 1驾考/2客运/3货运/4危险品')
    car_type = db.Column(db.String(8), nullable=True, comment='车型: C1/C2/A1/A2')
    status = db.Column(db.SmallInteger, default=1, comment='状态: 1正常/2结业/3弃学/4禁用')
    create_time = db.Column(db.DateTime, default=datetime.now, comment='创建时间')
    update_time = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')

    # 关系
    coach = db.relationship('Coach', backref=db.backref('students', lazy='dynamic'))
    evaluations = db.relationship('Evaluation', backref='student', lazy='dynamic')
    practice_exams = db.relationship('PracticeExam', backref='student', lazy='dynamic')
    study_plans = db.relationship('StudyPlan', backref='student', lazy='dynamic')
    error_questions = db.relationship('ErrorQuestion', backref='student', lazy='dynamic')
    ai_chats = db.relationship('AiChat', backref='student', lazy='dynamic')
    medals = db.relationship('UserMedal', backref='student', lazy='dynamic')
    notes = db.relationship('Note', backref='student', lazy='dynamic')

    def to_dict(self, include_sensitive=False):
        data = {
            'id': self.id,
            'email': self.email,
            'phone': self.phone,
            'name': self.name,
            'coach_id': self.coach_id,
            'train_type': self.train_type,
            'car_type': self.car_type,
            'status': self.status,
            'create_time': self.create_time.strftime('%Y-%m-%d %H:%M:%S') if self.create_time else None,
        }
        if include_sensitive:
            data['password'] = self.password
        return data


class Coach(BaseModel):
    """教练表"""
    __tablename__ = 'coach'

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True, comment='教练ID')
    email = db.Column(db.String(64), unique=True, nullable=False, index=True, comment='邮箱')
    password = db.Column(db.String(64), nullable=False, comment='密码(bcrypt加密)')
    phone = db.Column(db.String(64), unique=True, nullable=True, index=True, comment='手机号')
    school_name = db.Column(db.String(128), nullable=True, comment='驾校名称')
    school_address = db.Column(db.String(255), nullable=True, comment='驾校地址')
    school_phone = db.Column(db.String(64), nullable=True, comment='驾校电话')
    train_type = db.Column(db.SmallInteger, default=1, comment='培训类型')
    status = db.Column(db.SmallInteger, default=1, comment='状态: 1正常/2离职/3禁用')
    create_time = db.Column(db.DateTime, default=datetime.now, comment='创建时间')
    update_time = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')

    def to_dict(self, include_sensitive=False):
        data = {
            'id': self.id,
            'email': self.email,
            'phone': self.phone,
            'school_name': self.school_name,
            'school_address': self.school_address,
            'school_phone': self.school_phone,
            'train_type': self.train_type,
            'status': self.status,
        }
        if include_sensitive:
            data['password'] = self.password
        return data


class PlatformAdmin(BaseModel):
    """平台管理员表"""
    __tablename__ = 'platform_admin'

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True, comment='管理员ID')
    email = db.Column(db.String(64), unique=True, nullable=False, index=True, comment='邮箱')
    password = db.Column(db.String(64), nullable=False, comment='密码(bcrypt加密)')
    phone = db.Column(db.String(64), unique=True, nullable=True, index=True, comment='手机号')
    admin_type = db.Column(db.SmallInteger, default=2, comment='管理员类型: 1超级/2内容/3运营')
    status = db.Column(db.SmallInteger, default=1, comment='状态: 1正常/2禁用')
    create_time = db.Column(db.DateTime, default=datetime.now, comment='创建时间')
    update_time = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')

    def to_dict(self, include_sensitive=False):
        data = {
            'id': self.id,
            'email': self.email,
            'phone': self.phone,
            'admin_type': self.admin_type,
            'status': self.status,
        }
        if include_sensitive:
            data['password'] = self.password
        return data
