import os
import logging
import sys
from logging.handlers import TimedRotatingFileHandler
from flask import Flask, request, render_template, jsonify
from flask_migrate import Migrate

# 从同一目录的 config 模块导入配置字典
from .config import config, get_config
from .template_filters import register_template_filters
from .models import db
from .services.database_service import DatabaseService
from .services.transaction_service import TransactionService
from .services.analysis_service import AnalysisService
from .services.extractor_service import ExtractorService
from .services.file_processor_service import FileProcessorService

# Initialize extensions
migrate = Migrate()

def configure_logging(app):
    """配置应用日志"""
    log_level = getattr(logging, app.config.get('LOG_LEVEL', 'INFO'))
    
    # 创建日志格式器
    formatter = logging.Formatter(app.config.get('LOG_FORMAT'))
    
    # 配置文件处理器 - 每小时轮转
    log_file = os.path.join(app.config['LOG_DIR'], 'app.log')
    file_handler = TimedRotatingFileHandler(
        filename=log_file,
        when=app.config.get('LOG_ROTATION_WHEN', 'H'),
        interval=app.config.get('LOG_ROTATION_INTERVAL', 1),
        backupCount=app.config.get('LOG_BACKUP_COUNT', 168),
        encoding='utf-8'
    )
    # 设置轮转后文件的命名格式：app.log.2025-01-05_14
    file_handler.suffix = "%Y-%m-%d_%H"
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

def create_app(config_name='default'):
    app = Flask(__name__)
    
    # Load configuration
    config_obj = get_config(config_name)
    app.config.from_object(config_obj)
    
    # Initialize configuration
    config_obj.init_app(app)
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    
    # Configure logging
    configure_logging(app)

    # 添加 scripts 目录到 Python 路径 (scripts 在项目根目录 AiBookkeeping/scripts)
    project_root_dir = os.path.dirname(app.root_path) # app.root_path 是 app/
    scripts_path = os.path.join(project_root_dir, 'scripts')
    if scripts_path not in sys.path:
        sys.path.append(scripts_path)
        app.logger.info(f"已将 {scripts_path} 添加到 sys.path")
    # 如果有其他模块直接在项目根目录，也添加项目根目录
    if project_root_dir not in sys.path:
        sys.path.append(project_root_dir)
        app.logger.info(f"已将 {project_root_dir} 添加到 sys.path")

    # Initialize database and services
    with app.app_context():
        # Create database tables
        db.create_all()
        app.logger.info("数据库表已创建")
        
        # Initialize services
        app.database_service = DatabaseService()
        app.transaction_service = TransactionService()
        app.analysis_service = AnalysisService()
        app.extractor_service = ExtractorService()
        
        # Initialize file processor service with dependencies
        app.file_processor_service = FileProcessorService(
            extractor_service=app.extractor_service,
            database_service=app.database_service
        )
        
        # Initialize default data
        app.database_service.init_database()
        app.logger.info("数据库已初始化，默认数据已创建")
    
    # 为了向后兼容，保留旧的属性名
    app.db_facade = app.database_service
    app.extractor_factory = app.extractor_service
    app.logger.info("服务层已初始化并附加到 app 对象")

    # 注册自定义模板过滤器
    register_template_filters(app)

    # 注册蓝图
    from .blueprints.main.routes import main as main_blueprint
    app.register_blueprint(main_blueprint)
    app.logger.info("已注册 main_blueprint")

    from .blueprints.upload.routes import upload_bp
    app.register_blueprint(upload_bp, url_prefix='/upload')
    app.logger.info("已注册 upload_bp, 前缀 /upload")

    from .blueprints.transactions.routes import transactions_bp
    app.register_blueprint(transactions_bp, url_prefix='/transactions')
    app.logger.info("已注册 transactions_bp, 前缀 /transactions")

    from .blueprints.api.routes import api_bp
    app.register_blueprint(api_bp, url_prefix=app.config.get('API_URL_PREFIX', '/api'))
    app.logger.info(f"已注册 api_bp, 前缀 {app.config.get('API_URL_PREFIX', '/api')}")
    
    from .blueprints.income_analysis.routes import income_analysis_bp
    app.register_blueprint(income_analysis_bp, url_prefix='/income-analysis')
    app.logger.info("已注册 income_analysis_bp, 前缀 /income-analysis")

    # 注册全局错误处理函数
    @app.errorhandler(404)
    def page_not_found_error(e): 
        app.logger.warning(f"页面未找到 (404): {request.url} - {e}")
        # 检查请求是否期望JSON响应 (例如 API 请求)
        if request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html:
            return jsonify(error='Not Found', message=str(e)), 404
        return render_template('errors/404.html', error=e), 404
        
    @app.errorhandler(500)
    def internal_server_error_handler(e): 
        app.logger.error(f"服务器内部错误 (500): {e}", exc_info=True)
        if request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html:
            return jsonify(error='Internal Server Error', message=str(e)), 500
        return render_template('errors/500.html', error=e), 500

    @app.errorhandler(Exception)
    def handle_general_exception_handler(e):
        app.logger.error(f"发生未捕获的异常: {e}", exc_info=True)
        if request.path.startswith(app.config.get('API_URL_PREFIX', '/api')) or \
           (request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html):
            return jsonify(success=False, error="服务器发生内部错误", details=str(e)), 500
        return render_template('errors/500.html', error="发生了一个意外错误"), 500
    app.logger.info("已注册全局错误处理器。")

    # 应用启动时的数据库文件检查逻辑 (原 init_database 部分功能)
    # 使用 with app.app_context() 来确保在正确的上下文中执行，如果它需要访问 app 特定的东西
    # 但 FileProcessorService 在实例化时已经有了 app context
    # 这里可以直接调用服务，因为它已被实例化并附加到 app 对象
    try:
        app.logger.info("应用启动: 执行启动时文件处理检查。")
        # 注意：file_processor_service 现在通过 app.file_processor_service 访问
        processed_files_init, message = app.file_processor_service.process_files_in_upload_folder()
        if processed_files_init:
            app.logger.info(f"启动时处理了 {len(processed_files_init)} 个文件。消息: {message}")
        elif message != "未找到待处理的Excel文件": # 只记录非"未找到"的消息
             app.logger.info(f"启动时文件处理消息: {message}")
        # 数据库统计信息检查
        try:
            stats = app.database_service.get_database_stats()
            total_transactions = stats.get('transactions_count', 0)
            if total_transactions > 0:
                app.logger.info(f"数据库已连接并包含 {total_transactions} 条交易记录")
            else:
                app.logger.info("数据库为空或新创建")
        except Exception as e:
            app.logger.warning(f"获取数据库统计信息时出错: {e}")
            app.logger.info("数据库连接正常，但无法获取统计信息")
    except Exception as e_init:
        app.logger.error(f"应用启动时执行 init_database 逻辑出错: {e_init}", exc_info=True)

    return app