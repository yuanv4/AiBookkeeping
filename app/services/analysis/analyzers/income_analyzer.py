"""Income and Expense Analysis Module.

包含收入和支出平衡分析器以及收入稳定性分析器。
优化版本：使用新的基类和缓存策略。"""

from typing import Dict, List, Any
import logging
import statistics
from sqlalchemy import func, case

from app.models import Transaction, db
from app.models.analysis_models import (
    IncomeExpenseAnalysis, OverallStats, MonthlyData,
    IncomeStability, StabilityMetrics
)
from app.utils.query_builder import OptimizedQueryBuilder, AnalysisException
from app.utils.cache_manager import optimized_cache
from .base_analyzer import BaseAnalyzer, performance_monitor

logger = logging.getLogger(__name__)


class IncomeExpenseAnalyzer(BaseAnalyzer):
    """优化的收入支出平衡分析器。"""
    
    @performance_monitor("income_expense_analysis")
    def analyze(self) -> IncomeExpenseAnalysis:
        """分析收入支出平衡。"""
        try:
            # 使用基类的通用方法获取数据
            total_income, total_expense, income_count, expense_count = self._get_income_expense_totals()
            monthly_data = self._get_monthly_breakdown()
            
            # 构建总体统计
            net_saving = total_income - total_expense
            months_count = len(monthly_data) if monthly_data else 1
            avg_monthly_income = total_income / months_count if months_count > 0 else 0
            avg_monthly_expense = total_expense / months_count if months_count > 0 else 0
            avg_monthly_saving_rate = (net_saving / total_income * 100) if total_income > 0 else 0
            avg_monthly_ratio = (total_expense / total_income * 100) if total_income > 0 else 0
            
            overall_stats = OverallStats(
                total_income=total_income,
                total_expense=total_expense,
                net_saving=net_saving,
                avg_monthly_income=avg_monthly_income,
                avg_monthly_expense=avg_monthly_expense,
                avg_monthly_saving_rate=avg_monthly_saving_rate,
                avg_monthly_ratio=avg_monthly_ratio,
                avg_necessary_expense_coverage=0.0  # 暂时设为0，后续可以根据需要计算
            )
            
            # 转换月度数据格式
            monthly_stats = []
            for month_data in monthly_data:
                balance = month_data['income'] - month_data['expense']
                saving_rate = (balance / month_data['income'] * 100) if month_data['income'] > 0 else 0
                monthly_stats.append(MonthlyData(
                    year=month_data['year'],
                    month=month_data['month'],
                    income=month_data['income'],
                    expense=month_data['expense'],
                    balance=balance,
                    saving_rate=saving_rate
                ))
            
            return IncomeExpenseAnalysis(
                overall_stats=overall_stats,
                monthly_data=monthly_stats
            )
        except Exception as e:
            logger.error(f"收入支出分析失败: {e}")
            return IncomeExpenseAnalysis()
    
    # 移除了_calculate_overall_stats方法，现在使用基类的_get_income_expense_totals方法
    
    # 移除了_calculate_monthly_data方法，现在使用基类的_get_monthly_breakdown方法


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
    
    @optimized_cache(cache_name='monthly_incomes', expire_minutes=20)
    def _get_monthly_incomes(self) -> List[float]:
        """Get list of monthly income amounts."""
        try:
            query_builder = OptimizedQueryBuilder()
            query = query_builder.build_aggregated_analysis_query(
                start_date=self.start_date,
                end_date=self.end_date,
                account_id=self.account_id,
                group_by='month'
            )
            
            results = query_builder.execute_with_error_handling(query, 'monthly_income_analysis')
            
            # 提取月度收入金额
            monthly_incomes = []
            for result in results:
                if hasattr(result, 'total_income') and result.total_income:
                    monthly_incomes.append(float(result.total_income or 0))
                elif hasattr(result, 'amount') and result.amount:
                    monthly_incomes.append(float(result.amount or 0))
            
            return monthly_incomes
            
        except AnalysisException:
            raise
        except Exception as e:
            logger.error(f"Error getting monthly incomes: {e}")
            raise AnalysisException(f"Failed to get monthly incomes: {str(e)}")