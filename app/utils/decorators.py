"""简化装饰器模块

提供核心装饰器功能。
"""

import functools
import logging
from typing import Callable, Tuple, Any
from flask import request, render_template, jsonify

logger = logging.getLogger(__name__)


def is_api_request() -> bool:
    """判断是否为API请求"""
    return (request.path.startswith('/api/') or
            request.is_json or
            'application/json' in request.headers.get('Accept', ''))


def create_error_response(error: Exception, status_code: int = 500) -> Tuple[Any, int]:
    """创建统一的错误响应

    Args:
        error: 异常对象
        status_code: HTTP状态码

    Returns:
        响应对象和状态码的元组
    """
    error_message = str(error)

    # 记录错误日志
    if status_code >= 500:
        logger.error(f"服务器错误: {error_message}", exc_info=error)
    else:
        logger.warning(f"客户端错误: {error_message}")

    if is_api_request():
        # API请求返回JSON响应
        return jsonify({
            'success': False,
            'error': error_message,
            'status_code': status_code
        }), status_code
    else:
        # Web请求返回简洁的HTML响应
        if status_code == 404:
            html_content = f"""
            <!DOCTYPE html>
            <html><head><title>页面未找到 - 404</title></head>
            <body style="font-family: Arial, sans-serif; text-align: center; padding: 50px;">
                <h1>404 - 页面未找到</h1>
                <p>您访问的页面不存在。</p>
                <a href="/" style="color: #007bff; text-decoration: none;">返回首页</a>
            </body></html>
            """
        elif status_code == 500:
            html_content = f"""
            <!DOCTYPE html>
            <html><head><title>服务器错误 - 500</title></head>
            <body style="font-family: Arial, sans-serif; text-align: center; padding: 50px;">
                <h1>500 - 服务器错误</h1>
                <p>服务器遇到了问题，请稍后重试。</p>
                <a href="/" style="color: #007bff; text-decoration: none;">返回首页</a>
            </body></html>
            """
        else:
            html_content = f"""
            <!DOCTYPE html>
            <html><head><title>错误 - {status_code}</title></head>
            <body style="font-family: Arial, sans-serif; text-align: center; padding: 50px;">
                <h1>{status_code} - 错误</h1>
                <p>{error_message}</p>
                <a href="/" style="color: #007bff; text-decoration: none;">返回首页</a>
            </body></html>
            """
        return html_content, status_code


def handle_errors(func: Callable = None):
    """简化的错误处理装饰器

    自动捕获函数执行过程中的异常，并返回统一格式的错误响应。

    Usage:
        @handle_errors
        def my_route():
            # 可能抛出异常的代码
            return some_operation()
    """
    def decorator(f: Callable) -> Callable:
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            try:
                return f(*args, **kwargs)
            except Exception as e:
                logger.error(f"函数 {f.__name__} 执行出错: {e}", exc_info=True)
                return create_error_response(e, 500)
        return wrapper
    
    # 支持 @handle_errors 和 @handle_errors() 两种用法
    if func is None:
        return decorator
    else:
        return decorator(func)

# 导出主要接口
__all__ = [
    'handle_errors',
    'create_error_response'
]
