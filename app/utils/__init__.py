"""Utils package initialization"""

from .data_utils import DataUtils
from .service_helpers import get_import_service
from .compat_layer import TransactionCompatLayer
from .template_filters import register_template_filters
from .category_utils import CategoryUtils
from .decorators import handle_errors

def has_financial_data():
    """检查是否有财务数据"""
    from app.models import CoreTransaction
    return CoreTransaction.query.count() > 0

def get_categories_config():
    """获取分类配置"""
    from app.configs.categories import CATEGORIES
    return CATEGORIES

__all__ = [
    'DataUtils',
    'get_import_service',
    'TransactionCompatLayer',
    'register_template_filters',
    'CategoryUtils',
    'handle_errors',
    'has_financial_data',
    'get_categories_config'
]
