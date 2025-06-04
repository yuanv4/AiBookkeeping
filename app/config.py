import os

# 项目的根目录 (AiBookkeeping/)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) if __file__ != 'config.py' else os.path.dirname(os.path.abspath('.')) # Heuristic for multi-file setup

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'a_default_dev_secret_key_please_change_in_prod_bp' # Changed key for blueprint version
    DEBUG = True # 默认开启Debug，生产环境应设为False
    
    UPLOAD_FOLDER_NAME = 'uploads'
    DATA_FOLDER_NAME = 'data'
    SCRIPTS_FOLDER_NAME = 'scripts'
    # PROCESSED_FOLDER_NAME = 'processed_files' # 如果采纳归档建议，也应在此定义
    ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
    UPLOAD_FOLDER = os.path.join(PROJECT_ROOT, UPLOAD_FOLDER_NAME)
    DATA_FOLDER = os.path.join(PROJECT_ROOT, DATA_FOLDER_NAME)
    SCRIPTS_FOLDER = os.path.join(PROJECT_ROOT, SCRIPTS_FOLDER_NAME)
    # PROCESSED_FOLDER = os.path.join(ROOT_DIR, PROCESSED_FOLDER_NAME)
    ALLOWED_EXTENSIONS = {'xlsx', 'xls'}
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    ITEMS_PER_PAGE = 20 # 默认值
    TEMPLATES_AUTO_RELOAD = True
    API_URL_PREFIX = '/api' # For error handler
    DATABASE_PATH = os.path.join(PROJECT_ROOT, 'instance', 'app.db')
    # 数据库配置 (如果 DBManager 需要外部配置)
    # SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///your_default_database.db'
    # SQLALCHEMY_TRACK_MODIFICATIONS = False 

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False
    SECRET_KEY = os.environ.get('SECRET_KEY') # 生产环境必须从环境变量读取
    TEMPLATES_AUTO_RELOAD = False
    
    def __init__(self):
        super().__init__()
        # 仅在真正创建 ProductionConfig 实例时检查 SECRET_KEY
        if not self.SECRET_KEY:
            raise ValueError("生产环境中未设置 SECRET_KEY 环境变量")

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}