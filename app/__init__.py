import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from flask import Flask, request, render_template, jsonify
from flask_migrate import Migrate

# 从同一目录的 config 模块导入配置类
from .config import Config
from .utils.template_filters import register_template_filters
from .utils.service_manager import ServiceManager
from .utils.error_handler import ErrorHandler
from .models import db

# Initialize extensions
migrate = Migrate()

def configure_logging(app):
    """配置应用日志"""
    log_level = getattr(logging, app.config.get('LOG_LEVEL', 'INFO'))
    
    # 创建日志格式器
    formatter = logging.Formatter(app.config.get('LOG_FORMAT'))
    
    # 配置文件处理器 - 使用RotatingFileHandler按大小轮转
    log_file = app.config.get('LOG_FILE', 'logs/app.log')
    # 确保日志目录存在
    log_dir = os.path.dirname(log_file)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)
    
    file_handler = RotatingFileHandler(
        filename=log_file,
        maxBytes=app.config.get('LOG_MAX_BYTES', 10 * 1024 * 1024),
        backupCount=app.config.get('LOG_BACKUP_COUNT', 5),
        encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(log_level)
    
    # 配置控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(log_level)
    
    # 配置根日志器
    logging.basicConfig(
        level=log_level,
        handlers=[console_handler, file_handler]
    )
    
    app.logger.info(f"应用以 '{app.config.get('ENV', 'unknown')}' 配置启动。日志级别: {logging.getLevelName(log_level)}")
    app.logger.info(f"日志文件路径: {log_file}")


def _setup_python_path(app):
    """设置Python路径

    为项目添加必要的模块路径到sys.path，以支持动态导入。

    Args:
        app: Flask应用实例
    """
    project_root_dir = os.path.dirname(app.root_path)  # app.root_path 是 app/

    # 需要添加到sys.path的路径列表
    paths_to_add = [
        ('scripts', os.path.join(project_root_dir, 'scripts')),
        ('project_root', project_root_dir)
    ]

    for path_name, path_value in paths_to_add:
        if path_value not in sys.path:
            sys.path.append(path_value)
            app.logger.info(f"已将 {path_name} 路径 ({path_value}) 添加到 sys.path")
        else:
            app.logger.debug(f"{path_name} 路径 ({path_value}) 已存在于 sys.path 中")


def _initialize_database_and_services(app):
    """初始化数据库和服务

    Args:
        app: Flask应用实例
    """
    with app.app_context():
        # Create database tables
        db.create_all()
        app.logger.info("数据库表已创建")

        # Initialize service manager and register services
        service_manager = ServiceManager(app)
        service_manager.register_core_services()

        app.logger.info("服务层已通过ServiceManager初始化")


def _register_blueprints(app):
    """注册蓝图

    Args:
        app: Flask应用实例
    """
    # 注册main蓝图（仪表盘和主页）
    from .blueprints.main import main_bp
    app.register_blueprint(main_bp)
    app.logger.info("已注册 main_bp")

    from .blueprints.transactions.routes import transactions_bp
    app.register_blueprint(transactions_bp, url_prefix='/transactions')
    app.logger.info("已注册 transactions_bp, 前缀 /transactions")

    from .blueprints.settings.routes import settings_bp
    app.register_blueprint(settings_bp, url_prefix='/settings')
    app.logger.info("已注册 settings_bp, 前缀 /settings")

    from .blueprints.expense_analysis import expense_analysis_bp
    app.register_blueprint(expense_analysis_bp, url_prefix='/expense-analysis')
    app.logger.info("已注册 expense_analysis_bp, 前缀 /expense-analysis")


def create_app():
    """创建Flask应用实例

    Returns:
        配置完成的Flask应用实例
    """
    app = Flask(__name__)

    # 直接实例化配置类
    config = Config()
    config.init_app(app)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)

    # Configure logging
    configure_logging(app)

    # 设置Python路径
    _setup_python_path(app)

    # 初始化数据库和服务
    _initialize_database_and_services(app)

    # 注册自定义模板过滤器
    register_template_filters(app)

    # 注册蓝图
    _register_blueprints(app)

    # 注册统一的错误处理器
    ErrorHandler.register_error_handlers(app)

    return app