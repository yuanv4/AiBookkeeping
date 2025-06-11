# -*- coding: utf-8 -*-
"""
收入增长分析器。
优化版本：使用新的基类和缓存策略，减少代码重复。
"""

from datetime import date, datetime
from typing import Dict, List, Optional, Any, Union
from decimal import Decimal

from app.models import Bank, Account, Transaction, db
from app.services.analysis.analysis_models import IncomeGrowth, GrowthMetrics
from .base_analyzer import BaseAnalyzer


class GrowthAnalyzer(BaseAnalyzer):
    """收入增长分析器。
    
    专注于收入增长趋势和模式分析。
    """
    
    def analyze(self) -> IncomeGrowth:
        """分析收入增长情况。"""
        try:
            # 获取月度收入数据
            monthly_data = self._get_monthly_breakdown()
            
            # 计算增长指标
            growth_metrics = self._calculate_comprehensive_growth_metrics(monthly_data)
            
            # 构建历史增长数据
            historical_data = self._build_historical_growth_data(monthly_data)
            
            return IncomeGrowth(
                metrics=growth_metrics,
                historical_growth=[
                    *historical_data.get('monthly_growth', []),
                    *historical_data.get('quarterly_growth', []),
                    *historical_data.get('yearly_growth', [])
                ]
            )
        except Exception as e:
            self.logger.error(f"收入增长分析失败: {e}")
            return IncomeGrowth()
    
    def _calculate_comprehensive_growth_metrics(self, monthly_data: List[Dict[str, Any]]) -> GrowthMetrics:
        """计算综合增长指标。"""
        try:
            if not monthly_data or len(monthly_data) < 2:
                return GrowthMetrics()
            
            # 提取收入数据
            monthly_incomes = [month['income'] for month in monthly_data]
            
            # 计算月度增长率
            monthly_growth_rates = self._calculate_growth_rates(monthly_incomes)
            
            # 计算平均增长率
            avg_growth_rate = sum(monthly_growth_rates) / len(monthly_growth_rates) if monthly_growth_rates else 0.0
            
            # 计算季度和年度增长
            quarterly_growth = self._calculate_quarterly_growth(monthly_data)
            yearly_growth = self._calculate_yearly_growth(monthly_data)
            
            # 确定增长趋势
            growth_trend = self._determine_growth_trend(monthly_growth_rates)
            
            # 计算增长稳定性
            growth_volatility = self._calculate_coefficient_of_variation(monthly_growth_rates)
            
            # 计算复合增长率（CAGR）
            cagr = self._calculate_cagr(monthly_incomes)
            
            return GrowthMetrics(
                average_growth_rate=avg_growth_rate,
                quarterly_growth_rate=quarterly_growth,
                yearly_growth_rate=yearly_growth,
                growth_trend=growth_trend,
                growth_volatility=growth_volatility,
                compound_annual_growth_rate=cagr,
                positive_growth_months=sum(1 for rate in monthly_growth_rates if rate > 0),
                negative_growth_months=sum(1 for rate in monthly_growth_rates if rate < 0)
            )
            
        except Exception as e:
            self.logger.error(f"计算综合增长指标失败: {e}")
            return GrowthMetrics()
    
    def _calculate_quarterly_growth(self, monthly_data: List[Dict[str, Any]]) -> float:
        """计算季度增长率。"""
        try:
            if len(monthly_data) < 6:  # 至少需要两个季度的数据
                return 0.0
            
            # 按季度分组
            quarterly_incomes = self._group_by_quarter(monthly_data)
            
            # 计算季度增长率
            growth_rates = self._calculate_growth_rates(quarterly_incomes)
            
            return sum(growth_rates) / len(growth_rates) if growth_rates else 0.0
            
        except Exception as e:
            self.logger.error(f"计算季度增长率失败: {e}")
            return 0.0
    
    def _calculate_yearly_growth(self, monthly_data: List[Dict[str, Any]]) -> float:
        """计算年度增长率。"""
        try:
            if len(monthly_data) < 24:  # 至少需要两年的数据
                return 0.0
            
            # 按年分组
            yearly_incomes = self._group_by_year(monthly_data)
            
            # 计算年度增长率
            growth_rates = self._calculate_growth_rates(yearly_incomes)
            
            return sum(growth_rates) / len(growth_rates) if growth_rates else 0.0
            
        except Exception as e:
            self.logger.error(f"计算年度增长率失败: {e}")
            return 0.0
    
    def _determine_growth_trend(self, growth_rates: List[float]) -> str:
        """确定增长趋势。"""
        try:
            if not growth_rates:
                return "稳定"
            
            # 使用基类的趋势计算方法
            trend_slope = self._calculate_trend(growth_rates)
            
            if trend_slope > 0.01:  # 1%以上的正趋势
                return "上升"
            elif trend_slope < -0.01:  # 1%以上的负趋势
                return "下降"
            else:
                return "稳定"
                
        except Exception as e:
            self.logger.error(f"确定增长趋势失败: {e}")
            return "稳定"
    
    def _build_historical_growth_data(self, monthly_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """构建历史增长数据。"""
        try:
            if not monthly_data:
                return {}
            
            # 构建月度增长数据
            monthly_growth = self._build_monthly_growth_data(monthly_data)
            
            # 构建季度增长数据
            quarterly_growth = self._build_quarterly_growth_data(monthly_data)
            
            # 构建年度增长数据
            yearly_growth = self._build_yearly_growth_data(monthly_data)
            
            return {
                'monthly_growth': monthly_growth,
                'quarterly_growth': quarterly_growth,
                'yearly_growth': yearly_growth
            }
            
        except Exception as e:
            self.logger.error(f"构建历史增长数据失败: {e}")
            return {}
    
    def _calculate_growth_rates(self, values: List[float]) -> List[float]:
        """计算增长率序列。"""
        growth_rates = []
        for i in range(1, len(values)):
            if values[i-1] > 0:
                growth_rate = (values[i] - values[i-1]) / values[i-1]
                growth_rates.append(growth_rate)
        return growth_rates
    
    def _calculate_cagr(self, values: List[float]) -> float:
        """计算复合年增长率（CAGR）。"""
        if len(values) >= 12 and values[0] > 0:
            periods = len(values) - 1
            cagr = ((values[-1] / values[0]) ** (12 / periods)) - 1
            return cagr
        return 0.0
    
    def _group_by_quarter(self, monthly_data: List[Dict[str, Any]]) -> List[float]:
        """按季度分组数据。"""
        quarterly_data = {}
        for month in monthly_data:
            year = month.get('year', 0)
            month_num = month.get('month', 0)
            quarter = f"{year}-Q{(month_num - 1) // 3 + 1}"
            
            if quarter not in quarterly_data:
                quarterly_data[quarter] = 0.0
            quarterly_data[quarter] += month['income']
        
        quarters = sorted(quarterly_data.keys())
        return [quarterly_data[q] for q in quarters]
    
    def _group_by_year(self, monthly_data: List[Dict[str, Any]]) -> List[float]:
        """按年分组数据。"""
        yearly_data = {}
        for month in monthly_data:
            year = month.get('year', 0)
            if year not in yearly_data:
                yearly_data[year] = 0.0
            yearly_data[year] += month['income']
        
        years = sorted(yearly_data.keys())
        return [yearly_data[y] for y in years]
    
    def _build_monthly_growth_data(self, monthly_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """构建月度增长数据。"""
        monthly_growth = []
        monthly_incomes = [month['income'] for month in monthly_data]
        
        for i in range(1, len(monthly_incomes)):
            if monthly_incomes[i-1] > 0:
                growth_rate = (monthly_incomes[i] - monthly_incomes[i-1]) / monthly_incomes[i-1]
                monthly_growth.append({
                    'period': f"{monthly_data[i].get('year', '')}-{monthly_data[i].get('month', ''):02d}",
                    'growth_rate': growth_rate,
                    'income': monthly_incomes[i],
                    'previous_income': monthly_incomes[i-1]
                })
        
        return monthly_growth
    
    def _build_quarterly_growth_data(self, monthly_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """构建季度增长数据。"""
        quarterly_incomes = self._group_by_quarter(monthly_data)
        quarterly_growth = []
        
        for i in range(1, len(quarterly_incomes)):
            if quarterly_incomes[i-1] > 0:
                growth_rate = (quarterly_incomes[i] - quarterly_incomes[i-1]) / quarterly_incomes[i-1]
                quarterly_growth.append({
                    'period': f"Q{i+1}",
                    'growth_rate': growth_rate,
                    'income': quarterly_incomes[i],
                    'previous_income': quarterly_incomes[i-1]
                })
        
        return quarterly_growth
    
    def _build_yearly_growth_data(self, monthly_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """构建年度增长数据。"""
        yearly_incomes = self._group_by_year(monthly_data)
        yearly_growth = []
        
        for i in range(1, len(yearly_incomes)):
            if yearly_incomes[i-1] > 0:
                growth_rate = (yearly_incomes[i] - yearly_incomes[i-1]) / yearly_incomes[i-1]
                yearly_growth.append({
                    'period': f"Year {i+1}",
                    'growth_rate': growth_rate,
                    'income': yearly_incomes[i],
                    'previous_income': yearly_incomes[i-1]
                })
        
        return yearly_growth