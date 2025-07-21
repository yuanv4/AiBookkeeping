"""Services package for the Flask application.

简化的服务层架构，专注于简单、实用、易维护的原则。

架构特点:
- BankService: 银行数据管理服务
- AccountService: 账户数据管理服务
- TransactionService: 交易数据管理服务
- ImportService: 文件导入服务，集成了提取、解析、商家识别功能
- ReportService: 财务报告服务，专注于个人用户的核心分析需求
- CategoryService: 商户分类服务，提供分类算法和业务分析功能

使用示例:
    from app.services import BankService, AccountService, TransactionService
    from app.services import ImportService, ReportService, CategoryService

    # 专门的数据管理
    bank_service = BankService()
    account_service = AccountService(bank_service)
    transaction_service = TransactionService(account_service)

    # 文件导入
    import_service = ImportService(bank_service, account_service, transaction_service)
    result = import_service.process_uploaded_files(files)

    # 财务报告
    report_service = ReportService(bank_service, account_service, transaction_service, category_service)
    dashboard = report_service.get_dashboard_data()

    # 商户分类
    category_service = CategoryService()
    category = category_service.classify_merchant('麦当劳')
"""

# 核心服务类
from .base_service import BaseService
from .bank_service import BankService
from .account_service import AccountService
from .transaction_service import TransactionService
from .import_service import ImportService
from .report_service import ReportService
from .category_service import CategoryService

# 数据模型
from .models import (
    ExtractedData, ImportResult, DashboardData,  # 核心DTO类
    ImportConstants, DataConverters  # 工具类和常量
)

# 提取器（保留用于 ImportService）
from .extractors import ALL_EXTRACTORS

__all__ = [
    # 核心服务类
    'BaseService',
    'BankService',
    'AccountService',
    'TransactionService',
    'ImportService',
    'ReportService',
    'CategoryService',
    # 核心DTO类
    'ExtractedData', 'ImportResult', 'DashboardData',
    # 工具类和常量
    'ImportConstants', 'DataConverters',
    # 提取器
    'ALL_EXTRACTORS',
]