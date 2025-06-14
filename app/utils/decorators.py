"""通用装饰器模块

提供常用的装饰器功能，包括错误处理、日志记录等。
"""

import functools
from flask import current_app, render_template, jsonify, request
from typing import Callable, Any, Optional


def handle_errors(func_or_template=None, *,
                 template: Optional[str] = None, 
                 error_key: str = 'error',
                 default_data: Optional[dict] = None,
                 log_prefix: str = ""):
    """通用错误处理装饰器
    
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
                error_msg = f"{log_prefix}{func.__name__}错误: {str(e)}"
                current_app.logger.error(error_msg, exc_info=True)
                
                # 根据请求类型返回不同格式的错误响应
                if request.is_json or '/api/' in request.path:
                    return jsonify({
                        'success': False,
                        'error': str(e),
                        'data': default_data or {}
                    }), 500
                
                # HTML 响应
                if template:
                    context = default_data or {}
                    context[error_key] = str(e)
                    return render_template(template, **context)
                
                # 如果没有指定模板，重新抛出异常
                raise
                
        return wrapper
    
    # 如果直接使用 @handle_errors (不带括号)
    if func_or_template is not None and callable(func_or_template):
        return decorator(func_or_template)
    
    # 如果使用 @handle_errors() (带括号)
    return decorator


def log_execution(log_prefix: str = ""):
    """执行日志装饰器
    
    Args:
        log_prefix: 日志前缀
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            current_app.logger.info(f"{log_prefix}开始执行 {func.__name__}")
            try:
                result = func(*args, **kwargs)
                current_app.logger.info(f"{log_prefix}成功完成 {func.__name__}")
                return result
            except Exception as e:
                current_app.logger.error(f"{log_prefix}{func.__name__} 执行失败: {str(e)}")
                raise
        return wrapper
    return decorator


def validate_params(**validators):
    """参数验证装饰器
    
    Args:
        **validators: 参数验证器字典，键为参数名，值为验证函数
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # 验证参数
            for param_name, validator in validators.items():
                if param_name in kwargs:
                    value = kwargs[param_name]
                    if not validator(value):
                        raise ValueError(f"参数 {param_name} 验证失败: {value}")
            
            return func(*args, **kwargs)
        return wrapper
    return decorator