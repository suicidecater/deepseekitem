"""
知识体系模型：Knowledge（知识点）、Course（课程）、Material（学习资料）
"""
from datetime import datetime
from app.extensions import db
from . import BaseModel


class Knowledge(BaseModel):
    """知识点表"""
    __tablename__ = 'knowledge'

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True, comment='知识点ID')
    category_code = db.Column(db.SmallInteger, nullable=False, index=True, comment='分类: 1法规/2标志/3安全')
    category_name = db.Column(db.String(64), nullable=False, comment='分类名称')
    title = db.Column(db.String(128), nullable=False, comment='知识点标题')
    content = db.Column(db.Text, nullable=True, comment='知识点内容')
    train_type = db.Column(db.SmallInteger, default=1, comment='适用培训类型')
    difficulty = db.Column(db.SmallInteger, default=1, comment='难度: 1简单/2中等/3困难')
    create_time = db.Column(db.DateTime, default=datetime.now, comment='创建时间')

    # 关系（独立题库表无 know_id 外键，暂时移除 questions 关系）
    materials = db.relationship('Material', backref='knowledge', lazy='dynamic')

    def to_dict(self):
        return {
            'id': self.id,
            'category_code': self.category_code,
            'category_name': self.category_name,
            'title': self.title,
            'content': self.content,
            'train_type': self.train_type,
            'difficulty': self.difficulty,
        }


class Course(BaseModel):
    """课程表"""
    __tablename__ = 'course'

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True, comment='课程ID')
    title = db.Column(db.String(128), nullable=False, comment='课程标题')
    type = db.Column(db.SmallInteger, nullable=False, comment='类型: 1图文/2视频/3专项课/4章节')
    train_type = db.Column(db.SmallInteger, default=1, comment='培训类型')
    car_type = db.Column(db.String(8), nullable=True, comment='适用车型')
    tags = db.Column(db.String(255), nullable=True, comment='标签(逗号分隔)')
    status = db.Column(db.SmallInteger, default=1, comment='状态: 1草稿/2待审核/3已上线/4已下架')
    parent_id = db.Column(db.BigInteger, default=0, comment='父课程ID(0=顶级)')
    sort = db.Column(db.Integer, default=0, comment='排序')
    create_time = db.Column(db.DateTime, default=datetime.now, comment='创建时间')
    update_time = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')

    # 关系
    materials = db.relationship('Material', backref='course', lazy='dynamic')

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'type': self.type,
            'train_type': self.train_type,
            'car_type': self.car_type,
            'tags': self.tags.split(',') if self.tags else [],
            'status': self.status,
            'parent_id': self.parent_id,
            'sort': self.sort,
        }


class Material(BaseModel):
    """学习资料表"""
    __tablename__ = 'material'

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True, comment='资料ID')
    course_id = db.Column(db.BigInteger, db.ForeignKey('course.id'), nullable=False, index=True, comment='课程ID')
    know_id = db.Column(db.BigInteger, db.ForeignKey('knowledge.id'), nullable=True, index=True, comment='知识点ID')
    name = db.Column(db.String(128), nullable=False, comment='资料名称')
    url = db.Column(db.String(255), nullable=True, comment='资料URL')
    status = db.Column(db.SmallInteger, default=1, comment='状态: 1正常/2下架')
    create_time = db.Column(db.DateTime, default=datetime.now, comment='创建时间')

    def to_dict(self):
        return {
            'id': self.id,
            'course_id': self.course_id,
            'know_id': self.know_id,
            'name': self.name,
            'url': self.url,
            'status': self.status,
        }
