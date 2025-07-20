"""通用装饰器模块

提供常用的装饰器功能，包括错误处理、日志记录等。
"""

import functools
from flask import current_app
from typing import Callable, Any, Optional, Union, List
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


def require_service(*service_names: str, error_template: Optional[str] = None):
    """服务依赖装饰器

    自动获取指定的服务并注入到被装饰的函数中。如果服务不可用，
    自动返回错误响应，避免重复的服务获取和错误处理代码。

    Args:
        *service_names: 需要的服务名称列表，支持: 'data', 'import', 'report', 'category'
        error_template: 错误时渲染的模板路径（可选）

    Usage:
        @require_service('data', 'report')
        def my_route(data_service, report_service):
            # 服务已自动注入，可直接使用
            return data_service.get_something()

        @require_service('data')
        def another_route(data_service):
            # 单个服务注入
            return data_service.get_data()
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # 导入服务获取函数（避免循环导入）
            from . import get_data_service, get_import_service, get_report_service, get_category_service

            # 服务获取函数映射
            service_getters = {
                'data': get_data_service,
                'import': get_import_service,
                'report': get_report_service,
                'category': get_category_service
            }

            # 获取所需服务
            services = []
            for service_name in service_names:
                if service_name not in service_getters:
                    current_app.logger.error(f"未知的服务名称: {service_name}")
                    return _create_service_error_response(
                        f"未知的服务名称: {service_name}",
                        error_template
                    )

                service = service_getters[service_name]()
                if service is None:
                    current_app.logger.error(f"{service_name}服务不可用")
                    return _create_service_error_response(
                        f"{service_name}服务不可用",
                        error_template
                    )

                services.append(service)

            # 将服务作为参数传递给原函数
            return func(*args, *services, **kwargs)

        return wrapper
    return decorator


def _create_service_error_response(error_message: str, template: Optional[str] = None):
    """创建服务错误响应

    Args:
        error_message: 错误消息
        template: 模板路径（可选）

    Returns:
        错误响应
    """
    if template:
        # 如果指定了模板，渲染模板
        from flask import render_template
        return render_template(template, error=error_message), 500
    else:
        # 否则返回JSON响应（延迟导入避免循环导入）
        from .data_utils import DataUtils
        return DataUtils.format_api_response(
            success=False,
            error=error_message
        ), 500

