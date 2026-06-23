"""
Flask 应用工厂
"""
import os
from flask import Flask
from .config import config_map
from .extensions import init_extensions


def create_app(config_name=None):
    """创建 Flask 应用实例"""
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')

    app = Flask(__name__)
    app.config.from_object(config_map.get(config_name, config_map['default']))

    # 初始化扩展（SQLAlchemy, Redis, JWT, Celery, Limiter）
    init_extensions(app)

    # 注册 API 蓝图
    from .api.auth import auth_bp
    from .api.student import student_bp
    from .api.question import question_bp
    from .api.ai import ai_bp
    from .api.coach import coach_bp
    from .api.admin import admin_bp
    from .api.cms import cms_bp

    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(student_bp, url_prefix='/api/student')
    app.register_blueprint(question_bp, url_prefix='/api/question')
    app.register_blueprint(ai_bp, url_prefix='/api/ai')
    app.register_blueprint(coach_bp, url_prefix='/api/coach')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    app.register_blueprint(cms_bp, url_prefix='/api/cms')

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
