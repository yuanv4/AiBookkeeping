"""简化的服务辅助函数

重构后直接提供专门的服务类，移除DataService协调层。
使用简单的工厂模式，减少服务依赖复杂度。
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

# 保持向后兼容性的数据服务获取函数
def get_data_service():
    """获取数据服务实例（向后兼容）

    注意：这是为了向后兼容而保留的函数。
    新代码应该直接使用专门的服务类。

    Returns:
        dict: 包含各种服务的字典对象
    """
    if 'data_compat' not in _service_cache:
        # 创建一个兼容对象，包含所有服务的引用
        class DataServiceCompat:
            def __init__(self):
                self.bank_service = get_bank_service()
                self.account_service = get_account_service()
                self.transaction_service = get_transaction_service()

            # 委托方法以保持兼容性
            def get_or_create_bank(self, name: str, code: str = None):
                return self.bank_service.get_or_create_bank(name, code)

            def get_bank_by_name(self, name: str):
                return self.bank_service.get_bank_by_name(name)

            def get_all_banks(self):
                return self.bank_service.get_all_banks()

            def get_or_create_account(self, bank_id: int, account_number: str, account_name: str = None):
                return self.account_service.get_or_create_account(bank_id, account_number, account_name)

            def get_all_accounts(self):
                return self.account_service.get_all_accounts()

            def get_all_currencies(self):
                return self.transaction_service.get_all_currencies()

        _service_cache['data_compat'] = DataServiceCompat()
        logger.info("创建DataService兼容实例")
    return _service_cache['data_compat']

def get_import_service():
    """获取导入服务实例

    Returns:
        ImportService: 导入服务实例
    """
    if 'import' not in _service_cache:
        from ..services import ImportService
        # 使用兼容的数据服务
        data_service = get_data_service()
        _service_cache['import'] = ImportService(data_service)
        logger.info("创建ImportService实例")
    return _service_cache['import']

def get_report_service():
    """获取报告服务实例

    Returns:
        ReportService: 报告服务实例
    """
    if 'report' not in _service_cache:
        from ..services import ReportService
        # 使用兼容的数据服务
        data_service = get_data_service()
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
        services_status['data'] = get_data_service() is not None
        services_status['import'] = get_import_service() is not None
        services_status['report'] = get_report_service() is not None
        services_status['category'] = get_category_service() is not None
        services_status['cached_services'] = len(_service_cache)

        logger.info(f"服务健康检查完成: {services_status}")

    except Exception as e:
        logger.error(f"服务健康检查失败: {e}")
        services_status['error'] = str(e)

    return services_status
