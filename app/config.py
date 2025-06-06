import os
from datetime import timedelta

# 项目的根目录 (AiBookkeeping/)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) if __file__ != 'config.py' else os.path.dirname(os.path.abspath('.')) # Heuristic for multi-file setup

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'a_default_dev_secret_key_please_change_in_prod_bp' # Changed key for blueprint version
    DEBUG = True # 默认开启Debug，生产环境应设为False
    
    # 文件夹配置
    UPLOAD_FOLDER_NAME = 'uploads'
    DATA_FOLDER_NAME = 'data'
    SCRIPTS_FOLDER_NAME = 'scripts'
    ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
    UPLOAD_FOLDER = os.path.join(PROJECT_ROOT, UPLOAD_FOLDER_NAME)
    DATA_FOLDER = os.path.join(PROJECT_ROOT, DATA_FOLDER_NAME)
    SCRIPTS_FOLDER = os.path.join(PROJECT_ROOT, SCRIPTS_FOLDER_NAME)
    
    # 文件上传配置
    ALLOWED_EXTENSIONS = {'xlsx', 'xls', 'csv', 'txt'}
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    
    # 分页配置
    ITEMS_PER_PAGE = 20
    TRANSACTIONS_PER_PAGE = 50
    
    # Flask配置
    TEMPLATES_AUTO_RELOAD = True
    API_URL_PREFIX = '/api'
    
    # 数据库配置
    DATABASE_PATH = os.path.join(PROJECT_ROOT, 'instance', 'app.db')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or f'sqlite:///{DATABASE_PATH}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False
    
    # Session配置
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    
    # 货币设置
    DEFAULT_CURRENCY = 'CNY'
    SUPPORTED_CURRENCIES = ['CNY', 'USD', 'EUR', 'GBP', 'JPY']
    
    # 日期格式
    DATE_FORMAT = '%Y-%m-%d'
    DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'
    
    # 日志配置
    LOG_LEVEL = 'INFO'
    LOG_FILE = 'bookkeeping.log'
    
    # 安全设置
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600
    
    @staticmethod
    def init_app(app):
        """Initialize application with this configuration."""
        # 创建必要的文件夹
        for folder in [app.config['UPLOAD_FOLDER'], app.config['DATA_FOLDER'], 
                      os.path.dirname(app.config['DATABASE_PATH'])]:
            if not os.path.exists(folder):
                os.makedirs(folder, exist_ok=True) 

class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_ECHO = True
    LOG_LEVEL = 'DEBUG'
    
    # 开发环境数据库
    DATABASE_PATH = os.path.join(PROJECT_ROOT, 'instance', 'dev_app.db')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or f'sqlite:///{DATABASE_PATH}'
    
    # 开发环境禁用CSRF
    WTF_CSRF_ENABLED = False

class TestingConfig(Config):
    TESTING = True
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    LOG_LEVEL = 'ERROR'

class ProductionConfig(Config):
    DEBUG = False
    SECRET_KEY = os.environ.get('SECRET_KEY') # 生产环境必须从环境变量读取
    TEMPLATES_AUTO_RELOAD = False
    LOG_LEVEL = 'WARNING'
    
    # 生产环境数据库
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or f'sqlite:///{Config.DATABASE_PATH}'
    
    @classmethod
    def init_app(cls, app):
        Config.init_app(app)
        
        # 检查生产环境必需的环境变量
        if not os.environ.get('SECRET_KEY'):
            raise ValueError("生产环境中未设置 SECRET_KEY 环境变量")
        
        # 生产环境日志配置
        import logging
        from logging.handlers import RotatingFileHandler
        
        if not app.debug:
            file_handler = RotatingFileHandler(
                app.config['LOG_FILE'], maxBytes=10240000, backupCount=10
            )
            file_handler.setFormatter(logging.Formatter(
                '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
            ))
            file_handler.setLevel(logging.INFO)
            app.logger.addHandler(file_handler)
            app.logger.setLevel(logging.INFO)
            app.logger.info('Bookkeeping application startup')

config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

# 辅助函数
def get_config(config_name=None):
    """Get configuration class by name."""
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'default')
    return config.get(config_name, config['default'])

def create_upload_folder(app):
    """Create upload folder if it doesn't exist."""
    upload_folder = app.config.get('UPLOAD_FOLDER')
    if upload_folder and not os.path.exists(upload_folder):
        os.makedirs(upload_folder, exist_ok=True)
        app.logger.info(f"Created upload folder: {upload_folder}")

def create_data_folder():
    """Create data folder for database files."""
    data_folder = os.path.join(PROJECT_ROOT, 'data')
    if not os.path.exists(data_folder):
        os.makedirs(data_folder, exist_ok=True)
        print(f"Created data folder: {data_folder}")
    return data_folder