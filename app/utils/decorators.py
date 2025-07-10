"""通用装饰器模块

提供常用的装饰器功能，包括错误处理、日志记录等。
"""

import functools
from flask import current_app
from typing import Callable, Any, Optional
from .error_handler import ErrorHandler


def handle_errors(func_or_template=None, *,
                 template: Optional[str] = None,
                 error_key: str = 'error',
                 default_data: Optional[dict] = None,
                 log_prefix: str = ""):
    """通用错误处理装饰器

    支持两种调用方式:
    @handle_errors  # 不带括号
    @handle_errors()  # 带括号

    Args:
        func_or_template: 被装饰的函数或模板路径
        template: 错误时渲染的模板路径
        error_key: 错误信息在模板中的键名
        default_data: 错误时返回的默认数据
        log_prefix: 日志前缀
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # 记录错误日志
                if log_prefix:
                    current_app.logger.error(f"{log_prefix}{func.__name__}错误: {str(e)}")
                else:
                    current_app.logger.error(f"{func.__name__}错误: {str(e)}")

                # 使用统一的错误处理器
                return ErrorHandler.create_error_response(
                    error=e,
                    status_code=500,
                    template=template,
                    error_key=error_key,
                    default_data=default_data
                )
        return wrapper

    # 如果直接使用 @handle_errors (不带括号)
    if func_or_template is not None and callable(func_or_template):
        return decorator(func_or_template)

    # 如果使用 @handle_errors() (带括号)
    return decorator

