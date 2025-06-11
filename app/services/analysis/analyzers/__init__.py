"""分析器模块

包含所有财务分析器的实现。
"""

from .base_analyzer import BaseAnalyzer
from .analyzer_context import AnalyzerContext
from .analyzer_factory import AnalyzerFactory

# 单一职责分析器
from .single_balance_analyzer import BalanceAnalyzer
from .single_cash_flow_analyzer import CashFlowAnalyzer
from .single_database_stats_analyzer import DatabaseStatsAnalyzer
from .single_expense_pattern_analyzer import ExpensePatternAnalyzer
from .single_growth_analyzer import GrowthAnalyzer
from .single_income_expense_analyzer import IncomeExpenseAnalyzer
from .single_income_stability_analyzer import IncomeStabilityAnalyzer

# 综合分析器
from .composite_income_analyzer import ComprehensiveIncomeAnalyzer
from .composite_financial_health_analyzer import FinancialHealthAnalyzer

__all__ = [
    # 基础类
    'BaseAnalyzer',
    
    # 依赖注入和工厂模式
    'AnalyzerContext',
    'AnalyzerFactory',
    
    # 单一职责分析器
    'BalanceAnalyzer',
    'CashFlowAnalyzer',
    'DatabaseStatsAnalyzer',
    'ExpensePatternAnalyzer',
    'GrowthAnalyzer',
    'IncomeExpenseAnalyzer',
    'IncomeStabilityAnalyzer',
    
    # 综合分析器
    'ComprehensiveIncomeAnalyzer',
    'FinancialHealthAnalyzer',
]