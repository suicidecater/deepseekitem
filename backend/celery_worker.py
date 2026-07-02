"""
Celery Worker 入口
启动命令：celery -A celery_worker.celery worker --loglevel=info --concurrency=4
"""
from app import create_app
from app.extensions import celery

app = create_app()
app.app_context().push()
