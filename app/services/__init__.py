"""Services package for the Flask application.

优化后的服务层架构，提供简化的、易于维护的服务接口。

新架构特点:
- DataService: 统一的数据管理服务，替代原来的 AccountService、BankService、TransactionService
- ImportService: 完整的文件导入服务，集成了提取、解析、商家识别功能
- ReportService: 基础财务报告服务，专注于个人用户的核心分析需求
- 统一的数据模型: 简化的DTO定义，提供类型安全和数据验证

使用示例:
    from app.services import DataService, ImportService, ReportService

    # 统一数据管理
    data_service = DataService()
    banks = data_service.get_all_banks()

    # 文件导入
    import_service = ImportService(data_service)
    result = import_service.process_uploaded_files(files)

    # 财务报告
    report_service = ReportService(data_service)
    dashboard = report_service.get_dashboard_data()
"""

# 新的统一服务
from .data_service import DataService
from .import_service import ImportService
from .report_service import ReportService

# 数据模型 - 保留复杂DTO类，简单数据结构已改为字典
from .models import (
    ExtractedData, ImportResult, DashboardData,  # 保留的复杂DTO类
    create_period, create_composition_item, create_trend_point,  # 字典构造函数
    create_period_summary, create_account_summary, create_expense_item,
    DateUtils, DataConverters  # 工具类
)

# 提取器（保留用于 ImportService）
from .extractors import ALL_EXTRACTORS

__all__ = [
    # 新的统一服务
    'DataService',
    'ImportService',
    'ReportService',
    # 保留的复杂DTO类
    'ExtractedData', 'ImportResult', 'DashboardData',
    # 字典构造函数
    'create_period', 'create_composition_item', 'create_trend_point',
    'create_period_summary', 'create_account_summary', 'create_expense_item',
    # 工具类
    'DateUtils', 'DataConverters',
    # 提取器
    'ALL_EXTRACTORS',
]