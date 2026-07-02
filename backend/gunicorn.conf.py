"""
Gunicorn 配置文件
启动命令：gunicorn -c gunicorn.conf.py wsgi:app
"""
import multiprocessing

# 绑定地址
bind = '0.0.0.0:8000'

# Worker 配置
workers = 4
worker_class = 'sync'
worker_connections = 1000
timeout = 120
keepalive = 5

# 日志
accesslog = 'logs/gunicorn_access.log'
errorlog = 'logs/gunicorn_error.log'
loglevel = 'info'

# 进程名
proc_name = 'traffic_training_backend'

# 守护进程（生产环境启用）
# daemon = True
# pidfile = 'logs/gunicorn.pid'
