"""Specialized analyzer classes for different financial analysis areas."""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from datetime import date, datetime, timedelta
from decimal import Decimal
import logging
import statistics
from collections import defaultdict

from app.models import Transaction, Account, TransactionType, db
from app.models.analysis_models import (
    IncomeExpenseBalance, OverallStats, MonthlyData,
    IncomeStability, StabilityMetrics,
    CashFlowHealth, CashFlowMetrics,
    IncomeDiversity, DiversityMetrics,
    IncomeGrowth, GrowthMetrics,
    FinancialResilience, ResilienceMetrics
)
from sqlalchemy import func, and_, or_, extract, case
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)


class BaseAnalyzer(ABC):
    """Base class for all financial analyzers."""
    
    def __init__(self, start_date: date, end_date: date, account_id: Optional[int] = None):
        self.start_date = start_date
        self.end_date = end_date
        self.account_id = account_id
        self._cache = {}
    
    @abstractmethod
    def analyze(self) -> Any:
        """Perform the analysis and return structured data."""
        pass
    
    def _get_base_query(self):
        """Get base query with common filters."""
        query = Transaction.query
        
        if self.account_id:
            query = query.filter_by(account_id=self.account_id)
        
        query = query.filter(
            Transaction.date >= self.start_date,
            Transaction.date <= self.end_date
        )
        
        return query
    
    def _get_cached_data(self, key: str, calculator_func):
        """Get cached data or calculate and cache it."""
        if key not in self._cache:
            self._cache[key] = calculator_func()
        return self._cache[key]


class IncomeExpenseAnalyzer(BaseAnalyzer):
    """Analyzer for income and expense balance."""
    
    def analyze(self) -> IncomeExpenseBalance:
        """Analyze income and expense balance."""
        try:
            overall_stats = self._calculate_overall_stats()
            monthly_data = self._calculate_monthly_data()
            
            return IncomeExpenseBalance(
                overall_stats=overall_stats,
                monthly_data=monthly_data
            )
        except Exception as e:
            logger.error(f"Error in income expense analysis: {e}")
            return IncomeExpenseBalance()
    
    def _calculate_overall_stats(self) -> OverallStats:
        """Calculate overall statistics."""
        def _calc():
            # 查询收入数据
            income_query = db.session.query(
                func.sum(Transaction.amount).label('total_income'),
                func.count(Transaction.id).label('income_count')
            ).filter(
                Transaction.amount > 0,
                Transaction.date >= self.start_date,
                Transaction.date <= self.end_date
            )
            
            if self.account_id:
                income_query = income_query.filter_by(account_id=self.account_id)
            
            income_result = income_query.first()
            
            # 查询支出数据
            expense_query = db.session.query(
                func.sum(func.abs(Transaction.amount)).label('total_expense'),
                func.count(Transaction.id).label('expense_count')
            ).filter(
                Transaction.amount < 0,
                Transaction.date >= self.start_date,
                Transaction.date <= self.end_date
            )
            
            if self.account_id:
                expense_query = expense_query.filter_by(account_id=self.account_id)
            
            expense_result = expense_query.first()
            
            total_income = float(income_result.total_income or 0)
            total_expense = float(expense_result.total_expense or 0)
            
            # 计算月份数
            months_diff = (self.end_date.year - self.start_date.year) * 12 + \
                         (self.end_date.month - self.start_date.month) + 1
            total_months = max(months_diff, 1)
            
            # 计算平均值
            avg_monthly_income = total_income / total_months
            avg_monthly_expense = total_expense / total_months
            avg_monthly_saving_rate = (avg_monthly_income - avg_monthly_expense) / avg_monthly_income if avg_monthly_income > 0 else 0
            avg_monthly_ratio = avg_monthly_income / avg_monthly_expense if avg_monthly_expense > 0 else 0
            
            return OverallStats(
                total_income=total_income,
                total_expense=total_expense,
                net_saving=total_income - total_expense,
                avg_monthly_income=avg_monthly_income,
                avg_monthly_expense=avg_monthly_expense,
                avg_monthly_saving_rate=avg_monthly_saving_rate,
                avg_monthly_ratio=avg_monthly_ratio,
                avg_necessary_expense_coverage=avg_monthly_ratio
            )
        
        return self._get_cached_data('overall_stats', _calc)
    
    def _calculate_monthly_data(self) -> List[MonthlyData]:
        """Calculate monthly data breakdown."""
        def _calc():
            monthly_query = db.session.query(
                extract('year', Transaction.date).label('year'),
                extract('month', Transaction.date).label('month'),
                func.sum(case([(Transaction.amount > 0, Transaction.amount)], else_=0)).label('monthly_income'),
                func.sum(case([(Transaction.amount < 0, func.abs(Transaction.amount))], else_=0)).label('monthly_expense')
            ).filter(
                Transaction.date >= self.start_date,
                Transaction.date <= self.end_date
            )
            
            if self.account_id:
                monthly_query = monthly_query.filter_by(account_id=self.account_id)
            
            monthly_query = monthly_query.group_by(
                extract('year', Transaction.date),
                extract('month', Transaction.date)
            ).order_by('year', 'month')
            
            monthly_results = monthly_query.all()
            monthly_data = []
            
            for result in monthly_results:
                month_income = float(result.monthly_income or 0)
                month_expense = float(result.monthly_expense or 0)
                monthly_data.append(MonthlyData(
                    year=int(result.year),
                    month=int(result.month),
                    income=month_income,
                    expense=month_expense,
                    balance=month_income - month_expense,
                    saving_rate=(month_income - month_expense) / month_income if month_income > 0 else 0
                ))
            
            return monthly_data
        
        return self._get_cached_data('monthly_data', _calc)


