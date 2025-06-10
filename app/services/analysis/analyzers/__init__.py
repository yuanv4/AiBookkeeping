# -*- coding: utf-8 -*-
"""
Financial Analyzers Package

This package contains specialized analyzer classes for different aspects of financial analysis,
including income/expense balance, cash flow health, income diversity, growth analysis,
financial resilience assessment, balance analysis, and database statistics.

All analyzers inherit from BaseAnalyzer and follow a consistent interface pattern.
"""

from .base_analyzer import BaseAnalyzer
from .comprehensive_income_analyzer import ComprehensiveIncomeAnalyzer
from .financial_health_analyzer import FinancialHealthAnalyzer
from .growth_analyzer import GrowthAnalyzer
from .balance_analyzer import BalanceAnalyzer
from .database_stats_analyzer import DatabaseStatsAnalyzer

__all__ = [
    'BaseAnalyzer',
    'ComprehensiveIncomeAnalyzer',
    'FinancialHealthAnalyzer',
    'GrowthAnalyzer',
    'BalanceAnalyzer',
    'DatabaseStatsAnalyzer'
]