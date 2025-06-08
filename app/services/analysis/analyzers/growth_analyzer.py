"""Income Growth Analysis Module.

包含收入增长分析器。
优化版本：使用新的基类和缓存策略，实现真正的增长分析算法。"""

from typing import Dict, List, Any, Optional
import logging
from datetime import datetime, timedelta
from sqlalchemy import func
import statistics

from app.models import Transaction, db
from app.models.analysis_models import IncomeGrowthMetrics
from app.utils.query_builder import OptimizedQueryBuilder, AnalysisException
from app.utils.cache_manager import optimized_cache
from .base_analyzer import BaseAnalyzer, performance_monitor

logger = logging.getLogger(__name__)


class IncomeGrowthAnalyzer(BaseAnalyzer):
    """优化的收入增长分析器。"""
    
    @performance_monitor("income_growth_analysis")
    def analyze(self) -> IncomeGrowthMetrics:
        """分析收入增长。"""
        try:
            # 获取月度收入数据
            monthly_data = self._get_monthly_breakdown()
            
            # 计算增长指标
            growth_metrics = self._calculate_comprehensive_growth_metrics(monthly_data)
            
            # 获取历史增长数据
            historical_data = self._build_historical_growth_data(monthly_data)
            
            return IncomeGrowthMetrics(
                growth_rate=growth_metrics.get('monthly_growth_rate', 0.0),
                trend=growth_metrics.get('growth_trend', 'Stable'),
                volatility=growth_metrics.get('growth_volatility', 0.0),
                consistency_score=growth_metrics.get('consistency_score', 0.0),
                monthly_growth_rates=growth_metrics.get('monthly_growth_rates', []),
                recommendations=growth_metrics.get('recommendations', [])
            )
        except Exception as e:
            logger.error(f"收入增长分析失败: {e}")
            return IncomeGrowthMetrics()
    
    @optimized_cache('comprehensive_growth_metrics', expire_minutes=30, priority=2)
    def _calculate_comprehensive_growth_metrics(self, monthly_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """计算综合增长指标。"""
        try:
            if len(monthly_data) < 2:
                return {
                    'monthly_growth_rate': 0.0,
                    'quarterly_growth_rate': 0.0,
                    'yearly_growth_rate': 0.0,
                    'growth_trend': 'insufficient_data',
                    'growth_volatility': 0.0
                }
            
            # 提取月度收入数据
            monthly_incomes = [month['income'] for month in monthly_data]
            
            # 计算月度增长率
            monthly_growth_rates = []
            for i in range(1, len(monthly_incomes)):
                if monthly_incomes[i-1] > 0:
                    growth_rate = (monthly_incomes[i] - monthly_incomes[i-1]) / monthly_incomes[i-1]
                    monthly_growth_rates.append(growth_rate)
            
            # 计算平均月度增长率
            avg_monthly_growth = statistics.mean(monthly_growth_rates) if monthly_growth_rates else 0.0
            
            # 计算季度增长率（如果数据足够）
            quarterly_growth_rate = 0.0
            if len(monthly_data) >= 6:  # 至少需要两个季度的数据
                quarterly_growth_rate = self._calculate_quarterly_growth(monthly_data)
            
            # 计算年度增长率（如果数据足够）
            yearly_growth_rate = 0.0
            if len(monthly_data) >= 12:  # 至少需要一年的数据
                yearly_growth_rate = self._calculate_yearly_growth(monthly_data)
            
            # 计算增长趋势
            growth_trend = self._determine_growth_trend(monthly_growth_rates)
            
            # 计算增长波动性
            growth_volatility = self._calculate_coefficient_of_variation(monthly_growth_rates)
            
            return {
                'monthly_growth_rate': avg_monthly_growth,
                'quarterly_growth_rate': quarterly_growth_rate,
                'yearly_growth_rate': yearly_growth_rate,
                'growth_trend': growth_trend,
                'growth_volatility': growth_volatility
            }
            
        except Exception as e:
            logger.error(f"综合增长指标计算失败: {e}")
            return {}
    
    def _calculate_quarterly_growth(self, monthly_data: List[Dict[str, Any]]) -> float:
        """计算季度增长率。"""
        try:
            # 按季度分组
            quarterly_totals = []
            current_quarter = []
            
            for i, month in enumerate(monthly_data):
                current_quarter.append(month['income'])
                
                # 每三个月为一个季度
                if (i + 1) % 3 == 0:
                    quarterly_totals.append(sum(current_quarter))
                    current_quarter = []
            
            # 处理剩余月份
            if current_quarter:
                quarterly_totals.append(sum(current_quarter))
            
            # 计算季度间增长率
            if len(quarterly_totals) >= 2:
                quarterly_growth_rates = []
                for i in range(1, len(quarterly_totals)):
                    if quarterly_totals[i-1] > 0:
                        growth_rate = (quarterly_totals[i] - quarterly_totals[i-1]) / quarterly_totals[i-1]
                        quarterly_growth_rates.append(growth_rate)
                
                return statistics.mean(quarterly_growth_rates) if quarterly_growth_rates else 0.0
            
            return 0.0
            
        except Exception as e:
            logger.error(f"季度增长率计算失败: {e}")
            return 0.0
    
    def _calculate_yearly_growth(self, monthly_data: List[Dict[str, Any]]) -> float:
        """计算年度增长率。"""
        try:
            # 按年分组
            yearly_totals = {}
            
            for month in monthly_data:
                year = month['period'][:4]  # 假设period格式为'YYYY-MM'
                if year not in yearly_totals:
                    yearly_totals[year] = 0.0
                yearly_totals[year] += month['income']
            
            # 计算年度间增长率
            years = sorted(yearly_totals.keys())
            if len(years) >= 2:
                yearly_growth_rates = []
                for i in range(1, len(years)):
                    prev_year_total = yearly_totals[years[i-1]]
                    curr_year_total = yearly_totals[years[i]]
                    
                    if prev_year_total > 0:
                        growth_rate = (curr_year_total - prev_year_total) / prev_year_total
                        yearly_growth_rates.append(growth_rate)
                
                return statistics.mean(yearly_growth_rates) if yearly_growth_rates else 0.0
            
            return 0.0
            
        except Exception as e:
            logger.error(f"年度增长率计算失败: {e}")
            return 0.0
    
    def _determine_growth_trend(self, growth_rates: List[float]) -> str:
        """确定增长趋势。"""
        if not growth_rates:
            return 'insufficient_data'
        
        try:
            # 计算趋势
            trend = self._calculate_trend(growth_rates)
            avg_growth = statistics.mean(growth_rates)
            
            # 根据趋势和平均增长率确定趋势类型
            if trend > 0.01:  # 明显上升趋势
                return 'accelerating'
            elif trend < -0.01:  # 明显下降趋势
                return 'decelerating'
            elif avg_growth > 0.05:  # 平均增长率大于5%
                return 'increasing'
            elif avg_growth < -0.05:  # 平均增长率小于-5%
                return 'decreasing'
            else:
                return 'stable'
                
        except Exception as e:
            logger.error(f"增长趋势确定失败: {e}")
            return 'unknown'
    
    @optimized_cache('historical_growth_data', expire_minutes=60, priority=1)
    def _build_historical_growth_data(self, monthly_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """构建历史增长数据。"""
        try:
            historical_data = []
            
            for i, month in enumerate(monthly_data):
                # 计算同比增长率（如果有去年同期数据）
                year_over_year_growth = 0.0
                if i >= 12:  # 至少需要12个月前的数据
                    prev_year_income = monthly_data[i-12]['income']
                    if prev_year_income > 0:
                        year_over_year_growth = (month['income'] - prev_year_income) / prev_year_income
                
                # 计算环比增长率
                month_over_month_growth = 0.0
                if i > 0:
                    prev_month_income = monthly_data[i-1]['income']
                    if prev_month_income > 0:
                        month_over_month_growth = (month['income'] - prev_month_income) / prev_month_income
                
                # 计算累计增长率（相对于第一个月）
                cumulative_growth = 0.0
                if monthly_data[0]['income'] > 0:
                    cumulative_growth = (month['income'] - monthly_data[0]['income']) / monthly_data[0]['income']
                
                historical_data.append({
                    'period': month['period'],
                    'income': month['income'],
                    'month_over_month_growth': month_over_month_growth,
                    'year_over_year_growth': year_over_year_growth,
                    'cumulative_growth': cumulative_growth
                })
            
            return historical_data
            
        except Exception as e:
            logger.error(f"历史增长数据构建失败: {e}")
            return []