"""
系统配置模型：system_config 表
用于存储运行时可变的系统配置项（如 DeepSeek API Key、QQ邮箱地址等）

敏感配置项（如 deepseek_api_key）存储时自动 AES 加密，读取时自动解密。
管理员可通过 /api/admin/config 和 /api/admin/cms/api-config 端点管理。
"""
from datetime import datetime
from app.extensions import db
from . import BaseModel


# 需要加密存储的敏感配置键
SENSITIVE_KEYS = {'deepseek_api_key'}


class SystemConfig(BaseModel):
    """系统配置表"""
    __tablename__ = 'system_config'

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True, comment='配置ID')
    config_key = db.Column(db.String(64), unique=True, nullable=False, index=True, comment='配置键')
    config_value = db.Column(db.Text, nullable=True, comment='配置值（敏感项AES加密存储）')
    description = db.Column(db.String(255), nullable=True, comment='配置说明')
    updated_by = db.Column(db.BigInteger, nullable=True, comment='更新人ID')
    update_time = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    create_time = db.Column(db.DateTime, default=datetime.now, comment='创建时间')

    def to_dict(self, mask_sensitive=True):
        value = self.config_value
        if self.config_key in SENSITIVE_KEYS and mask_sensitive:
            value = SystemConfig._mask_value(value)
        return {
            'id': self.id,
            'config_key': self.config_key,
            'config_value': value,
            'description': self.description,
            'updated_by': self.updated_by,
            'update_time': self.update_time.strftime('%Y-%m-%d %H:%M:%S') if self.update_time else None,
        }

    @staticmethod
    def _mask_value(value):
        """脱敏显示：sk-****xxxx"""
        if not value:
            return ''
        if len(value) > 8:
            return value[:4] + '****' + value[-4:]
        elif len(value) > 2:
            return value[:2] + '****'
        return '****'

    @classmethod
    def get_value(cls, key, default=None):
        """
        根据 config_key 获取配置值（自动解密敏感项）
        """
        config = cls.query.filter_by(config_key=key).first()
        if config:
            value = config.config_value
            if key in SENSITIVE_KEYS and value:
                from app.utils.crypto import decrypt
                try:
                    value = decrypt(value)
                except Exception:
                    pass
            return value
        return default

    @classmethod
    def set_value(cls, key, value, description=None, updated_by=None):
        """
        设置或更新配置值（敏感项自动AES加密存储）
        """
        # 敏感项加密
        stored_value = value
        if key in SENSITIVE_KEYS and value:
            from app.utils.crypto import encrypt
            try:
                stored_value = encrypt(value)
            except Exception:
                stored_value = value  # 加密失败时原样存储

        config = cls.query.filter_by(config_key=key).first()
        if config:
            config.config_value = stored_value
            if description is not None:
                config.description = description
            if updated_by is not None:
                config.updated_by = updated_by
            config.update_time = datetime.now()
            db.session.commit()
        else:
            config = cls(
                config_key=key,
                config_value=stored_value,
                description=description,
                updated_by=updated_by,
            )
            config.save()
        return config