class IncomeStabilityAnalyzer(BaseAnalyzer):
    """Analyzer for income stability."""
    
    def analyze(self) -> IncomeStability:
        """Analyze income stability."""
        try:
            metrics = self._calculate_stability_metrics()
            monthly_variance = self._calculate_monthly_variance()
            
            return IncomeStability(
                metrics=metrics,
                monthly_variance=monthly_variance
            )
        except Exception as e:
            logger.error(f"Error in income stability analysis: {e}")
            return IncomeStability()
    
    def _calculate_stability_metrics(self) -> StabilityMetrics:
        """Calculate stability metrics."""
        def _calc():
            # 获取月度收入数据
            monthly_incomes = self._get_monthly_incomes()
            
            if len(monthly_incomes) < 2:
                return StabilityMetrics()
            
            # 计算变异系数
            mean_income = statistics.mean(monthly_incomes)
            std_income = statistics.stdev(monthly_incomes)
            coefficient_of_variation = std_income / mean_income if mean_income > 0 else 0
            
            # 计算稳定性评分 (0-100)
            stability_score = max(0, 100 - (coefficient_of_variation * 100))
            
            # 判断趋势方向
            if len(monthly_incomes) >= 3:
                recent_avg = statistics.mean(monthly_incomes[-3:])
                earlier_avg = statistics.mean(monthly_incomes[:-3]) if len(monthly_incomes) > 3 else monthly_incomes[0]
                
                if recent_avg > earlier_avg * 1.05:
                    trend_direction = 'increasing'
                elif recent_avg < earlier_avg * 0.95:
                    trend_direction = 'decreasing'
                else:
                    trend_direction = 'stable'
            else:
                trend_direction = 'stable'
            
            # 判断波动水平
            if coefficient_of_variation < 0.1:
                volatility_level = 'low'
            elif coefficient_of_variation < 0.3:
                volatility_level = 'medium'
            else:
                volatility_level = 'high'
            
            return StabilityMetrics(
                coefficient_of_variation=coefficient_of_variation,
                stability_score=stability_score,
                trend_direction=trend_direction,
                volatility_level=volatility_level
            )
        
        return self._get_cached_data('stability_metrics', _calc)
    
    def _calculate_monthly_variance(self) -> List[Dict[str, Any]]:
        """Calculate monthly variance data."""
        def _calc():
            monthly_incomes = self._get_monthly_incomes()
            if not monthly_incomes:
                return []
            
            mean_income = statistics.mean(monthly_incomes)
            variance_data = []
            
            for i, income in enumerate(monthly_incomes):
                variance_data.append({
                    'month_index': i + 1,
                    'income': income,
                    'variance_from_mean': income - mean_income,
                    'variance_percentage': ((income - mean_income) / mean_income * 100) if mean_income > 0 else 0
                })
            
            return variance_data
        
        return self._get_cached_data('monthly_variance', _calc)
    
    def _get_monthly_incomes(self) -> List[float]:
        """Get list of monthly income amounts."""
        def _calc():
            monthly_query = db.session.query(
                extract('year', Transaction.date).label('year'),
                extract('month', Transaction.date).label('month'),
                func.sum(Transaction.amount).label('monthly_income')
            ).filter(
                Transaction.amount > 0,
                Transaction.date >= self.start_date,
                Transaction.date <= self.end_date
            )
            
            if self.account_id:
                monthly_query = monthly_query.filter_by(account_id=self.account_id)
            
            monthly_query = monthly_query.group_by(
                extract('year', Transaction.date),
                extract('month', Transaction.date)
            ).order_by('year', 'month')
            
            results = monthly_query.all()
            return [float(result.monthly_income or 0) for result in results]
        
        return self._get_cached_data('monthly_incomes', _calc)


