"""分析器模块

提供各种财务分析功能，包括收支分析、现金流分析、支出模式分析等。
采用单一职责原则和组合模式设计，确保代码的可维护性和可扩展性。
"""

# 基础类
from .base_analyzer import BaseAnalyzer
# from .analysis_result import AnalysisResult  # 文件不存在，已注释

# 依赖注入和工厂模式
from .analyzer_context import AnalyzerContext
from .analyzer_factory import AnalyzerFactory

# 单一职责分析器
from .income_expense_analyzer import IncomeExpenseAnalyzer
from .income_stability_analyzer import IncomeStabilityAnalyzer
from .cash_flow_analyzer import CashFlowAnalyzer
from .expense_pattern_analyzer import ExpensePatternAnalyzer
# from .budget_variance_analyzer import BudgetVarianceAnalyzer  # 文件不存在，已注释

# 综合分析器
from .comprehensive_income_analyzer import ComprehensiveIncomeAnalyzer
from .financial_health_analyzer import FinancialHealthAnalyzer

__all__ = [
    # 基础类
    'BaseAnalyzer',
    # 'AnalysisResult',  # 文件不存在
    
    # 依赖注入和工厂模式
    'AnalyzerContext',
    'AnalyzerFactory',
    
    # 单一职责分析器
    'IncomeExpenseAnalyzer',
    'IncomeStabilityAnalyzer',
    'CashFlowAnalyzer',
    'ExpensePatternAnalyzer',
    # 'BudgetVarianceAnalyzer',  # 文件不存在
    
    # 综合分析器
    'ComprehensiveIncomeAnalyzer',
    'FinancialHealthAnalyzer',
]