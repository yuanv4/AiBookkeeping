import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from flask import Flask, request, render_template, jsonify
from flask_migrate import Migrate

# 从同一目录的 config 模块导入配置类
from .config import Config
from .utils.template_filters import register_template_filters
from .utils.error_handler import ErrorHandler
from .models import db

# Initialize extensions
migrate = Migrate()

def configure_logging(app):
    """配置应用日志"""
    log_level = getattr(logging, app.config.get('LOG_LEVEL', 'INFO'))
    log_format = app.config.get('LOG_FORMAT', '%(asctime)s %(levelname)s %(name)s %(message)s')

    # 基本的文件和控制台输出
    log_file = app.config.get('LOG_FILE', 'logs/app.log')
    # 确保日志目录存在
    log_dir = os.path.dirname(log_file)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)

    # 使用基本的日志配置
    logging.basicConfig(
        level=log_level,
        format=log_format,
        handlers=[
            logging.StreamHandler(),  # 控制台输出
            RotatingFileHandler(
                filename=log_file,
                maxBytes=10 * 1024 * 1024,  # 10MB
                backupCount=5,
                encoding='utf-8'
            )
        ]
    )

    app.logger.info(f"应用启动，日志级别: {logging.getLevelName(log_level)}")

def _initialize_database_and_services(app):
    """初始化数据库和服务

    Args:
        app: Flask应用实例
    """
    with app.app_context():
        # Create database tables
        db.create_all()
        app.logger.info("数据库表已创建")

        # 直接初始化服务 - 简化的服务管理
        from .services import DataService, ImportService, ReportService
        from .services.category_service import CategoryService

        data_service = DataService()
        category_service = CategoryService()
        import_service = ImportService(data_service)
        report_service = ReportService(data_service, category_service=category_service)
        # 将服务直接设置到app对象上
        app.data_service = data_service
        app.category_service = category_service
        app.import_service = import_service
        app.report_service = report_service
        app.logger.info("服务层已直接初始化")

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

    # 初始化数据库和服务
    _initialize_database_and_services(app)

    # 注册自定义模板过滤器
    register_template_filters(app)

    # 注册蓝图
    _register_blueprints(app)

    # 注册统一的错误处理器
    ErrorHandler.register_error_handlers(app)

    return app