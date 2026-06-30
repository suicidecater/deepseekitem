"""
Flask 应用工厂
"""
import os
import logging
import importlib
from flask import Flask
from .config import config_map
from .extensions import init_extensions, redis_store, jwt


def create_app(config_name=None):
    """创建 Flask 应用实例"""
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')

    app = Flask(__name__)
    app.config.from_object(config_map.get(config_name, config_map['default']))

    # 初始化扩展（SQLAlchemy, Redis, JWT, Celery, Limiter）
    init_extensions(app)

    # JWT黑名单检查回调（用于logout）
    @jwt.token_in_blocklist_loader
    def check_if_token_in_blocklist(jwt_header, jwt_payload):
        jti = jwt_payload.get('jti')
        if jti is None:
            return False
        if redis_store is None:
            return False
        return redis_store.exists(f'jwt_blacklist:{jti}')

    # 注册 API 蓝图（只有已实现的蓝图才会注册）
    blueprint_registry = {
        ('api.auth', 'auth_bp'): '/api/auth',
        ('api.student', 'student_bp'): '/api/student',
        ('api.question', 'question_bp'): '/api/question',
        ('api.ai', 'ai_bp'): '/api/ai',
        ('api.coach', 'coach_bp'): '/api/coach',
        ('api.admin', 'admin_bp'): '/api/admin',
        ('api.cms', 'cms_bp'): '/api/cms',
    }

    for (module_path, bp_name), url_prefix in blueprint_registry.items():
        try:
            mod = importlib.import_module(f'.{module_path}', package='app')
            bp = getattr(mod, bp_name, None)
            if bp is not None:
                app.register_blueprint(bp, url_prefix=url_prefix)
                logging.getLogger(__name__).info(f'Blueprint registered: {url_prefix}')
        except (ImportError, ModuleNotFoundError) as e:
            logging.getLogger(__name__).warning(
                f'Blueprint {url_prefix} not available ({module_path}): {e}'
            )

    # 健康检查
    @app.route('/api/health')
    def health_check():
        return {'code': 200, 'message': 'ok', 'data': {'status': 'healthy'}}

    # 全局错误处理
    from .utils.response import error
    from flask_jwt_extended.exceptions import NoAuthorizationError, InvalidHeaderError

    @app.errorhandler(400)
    def bad_request(e):
        return error(400, str(e.description) if hasattr(e, 'description') else '请求参数错误')

    @app.errorhandler(404)
    def not_found(e):
        return error(404, '资源不存在')

    @app.errorhandler(405)
    def method_not_allowed(e):
        return error(405, '请求方法不允许')

    @app.errorhandler(429)
    def too_many_requests(e):
        return error(429, '请求过于频繁，请稍后再试')

    @app.errorhandler(500)
    def internal_error(e):
        return error(500, '服务器内部错误')

    @app.errorhandler(NoAuthorizationError)
    def handle_no_auth(e):
        return error(401, '未提供认证Token')

    @app.errorhandler(InvalidHeaderError)
    def handle_invalid_header(e):
        return error(401, '认证Token格式无效')

    return app
