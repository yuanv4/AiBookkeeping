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
class RecurringExpense:
    """周期性支出项目"""
    category: str
    total_amount: float  # 历史累计总金额
    amount: float  # 平均金额（保持向后兼容）
    frequency: str  # 'monthly', 'weekly', 'quarterly'
    confidence_score: float  # 0-100的置信度分数
    last_occurrence: str  # 最近一次发生日期
    count: int  # 识别到的交易次数
    combination_key: str  # 完整的组合键，用于精确匹配

@dataclass
class ExpenseTrend:
    """支出趋势数据点"""
    date: str
    value: float
    category: str = "total"  # 可以是 'total', 'recurring', 'flexible'

@dataclass
class ExpenseAnalysisData:
    """支出分析综合数据"""
    target_month: str
    total_expense: float
    expense_trend: List[ExpenseTrend]  # 近6个月趋势
    recurring_expenses: List[RecurringExpense]  # 周期性支出排行
    flexible_composition: List[CompositionItem]  # 弹性支出分类占比
    top_categories: List[TopExpenseCategory]  # 支出分类排行（保持向后兼容）
    recurring_transactions: List[dict] = None  # 周期性支出交易明细
    flexible_transactions: List[dict] = None  # 弹性支出交易明细

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