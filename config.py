"""配置文件"""
import os
import hanlp

class Config:
    """应用配置"""
    
    # Flask配置
    DEBUG = os.environ.get('DEBUG', 'False') == 'True'
    PORT = int(os.environ.get('PORT', 8000))
    
    # 脱敏配置
    DEFAULT_REPLACEMENT = os.environ.get('DEFAULT_REPLACEMENT', '[SECRET]')
    DEFAULT_SCOPE = os.environ.get('DEFAULT_SCOPE', 'basic')  # basic, enhanced, full
    
    # 远程API配置
    REMOTE_API_ENDPOINT = os.environ.get('REMOTE_API_ENDPOINT', 'https://api.openai.com')
    REMOTE_API_KEY = os.environ.get('REMOTE_API_KEY', '')
    
    # 代理配置
    PROXY_TIMEOUT = int(os.environ.get('PROXY_TIMEOUT', 300))  # 秒（5分钟）
    
    # HanLP模型配置
    HANLP_MODEL = hanlp.pretrained.mtl.CLOSE_TOK_POS_NER_SRL_DEP_SDP_CON_ELECTRA_BASE_ZH
    
    # Gunicorn配置
    GUNICORN_WORKERS = int(os.environ.get('GUNICORN_WORKERS', 1))
    GUNICORN_WORKER_CLASS = os.environ.get('GUNICORN_WORKER_CLASS', 'gevent')
    GUNICORN_BIND = os.environ.get('GUNICORN_BIND', f'0.0.0.0:{PORT}')
