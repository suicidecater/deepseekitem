"""
Flask 多环境配置
"""
import os
from datetime import timedelta

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class BaseConfig:
    """基础配置"""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'traffic-training-secret-key-change-in-production')

    # MySQL 数据库
    DB_USER = os.environ.get('DB_USER', 'root')
    DB_PASSWORD = os.environ.get('DB_PASSWORD', 'root123')
    DB_HOST = os.environ.get('DB_HOST', '127.0.0.1')
    DB_PORT = os.environ.get('DB_PORT', '3306')
    DB_NAME = os.environ.get('DB_NAME', 'traffic_training')
    SQLALCHEMY_DATABASE_URI = (
        f'mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
        '?charset=utf8mb4'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 20,
        'max_overflow': 40,
        'pool_recycle': 3600,
        'pool_pre_ping': True,
    }

    # Redis
    REDIS_HOST = os.environ.get('REDIS_HOST', '127.0.0.1')
    REDIS_PORT = int(os.environ.get('REDIS_PORT', 6379))
    REDIS_DB = int(os.environ.get('REDIS_DB', 0))
    REDIS_PASSWORD = os.environ.get('REDIS_PASSWORD', None)
    REDIS_URL = f'redis://{":" + REDIS_PASSWORD + "@" if REDIS_PASSWORD else ""}{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}'

    # JWT
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'jwt-secret-key-change-in-production')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=2)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=7)
    JWT_TOKEN_LOCATION = ['headers']
    JWT_HEADER_NAME = 'Authorization'
    JWT_HEADER_TYPE = 'Bearer'
    JWT_BLACKLIST_ENABLED = True
    JWT_BLACKLIST_TOKEN_CHECKS = ['access', 'refresh']

    # Celery
    CELERY_BROKER_URL = REDIS_URL + '/1'
    CELERY_RESULT_BACKEND = REDIS_URL + '/2'
    CELERY_TASK_SERIALIZER = 'json'
    CELERY_RESULT_SERIALIZER = 'json'
    CELERY_ACCEPT_CONTENT = ['json']
    CELERY_TIMEZONE = 'Asia/Shanghai'
    CELERY_ENABLE_UTC = False
    CELERY_TASK_TRACK_STARTED = True
    CELERY_TASK_TIME_LIMIT = 30 * 60  # 30分钟

    # 验证码
    VERIFY_CODE_LENGTH = 6
    VERIFY_CODE_EXPIRE = 300  # 5分钟
    VERIFY_CODE_RATE_LIMIT = 60  # 60秒内同邮箱/手机号限发送1次

    # QQ邮箱 SMTP
    SMTP_HOST = os.environ.get('SMTP_HOST', 'smtp.qq.com')
    SMTP_PORT = int(os.environ.get('SMTP_PORT', 587))
    SMTP_USER = os.environ.get('SMTP_USER', '')
    SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD', '')

    # 腾讯云短信 API（预留）
    TENCENT_SMS_SECRET_ID = os.environ.get('TENCENT_SMS_SECRET_ID', '')
    TENCENT_SMS_SECRET_KEY = os.environ.get('TENCENT_SMS_SECRET_KEY', '')
    TENCENT_SMS_SDK_APP_ID = os.environ.get('TENCENT_SMS_SDK_APP_ID', '')
    TENCENT_SMS_SIGN_NAME = os.environ.get('TENCENT_SMS_SIGN_NAME', '')

    # DeepSeek API
    DEEPSEEK_API_KEY = os.environ.get('DEEPSEEK_API_KEY', '')
    DEEPSEEK_BASE_URL = os.environ.get('DEEPSEEK_BASE_URL', 'https://api.deepseek.com/v1')
    DEEPSEEK_MODEL = os.environ.get('DEEPSEEK_MODEL', 'deepseek-chat')
    DEEPSEEK_TIMEOUT = 3  # 超时3秒
    DEEPSEEK_MAX_RETRIES = 2

    # 接口限流
    RATELIMIT_STORAGE_URL = REDIS_URL + '/3'
    RATELIMIT_DEFAULT = '200 per minute'

    # 分页
    DEFAULT_PAGE_SIZE = 20
    MAX_PAGE_SIZE = 100

    # CORS
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', 'http://localhost:5173').split(',')


class DevelopmentConfig(BaseConfig):
    """开发环境"""
    DEBUG = True
    SQLALCHEMY_ECHO = True
    RATELIMIT_ENABLED = False


class TestingConfig(BaseConfig):
    """测试环境"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    RATELIMIT_ENABLED = False
    CELERY_TASK_ALWAYS_EAGER = True


class ProductionConfig(BaseConfig):
    """生产环境"""
    DEBUG = False
    SQLALCHEMY_ECHO = False
    RATELIMIT_ENABLED = True
    RATELIMIT_DEFAULT = '100 per minute'


config_map = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig,
}
