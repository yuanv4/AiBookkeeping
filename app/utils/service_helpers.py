"""简化的服务助手模块

提供简单的服务实例获取功能。
"""

import logging

logger = logging.getLogger(__name__)

def get_transaction_service():
    """获取交易服务实例"""
    from ..services import TransactionService
    return TransactionService()

def get_import_service():
    """获取导入服务实例"""
    from ..services import ImportService
    transaction_service = get_transaction_service()
    return ImportService(transaction_service)

def get_category_service():
    """获取分类服务实例"""
    from ..services import CategoryService
    return CategoryService()

def get_categories_config():
    """获取分类配置"""
    from app.configs.categories import CATEGORIES
    return CATEGORIES

def get_valid_category_codes():
    """获取有效分类代码列表"""
    from app.configs.categories import CATEGORIES
    return list(CATEGORIES.keys())


