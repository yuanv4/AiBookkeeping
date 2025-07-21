"""服务辅助函数

提供简化的服务类实例获取函数。
移除复杂的缓存机制，使用简单的单例模式。
"""

import logging

logger = logging.getLogger(__name__)

def get_bank_service():
    """获取银行服务实例

    Returns:
        BankService: 银行服务实例
    """
    from ..services import BankService
    return BankService()

def get_account_service():
    """获取账户服务实例

    Returns:
        AccountService: 账户服务实例
    """
    from ..services import AccountService
    bank_service = get_bank_service()
    return AccountService(bank_service)

def get_transaction_service():
    """获取交易服务实例

    Returns:
        TransactionService: 交易服务实例
    """
    from ..services import TransactionService
    account_service = get_account_service()
    return TransactionService(account_service)



def get_import_service():
    """获取导入服务实例

    Returns:
        ImportService: 导入服务实例
    """
    from ..services import ImportService
    # ImportService现在需要直接使用专门的服务，而不是DataService
    bank_service = get_bank_service()
    account_service = get_account_service()
    transaction_service = get_transaction_service()
    return ImportService(bank_service, account_service, transaction_service)

def get_report_service():
    """获取报告服务实例

    Returns:
        ReportService: 报告服务实例
    """
    from ..services import ReportService
    # ReportService现在需要直接使用专门的服务，而不是DataService
    bank_service = get_bank_service()
    account_service = get_account_service()
    transaction_service = get_transaction_service()
    category_service = get_category_service()
    return ReportService(bank_service, account_service, transaction_service, category_service)

def get_category_service():
    """获取分类服务实例

    Returns:
        CategoryService: 分类服务实例
    """
    from ..services.category_service import CategoryService
    return CategoryService()

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

        logger.info(f"服务健康检查完成: {services_status}")

    except Exception as e:
        logger.error(f"服务健康检查失败: {e}")
        services_status['error'] = str(e)

    return services_status
