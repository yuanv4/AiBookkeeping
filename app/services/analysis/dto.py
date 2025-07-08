"""分析服务数据模型

定义分析服务使用的数据传输对象（DTOs），使用dataclass提供类型安全和清晰的数据结构。
"""

from dataclasses import dataclass
from typing import List
from datetime import date
from decimal import Decimal

@dataclass
class Period:
    """时间周期"""
    start_date: str
    end_date: str
    days: int

@dataclass
class CoreMetrics:
    """核心现金流指标"""
    current_total_assets: Decimal
    total_income: Decimal
    total_expense: Decimal
    net_income: Decimal
    income_change_percentage: Decimal
    expense_change_percentage: Decimal
    net_change_percentage: Decimal
    emergency_reserve_months: Decimal

@dataclass
class CompositionItem:
    """构成项目（收入或支出分类）"""
    name: str
    amount: Decimal
    percentage: Decimal
    count: int

@dataclass
class TrendPoint:
    """趋势数据点"""
    date: str
    value: Decimal



# 注意：为了保持向后兼容性，这些复杂的数据类被移动到 expense_analyzer.py 中
# 如果需要使用 RecurringExpense, ExpenseTrend, ExpenseAnalysisData，请从 expense_analyzer 模块导入

@dataclass
class DashboardData:
    """仪表盘完整数据"""
    period: Period
    net_worth_trend: List[TrendPoint]
    core_metrics: CoreMetrics
    cash_flow: List[TrendPoint]
    income_composition: List[CompositionItem]
    expense_composition: List[CompositionItem]
    latest_transaction_month: str = None  # 最新交易月份，格式：YYYY-MM