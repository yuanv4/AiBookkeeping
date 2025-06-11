"""支出模式分析器

专门负责支出模式相关的财务分析功能。
从综合分析器中提取出来，遵循单一职责原则。

Created: 2024-12-19
Author: AI Assistant
"""

from datetime import date
from typing import Dict, List, Optional, Any
from decimal import Decimal
from collections import defaultdict

from .base_analyzer import BaseAnalyzer
from ..analyzer_context import AnalyzerContext


class ExpensePatternAnalyzer(BaseAnalyzer):
    """支出模式分析器
    
    专门负责支出模式相关的分析，包括：
    - 支出分类分析
    - 支出趋势分析
    - 支出习惯识别
    - 异常支出检测
    """
    
    def __init__(
        self,
        start_date: date,
        end_date: date,
        context: AnalyzerContext,
        account_id: Optional[int] = None
    ):
        """初始化支出模式分析器
        
        Args:
            start_date: 分析开始日期
            end_date: 分析结束日期
            context: 分析器上下文
            account_id: 可选的账户ID
        """
        super().__init__(start_date, end_date, context, account_id)
    
    def _perform_analysis(self) -> Dict[str, Any]:
        """执行支出模式分析的具体逻辑
        
        Returns:
            包含支出模式分析结果的字典
        """
        return {
            'category_analysis': self.analyze_expense_categories(),
            'spending_patterns': self.identify_spending_patterns(),
            'trend_analysis': self.analyze_expense_trends(),
            'anomaly_detection': self.detect_expense_anomalies(),
            'seasonal_analysis': self.analyze_seasonal_patterns(),
            'recommendations': self.generate_recommendations(),
            'summary': self.get_summary()
        }
    
    def analyze_expense_categories(self) -> Dict[str, Any]:
        """分析支出分类
        
        Returns:
            支出分类分析结果
        """
        try:
            # 检查缓存
            cached_result = self.get_cached_result('analyze_expense_categories')
            if cached_result:
                return cached_result
            
            # 获取分类数据
            categories = self.data_service.get_transaction_categories(
                start_date=self.start_date,
                end_date=self.end_date,
                account_id=self.account_id,
                transaction_type='expense'
            )
            
            if not categories:
                return {
                    'total_categories': 0,
                    'category_breakdown': [],
                    'top_categories': [],
                    'diversity_index': 0.0,
                    'concentration_ratio': 0.0
                }
            
            # 计算总支出
            total_expense = sum(cat['amount'] for cat in categories)
            
            # 计算每个分类的占比
            category_breakdown = []
            for cat in categories:
                percentage = (cat['amount'] / total_expense * 100) if total_expense > 0 else 0
                category_breakdown.append({
                    'category': cat['category'],
                    'amount': cat['amount'],
                    'percentage': percentage,
                    'transaction_count': cat.get('transaction_count', 0)
                })
            
            # 按金额排序
            category_breakdown.sort(key=lambda x: x['amount'], reverse=True)
            
            # 获取前5大分类
            top_categories = category_breakdown[:5]
            
            # 计算多样性指数（基于分类数量和分布均匀性）
            diversity_index = self.calculation_service.calculate_diversity_index(
                [cat['amount'] for cat in categories]
            )
            
            # 计算集中度比率（前3大分类占比）
            top3_amount = sum(cat['amount'] for cat in category_breakdown[:3])
            concentration_ratio = (top3_amount / total_expense * 100) if total_expense > 0 else 0
            
            result = {
                'total_categories': len(categories),
                'total_expense': total_expense,
                'category_breakdown': category_breakdown,
                'top_categories': top_categories,
                'diversity_index': diversity_index,
                'concentration_ratio': concentration_ratio
            }
            
            # 缓存结果
            self.set_cached_result('analyze_expense_categories', result, ttl_minutes=60)
            
            return result
            
        except Exception as e:
            self.logger.error(f"分析支出分类失败: {e}")
            return {
                'total_categories': 0,
                'category_breakdown': [],
                'top_categories': [],
                'diversity_index': 0.0,
                'concentration_ratio': 0.0
            }
    
    def identify_spending_patterns(self) -> Dict[str, Any]:
        """识别支出模式
        
        Returns:
            支出模式识别结果
        """
        try:
            # 检查缓存
            cached_result = self.get_cached_result('identify_spending_patterns')
            if cached_result:
                return cached_result
            
            # 获取月度数据
            monthly_data = self.data_service.get_monthly_breakdown(
                start_date=self.start_date,
                end_date=self.end_date,
                account_id=self.account_id
            )
            
            if len(monthly_data) < 2:
                return {
                    'pattern_type': 'insufficient_data',
                    'spending_consistency': 'unknown',
                    'average_monthly_expense': 0.0,
                    'expense_volatility': 'unknown',
                    'peak_spending_months': [],
                    'low_spending_months': []
                }
            
            expense_values = [month['expense'] for month in monthly_data]
            avg_expense = sum(expense_values) / len(expense_values)
            
            # 计算支出一致性
            cv = self.calculation_service.calculate_coefficient_of_variation(expense_values)
            
            if cv < 15:
                spending_consistency = 'very_consistent'
                expense_volatility = 'low'
            elif cv < 30:
                spending_consistency = 'consistent'
                expense_volatility = 'moderate'
            elif cv < 50:
                spending_consistency = 'somewhat_variable'
                expense_volatility = 'high'
            else:
                spending_consistency = 'highly_variable'
                expense_volatility = 'very_high'
            
            # 识别支出模式类型
            trend = self.calculation_service.calculate_trend(expense_values)
            
            if trend == 'increasing':
                pattern_type = 'increasing_spending'
            elif trend == 'decreasing':
                pattern_type = 'decreasing_spending'
            else:
                if cv < 20:
                    pattern_type = 'stable_spending'
                else:
                    pattern_type = 'irregular_spending'
            
            # 识别高支出和低支出月份
            threshold_high = avg_expense * 1.2
            threshold_low = avg_expense * 0.8
            
            peak_spending_months = []
            low_spending_months = []
            
            for month_data, expense in zip(monthly_data, expense_values):
                if expense > threshold_high:
                    peak_spending_months.append({
                        'year': month_data['year'],
                        'month': month_data['month'],
                        'expense': expense,
                        'deviation_percent': ((expense - avg_expense) / avg_expense * 100)
                    })
                elif expense < threshold_low:
                    low_spending_months.append({
                        'year': month_data['year'],
                        'month': month_data['month'],
                        'expense': expense,
                        'deviation_percent': ((expense - avg_expense) / avg_expense * 100)
                    })
            
            result = {
                'pattern_type': pattern_type,
                'spending_consistency': spending_consistency,
                'average_monthly_expense': avg_expense,
                'expense_volatility': expense_volatility,
                'coefficient_of_variation': cv,
                'peak_spending_months': peak_spending_months,
                'low_spending_months': low_spending_months,
                'data_points': len(expense_values)
            }
            
            # 缓存结果
            self.set_cached_result('identify_spending_patterns', result, ttl_minutes=60)
            
            return result
            
        except Exception as e:
            self.logger.error(f"识别支出模式失败: {e}")
            return {
                'pattern_type': 'unknown',
                'spending_consistency': 'unknown',
                'average_monthly_expense': 0.0,
                'expense_volatility': 'unknown',
                'peak_spending_months': [],
                'low_spending_months': []
            }
    
    def analyze_expense_trends(self) -> Dict[str, Any]:
        """分析支出趋势
        
        Returns:
            支出趋势分析结果
        """
        try:
            # 检查缓存
            cached_result = self.get_cached_result('analyze_expense_trends')
            if cached_result:
                return cached_result
            
            # 获取月度数据
            monthly_data = self.data_service.get_monthly_breakdown(
                start_date=self.start_date,
                end_date=self.end_date,
                account_id=self.account_id
            )
            
            if len(monthly_data) < 3:
                return {
                    'overall_trend': 'insufficient_data',
                    'trend_strength': 0.0,
                    'growth_rate': 0.0,
                    'trend_consistency': 'unknown',
                    'recent_trend': 'unknown'
                }
            
            expense_values = [month['expense'] for month in monthly_data]
            
            # 计算整体趋势
            overall_trend = self.calculation_service.calculate_trend(expense_values)
            
            # 计算增长率
            if len(expense_values) >= 2:
                first_expense = expense_values[0] if expense_values[0] > 0 else 1
                last_expense = expense_values[-1]
                growth_rate = ((last_expense - first_expense) / first_expense * 100)
            else:
                growth_rate = 0.0
            
            # 计算趋势强度（基于线性回归的R²）
            # 这里使用简化的方法：计算与平均值的偏差
            avg_expense = sum(expense_values) / len(expense_values)
            variance = sum((x - avg_expense) ** 2 for x in expense_values) / len(expense_values)
            trend_strength = min(100, variance / avg_expense * 10) if avg_expense > 0 else 0
            
            # 分析最近趋势（最近3个月）
            if len(expense_values) >= 3:
                recent_values = expense_values[-3:]
                recent_trend = self.calculation_service.calculate_trend(recent_values)
            else:
                recent_trend = overall_trend
            
            # 评估趋势一致性
            # 将数据分成两半，比较两半的趋势
            mid_point = len(expense_values) // 2
            if mid_point >= 2:
                first_half = expense_values[:mid_point]
                second_half = expense_values[mid_point:]
                
                first_trend = self.calculation_service.calculate_trend(first_half)
                second_trend = self.calculation_service.calculate_trend(second_half)
                
                if first_trend == second_trend:
                    trend_consistency = 'consistent'
                else:
                    trend_consistency = 'inconsistent'
            else:
                trend_consistency = 'unknown'
            
            result = {
                'overall_trend': overall_trend,
                'trend_strength': trend_strength,
                'growth_rate': growth_rate,
                'trend_consistency': trend_consistency,
                'recent_trend': recent_trend,
                'analysis_period_months': len(expense_values)
            }
            
            # 缓存结果
            self.set_cached_result('analyze_expense_trends', result, ttl_minutes=60)
            
            return result
            
        except Exception as e:
            self.logger.error(f"分析支出趋势失败: {e}")
            return {
                'overall_trend': 'unknown',
                'trend_strength': 0.0,
                'growth_rate': 0.0,
                'trend_consistency': 'unknown',
                'recent_trend': 'unknown'
            }
    
    def detect_expense_anomalies(self) -> Dict[str, Any]:
        """检测支出异常
        
        Returns:
            支出异常检测结果
        """
        try:
            # 检查缓存
            cached_result = self.get_cached_result('detect_expense_anomalies')
            if cached_result:
                return cached_result
            
            # 获取月度数据
            monthly_data = self.data_service.get_monthly_breakdown(
                start_date=self.start_date,
                end_date=self.end_date,
                account_id=self.account_id
            )
            
            if len(monthly_data) < 3:
                return {
                    'anomalies_detected': False,
                    'anomaly_count': 0,
                    'anomalous_months': [],
                    'anomaly_threshold': 0.0,
                    'detection_method': 'insufficient_data'
                }
            
            expense_values = [month['expense'] for month in monthly_data]
            
            # 计算统计指标
            avg_expense = sum(expense_values) / len(expense_values)
            variance = sum((x - avg_expense) ** 2 for x in expense_values) / len(expense_values)
            std_dev = variance ** 0.5
            
            # 设置异常阈值（2个标准差）
            anomaly_threshold = 2 * std_dev
            
            # 检测异常
            anomalous_months = []
            for month_data, expense in zip(monthly_data, expense_values):
                deviation = abs(expense - avg_expense)
                if deviation > anomaly_threshold:
                    anomaly_type = 'high' if expense > avg_expense else 'low'
                    anomalous_months.append({
                        'year': month_data['year'],
                        'month': month_data['month'],
                        'expense': expense,
                        'average_expense': avg_expense,
                        'deviation': deviation,
                        'deviation_percent': (deviation / avg_expense * 100) if avg_expense > 0 else 0,
                        'anomaly_type': anomaly_type,
                        'severity': 'high' if deviation > 3 * std_dev else 'moderate'
                    })
            
            anomalies_detected = len(anomalous_months) > 0
            
            result = {
                'anomalies_detected': anomalies_detected,
                'anomaly_count': len(anomalous_months),
                'anomalous_months': anomalous_months,
                'anomaly_threshold': anomaly_threshold,
                'detection_method': 'statistical_outlier',
                'average_expense': avg_expense,
                'standard_deviation': std_dev
            }
            
            # 缓存结果
            self.set_cached_result('detect_expense_anomalies', result, ttl_minutes=60)
            
            return result
            
        except Exception as e:
            self.logger.error(f"检测支出异常失败: {e}")
            return {
                'anomalies_detected': False,
                'anomaly_count': 0,
                'anomalous_months': [],
                'anomaly_threshold': 0.0,
                'detection_method': 'error'
            }
    
    def analyze_seasonal_patterns(self) -> Dict[str, Any]:
        """分析季节性模式
        
        Returns:
            季节性模式分析结果
        """
        try:
            # 检查缓存
            cached_result = self.get_cached_result('analyze_seasonal_patterns')
            if cached_result:
                return cached_result
            
            # 获取月度数据
            monthly_data = self.data_service.get_monthly_breakdown(
                start_date=self.start_date,
                end_date=self.end_date,
                account_id=self.account_id
            )
            
            if len(monthly_data) < 12:
                return {
                    'seasonal_pattern_detected': False,
                    'reason': 'insufficient_data_for_seasonal_analysis',
                    'monthly_averages': {},
                    'peak_months': [],
                    'low_months': []
                }
            
            # 按月份分组计算平均值
            monthly_totals = defaultdict(list)
            for month_data in monthly_data:
                month_num = month_data['month']
                expense = month_data['expense']
                monthly_totals[month_num].append(expense)
            
            # 计算每个月的平均支出
            monthly_averages = {}
            for month_num in range(1, 13):
                if month_num in monthly_totals:
                    monthly_averages[month_num] = sum(monthly_totals[month_num]) / len(monthly_totals[month_num])
                else:
                    monthly_averages[month_num] = 0.0
            
            # 计算整体平均值
            overall_avg = sum(monthly_averages.values()) / 12
            
            # 识别高峰和低谷月份
            peak_months = []
            low_months = []
            
            for month_num, avg_expense in monthly_averages.items():
                deviation_percent = ((avg_expense - overall_avg) / overall_avg * 100) if overall_avg > 0 else 0
                
                if avg_expense > overall_avg * 1.15:  # 高于平均15%
                    peak_months.append({
                        'month': month_num,
                        'average_expense': avg_expense,
                        'deviation_percent': deviation_percent
                    })
                elif avg_expense < overall_avg * 0.85:  # 低于平均15%
                    low_months.append({
                        'month': month_num,
                        'average_expense': avg_expense,
                        'deviation_percent': deviation_percent
                    })
            
            # 检测是否存在季节性模式
            seasonal_pattern_detected = len(peak_months) > 0 or len(low_months) > 0
            
            # 计算季节性强度
            monthly_values = list(monthly_averages.values())
            seasonal_cv = self.calculation_service.calculate_coefficient_of_variation(monthly_values)
            
            result = {
                'seasonal_pattern_detected': seasonal_pattern_detected,
                'monthly_averages': monthly_averages,
                'overall_monthly_average': overall_avg,
                'peak_months': peak_months,
                'low_months': low_months,
                'seasonal_intensity': seasonal_cv,
                'analysis_months': len(monthly_data)
            }
            
            # 缓存结果
            self.set_cached_result('analyze_seasonal_patterns', result, ttl_minutes=60)
            
            return result
            
        except Exception as e:
            self.logger.error(f"分析季节性模式失败: {e}")
            return {
                'seasonal_pattern_detected': False,
                'reason': 'analysis_error',
                'monthly_averages': {},
                'peak_months': [],
                'low_months': []
            }
    
    def generate_recommendations(self) -> List[str]:
        """生成支出优化建议
        
        Returns:
            建议列表
        """
        try:
            recommendations = []
            
            category_analysis = self.analyze_expense_categories()
            patterns = self.identify_spending_patterns()
            trends = self.analyze_expense_trends()
            anomalies = self.detect_expense_anomalies()
            seasonal = self.analyze_seasonal_patterns()
            
            # 基于分类分析的建议
            concentration_ratio = category_analysis.get('concentration_ratio', 0)
            if concentration_ratio > 70:
                recommendations.append("支出过于集中在少数分类，建议审查主要支出分类的必要性")
            
            top_categories = category_analysis.get('top_categories', [])
            if top_categories:
                top_category = top_categories[0]
                if top_category['percentage'] > 40:
                    recommendations.append(f"'{top_category['category']}'分类支出占比过高({top_category['percentage']:.1f}%)，建议重点关注")
            
            # 基于支出模式的建议
            spending_consistency = patterns.get('spending_consistency')
            if spending_consistency == 'highly_variable':
                recommendations.append("支出波动较大，建议制定更详细的预算计划")
                recommendations.append("考虑设置每月支出限额以控制支出")
            
            # 基于趋势的建议
            overall_trend = trends.get('overall_trend')
            growth_rate = trends.get('growth_rate', 0)
            
            if overall_trend == 'increasing' and growth_rate > 20:
                recommendations.append(f"支出呈快速增长趋势(增长率{growth_rate:.1f}%)，建议审查支出增长原因")
                recommendations.append("考虑制定支出控制措施")
            
            # 基于异常检测的建议
            if anomalies.get('anomalies_detected'):
                anomaly_count = anomalies.get('anomaly_count', 0)
                recommendations.append(f"检测到{anomaly_count}个异常支出月份，建议分析异常原因")
                
                high_anomalies = [a for a in anomalies.get('anomalous_months', []) if a.get('anomaly_type') == 'high']
                if high_anomalies:
                    recommendations.append("存在异常高支出月份，建议建立支出预警机制")
            
            # 基于季节性的建议
            if seasonal.get('seasonal_pattern_detected'):
                peak_months = seasonal.get('peak_months', [])
                if peak_months:
                    peak_month_nums = [m['month'] for m in peak_months]
                    recommendations.append(f"第{peak_month_nums}月通常支出较高，建议提前做好资金准备")
                
                low_months = seasonal.get('low_months', [])
                if low_months:
                    low_month_nums = [m['month'] for m in low_months]
                    recommendations.append(f"第{low_month_nums}月支出较低，可考虑在这些月份增加储蓄")
            
            return recommendations
            
        except Exception as e:
            self.logger.error(f"生成建议失败: {e}")
            return ["无法生成支出优化建议"]
    
    def get_summary(self) -> str:
        """获取支出模式分析摘要
        
        Returns:
            分析摘要文本
        """
        try:
            category_analysis = self.analyze_expense_categories()
            patterns = self.identify_spending_patterns()
            trends = self.analyze_expense_trends()
            
            total_categories = category_analysis.get('total_categories', 0)
            avg_monthly_expense = patterns.get('average_monthly_expense', 0)
            spending_consistency = patterns.get('spending_consistency', 'unknown')
            overall_trend = trends.get('overall_trend', 'unknown')
            
            # 一致性描述
            consistency_descriptions = {
                'very_consistent': '非常稳定',
                'consistent': '较为稳定',
                'somewhat_variable': '有一定波动',
                'highly_variable': '波动较大',
                'unknown': '未知'
            }
            
            # 趋势描述
            trend_descriptions = {
                'increasing': '上升',
                'decreasing': '下降',
                'stable': '稳定',
                'unknown': '未知'
            }
            
            summary_text = (
                f"分析期间共有{total_categories}个支出分类，"
                f"月均支出 {avg_monthly_expense:,.2f} 元。"
                f"支出模式{consistency_descriptions.get(spending_consistency, '未知')}，"
                f"整体趋势呈{trend_descriptions.get(overall_trend, '未知')}态势。"
            )
            
            return summary_text
            
        except Exception as e:
            self.logger.error(f"生成摘要失败: {e}")
            return "无法生成支出模式分析摘要。"