"""
数据模型统一基类和导入入口
"""
from app.extensions import db

# 统一基类
class BaseModel(db.Model):
    """抽象基类，提供通用方法"""
    __abstract__ = True

    @classmethod
    def get_by_id(cls, obj_id):
        return cls.query.get(obj_id)

    @classmethod
    def get_or_404(cls, obj_id):
        return cls.query.get_or_404(obj_id)

    def save(self):
        db.session.add(self)
        db.session.commit()
        return self

    def update(self, **kwargs):
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        db.session.commit()
        return self

    def delete(self, soft=False):
        if soft and hasattr(self, 'status'):
            self.status = 99  # 逻辑删除状态
            db.session.commit()
        else:
            db.session.delete(self)
            db.session.commit()
