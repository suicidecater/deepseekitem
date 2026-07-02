"""
Flask + SocketIO 开发启动入口
- 自动创建数据库表（开发环境）
- 使用 flask_app 变量名避免与 app 模块名冲突
"""
import os
import logging
from app import create_app
from app.extensions import db, socketio

# 变量名用 flask_app 避免与 app 模块冲突
flask_app = create_app()

# 开发环境自动建表（确保 conversation、chat_message 等新表存在）
with flask_app.app_context():
    try:
        # 导入所有模型以便 SQLAlchemy 检测表结构
        import app.models.user       # noqa: F401  (Student, Coach, PlatformAdmin)
        import app.models.chat       # noqa: F401  (Conversation, ChatMessage)
        import app.models.question   # noqa: F401
        import app.models.exam       # noqa: F401  (Evaluation, PracticeExam)
        import app.models.social     # noqa: F401
        import app.models.study      # noqa: F401
        import app.models.knowledge  # noqa: F401
        import app.models.system_config  # noqa: F401

        db.create_all()
        logging.getLogger(__name__).info('数据库表检查/创建完成')
    except Exception as e:
        logging.getLogger(__name__).warning(f'自动建表跳过（可能表已存在）: {e}')

# 开发环境：使用 Flask-SocketIO 的 run 以支持 WebSocket
if __name__ == '__main__':
    socketio.run(
        flask_app,
        host='0.0.0.0',
        port=5000,
        use_reloader=False,
        allow_unsafe_werkzeug=True
    )
