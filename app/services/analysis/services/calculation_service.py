"""计算服务层 - 提供通用的财务计算方法

该模块包含所有通用的财务计算逻辑，从分析器中分离出来，
提高代码复用性和可测试性。

Created: 2024-12-19
Author: AI Assistant
"""

import math
from typing import List, Dict, Any, Optional, Tuple
from decimal import Decimal, ROUND_HALF_UP
from datetime import date, datetime
import numpy as np
from scipy import stats


class CalculationService:
    """财务计算服务
    
    提供各种财务分析中常用的计算方法。
    """
    
    @staticmethod
    def calculate_growth_rate(
        current_value: Decimal, 
        previous_value: Decimal, 
        periods: int = 1
    ) -> Decimal:
        """计算增长率
        
        Args:
            current_value: 当前值
            previous_value: 之前的值
            periods: 期间数（用于年化计算）
            
        Returns:
            增长率（百分比）
        """
        try:
            if previous_value == 0:
                return Decimal('0') if current_value == 0 else Decimal('100')
            
            growth_rate = ((current_value - previous_value) / previous_value) * 100
            
            # 如果需要年化
            if periods > 1:
                growth_rate = (pow(float(current_value / previous_value), 1/periods) - 1) * 100
                growth_rate = Decimal(str(growth_rate))
            
            return growth_rate.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            
        except (ZeroDivisionError, ValueError, TypeError):
            return Decimal('0')
    
    @staticmethod
    def calculate_variance(values: List[Decimal]) -> Decimal:
        """计算方差
        
        Args:
            values: 数值列表
            
        Returns:
            方差
        """
        try:
            if len(values) < 2:
                return Decimal('0')
            
            # 转换为float进行计算
            float_values = [float(v) for v in values]
            variance = np.var(float_values, ddof=1)  # 样本方差
            
            return Decimal(str(variance)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            
        except (ValueError, TypeError):
            return Decimal('0')
    
    @staticmethod
    def calculate_standard_deviation(values: List[Decimal]) -> Decimal:
        """计算标准差
        
        Args:
            values: 数值列表
            
        Returns:
            标准差
        """
        try:
            variance = CalculationService.calculate_variance(values)
            std_dev = Decimal(str(math.sqrt(float(variance))))
            
            return std_dev.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            
        except (ValueError, TypeError):
            return Decimal('0')
    
    @staticmethod
    def calculate_coefficient_of_variation(values: List[Decimal]) -> Decimal:
        """计算变异系数
        
        Args:
            values: 数值列表
            
        Returns:
            变异系数（百分比）
        """
        try:
            if len(values) < 2:
                return Decimal('0')
            
            mean_value = sum(values) / len(values)
            if mean_value == 0:
                return Decimal('0')
            
            std_dev = CalculationService.calculate_standard_deviation(values)
            cv = (std_dev / mean_value) * 100
            
            return cv.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            
        except (ZeroDivisionError, ValueError, TypeError):
            return Decimal('0')
    
    @staticmethod
    def calculate_trend(
        values: List[Decimal], 
        time_periods: Optional[List[int]] = None
    ) -> Dict[str, Decimal]:
        """计算趋势分析
        
        Args:
            values: 数值列表
            time_periods: 时间期间列表，如果为None则使用序号
            
        Returns:
            包含斜率、截距、相关系数等的趋势分析结果
        """
        try:
            if len(values) < 2:
                return {
                    'slope': Decimal('0'),
                    'intercept': Decimal('0'),
                    'correlation': Decimal('0'),
                    'trend_direction': 'stable'
                }
            
            # 如果没有提供时间期间，使用序号
            if time_periods is None:
                time_periods = list(range(len(values)))
            
            # 转换为float进行计算
            x_values = [float(t) for t in time_periods]
            y_values = [float(v) for v in values]
            
            # 线性回归
            slope, intercept, r_value, p_value, std_err = stats.linregress(x_values, y_values)
            
            # 确定趋势方向
            if abs(slope) < 0.01:  # 阈值可以调整
                trend_direction = 'stable'
            elif slope > 0:
                trend_direction = 'increasing'
            else:
                trend_direction = 'decreasing'
            
            return {
                'slope': Decimal(str(slope)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
                'intercept': Decimal(str(intercept)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
                'correlation': Decimal(str(r_value)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
                'p_value': Decimal(str(p_value)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
                'trend_direction': trend_direction
            }
            
        except (ValueError, TypeError):
            return {
                'slope': Decimal('0'),
                'intercept': Decimal('0'),
                'correlation': Decimal('0'),
                'trend_direction': 'stable'
            }
    
    @staticmethod
    def calculate_diversity_index(
        category_amounts: List[Decimal], 
        index_type: str = 'shannon'
    ) -> Decimal:
        """计算多样性指数
        
        Args:
            category_amounts: 各分类的金额列表
            index_type: 指数类型 ('shannon', 'simpson', 'gini')
            
        Returns:
            多样性指数
        """
        try:
            if not category_amounts or len(category_amounts) < 2:
                return Decimal('0')
            
            # 过滤掉零值
            amounts = [amt for amt in category_amounts if amt > 0]
            if len(amounts) < 2:
                return Decimal('0')
            
            total = sum(amounts)
            if total == 0:
                return Decimal('0')
            
            # 计算比例
            proportions = [float(amt / total) for amt in amounts]
            
            if index_type == 'shannon':
                # 香农多样性指数
                diversity = -sum(p * math.log(p) for p in proportions if p > 0)
            elif index_type == 'simpson':
                # 辛普森多样性指数
                diversity = 1 - sum(p * p for p in proportions)
            elif index_type == 'gini':
                # 基尼系数（不平等指数）
                sorted_props = sorted(proportions)
                n = len(sorted_props)
                cumsum = np.cumsum(sorted_props)
                diversity = (n + 1 - 2 * sum((n + 1 - i) * y for i, y in enumerate(cumsum, 1))) / n
            else:
                diversity = 0
            
            return Decimal(str(diversity)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            
        except (ValueError, TypeError, ZeroDivisionError):
            return Decimal('0')
    
    @staticmethod
    def calculate_moving_average(
        values: List[Decimal], 
        window_size: int = 3
    ) -> List[Decimal]:
        """计算移动平均
        
        Args:
            values: 数值列表
            window_size: 窗口大小
            
        Returns:
            移动平均值列表
        """
        try:
            if len(values) < window_size:
                return values.copy()
            
            moving_averages = []
            for i in range(len(values) - window_size + 1):
                window_values = values[i:i + window_size]
                avg = sum(window_values) / len(window_values)
                moving_averages.append(avg.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))
            
            return moving_averages
            
        except (ValueError, TypeError):
            return values.copy()
    
    @staticmethod
    def calculate_percentile(
        values: List[Decimal], 
        percentile: float
    ) -> Decimal:
        """计算百分位数
        
        Args:
            values: 数值列表
            percentile: 百分位数 (0-100)
            
        Returns:
            百分位数值
        """
        try:
            if not values:
                return Decimal('0')
            
            float_values = [float(v) for v in values]
            result = np.percentile(float_values, percentile)
            
            return Decimal(str(result)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            
        except (ValueError, TypeError):
            return Decimal('0')
    
    @staticmethod
    def calculate_z_score(value: Decimal, mean: Decimal, std_dev: Decimal) -> Decimal:
        """计算Z分数
        
        Args:
            value: 要计算的值
            mean: 平均值
            std_dev: 标准差
            
        Returns:
            Z分数
        """
        try:
            if std_dev == 0:
                return Decimal('0')
            
            z_score = (value - mean) / std_dev
            return z_score.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            
        except (ValueError, TypeError, ZeroDivisionError):
            return Decimal('0')
    
    @staticmethod
    def calculate_compound_growth_rate(
        start_value: Decimal, 
        end_value: Decimal, 
        periods: int
    ) -> Decimal:
        """计算复合增长率 (CAGR)
        
        Args:
            start_value: 起始值
            end_value: 结束值
            periods: 期间数
            
        Returns:
            复合增长率（百分比）
        """
        try:
            if start_value <= 0 or periods <= 0:
                return Decimal('0')
            
            if end_value <= 0:
                return Decimal('-100')  # 完全损失
            
            cagr = (pow(float(end_value / start_value), 1/periods) - 1) * 100
            return Decimal(str(cagr)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            
        except (ValueError, TypeError, ZeroDivisionError):
            return Decimal('0')
    
    @staticmethod
    def calculate_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
        """计算比率
        
        Args:
            numerator: 分子
            denominator: 分母
            
        Returns:
            比率
        """
        try:
            if denominator == 0:
                return Decimal('0')
            
            ratio = numerator / denominator
            return ratio.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            
        except (ValueError, TypeError, ZeroDivisionError):
            return Decimal('0')
    
    @staticmethod
    def calculate_percentage(part: Decimal, total: Decimal) -> Decimal:
        """计算百分比
        
        Args:
            part: 部分值
            total: 总值
            
        Returns:
            百分比
        """
        try:
            if total == 0:
                return Decimal('0')
            
            percentage = (part / total) * 100
            return percentage.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            
        except (ValueError, TypeError, ZeroDivisionError):
            return Decimal('0')
    
    @staticmethod
    def normalize_values(values: List[Decimal]) -> List[Decimal]:
        """标准化数值（0-1范围）
        
        Args:
            values: 数值列表
            
        Returns:
            标准化后的数值列表
        """
        try:
            if not values:
                return []
            
            min_val = min(values)
            max_val = max(values)
            
            if max_val == min_val:
                return [Decimal('0.5')] * len(values)  # 所有值相同时返回中间值
            
            normalized = []
            for value in values:
                norm_val = (value - min_val) / (max_val - min_val)
                normalized.append(norm_val.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))
            
            return normalized
            
        except (ValueError, TypeError):
            return values.copy()