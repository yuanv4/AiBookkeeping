"""分析服务模块

提供现金流分析和报告生成相关的服务。

主要组件:
- FinancialAnalysisService: 统一的财务分析服务，提供核心分析功能
- ExpenseAnalyzer: 复杂算法实现，包含周期性支出识别等高级分析
- dto: 数据传输对象，定义分析服务使用的数据结构

使用示例:
    from app.services.analysis import FinancialAnalysisService

    service = FinancialAnalysisService()
    dashboard_data = service.get_dashboard_initial_data()
"""

from .financial_analysis_service import FinancialAnalysisService
from .expense_analyzer import ExpenseAnalyzer, RecurringExpense, ExpenseTrend, ExpenseAnalysisData
from .dto import (
    Period,
    CoreMetrics,
    CompositionItem,
    TrendPoint,
    DashboardData
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