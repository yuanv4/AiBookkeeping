import logging
from flask import Flask
from flask_migrate import Migrate

# 从同一目录的 config.py 文件导入配置类
from .config import Config
from .utils.template_filters import register_template_filters

from .models import db

# Initialize extensions
migrate = Migrate()

def configure_logging(app):
    """配置应用日志 - 使用Config类提供的配置"""
    from pathlib import Path

    # 直接使用app.config中已经处理好的配置，不设置默认值
    log_level = getattr(logging, app.config['LOG_LEVEL'])
    log_format = '%(asctime)s %(levelname)s %(name)s %(message)s'
    log_date_format = '%Y-%m-%d %H:%M:%S'
    log_file = 'logs/app.log'

    # 创建统一的格式化器
    formatter = logging.Formatter(log_format, log_date_format)

    # 创建处理器列表
    handlers = []

    # 1. 控制台处理器（始终添加）
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    handlers.append(console_handler)

    # 2. 文件处理器（尝试添加，失败时继续）
    file_output_enabled = False
    try:
        # 确保日志目录存在（统一在这里处理）
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(formatter)
        handlers.append(file_handler)
        file_output_enabled = True
    except Exception as e:
        # 文件处理器创建失败时，记录警告但继续运行
        print(f"警告：无法创建日志文件处理器 ({log_file}): {e}")
        file_output_enabled = False

    # 配置根日志记录器
    logging.basicConfig(
        level=log_level,
        handlers=handlers,
        force=True  # 强制重新配置，覆盖之前的配置
    )

    # 记录日志配置信息
    app.logger.info(f"应用启动，日志级别: {logging.getLevelName(log_level)}")
    if file_output_enabled:
        app.logger.info(f"日志输出: 控制台 + 文件({log_file})")
    else:
        app.logger.warning("日志输出: 仅控制台（文件输出失败）")

def _initialize_database_and_services(app):
    """初始化数据库和服务

    Args:
        app: Flask应用实例
    """
    with app.app_context():
        # Create database tables
        db.create_all()
        app.logger.info("数据库表已创建")

        # 服务将按需初始化，无需预先创建
        app.logger.info("服务层将按需初始化")

def _register_blueprints(app):
    """注册蓝图

    Args:
        app: Flask应用实例
    """
    # 注册main蓝图（基础路由和重定向）
    from .blueprints.main import main_bp
    app.register_blueprint(main_bp)
    app.logger.info("已注册 main_bp")

    # 注册分析页面蓝图
    from .blueprints.analytics import analytics_bp
    app.register_blueprint(analytics_bp, url_prefix='/analytics')
    app.logger.info("已注册 analytics_bp, 前缀 /analytics")

    from .blueprints.settings.routes import settings_bp
    app.register_blueprint(settings_bp, url_prefix='/settings')
    app.logger.info("已注册 settings_bp, 前缀 /settings")

    from .blueprints.merchant_categories import merchant_categories_bp
    app.register_blueprint(merchant_categories_bp, url_prefix='/merchant-categories')
    app.logger.info("已注册 merchant_categories_bp, 前缀 /merchant-categories")


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
    from .utils.decorators import create_error_response

    @app.errorhandler(404)
    def handle_404(error):
        return create_error_response(Exception("页面未找到"), 404)

    @app.errorhandler(500)
    def handle_500(error):
        return create_error_response(error, 500)

    app.logger.info("已注册统一错误处理器")

    return app