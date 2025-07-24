"""Services package for the Flask application.

简化的服务层架构，专注于简单、实用、易维护的原则。

架构特点:
- TransactionService: 交易数据管理服务
- ImportService: 文件导入服务，集成了提取、解析、商家识别功能
- ReportService: 财务报告服务，专注于个人用户的核心分析需求
- CategoryService: 商户分类服务，提供分类算法和业务分析功能

使用示例:
    from app.services import TransactionService, ImportService, ReportService, CategoryService
    from app.models import Transaction

    # 查询账户汇总
    account_summaries = Transaction.get_account_summary()

    # 按银行查询交易
    cmb_transactions = Transaction.get_by_bank("招商银行")

    # 按账户查询交易
    account_transactions = Transaction.get_by_account("1234567890")

    # 服务层操作
    transaction_service = TransactionService()
    category_service = CategoryService()

    # 文件导入（自动提取银行和账户信息）
    import_service = ImportService(transaction_service)
    result = import_service.process_uploaded_files(files)

    # 财务报告
    report_service = ReportService(transaction_service, category_service)
    dashboard = report_service.get_dashboard_data()

    # 商户分类
    category = category_service.classify_merchant('麦当劳')
"""

# 核心服务类
from .base_service import BaseService
from .transaction_service import TransactionService
from .import_service import ImportService
from .report_service import ReportService
from .category_service import CategoryService

# 提取器和数据模型
from .extractors import ExtractedData, ALL_EXTRACTORS

__all__ = [
    # 核心服务类
    'BaseService',
    'TransactionService',
    'ImportService',
    'ReportService',
    'CategoryService',
    # 核心DTO类
    'ExtractedData',
    # 提取器
    'ALL_EXTRACTORS',
]