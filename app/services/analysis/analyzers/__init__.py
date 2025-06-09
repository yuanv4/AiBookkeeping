# -*- coding: utf-8 -*-
"""
Financial Analyzers Package

This package contains specialized analyzer classes for different aspects of financial analysis,
including income/expense balance, cash flow health, income diversity, growth analysis,
financial resilience assessment, balance analysis, and database statistics.

All analyzers inherit from BaseAnalyzer and follow a consistent interface pattern.
"""

from .base_analyzer import BaseAnalyzer
from .income_analyzer import IncomeExpenseAnalyzer, IncomeStabilityAnalyzer
from .cash_flow_analyzer import CashFlowAnalyzer
from .diversity_analyzer import IncomeDiversityAnalyzer
from .growth_analyzer import IncomeGrowthAnalyzer
from .resilience_analyzer import FinancialResilienceAnalyzer
from .balance_analyzer import BalanceAnalyzer
from .database_stats_analyzer import DatabaseStatsAnalyzer

__all__ = [
    'BaseAnalyzer',
    'IncomeExpenseAnalyzer',
    'IncomeStabilityAnalyzer',
    'CashFlowAnalyzer',
    'IncomeDiversityAnalyzer',
    'IncomeGrowthAnalyzer',
    'FinancialResilienceAnalyzer',
    'BalanceAnalyzer',
    'DatabaseStatsAnalyzer'
]