"""简化的数据模型

提供简洁、实用的数据结构，替代原有的复杂模型架构。
专注于核心功能，减少不必要的复杂性。

Created: 2024-12-19
Author: AI Assistant
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import date


@dataclass
class AnalysisResult:
    """分析结果
    
    通用的分析结果数据结构，适用于各种财务分析
    """
    total_amount: float = 0.0
    by_category: Dict[str, float] = field(default_factory=dict)
    by_month: Dict[str, float] = field(default_factory=dict)
    transaction_count: int = 0
    average_amount: float = 0.0
    
    def get_top_categories(self, limit: int = 5) -> List[tuple]:
        """获取金额最高的类别"""
        return sorted(self.by_category.items(), key=lambda x: x[1], reverse=True)[:limit]
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'total_amount': self.total_amount,
            'by_category': self.by_category,
            'by_month': self.by_month,
            'transaction_count': self.transaction_count,
            'average_amount': self.average_amount,
            'top_categories': self.get_top_categories()
        }


@dataclass
class MonthlyData:
    """月度数据"""
    year: int
    month: int
    income: float = 0.0
    expense: float = 0.0
    net_amount: float = 0.0
    transaction_count: int = 0
    
    @property
    def month_key(self) -> str:
        """月份键值"""
        return f"{self.year}-{self.month:02d}"
    
    @property
    def savings_rate(self) -> float:
        """储蓄率"""
        return (self.income - self.expense) / self.income if self.income > 0 else 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'year': self.year,
            'month': self.month,
            'month_key': self.month_key,
            'income': self.income,
            'expense': self.expense,
            'net_amount': self.net_amount,
            'transaction_count': self.transaction_count,
            'savings_rate': self.savings_rate
        }


@dataclass
class FinancialSummary:
    """财务总览"""
    total_income: float = 0.0
    total_expense: float = 0.0
    net_saving: float = 0.0
    avg_monthly_income: float = 0.0
    avg_monthly_expense: float = 0.0
    savings_rate: float = 0.0
    expense_ratio: float = 0.0
    
    def to_dict(self) -> Dict[str, float]:
        """转换为字典"""
        return {
            'total_income': self.total_income,
            'total_expense': self.total_expense,
            'net_saving': self.net_saving,
            'avg_monthly_income': self.avg_monthly_income,
            'avg_monthly_expense': self.avg_monthly_expense,
            'savings_rate': self.savings_rate,
            'expense_ratio': self.expense_ratio
        }


@dataclass
class FinancialHealthMetrics:
    """财务健康指标"""
    health_score: int = 0
    health_level: str = 'unknown'  # excellent, good, fair, poor
    savings_rate: float = 0.0
    expense_ratio: float = 0.0
    cash_flow_stability: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'health_score': self.health_score,
            'health_level': self.health_level,
            'savings_rate': self.savings_rate,
            'expense_ratio': self.expense_ratio,
            'cash_flow_stability': self.cash_flow_stability
        }


@dataclass
class ComprehensiveReport:
    """综合财务报告"""
    period_info: Dict[str, Any] = field(default_factory=dict)
    income_summary: AnalysisResult = field(default_factory=AnalysisResult)
    expense_summary: AnalysisResult = field(default_factory=AnalysisResult)
    cash_flow_data: Dict[str, Any] = field(default_factory=dict)
    financial_health: FinancialHealthMetrics = field(default_factory=FinancialHealthMetrics)
    monthly_trends: List[MonthlyData] = field(default_factory=list)
    key_insights: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'period_info': self.period_info,
            'income_summary': self.income_summary.to_dict(),
            'expense_summary': self.expense_summary.to_dict(),
            'cash_flow_data': self.cash_flow_data,
            'financial_health': self.financial_health.to_dict(),
            'monthly_trends': [trend.to_dict() for trend in self.monthly_trends],
            'key_insights': self.key_insights
        }