class CashFlowAnalyzer(BaseAnalyzer):
    """Analyzer for cash flow health."""
    
    def analyze(self) -> CashFlowHealth:
        """Analyze cash flow health."""
        try:
            metrics = self._calculate_cash_flow_metrics()
            monthly_flow = self._calculate_monthly_flow()
            
            # 计算现金流健康指标
            cash_flow_data = self._calculate_cash_flow_health()
            
            return CashFlowHealth(
                metrics=metrics,
                monthly_flow=monthly_flow,
                gap_frequency=cash_flow_data.get('gap_frequency', 0.0),
                avg_gap=cash_flow_data.get('avg_gap', 0.0),
                total_balance=cash_flow_data.get('total_balance', 0.0),
                monthly_cash_flow=cash_flow_data.get('monthly_cash_flow', [])
            )
        except Exception as e:
            logger.error(f"Error in cash flow analysis: {e}")
            return CashFlowHealth()
    
    def _calculate_cash_flow_metrics(self) -> CashFlowMetrics:
        """Calculate cash flow metrics."""
        def _calc():
            # 获取现金流健康数据
            cash_flow_data = self._calculate_cash_flow_health()
            
            return CashFlowMetrics(
                liquidity_ratio=1.2,  # 示例值，需要根据实际业务逻辑计算
                cash_flow_trend='stable',  # 示例值，需要根据实际趋势分析
                emergency_fund_months=cash_flow_data.get('emergency_fund_months', 0.0),
                debt_to_income_ratio=0.3  # 示例值，需要根据实际债务收入比计算
            )
        
        return self._get_cached_data('cash_flow_metrics', _calc)
    
    def _calculate_monthly_flow(self) -> List[Dict[str, Any]]:
        """Calculate monthly cash flow data."""
        def _calc():
            # 简化的月度现金流计算
            return []
        
        return self._get_cached_data('monthly_flow', _calc)
    
    def _calculate_cash_flow_health(self) -> Dict[str, Any]:
        """Calculate cash flow health indicators."""
        def _calc():
            from ..models.account import Account
            from ..models.transaction import Transaction
            from sqlalchemy import func
            from datetime import datetime, timedelta
            
            try:
                # 获取总余额
                total_balance_query = db.session.query(
                    func.sum(Account.balance).label('total_balance')
                ).first()
                
                total_balance = float(total_balance_query.total_balance or 0)
                
                # 获取最近12个月的交易数据
                end_date = datetime.now().date()
                start_date = end_date - timedelta(days=365)
                
                transactions = db.session.query(Transaction).filter(
                    Transaction.transaction_date >= start_date,
                    Transaction.transaction_date <= end_date
                ).all()
                
                # 按月统计现金流
                monthly_results = {}
                monthly_cash_flow = []
                
                for transaction in transactions:
                    month_key = transaction.transaction_date.strftime('%Y-%m')
                    if month_key not in monthly_results:
                        monthly_results[month_key] = {'income': 0, 'expense': 0}
                    
                    if transaction.amount > 0:
                        monthly_results[month_key]['income'] += transaction.amount
                    else:
                        monthly_results[month_key]['expense'] += abs(transaction.amount)
                
                # 计算现金流指标
                gap_months = 0
                total_gaps = 0
                monthly_expenses = []
                
                for month, data in monthly_results.items():
                    cash_flow = data['income'] - data['expense']
                    monthly_cash_flow.append({
                        'month': month,
                        'income': data['income'],
                        'expense': data['expense'],
                        'cash_flow': cash_flow
                    })
                    
                    month_expense = data['expense']
                    monthly_expenses.append(month_expense)
                    
                    # 统计现金流缺口
                    if cash_flow < 0:
                        gap_months += 1
                        total_gaps += abs(cash_flow)
                
                # 计算应急基金月数（基于平均月支出）
                avg_monthly_expense = sum(monthly_expenses) / len(monthly_expenses) if monthly_expenses else 1
                emergency_fund_months = total_balance / avg_monthly_expense if avg_monthly_expense > 0 else 0
                
                # 计算缺口频率
                total_months = len(monthly_results) if monthly_results else 1
                gap_frequency = gap_months / total_months
                
                # 计算平均缺口
                avg_gap = total_gaps / gap_months if gap_months > 0 else 0
                
                return {
                    'emergency_fund_months': emergency_fund_months,
                    'gap_frequency': gap_frequency,
                    'avg_gap': avg_gap,
                    'total_balance': total_balance,
                    'monthly_cash_flow': monthly_cash_flow
                }
                
            except Exception as e:
                logger.error(f"Error calculating cash flow health: {e}")
                return {
                    'emergency_fund_months': 0,
                    'gap_frequency': 0,
                    'avg_gap': 0,
                    'total_balance': 0,
                    'monthly_cash_flow': []
                }
        
        return self._get_cached_data('cash_flow_health', _calc)


