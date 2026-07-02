"""
Flask 扩展初始化
"""
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_jwt_extended import JWTManager
from flask_socketio import SocketIO
from celery import Celery
import redis as redis_client

# SQLAlchemy ORM
db = SQLAlchemy()

# 数据库迁移
migrate = Migrate()

# CORS 跨域
cors = CORS()

# JWT 认证
jwt = JWTManager()

# Redis
redis_store: redis_client.Redis = None

# Celery
celery = Celery()

# 限流器
limiter = Limiter(key_func=get_remote_address)

# WebSocket (Flask-SocketIO)
socketio = SocketIO()


def init_extensions(app):
    """初始化所有 Flask 扩展"""
    db.init_app(app)
    migrate.init_app(app, db)
    cors.init_app(app, resources={
        r"/api/*": {"origins": app.config.get('CORS_ORIGINS', '*')}
    })
    jwt.init_app(app)
    limiter.init_app(app)

    # 初始化 SocketIO
    socketio.init_app(
        app,
        cors_allowed_origins=app.config.get('CORS_ORIGINS', '*'),
        async_mode=app.config.get('SOCKETIO_ASYNC_MODE', 'threading'),
        logger=app.config.get('SOCKETIO_LOGGER', False),
        engineio_logger=app.config.get('SOCKETIO_ENGINEIO_LOGGER', False),
        ping_timeout=app.config.get('SOCKETIO_PING_TIMEOUT', 60),
        ping_interval=app.config.get('SOCKETIO_PING_INTERVAL', 25),
    )

    # 初始化 Redis 连接
    global redis_store
    redis_config = app.config['REDIS_URL']
    redis_store = redis_client.from_url(redis_config, decode_responses=True)

    # 初始化 Celery
    init_celery(app)


def init_celery(app):
    """配置 Celery"""
    celery.conf.update(
        broker_url=app.config['CELERY_BROKER_URL'],
        result_backend=app.config['CELERY_RESULT_BACKEND'],
        task_serializer=app.config['CELERY_TASK_SERIALIZER'],
        result_serializer=app.config['CELERY_RESULT_SERIALIZER'],
        accept_content=app.config['CELERY_ACCEPT_CONTENT'],
        timezone=app.config['CELERY_TIMEZONE'],
        enable_utc=app.config['CELERY_ENABLE_UTC'],
        task_track_started=app.config['CELERY_TASK_TRACK_STARTED'],
        task_time_limit=app.config['CELERY_TASK_TIME_LIMIT'],
    )

    class ContextTask(celery.Task):
        """在 Celery 任务中自动注入 Flask 应用上下文"""
        abstract = True

        def __call__(self, *args, **kwargs):
            with app.app_context():
                return super().__call__(*args, **kwargs)

    celery.Task = ContextTask
    return celery
