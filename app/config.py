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
    # 数据库配置 (示例，具体根据DBManager调整)
    DB_TYPE = 'sqlite'
    DB_NAME = 'bookkeeping.db' # 默认数据库文件名
    # DB_PATH 将在下面基于 DATA_FOLDER 构建

    # DBManager specific configurations (previously from ConfigManager)
    DATABASE_TIMEOUT = 30.0
    DATABASE_BUSY_TIMEOUT = 30000  # milliseconds

    ANALYSIS_CATEGORY_MAPPING = {
        'income': ['收入', '工资', '退款', '红包', '利息'],
        'expense': ['支出', '购物', '餐饮', '交通', '房租', '医疗', '教育', '娱乐', '旅行'],
        'transfer': ['转账', '信用卡还款']
    }

    EXTRACTORS_SUPPORTED_BANKS = ['CMB', 'CCB'] # Example, adjust as needed
    EXTRACTORS_BANKS = {
        'CMB': {'bank_name': '招商银行'},
        'CCB': {'bank_name': '建设银行'}
        # Add other bank configurations here if needed
    }

    # Logging configurations (previously from ConfigManager)
    LOG_LEVEL = 'INFO'
    LOG_DIR = 'logs' # Relative to project root, or absolute path
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    LOG_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
    LOG_MAX_BYTES = 10 * 1024 * 1024  # 10MB
    LOG_BACKUP_COUNT = 5

    # Visualization configurations (previously from ConfigManager)
    VISUALIZATION_THEME = 'seaborn-v0_8-pastel' # 'default' or any valid matplotlib style
    VISUALIZATION_CHARTS_DIR = 'app/frontend/static/charts' # Relative to project root, or absolute path
    VISUALIZATION_FONT_DEFAULT = 'SimHei'
    VISUALIZATION_FONT_FALLBACK = ['Microsoft YaHei', 'SimSun', 'STSong', 'WenQuanYi Micro Hei']
    VISUALIZATION_COLORS = {
        'income': '#4CAF50',
        'expense': '#F44336',
        'net': '#2196F3',
        'transfer': '#FF9800'
    }

    # 其他应用特有的配置
    pass 

class DevelopmentConfig(Config):
    DEBUG = True
    # 开发环境数据库路径 (通常与基本配置相同，除非特别指定)
    # SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.join(Config.DATA_FOLDER, Config.DB_NAME)}"
    DB_PATH = os.path.join(Config.DATA_FOLDER, Config.DB_NAME)
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{DB_PATH}"

class ProductionConfig(Config):
    # 生产环境特有配置，例如关闭DEBUG模式
    DEBUG = False
    # 生产环境数据库路径
    # SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.join(Config.DATA_FOLDER, Config.DB_NAME)}"
    DB_PATH = os.path.join(Config.DATA_FOLDER, Config.DB_NAME) # 通常与Config中的定义一致，除非需要区分
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{DB_PATH}"
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