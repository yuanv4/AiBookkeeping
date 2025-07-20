"""统一装饰器模块

提供项目中所有装饰器功能：
- 错误处理装饰器
- 缓存装饰器
"""

import functools
import logging
from functools import lru_cache
from typing import Callable, Tuple, Any
from flask import request, render_template, jsonify

logger = logging.getLogger(__name__)


def cached_query(maxsize: int = 128):
    """简化的查询缓存装饰器

    Args:
        maxsize: 缓存最大条目数，默认128

    Usage:
        @cached_query()  # 使用默认缓存大小
        def expensive_query():
            return some_expensive_operation()

        @cached_query(maxsize=256)  # 自定义缓存大小
        def another_query():
            return another_operation()
    """
    def decorator(func: Callable) -> Callable:
        return lru_cache(maxsize=maxsize)(func)
    return decorator


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
        # Web请求返回HTML响应
        return render_template('error.html',
                             error=error_message,
                             status_code=status_code), status_code


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
__all__ = ['handle_errors', 'create_error_response', 'cached_query']
