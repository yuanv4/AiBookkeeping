"""Utils package for the Flask application.

This package contains utility functions, decorators, and helper classes.
"""

# 聚合所有工具函数/类
from .decorators import handle_errors
from .template_filters import register_template_filters
from .data_utils import DataUtils
from .service_helpers import (
    get_transaction_service,
    get_import_service, get_report_service, get_category_service,
    get_categories_config, get_valid_category_codes,
    check_services_health
)

def has_financial_data():
    """检测是否有财务数据的简单函数"""
    try:
        from app.models import Transaction
        return Transaction.query.count() > 0
    except Exception:
        return True  # 出错时假设有数据，避免误显示


__all__ = [
    'handle_errors',
    'register_template_filters',
    'DataUtils',
    # 专门服务获取函数
    'get_bank_service',
    'get_account_service',
    'get_transaction_service',
    'get_import_service',
    'get_report_service',
    'get_category_service',
    'get_categories_config',
    'get_valid_category_codes',
    'check_services_health',
    'has_financial_data'
]