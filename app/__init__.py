import os
import logging
import sys
from flask import Flask, request, render_template, jsonify 

# 从同一目录的 config 模块导入配置字典
# 假设 config.py 已经被移动到了 app/config.py
from .config import config
from .template_filters import register_template_filters

def create_app(config_name='default'):
    app = Flask(__name__) # 使用 __name__ (即 'app') 作为蓝图的模板/静态文件查找起点
    app.config.from_object(config[config_name])

    # 配置日志
    log_level = logging.DEBUG if app.debug else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler()]
    )
    # 可以使用 app.logger 记录应用特定的日志
    app.logger.info(f"应用以 '{config_name}' 配置启动。日志级别: {logging.getLevelName(log_level)}")

    # 确保上传和数据文件夹存在 (路径来自 app.config)
    try:
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        os.makedirs(app.config['DATA_FOLDER'], exist_ok=True)
        app.logger.info(f"Upload folder: {app.config['UPLOAD_FOLDER']}")
        app.logger.info(f"Data folder: {app.config['DATA_FOLDER']}")
    except OSError as e:
        app.logger.error(f"创建目录失败: {e}")
        # 根据情况决定是否抛出异常或优雅退出

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

    # 导入和初始化核心服务/管理器
    # 这些依赖于上面的 sys.path 修改可能已经完成
    from scripts.db.db_facade import DBFacade
    from scripts.extractors.factory.extractor_factory import get_extractor_factory
    # services 目录现在是 app/services/
    from app.services.file_processor_service import FileProcessorService

    # 将实例附加到 app 对象，供蓝图和应用上下文使用
    # 初始化数据库门面
    # 注意：这里只创建 DBFacade 实例，不直接初始化连接
    # 连接将在每个请求中通过 db_facade.get_connection() 获取
    app.db_facade = DBFacade(app.config['DATABASE_PATH'])

    # 在应用上下文销毁时关闭数据库连接
    @app.teardown_appcontext
    def close_db_connection(exception):
        # 确保在应用关闭时，所有线程的连接都被关闭
        # 对于 threading.local() 管理的连接，这里不需要额外操作
        # 因为每个请求结束时，连接已经在 after_request 中关闭
        pass # 实际的关闭逻辑已移至 after_request

    # 确保在应用启动时，主线程的数据库连接被初始化
    with app.app_context():
        app.db_facade.init_db() # Ensure database tables are created

    app.extractor_factory = get_extractor_factory()
    app.file_processor_service = FileProcessorService(
        app.extractor_factory,
        app.db_facade,
        app.config['UPLOAD_FOLDER']
    )
    app.logger.info("DBManager, ExtractorFactory, FileProcessorService 已初始化并附加到 app 对象。")

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
        stats = app.db_facade.get_general_statistics()
        if stats and stats.get('total_transactions', 0) > 0:
            app.logger.info(f"数据库已连接并包含 {stats.get('total_transactions', 0)} 条交易记录")
        else:
            app.logger.info("数据库为空或新创建")
    except Exception as e_init:
        app.logger.error(f"应用启动时执行 init_database 逻辑出错: {e_init}", exc_info=True)

    return app