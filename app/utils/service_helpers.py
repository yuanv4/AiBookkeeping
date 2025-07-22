"""服务助手模块

提供统一的服务实例获取和管理功能。
使用ServiceContainer管理依赖注入，确保服务实例的一致性。
"""

import logging

logger = logging.getLogger(__name__)


class ServiceContainer:
    """服务容器，管理服务实例的创建和依赖注入

    确保服务实例的单例模式和正确的依赖关系。
    遵循简单性、实用性、易维护性原则。
    """

    def __init__(self):
        """初始化服务容器"""
        self._services = {}
        self._initialized = False
        self.logger = logging.getLogger(__name__)

    def get_bank_service(self):
        """获取银行服务实例"""
        if 'bank_service' not in self._services:
            from ..services import BankService
            self._services['bank_service'] = BankService()
            self.logger.debug("创建BankService实例")
        return self._services['bank_service']

    def get_account_service(self):
        """获取账户服务实例"""
        if 'account_service' not in self._services:
            from ..services import AccountService
            bank_service = self.get_bank_service()
            self._services['account_service'] = AccountService(bank_service)
            self.logger.debug("创建AccountService实例")
        return self._services['account_service']

    def get_transaction_service(self):
        """获取交易服务实例"""
        if 'transaction_service' not in self._services:
            from ..services import TransactionService
            account_service = self.get_account_service()
            self._services['transaction_service'] = TransactionService(account_service)
            self.logger.debug("创建TransactionService实例")
        return self._services['transaction_service']


    def get_import_service(self):
        """获取导入服务实例"""
        if 'import_service' not in self._services:
            from ..services import ImportService
            bank_service = self.get_bank_service()
            account_service = self.get_account_service()
            transaction_service = self.get_transaction_service()
            self._services['import_service'] = ImportService(
                bank_service, account_service, transaction_service
            )
            self.logger.debug("创建ImportService实例")
        return self._services['import_service']

    def get_category_service(self):
        """获取分类服务实例"""
        if 'category_service' not in self._services:
            from ..services.category_service import CategoryService
            self._services['category_service'] = CategoryService()
            self.logger.debug("创建CategoryService实例")
        return self._services['category_service']

    def get_categories_config(self):
        """统一获取分类配置"""
        return self.get_category_service().get_all_categories()

    def get_valid_category_codes(self):
        """统一获取有效分类代码列表"""
        return self.get_category_service().get_valid_category_codes()

    def get_report_service(self):
        """获取报告服务实例"""
        if 'report_service' not in self._services:
            from ..services import ReportService
            bank_service = self.get_bank_service()
            account_service = self.get_account_service()
            transaction_service = self.get_transaction_service()
            category_service = self.get_category_service()
            self._services['report_service'] = ReportService(
                bank_service, account_service, transaction_service, category_service
            )
            self.logger.debug("创建ReportService实例")
        return self._services['report_service']

    def clear_cache(self):
        """清空服务缓存（主要用于测试）"""
        self._services.clear()
        self._initialized = False
        self.logger.debug("清空服务缓存")


# 全局服务容器实例
_service_container = ServiceContainer()

# 向后兼容的函数接口
def get_bank_service():
    """获取银行服务实例（向后兼容）"""
    return _service_container.get_bank_service()

def get_account_service():
    """获取账户服务实例（向后兼容）"""
    return _service_container.get_account_service()

def get_transaction_service():
    """获取交易服务实例（向后兼容）"""
    return _service_container.get_transaction_service()

def get_import_service():
    """获取导入服务实例（向后兼容）"""
    return _service_container.get_import_service()

def get_report_service():
    """获取报告服务实例（向后兼容）"""
    return _service_container.get_report_service()

def get_category_service():
    """获取分类服务实例（向后兼容）"""
    return _service_container.get_category_service()

def get_categories_config():
    """统一获取分类配置"""
    return _service_container.get_categories_config()

def get_valid_category_codes():
    """统一获取有效分类代码列表"""
    return _service_container.get_valid_category_codes()

def check_services_health() -> dict:
    """检查所有服务的健康状态"""
    services_status = {}
    try:
        services_status['bank'] = _service_container.get_bank_service() is not None
        services_status['account'] = _service_container.get_account_service() is not None
        services_status['transaction'] = _service_container.get_transaction_service() is not None
        services_status['import'] = _service_container.get_import_service() is not None
        services_status['report'] = _service_container.get_report_service() is not None
        services_status['category'] = _service_container.get_category_service() is not None
        logger.info(f"服务健康检查完成: {services_status}")
    except Exception as e:
        logger.error(f"服务健康检查失败: {e}")
        services_status['error'] = str(e)
    return services_status
