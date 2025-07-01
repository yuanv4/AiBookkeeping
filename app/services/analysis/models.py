"""分析服务数据模型

定义分析服务使用的数据传输对象（DTOs），使用dataclass提供类型安全和清晰的数据结构。
"""

from dataclasses import dataclass
from typing import List
from datetime import date

@dataclass
class Period:
    """时间周期"""
    start_date: str
    end_date: str
    days: int

@dataclass
class CoreMetrics:
    """核心现金流指标"""
    current_total_assets: float
    total_income: float
    total_expense: float
    net_income: float
    income_change_percentage: float
    expense_change_percentage: float
    net_change_percentage: float
    emergency_reserve_months: float

@dataclass
class CompositionItem:
    """构成项目（收入或支出分类）"""
    name: str
    amount: float
    percentage: float
    count: int

@dataclass
class TrendPoint:
    """趋势数据点"""
    date: str
    value: float

@dataclass
class TopExpenseCategory:
    """支出分类排行项目"""
    category: str
    total_amount: float
    percentage: float
    count: int

@dataclass
class DashboardData:
    """仪表盘完整数据"""
    period: Period
    net_worth_trend: List[TrendPoint]
    core_metrics: CoreMetrics
    cash_flow: List[TrendPoint]
    income_composition: List[CompositionItem]
    expense_composition: List[CompositionItem]
    top_expense_categories: List[TopExpenseCategory] 