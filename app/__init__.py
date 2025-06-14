import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from flask import Flask, request, render_template, jsonify
from flask_migrate import Migrate

# 从同一目录的 config 模块导入配置类
from .config import Config
from .template_filters import register_template_filters
from .models import db

from .services.core.transaction_service import TransactionService
from .services import FinancialService as AnalysisService
from .services.extraction.service import BankStatementExtractor
from .services.core.file_processor_service import FileProcessorService

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

def create_app():
    app = Flask(__name__)
    
    # 直接实例化配置类
    config = Config()
    config.init_app(app)
    
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
        app.transaction_service = TransactionService()
        app.analysis_service = AnalysisService()
        app.extractor_service = BankStatementExtractor()
        
        # Initialize file processor service with dependencies
        app.file_processor_service = FileProcessorService(
            extractor_service=app.extractor_service
        )
    

    app.logger.info("服务层已初始化并附加到 app 对象")

    # 注册自定义模板过滤器
    register_template_filters(app)

    # 注册蓝图
    from .blueprints.main.routes import main as main_blueprint
    app.register_blueprint(main_blueprint)
    app.logger.info("已注册 main_blueprint")

    # upload_bp 已迁移到 settings_bp，不再需要单独注册

    from .blueprints.transactions.routes import transactions_bp
    app.register_blueprint(transactions_bp, url_prefix='/transactions')
    app.logger.info("已注册 transactions_bp, 前缀 /transactions")

    from .blueprints.api.routes import api_bp
    app.register_blueprint(api_bp, url_prefix='/api')
    app.logger.info(f"已注册 api_bp, 前缀 {'/api'}")
    
    from .blueprints.income_analysis.routes import income_analysis_bp
    app.register_blueprint(income_analysis_bp, url_prefix='/income-analysis')
    app.logger.info("已注册 income_analysis_bp, 前缀 /income-analysis")
    
    from .blueprints.expense_analysis.routes import expense_analysis_bp
    app.register_blueprint(expense_analysis_bp, url_prefix='/expense-analysis')
    app.logger.info("已注册 expense_analysis_bp, 前缀 /expense-analysis")
    
    from .blueprints.settings.routes import settings_bp
    app.register_blueprint(settings_bp, url_prefix='/settings')
    app.logger.info("已注册 settings_bp, 前缀 /settings")

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
        if request.path.startswith('/api') or \
           (request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html):
            return jsonify(success=False, error="服务器发生内部错误", details=str(e)), 500
        return render_template('errors/500.html', error="发生了一个意外错误"), 500
    app.logger.info("已注册全局错误处理器。")

    # 数据库统计信息检查
    try:
        with app.app_context():
            from app.services import FinancialService
            from datetime import date, datetime
            
            analyzer = FinancialService()
            # 使用新的分析器获取基本统计信息
            analysis_result = analyzer.get_comprehensive_analysis(1)
            
            # 从分析结果中提取交易数量信息
            if analysis_result and 'overall_stats' in analysis_result:
                total_transactions = analysis_result['overall_stats'].get('total_transactions', 0)
                if total_transactions > 0:
                    app.logger.info(f"数据库已连接并包含 {total_transactions} 条交易记录")
                else:
                    app.logger.info("数据库已连接但暂无交易记录")
            else:
                app.logger.info("数据库已连接，统计信息获取中...")
    except Exception as e:
        app.logger.warning(f"获取数据库统计信息时出错: {e}")
        app.logger.info("数据库连接正常，但无法获取统计信息")
        
    return app