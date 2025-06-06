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
    
    @staticmethod
    def init_app(app):
        """初始化应用配置"""
        # 创建必要的文件夹
        for folder in [app.config['UPLOAD_FOLDER'], 
                      os.path.dirname(app.config['DATABASE_PATH'])]:
            if not os.path.exists(folder):
                os.makedirs(folder, exist_ok=True) 

class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True
    SQLALCHEMY_ECHO = True
    
    # 开发环境数据库
    DATABASE_PATH = os.path.join(PROJECT_ROOT, 'instance', 'dev_app.db')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or f'sqlite:///{DATABASE_PATH}'

class TestingConfig(Config):
    """测试环境配置"""
    TESTING = True
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite://'
    
    # 测试环境使用临时目录
    import tempfile
    UPLOAD_FOLDER = os.path.join(tempfile.gettempdir(), 'test_uploads')

class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False
    
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