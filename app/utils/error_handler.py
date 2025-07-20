"""统一错误处理模块

提供统一的错误响应处理功能，消除重复的错误处理逻辑。
"""

import logging
from flask import request, render_template, jsonify, current_app
from typing import Optional, Dict, Any, Tuple


logger = logging.getLogger(__name__)


class ErrorHandler:
    """统一错误处理器类
    
    提供统一的错误响应格式和处理逻辑，支持JSON和HTML两种响应格式。
    """
    
    @staticmethod
    def is_api_request() -> bool:
        """判断是否为API请求
        
        Returns:
            如果是API请求返回True，否则返回False
        """
        return (request.path.startswith('/api/') or 
                request.is_json or
                (request.accept_mimetypes.accept_json and 
                 not request.accept_mimetypes.accept_html))
    
    @staticmethod
    def create_error_response(error: Exception, 
                            status_code: int = 500,
                            template: Optional[str] = None,
                            error_key: str = 'error',
                            default_data: Optional[Dict[str, Any]] = None) -> Tuple[Any, int]:
        """创建统一的错误响应
        
        Args:
            error: 异常对象
            status_code: HTTP状态码
            template: 错误模板路径（用于HTML响应）
            error_key: 错误信息在模板中的键名
            default_data: 默认数据
            
        Returns:
            响应对象和状态码的元组
        """
        error_message = str(error)
        
        # 记录错误日志
        if status_code >= 500:
            current_app.logger.error(f"服务器错误: {error_message}", exc_info=True)
        else:
            current_app.logger.warning(f"客户端错误 ({status_code}): {error_message}")
        
        # API请求返回JSON响应
        if ErrorHandler.is_api_request():
            return jsonify({
                'success': False,
                'error': error_message,
                'data': default_data or {}
            }), status_code
        
        # HTML请求返回模板响应
        if template:
            context = default_data or {}
            context[error_key] = error_message
            return render_template(template, **context), status_code
        
        # 如果没有指定模板，返回通用错误页面
        error_template = ErrorHandler._get_default_error_template(status_code)
        return render_template(error_template, error=error_message), status_code
    
    @staticmethod
    def _get_default_error_template(status_code: int) -> str:
        """获取默认错误模板

        Args:
            status_code: HTTP状态码

        Returns:
            错误模板路径
        """
        if status_code == 404:
            return 'errors/404.html'
        elif status_code >= 500:
            return 'errors/500.html'
        else:
            # 对于其他错误代码，使用500错误页面作为通用错误页面
            return 'errors/500.html'
    
    @staticmethod
    def handle_404_error(error) -> Tuple[Any, int]:
        """处理404错误
        
        Args:
            error: 404错误对象
            
        Returns:
            响应对象和状态码的元组
        """
        current_app.logger.warning(f"页面未找到 (404): {request.url} - {error}")
        return ErrorHandler.create_error_response(
            error=error,
            status_code=404,
            template='errors/404.html'
        )
    
    @staticmethod
    def handle_500_error(error) -> Tuple[Any, int]:
        """处理500错误
        
        Args:
            error: 500错误对象
            
        Returns:
            响应对象和状态码的元组
        """
        return ErrorHandler.create_error_response(
            error=error,
            status_code=500,
            template='errors/500.html'
        )
    
    @staticmethod
    def handle_general_exception(error) -> Tuple[Any, int]:
        """处理一般异常
        
        Args:
            error: 异常对象
            
        Returns:
            响应对象和状态码的元组
        """
        current_app.logger.error(f"发生未捕获的异常: {error}", exc_info=True)
        
        # 对于API请求或JSON请求，返回JSON格式错误
        if ErrorHandler.is_api_request():
            return jsonify({
                'success': False,
                'error': "服务器发生内部错误",
                'details': str(error)
            }), 500
        
        # 对于HTML请求，返回错误页面
        return render_template('errors/500.html', error="发生了一个意外错误"), 500
    
    @staticmethod
    def register_error_handlers(app):
        """注册全局错误处理器到Flask应用
        
        Args:
            app: Flask应用实例
        """
        @app.errorhandler(404)
        def page_not_found_error(e):
            return ErrorHandler.handle_404_error(e)
        
        @app.errorhandler(500)
        def internal_server_error_handler(e):
            return ErrorHandler.handle_500_error(e)
        
        @app.errorhandler(Exception)
        def handle_general_exception_handler(e):
            return ErrorHandler.handle_general_exception(e)
        
        app.logger.info("已注册统一错误处理器")


# ErrorResponseBuilder类已删除，因为没有实际使用
# 如果需要链式调用，可以直接使用ErrorHandler.create_error_response()方法
