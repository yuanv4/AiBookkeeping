"""Analysis data models using dataclasses for better type safety and structure."""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from decimal import Decimal


@dataclass
class OverallStats:
    """Overall financial statistics."""
    total_income: float = 0.0
    total_expense: float = 0.0
    net_saving: float = 0.0
    avg_monthly_income: float = 0.0
    avg_monthly_expense: float = 0.0
    avg_monthly_saving_rate: float = 0.0
    avg_monthly_ratio: float = 0.0
    avg_necessary_expense_coverage: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for template compatibility."""
        return {
            'total_income': self.total_income,
            'total_expense': self.total_expense,
            'net_saving': self.net_saving,
            'avg_monthly_income': self.avg_monthly_income,
            'avg_monthly_expense': self.avg_monthly_expense,
            'avg_monthly_saving_rate': self.avg_monthly_saving_rate,
            'avg_monthly_ratio': self.avg_monthly_ratio,
            'avg_necessary_expense_coverage': self.avg_necessary_expense_coverage
        }


@dataclass
class MonthlyData:
    """Monthly financial data."""
    year: int
    month: int
    income: float = 0.0
    expense: float = 0.0
    balance: float = 0.0
    saving_rate: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for template compatibility."""
        return {
            'year': self.year,
            'month': self.month,
            'income': self.income,
            'expense': self.expense,
            'balance': self.balance,
            'saving_rate': self.saving_rate
        }


@dataclass
class IncomeExpenseBalance:
    """Income and expense balance analysis data."""
    overall_stats: OverallStats = field(default_factory=OverallStats)
    monthly_data: List[MonthlyData] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for template compatibility."""
        return {
            'overall_stats': self.overall_stats.to_dict(),
            'monthly_data': [data.to_dict() for data in self.monthly_data]
        }


@dataclass
class StabilityMetrics:
    """Income stability metrics."""
    coefficient_of_variation: float = 0.0
    stability_score: float = 0.0
    trend_direction: str = 'stable'
    volatility_level: str = 'low'
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for template compatibility."""
        return {
            'coefficient_of_variation': self.coefficient_of_variation,
            'stability_score': self.stability_score,
            'trend_direction': self.trend_direction,
            'volatility_level': self.volatility_level
        }


