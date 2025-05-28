import os
import logging
import sys
import os # Added import os
from flask import Flask, current_app, g, send_from_directory, flash, url_for, session, get_flashed_messages, request, jsonify, render_template

# 从同一目录的 config 模块导入配置字典
from .config import config
from .frontend.template_filters import register_template_filters
from core.common.logging_setup import setup_logging # Ensure setup_logging is imported

def create_app(config_name='development'):
    """应用工厂函数"""
    # 设置模板和静态文件路径
    # __file__ 是当前文件的路径 (app/__init__.py)
    # os.path.dirname(__file__) 是 app 目录
    template_folder = os.path.join(os.path.dirname(__file__), 'frontend', 'templates')
    static_folder = os.path.join(os.path.dirname(__file__), 'frontend', 'static')
    
    app = Flask(__name__, 
                template_folder=template_folder,
                static_folder=static_folder)
    app.config.from_object(config[config_name])

    # 配置日志系统，可以根据需要传递覆盖参数
    initial_log_level = app.config.get('LOG_LEVEL', 'INFO')
    # Pass the app instance to setup_logging
    setup_logging(app, log_level_override=initial_log_level, console_output_override=True, file_output_override=True, module_name=None) # 明确 module_name=None 配置根记录器
    # app.logger.info(f"Root logger configured with level: {logging.getLogger().getLevel()}") # Temporarily commented out to ensure stability

    # 确保上传和数据文件夹存在 (路径来自 app.config)
    try:
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        os.makedirs(app.config['DATA_FOLDER'], exist_ok=True)
        app.logger.info(f"Upload folder: {app.config['UPLOAD_FOLDER']}")
        app.logger.info(f"Data folder: {app.config['DATA_FOLDER']}")
    except OSError as e:
        app.logger.error(f"创建目录失败: {e}")
        # 根据情况决定是否抛出异常或优雅退出

    # 导入和初始化核心服务/管理器
    # 这些依赖于上面的 sys.path 修改可能已经完成
    # 注意：由于 'scripts' 目录已重命名为 'core' 并且项目根目录已添加到 sys.path (在 run.py 中),
    # 下面的导入语句需要更新
    from core.db.db_manager import DBManager
    from core.extractors.factory.extractor_factory import get_extractor_factory # Modified to accept app
    from core.analyzers.modules.analyzer_factory import get_analyzer_factory # Updated import
    # services 目录现在是 app/services/
    from app.services.file_processor_service import FileProcessorService

    # 初始化核心服务
    app.db_manager = DBManager(app)  # 传递 app 实例
    app.extractor_factory = get_extractor_factory(app) # 传递 app 实例
    # FileProcessorService 现在需要 app, db_manager, extractor_factory, 和 upload_folder
    # upload_folder 通常从 app.config 获取
    upload_folder = app.config.get('UPLOAD_FOLDER', os.path.join(app.root_path, 'uploads')) # Default if not in config
    app.file_processor_service = FileProcessorService(app, app.extractor_factory, app.db_manager, upload_folder)
    app.analyzer_factory = get_analyzer_factory(app, app.db_manager) # 初始化分析器工厂并传递 app 和 db_manager

    # 注册自定义模板过滤器
    register_template_filters(app)

    # 注册蓝图
    from .main.routes import main as main_blueprint # 蓝图实例通常在 routes.py 中定义或在其 __init__ 中
    app.register_blueprint(main_blueprint)
    app.logger.info("已注册 main_blueprint")

    from .upload_bp.routes import upload_bp
    app.register_blueprint(upload_bp, url_prefix='/upload')
    app.logger.info("已注册 upload_bp, 前缀 /upload")

    from .transactions_bp.routes import transactions_bp
    app.register_blueprint(transactions_bp, url_prefix='/transactions')
    app.logger.info("已注册 transactions_bp, 前缀 /transactions")

    from .api_bp.routes import api_bp
    app.register_blueprint(api_bp, url_prefix=app.config.get('API_URL_PREFIX', '/api'))
    app.logger.info(f"已注册 api_bp, 前缀 {app.config.get('API_URL_PREFIX', '/api')}")
    
    from .income_analysis_bp.routes import income_analysis_bp
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
        stats = app.db_manager.get_statistics()
        if stats and stats.get('total_transactions', 0) > 0:
            app.logger.info(f"数据库已连接并包含 {stats.get('total_transactions', 0)} 条交易记录")
        else:
            app.logger.info("数据库为空或新创建")
    except Exception as e_init:
        app.logger.error(f"应用启动时执行 init_database 逻辑出错: {e_init}", exc_info=True)

    return app