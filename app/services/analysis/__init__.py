"""分析服务模块

提供现金流分析和报告生成相关的服务。

主要组件:
- FinancialAnalysisService: 统一的财务分析服务，提供核心分析功能
- ExpenseAnalyzer: 复杂算法实现，包含周期性支出识别等高级分析
- dto: 数据传输对象，定义分析服务使用的数据结构
- utils: 通用工具函数，包含日期处理、数据验证等功能

代码组织:
- 消除了重复代码，统一了工具函数
- 集中管理数据类定义，提高一致性
- 优化了模块依赖关系，增强可维护性

使用示例:
    from app.services.analysis import FinancialAnalysisService

    service = FinancialAnalysisService()
    dashboard_data = service.get_dashboard_initial_data()
"""

from .financial_analysis_service import FinancialAnalysisService
from .expense_analyzer import ExpenseAnalyzer
from .dto import (
    Period,
    CoreMetrics,
    CompositionItem,
    TrendPoint,
    DashboardData,
    RecurringExpense,
    ExpenseTrend,
    ExpenseAnalysisData
)



__all__ = [
    'FinancialAnalysisService',
    'ExpenseAnalyzer',
    'Period',
    'CoreMetrics',
    'CompositionItem',
    'TrendPoint',
    'RecurringExpense',
    'ExpenseTrend',
    'ExpenseAnalysisData',
    'DashboardData'
]