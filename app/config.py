import os

# 项目的根目录
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

class Config:
    """基础配置类"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # 数据库配置
    DATABASE_PATH = os.path.join(PROJECT_ROOT, 'instance', 'app.db')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or f'sqlite:///{DATABASE_PATH}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # 文件上传配置
    UPLOAD_FOLDER = os.path.join(PROJECT_ROOT, 'uploads')
    ALLOWED_EXTENSIONS = {'xlsx', 'xls', 'csv', 'txt'}
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    
    # 分页配置
    TRANSACTIONS_PER_PAGE = 50
    
    # 货币设置
    DEFAULT_CURRENCY = 'CNY'
    
    # 日期格式
    DATE_FORMAT = '%Y-%m-%d'
    DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'
    
    # 日志配置
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_DIR = os.path.join(PROJECT_ROOT, 'logs')
    LOG_FILE_MAX_BYTES = 10 * 1024 * 1024  # 10MB
    LOG_BACKUP_COUNT = 168  # 保留7天的小时日志 (24*7=168)
    LOG_ROTATION_WHEN = 'H'  # 按小时轮转
    LOG_ROTATION_INTERVAL = 1  # 每1小时
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    @staticmethod
    def init_app(app):
        """初始化应用配置"""
        # 创建必要的文件夹
        for folder in [app.config['UPLOAD_FOLDER'], 
                      os.path.dirname(app.config['DATABASE_PATH']),
                      app.config['LOG_DIR']]:
            if not os.path.exists(folder):
                os.makedirs(folder, exist_ok=True) 

class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True
    SQLALCHEMY_ECHO = True
    
    # 开发环境数据库
    DATABASE_PATH = os.path.join(PROJECT_ROOT, 'instance', 'dev_app.db')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or f'sqlite:///{DATABASE_PATH}'
    
    # 开发环境日志配置
    LOG_LEVEL = 'DEBUG'
    LOG_BACKUP_COUNT = 24  # 开发环境保留24小时日志

class TestingConfig(Config):
    """测试环境配置"""
    TESTING = True
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite://'
    
    # 测试环境使用临时目录
    import tempfile
    UPLOAD_FOLDER = os.path.join(tempfile.gettempdir(), 'test_uploads')
    
    # 测试环境日志配置
    LOG_LEVEL = 'INFO'
    LOG_BACKUP_COUNT = 48  # 测试环境保留48小时日志

class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False
    
    # 生产环境日志配置
    LOG_LEVEL = 'WARNING'
    LOG_BACKUP_COUNT = 168  # 生产环境保留7天日志
    
    @classmethod
    def init_app(cls, app):
        Config.init_app(app)
        
        # 检查生产环境必需的环境变量
        if not os.environ.get('SECRET_KEY'):
            raise ValueError("生产环境中未设置 SECRET_KEY 环境变量")

config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

def get_config(config_name=None):
    """获取配置类"""
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'default')
    return config.get(config_name, config['default'])