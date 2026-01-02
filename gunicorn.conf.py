from config import Config

workers = Config.GUNICORN_WORKERS
# 使用sync worker避免gevent与SSL的兼容性问题
worker_class = 'sync'  
bind = Config.GUNICORN_BIND

# 增加超时时间，支持长响应
timeout = 300  # 5分钟超时

# 保持连接活跃，支持长轮询
keepalive = 5  # 保持TCP连接5秒

# 限制单个请求大小（防止恶意请求）
limit_request_line = 4096
limit_request_fields = 100