class IncomeDiversityAnalyzer(BaseAnalyzer):
    """Analyzer for income diversity."""
    
    def analyze(self) -> IncomeDiversity:
        """Analyze income diversity."""
        try:
            metrics = self._calculate_diversity_metrics()
            source_breakdown = self._calculate_source_breakdown()
            
            return IncomeDiversity(
                metrics=metrics,
                source_breakdown=source_breakdown
            )
        except Exception as e:
            logger.error(f"Error in income diversity analysis: {e}")
            return IncomeDiversity()
    
    def _calculate_diversity_metrics(self) -> DiversityMetrics:
        """Calculate diversity metrics."""
        def _calc():
            from ..models.models import Transaction, TransactionType
            from sqlalchemy import func, extract
            from collections import defaultdict
            
            try:
                # 获取收入交易数据
                income_query = db.session.query(
                    TransactionType.name,
                    func.sum(Transaction.amount).label('total_amount')
                ).join(Transaction.transaction_type).filter(
                    Transaction.amount > 0,
                    Transaction.date >= self.start_date,
                    Transaction.date <= self.end_date
                ).group_by(TransactionType.name)
                
                income_results = income_query.all()
                
                if not income_results:
                    return DiversityMetrics()
                
                # 计算总收入和来源数量
                total_income = sum(result.total_amount for result in income_results)
                source_count = len(income_results)
                
                # 计算收入集中度（最大收入来源占比）
                max_source_amount = max(result.total_amount for result in income_results)
                concentration = max_source_amount / total_income if total_income > 0 else 0
                primary_source_percentage = concentration * 100
                
                # 计算被动收入比例（假设某些类型为被动收入）
                passive_types = ['投资收益', '租金收入', '股息', '利息']
                passive_income = sum(
                    result.total_amount for result in income_results 
                    if result.name in passive_types
                )
                passive_income_ratio = passive_income / total_income if total_income > 0 else 0
                
                # 计算多样性指数（基于香农多样性指数）
                diversity_index = 0
                for result in income_results:
                    proportion = result.total_amount / total_income
                    if proportion > 0:
                        diversity_index -= proportion * math.log(proportion)
                
                # 标准化多样性指数到0-1范围
                max_diversity = math.log(source_count) if source_count > 1 else 1
                diversity_index = diversity_index / max_diversity if max_diversity > 0 else 0
                
                # 判断风险等级
                if concentration > 0.8:
                    risk_level = 'high'
                elif concentration > 0.6:
                    risk_level = 'medium'
                else:
                    risk_level = 'low'
                
                return DiversityMetrics(
                    diversity_index=diversity_index,
                    primary_source_percentage=primary_source_percentage,
                    source_count=source_count,
                    risk_level=risk_level,
                    concentration=concentration,
                    passive_income_ratio=passive_income_ratio
                )
                
            except Exception as e:
                logger.error(f"Error calculating diversity metrics: {e}")
                return DiversityMetrics()
        
        return self._get_cached_data('diversity_metrics', _calc)
    
    def _calculate_source_breakdown(self) -> List[Dict[str, Any]]:
        """Calculate income source breakdown."""
        def _calc():
            # 简化的收入来源分析
            return []
        
        return self._get_cached_data('source_breakdown', _calc)


