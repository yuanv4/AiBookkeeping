"""Analysis models for financial data analysis."""

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
class IncomeExpenseAnalysis:
    """Income and expense analysis results."""
    overall_stats: OverallStats
    monthly_data: List[MonthlyData] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for template compatibility."""
        return {
            'overall_stats': self.overall_stats.to_dict(),
            'monthly_data': [month.to_dict() for month in self.monthly_data]
        }


# Legacy compatibility classes
@dataclass
class IncomeExpenseBalance:
    """Legacy compatibility class for IncomeExpenseAnalysis."""
    overall_stats: OverallStats = field(default_factory=OverallStats)
    monthly_data: List[MonthlyData] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for template compatibility."""
        return {
            'overall_stats': self.overall_stats.to_dict(),
            'monthly_data': [month.to_dict() for month in self.monthly_data]
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
    
    # 向后兼容的属性代理
    @property
    def concentration_risk(self) -> float:
        """获取集中度风险（向后兼容）。"""
        return getattr(self.metrics, 'concentration_risk', 0.0)
    
    @property
    def source_count(self) -> int:
        """获取收入来源数量（向后兼容）。"""
        return getattr(self.metrics, 'source_count', 0)
    
    @property
    def passive_income_ratio(self) -> float:
        """获取被动收入比例（向后兼容）。"""
        return getattr(self.metrics, 'passive_income_ratio', 0.0)
    
    @property
    def diversity_score(self) -> float:
        """获取多样性分数（向后兼容）。"""
        return getattr(self.metrics, 'diversity_score', 0.0)
    
    @property
    def primary_source_ratio(self) -> float:
        """获取主要收入来源占比（向后兼容）。"""
        return getattr(self.metrics, 'primary_source_percentage', 0.0) / 100.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for template compatibility."""
        result = {
            'metrics': self.metrics.to_dict(),
            'source_breakdown': self.source_breakdown
        }
        # Add backward compatibility for direct field access
        result.update({
            'concentration': getattr(self.metrics, 'concentration', 0.0),
            'passive_income_ratio': self.passive_income_ratio,
            'source_count': self.source_count,
            'diversity_index': getattr(self.metrics, 'diversity_index', 0.0),
            'primary_source_percentage': getattr(self.metrics, 'primary_source_percentage', 0.0),
            'risk_level': getattr(self.metrics, 'risk_level', 'low'),
            'concentration_risk': self.concentration_risk,
            'diversity_score': self.diversity_score
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
class CashFlowMetrics:
    """Cash flow analysis metrics."""
    total_inflow: float = 0.0
    total_outflow: float = 0.0
    net_cash_flow: float = 0.0
    average_monthly_inflow: float = 0.0
    average_monthly_outflow: float = 0.0
    cash_flow_volatility: float = 0.0
    positive_months: int = 0
    negative_months: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for template compatibility."""
        return {
            'total_inflow': self.total_inflow,
            'total_outflow': self.total_outflow,
            'net_cash_flow': self.net_cash_flow,
            'average_monthly_inflow': self.average_monthly_inflow,
            'average_monthly_outflow': self.average_monthly_outflow,
            'cash_flow_volatility': self.cash_flow_volatility,
            'positive_months': self.positive_months,
            'negative_months': self.negative_months
        }


@dataclass
class CashFlowHealth:
    """Cash flow health assessment."""
    health_score: float = 0.0
    health_level: str = "Unknown"
    recommendations: List[str] = field(default_factory=list)
    metrics: CashFlowMetrics = field(default_factory=CashFlowMetrics)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for template compatibility."""
        return {
            'health_score': self.health_score,
            'health_level': self.health_level,
            'recommendations': self.recommendations,
            'metrics': self.metrics.to_dict()
        }


@dataclass
class IncomeDiversityMetrics:
    """Income diversity analysis metrics."""
    diversity_score: float = 0.0
    income_sources: Dict[str, float] = field(default_factory=dict)
    concentration_risk: float = 0.0
    stability_score: float = 0.0
    recommendations: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for template compatibility."""
        return {
            'diversity_score': self.diversity_score,
            'income_sources': self.income_sources,
            'concentration_risk': self.concentration_risk,
            'stability_score': self.stability_score,
            'recommendations': self.recommendations
        }


@dataclass
class IncomeGrowthMetrics:
    """Income growth analysis metrics."""
    growth_rate: float = 0.0
    trend: str = "Stable"
    volatility: float = 0.0
    consistency_score: float = 0.0
    monthly_growth_rates: List[float] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for template compatibility."""
        return {
            'growth_rate': self.growth_rate,
            'trend': self.trend,
            'volatility': self.volatility,
            'consistency_score': self.consistency_score,
            'monthly_growth_rates': self.monthly_growth_rates,
            'recommendations': self.recommendations
        }


@dataclass
class ResilienceMetrics:
    """Financial resilience metrics."""
    emergency_fund_months: float = 0.0
    debt_to_income_ratio: float = 0.0
    savings_rate: float = 0.0
    expense_stability: float = 0.0
    income_stability: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for template compatibility."""
        return {
            'emergency_fund_months': self.emergency_fund_months,
            'debt_to_income_ratio': self.debt_to_income_ratio,
            'savings_rate': self.savings_rate,
            'expense_stability': self.expense_stability,
            'income_stability': self.income_stability
        }


@dataclass
class FinancialResilience:
    """Financial resilience analysis results."""
    resilience_score: float = 0.0
    resilience_level: str = "Unknown"
    metrics: ResilienceMetrics = field(default_factory=ResilienceMetrics)
    recommendations: List[str] = field(default_factory=list)
    risk_factors: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for template compatibility."""
        return {
            'resilience_score': self.resilience_score,
            'resilience_level': self.resilience_level,
            'metrics': self.metrics.to_dict(),
            'recommendations': self.recommendations,
            'risk_factors': self.risk_factors
        }


@dataclass
class ComprehensiveAnalysis:
    """Comprehensive financial analysis results."""
    income_expense: IncomeExpenseAnalysis = field(default_factory=IncomeExpenseAnalysis)
    cash_flow: CashFlowHealth = field(default_factory=CashFlowHealth)
    diversity: IncomeDiversityMetrics = field(default_factory=IncomeDiversityMetrics)
    growth: IncomeGrowthMetrics = field(default_factory=IncomeGrowthMetrics)
    resilience: FinancialResilience = field(default_factory=FinancialResilience)
    overall_score: float = 0.0
    summary: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for template compatibility."""
        return {
            'income_expense': self.income_expense.to_dict(),
            'cash_flow': self.cash_flow.to_dict(),
            'diversity': self.diversity.to_dict(),
            'growth': self.growth.to_dict(),
            'resilience': self.resilience.to_dict(),
            'overall_score': self.overall_score,
            'summary': self.summary
        }


@dataclass
class BalanceMetrics:
    """Balance analysis metrics."""
    total_balance: float = 0.0
    min_balance: float = 0.0
    max_balance: float = 0.0
    balance_range: float = 0.0
    account_count: int = 0
    balance_trend: str = "稳定"
    balance_stability: float = 1.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for template compatibility."""
        return {
            'total_balance': self.total_balance,
            'min_balance': self.min_balance,
            'max_balance': self.max_balance,
            'balance_range': self.balance_range,
            'account_count': self.account_count,
            'balance_trend': self.balance_trend,
            'balance_stability': self.balance_stability
        }


@dataclass
class BalanceAnalysis:
    """Balance analysis results."""
    metrics: BalanceMetrics = field(default_factory=BalanceMetrics)
    balance_range: Dict[str, Any] = field(default_factory=dict)
    monthly_history: List[Dict[str, Any]] = field(default_factory=list)
    balance_summary: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for template compatibility."""
        return {
            'metrics': self.metrics.to_dict(),
            'balance_range': self.balance_range,
            'monthly_history': self.monthly_history,
            'balance_summary': self.balance_summary
        }


@dataclass
class DatabaseMetrics:
    """Database statistics metrics."""
    total_banks: int = 0
    active_banks: int = 0
    total_accounts: int = 0
    active_accounts: int = 0
    total_transactions: int = 0
    income_transactions: int = 0
    expense_transactions: int = 0
    active_banks_ratio: float = 0.0
    active_accounts_ratio: float = 0.0
    income_ratio: float = 0.0
    expense_ratio: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for template compatibility."""
        return {
            'total_banks': self.total_banks,
            'active_banks': self.active_banks,
            'total_accounts': self.total_accounts,
            'active_accounts': self.active_accounts,
            'total_transactions': self.total_transactions,
            'income_transactions': self.income_transactions,
            'expense_transactions': self.expense_transactions,
            'active_banks_ratio': self.active_banks_ratio,
            'active_accounts_ratio': self.active_accounts_ratio,
            'income_ratio': self.income_ratio,
            'expense_ratio': self.expense_ratio
        }


@dataclass
class DatabaseStats:
    """Database statistics analysis results."""
    metrics: DatabaseMetrics = field(default_factory=DatabaseMetrics)
    basic_stats: Dict[str, Any] = field(default_factory=dict)
    health_score: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for template compatibility."""
        return {
            'metrics': self.metrics.to_dict(),
            'basic_stats': self.basic_stats,
            'health_score': self.health_score
        }


@dataclass
class ComprehensiveAnalysisData:
    """Legacy compatibility class for comprehensive analysis data."""
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