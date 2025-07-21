"""服务辅助函数

提供专门的服务类实例获取函数。
使用简单的工厂模式和缓存机制，优化服务实例管理。
"""

from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

# 全局服务实例缓存
_service_cache: Dict[str, Any] = {}

def get_bank_service():
    """获取银行服务实例

    Returns:
        BankService: 银行服务实例
    """
    if 'bank' not in _service_cache:
        from ..services import BankService
        _service_cache['bank'] = BankService()
        logger.info("创建BankService实例")
    return _service_cache['bank']

def get_account_service():
    """获取账户服务实例

    Returns:
        AccountService: 账户服务实例
    """
    if 'account' not in _service_cache:
        from ..services import AccountService, BankService
        bank_service = get_bank_service()
        _service_cache['account'] = AccountService(bank_service)
        logger.info("创建AccountService实例")
    return _service_cache['account']

def get_transaction_service():
    """获取交易服务实例

    Returns:
        TransactionService: 交易服务实例
    """
    if 'transaction' not in _service_cache:
        from ..services import TransactionService
        account_service = get_account_service()
        _service_cache['transaction'] = TransactionService(account_service)
        logger.info("创建TransactionService实例")
    return _service_cache['transaction']



def get_import_service():
    """获取导入服务实例

    Returns:
        ImportService: 导入服务实例
    """
    if 'import' not in _service_cache:
        from ..services import ImportService, DataService
        data_service = DataService()
        _service_cache['import'] = ImportService(data_service)
        logger.info("创建ImportService实例")
    return _service_cache['import']

def get_report_service():
    """获取报告服务实例

    Returns:
        ReportService: 报告服务实例
    """
    if 'report' not in _service_cache:
        from ..services import ReportService, DataService
        data_service = DataService()
        category_service = get_category_service()
        _service_cache['report'] = ReportService(data_service, category_service=category_service)
        logger.info("创建ReportService实例")
    return _service_cache['report']

def get_category_service():
    """获取分类服务实例

    Returns:
        CategoryService: 分类服务实例
    """
    if 'category' not in _service_cache:
        from ..services.category_service import CategoryService
        _service_cache['category'] = CategoryService()
        logger.info("创建CategoryService实例")
    return _service_cache['category']

def check_services_health() -> dict:
    """检查所有服务的健康状态"""
    services_status = {}

    try:
        # 检查专门的服务类
        services_status['bank'] = get_bank_service() is not None
        services_status['account'] = get_account_service() is not None
        services_status['transaction'] = get_transaction_service() is not None
        services_status['import'] = get_import_service() is not None
        services_status['report'] = get_report_service() is not None
        services_status['category'] = get_category_service() is not None
        services_status['cached_services'] = len(_service_cache)

        logger.info(f"服务健康检查完成: {services_status}")

    except Exception as e:
        logger.error(f"服务健康检查失败: {e}")
        services_status['error'] = str(e)

    return services_status