@dataclass
class IncomeStability:
    """Income stability analysis data."""
    metrics: StabilityMetrics = field(default_factory=StabilityMetrics)
    monthly_variance: List[Dict[str, Any]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for template compatibility."""
        return {
            'metrics': self.metrics.to_dict(),
            'monthly_variance': self.monthly_variance
        }


@dataclass
class CashFlowMetrics:
    """Cash flow health metrics."""
    liquidity_ratio: float = 0.0
    cash_flow_trend: str = 'stable'
    emergency_fund_months: float = 0.0
    debt_to_income_ratio: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for template compatibility."""
        return {
            'liquidity_ratio': self.liquidity_ratio,
            'cash_flow_trend': self.cash_flow_trend,
            'emergency_fund_months': self.emergency_fund_months,
            'debt_to_income_ratio': self.debt_to_income_ratio
        }


@dataclass
class CashFlowHealth:
    """Cash flow health analysis data."""
    metrics: CashFlowMetrics = field(default_factory=CashFlowMetrics)
    monthly_flow: List[Dict[str, Any]] = field(default_factory=list)
    gap_frequency: float = 0.0
    avg_gap: float = 0.0
    total_balance: float = 0.0
    monthly_cash_flow: List[Dict[str, Any]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for template compatibility."""
        return {
            'metrics': self.metrics.to_dict(),
            'monthly_flow': self.monthly_flow,
            'gap_frequency': self.gap_frequency,
            'avg_gap': self.avg_gap,
            'total_balance': self.total_balance,
            'monthly_cash_flow': self.monthly_cash_flow
        }


@dataclass
class DiversityMetrics:
    """Income diversity metrics."""
    diversity_index: float = 0.0
    primary_source_percentage: float = 0.0
    source_count: int = 0
    risk_level: str = 'medium'
    concentration: float = 0.0
    passive_income_ratio: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for template compatibility."""
        return {
            'diversity_index': self.diversity_index,
            'primary_source_percentage': self.primary_source_percentage,
            'source_count': self.source_count,
            'risk_level': self.risk_level,
            'concentration': self.concentration,
            'passive_income_ratio': self.passive_income_ratio
        }


@dataclass
class IncomeDiversity:
    """Income diversity analysis data."""
    metrics: DiversityMetrics = field(default_factory=DiversityMetrics)
    source_breakdown: List[Dict[str, Any]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for template compatibility."""
        result = {
            'metrics': self.metrics.to_dict(),
            'source_breakdown': self.source_breakdown
        }
        # Add backward compatibility for direct field access
        result.update({
            'concentration': self.metrics.concentration,
            'passive_income_ratio': self.metrics.passive_income_ratio,
            'source_count': self.metrics.source_count,
            'diversity_index': self.metrics.diversity_index,
            'primary_source_percentage': self.metrics.primary_source_percentage,
            'risk_level': self.metrics.risk_level
        })
        return result


@dataclass
class GrowthMetrics:
    """Income growth metrics."""
    year_over_year_growth: float = 0.0
    quarter_over_quarter_growth: float = 0.0
    growth_trend: str = 'stable'
    projected_annual_income: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for template compatibility."""
        return {
            'year_over_year_growth': self.year_over_year_growth,
            'quarter_over_quarter_growth': self.quarter_over_quarter_growth,
            'growth_trend': self.growth_trend,
            'projected_annual_income': self.projected_annual_income
        }


@dataclass
class IncomeGrowth:
    """Income growth analysis data."""
    metrics: GrowthMetrics = field(default_factory=GrowthMetrics)
    historical_growth: List[Dict[str, Any]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for template compatibility."""
        return {
            'metrics': self.metrics.to_dict(),
            'historical_growth': self.historical_growth
        }


@dataclass
class ResilienceMetrics:
    """Financial resilience metrics."""
    resilience_score: float = 0.0
    stress_test_result: str = 'good'
    recovery_capacity: float = 0.0
    financial_buffer_months: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for template compatibility."""
        return {
            'resilience_score': self.resilience_score,
            'stress_test_result': self.stress_test_result,
            'recovery_capacity': self.recovery_capacity,
            'financial_buffer_months': self.financial_buffer_months
        }


@dataclass
class FinancialResilience:
    """Financial resilience analysis data."""
    metrics: ResilienceMetrics = field(default_factory=ResilienceMetrics)
    scenario_analysis: List[Dict[str, Any]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for template compatibility."""
        return {
            'metrics': self.metrics.to_dict(),
            'scenario_analysis': self.scenario_analysis
        }


@dataclass
class ComprehensiveAnalysisData:
    """Complete comprehensive analysis data structure."""
    income_expense_balance: IncomeExpenseBalance = field(default_factory=IncomeExpenseBalance)
    income_stability: IncomeStability = field(default_factory=IncomeStability)
    cash_flow_health: CashFlowHealth = field(default_factory=CashFlowHealth)
    income_diversity: IncomeDiversity = field(default_factory=IncomeDiversity)
    income_growth: IncomeGrowth = field(default_factory=IncomeGrowth)
    financial_resilience: FinancialResilience = field(default_factory=FinancialResilience)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for template compatibility."""
        return {
            'income_expense_balance': self.income_expense_balance.to_dict(),
            'income_stability': self.income_stability.to_dict(),
            'cash_flow_health': self.cash_flow_health.to_dict(),
            'income_diversity': self.income_diversity.to_dict(),
            'income_growth': self.income_growth.to_dict(),
            'financial_resilience': self.financial_resilience.to_dict()
        }