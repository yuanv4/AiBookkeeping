import os
from pathlib import Path

class Config:
    """应用配置类 - 从环境变量读取所有配置"""
    
    def __init__(self):
        # 基础配置
        self.APP_NAME = '银行账单分析系统'
        self.SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key'
        self.DEBUG = os.getenv('DEBUG', 'False').lower() in ('true', '1', 'yes', 'on')

        # 环境配置
        self.FLASK_ENV = os.environ.get('FLASK_CONFIG', 'development')
        
        # 数据库配置
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if self.FLASK_ENV == 'testing':
            # 测试环境使用内存数据库
            self.SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
        elif self.FLASK_ENV == 'production':
            # 生产环境使用固定的SQLite数据库文件
            db_path = os.path.join(project_root, 'instance', 'prod_app.db')
            self.SQLALCHEMY_DATABASE_URI = f'sqlite:///{db_path}'
        else:
            # 开发环境使用固定的SQLite数据库文件
            db_path = os.path.join(project_root, 'instance', 'dev_app.db')
            self.SQLALCHEMY_DATABASE_URI = f'sqlite:///{db_path}'

        # 文件上传配置
        self.UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', 'uploads')
        allowed_extensions = os.getenv('ALLOWED_EXTENSIONS', 'xlsx,xls').split(',')
        allowed_extensions = [ext.strip() for ext in allowed_extensions if ext.strip()]
        self.ALLOWED_EXTENSIONS = set(allowed_extensions)

        # 日志配置
        self.LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
        self.LOG_FILE = os.environ.get('LOG_FILE', 'logs/app.log')
        self.LOG_MAX_BYTES = int(os.getenv('LOG_MAX_BYTES', '10485760'))  # 10MB
        self.LOG_BACKUP_COUNT = int(os.getenv('LOG_BACKUP_COUNT', '5'))
        self.LOG_FORMAT = os.environ.get('LOG_FORMAT', '%(asctime)s %(levelname)s %(name)s %(message)s')
        self.LOG_DATE_FORMAT = os.environ.get('LOG_DATE_FORMAT', '%Y-%m-%d %H:%M:%S')

        # 生产环境配置验证
        if self.FLASK_ENV == 'production':
            if not os.environ.get('SECRET_KEY') or os.environ.get('SECRET_KEY') == 'dev-secret-key-change-in-production':
                raise ValueError("生产环境中未设置有效的 SECRET_KEY 环境变量")

    
    def init_app(self, app):
        """初始化应用配置"""
        # 将配置应用到Flask应用
        for key, value in self.__dict__.items():
            if key.isupper():
                app.config[key] = value
        
        # 确保上传目录存在
        upload_path = Path(self.UPLOAD_FOLDER)
        upload_path.mkdir(parents=True, exist_ok=True)
        
        # 确保日志目录存在
        log_path = Path(self.LOG_FILE).parent
        log_path.mkdir(parents=True, exist_ok=True) 

def get_config():
    """获取配置实例"""
    return Config()