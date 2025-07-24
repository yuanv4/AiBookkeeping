import os
from pathlib import Path

class Config:
    """简化的应用配置类"""

    def __init__(self):
        # 基础配置
        self.SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key'
        self.DEBUG = os.getenv('DEBUG', 'False').lower() in ('true', '1')

        # 数据库配置
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        db_path = os.path.join(project_root, 'instance', 'app.db')
        self.SQLALCHEMY_DATABASE_URI = f'sqlite:///{db_path}'

        # 日志配置
        self.LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
        self.LOG_FILE = 'logs/app.log'
        self.LOG_FORMAT = '%(asctime)s %(levelname)s %(name)s %(message)s'

    def init_app(self, app):
        """初始化应用配置"""
        # 将配置应用到Flask应用
        for key, value in self.__dict__.items():
            if key.isupper():
                app.config[key] = value

        Path(self.LOG_FILE).parent.mkdir(parents=True, exist_ok=True)