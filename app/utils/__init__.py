"""Utils package for the Flask application.

This package contains utility functions, decorators, and helper classes.
"""

# 聚合所有工具函数/类
from .decorators import handle_errors
from .template_filters import register_template_filters
from .data_utils import DataUtils
from .service_helpers import (
    get_bank_service, get_account_service, get_transaction_service,
    get_data_service, get_import_service, get_report_service, get_category_service,
    check_services_health
)

__all__ = [
    'handle_errors',
    'register_template_filters',
    'DataUtils',
    # 新的专门服务获取函数
    'get_bank_service',
    'get_account_service',
    'get_transaction_service',
    # 保持向后兼容的函数
    'get_data_service',
    'get_import_service',
    'get_report_service',
    'get_category_service',
    'check_services_health'
]