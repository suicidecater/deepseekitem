"""
Gunicorn WSGI 入口
启动命令：gunicorn -c gunicorn.conf.py wsgi:app
"""
from app import create_app

app = create_app()