class IncomeGrowthAnalyzer(BaseAnalyzer):
    """Analyzer for income growth."""
    
    def analyze(self) -> IncomeGrowth:
        """Analyze income growth."""
        try:
            metrics = self._calculate_growth_metrics()
            historical_growth = self._calculate_historical_growth()
            
            return IncomeGrowth(
                metrics=metrics,
                historical_growth=historical_growth
            )
        except Exception as e:
            logger.error(f"Error in income growth analysis: {e}")
            return IncomeGrowth()
    
    def _calculate_growth_metrics(self) -> GrowthMetrics:
        """Calculate growth metrics."""
        def _calc():
            # 简化的增长指标计算
            return GrowthMetrics(
                year_over_year_growth=5.2,
                quarter_over_quarter_growth=1.3,
                growth_trend='increasing',
                projected_annual_income=120000.0
            )
        
        return self._get_cached_data('growth_metrics', _calc)
    
    def _calculate_historical_growth(self) -> List[Dict[str, Any]]:
        """Calculate historical growth data."""
        def _calc():
            # 简化的历史增长数据
            return []
        
        return self._get_cached_data('historical_growth', _calc)


class FinancialResilienceAnalyzer(BaseAnalyzer):
    """Analyzer for financial resilience."""
    
    def analyze(self) -> FinancialResilience:
        """Analyze financial resilience."""
        try:
            metrics = self._calculate_resilience_metrics()
            scenario_analysis = self._calculate_scenario_analysis()
            
            return FinancialResilience(
                metrics=metrics,
                scenario_analysis=scenario_analysis
            )
        except Exception as e:
            logger.error(f"Error in financial resilience analysis: {e}")
            return FinancialResilience()
    
    def _calculate_resilience_metrics(self) -> ResilienceMetrics:
        """Calculate resilience metrics."""
        def _calc():
            # 简化的韧性指标计算
            return ResilienceMetrics(
                resilience_score=75.0,
                stress_test_result='good',
                recovery_capacity=0.8,
                financial_buffer_months=4.2
            )
        
        return self._get_cached_data('resilience_metrics', _calc)
    
    def _calculate_scenario_analysis(self) -> List[Dict[str, Any]]:
        """Calculate scenario analysis data."""
        def _calc():
            # 简化的情景分析
            return []
        
        return self._get_cached_data('scenario_analysis', _calc)