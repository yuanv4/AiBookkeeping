"""Utils package for the Flask application.

This package contains utility functions, decorators, and helper classes.
"""

# 聚合所有工具函数/类
from .decorators import handle_errors
from .template_filters import register_template_filters
from .data_utils import DataUtils
from .service_registry import ServiceRegistry
from .service_helpers import (
    get_data_service, get_import_service, get_report_service, get_category_service,
    initialize_core_services, check_services_health
)

__all__ = [
    'handle_errors',
    'register_template_filters',
    'DataUtils',
    'ServiceRegistry',
    'get_data_service',
    'get_import_service',
    'get_report_service',
    'get_category_service',
    'initialize_core_services',
    'check_services_health'
]