"""收入稳定性分析器

专门负责收入稳定性相关的财务分析功能。
从综合分析器中提取出来，遵循单一职责原则。

Created: 2024-12-19
Author: AI Assistant
"""

from datetime import date, datetime
from typing import Dict, List, Optional, Any, Union
from decimal import Decimal

from app.models import Bank, Account, Transaction, db
from app.services.analysis.analysis_models import IncomeStability, StabilityMetrics
from .analyzer_context import AnalyzerContext
from .base_analyzer import BaseAnalyzer


class IncomeStabilityAnalyzer(BaseAnalyzer):
    """收入稳定性分析器
    
    专门负责收入稳定性相关的分析，包括：
    - 收入稳定性指标计算
    - 收入波动性分析
    - 收入可预测性评估
    - 稳定性等级评定
    """
    
    def __init__(
        self,
        start_date: date,
        end_date: date,
        context: AnalyzerContext,
        account_id: Optional[int] = None
    ):
        """初始化收入稳定性分析器
        
        Args:
            start_date: 分析开始日期
            end_date: 分析结束日期
            context: 分析器上下文
            account_id: 可选的账户ID
        """
        super().__init__(start_date, end_date, context, account_id)
    
    def _perform_analysis(self) -> Dict[str, Any]:
        """执行收入稳定性分析的具体逻辑
        
        Returns:
            包含收入稳定性分析结果的字典
        """
        return {
            'stability_metrics': self.calculate_stability_metrics(),
            'volatility_analysis': self.analyze_volatility(),
            'predictability': self.assess_predictability(),
            'stability_level': self.get_stability_level(),
            'recommendations': self.generate_recommendations(),
            'summary': self.get_summary()
        }
    
    def calculate_stability_metrics(self) -> Dict[str, float]:
        """计算收入稳定性指标
        
        Returns:
            稳定性指标字典
        """
        try:
            # 检查缓存
            cached_result = self.get_cached_result('calculate_stability_metrics')
            if cached_result:
                return cached_result
            
            # 获取月度收入数据
            monthly_data = self.data_service.get_monthly_breakdown(
                start_date=self.start_date,
                end_date=self.end_date,
                account_id=self.account_id
            )
            
            if not monthly_data:
                return {
                    'coefficient_of_variation': 0.0,
                    'income_variance': 0.0,
                    'income_std_dev': 0.0,
                    'stability_score': 0.0
                }
            
            # 提取收入数据
            income_values = [month['income'] for month in monthly_data]
            
            # 使用计算服务计算指标
            cv = self.calculation_service.calculate_coefficient_of_variation(income_values)
            variance = self.calculation_service.calculate_variance(income_values)
            std_dev = variance ** 0.5 if variance > 0 else 0.0
            
            # 计算稳定性得分 (0-100, 100为最稳定)
            stability_score = max(0, 100 - cv)
            
            result = {
                'coefficient_of_variation': cv,
                'income_variance': variance,
                'income_std_dev': std_dev,
                'stability_score': stability_score,
                'sample_size': len(income_values)
            }
            
            # 缓存结果
            self.set_cached_result('calculate_stability_metrics', result, ttl_minutes=60)
            
            return result
            
        except Exception as e:
            self.logger.error(f"计算稳定性指标失败: {e}")
            return {
                'coefficient_of_variation': 0.0,
                'income_variance': 0.0,
                'income_std_dev': 0.0,
                'stability_score': 0.0,
                'sample_size': 0
            }
    
    def analyze_volatility(self) -> Dict[str, Any]:
        """分析收入波动性
        
        Returns:
            波动性分析结果
        """
        try:
            # 检查缓存
            cached_result = self.get_cached_result('analyze_volatility')
            if cached_result:
                return cached_result
            
            # 获取月度收入数据
            monthly_data = self.data_service.get_monthly_breakdown(
                start_date=self.start_date,
                end_date=self.end_date,
                account_id=self.account_id
            )
            
            if not monthly_data:
                return {
                    'volatility_level': 'unknown',
                    'max_income': 0.0,
                    'min_income': 0.0,
                    'income_range': 0.0,
                    'outlier_months': []
                }
            
            income_values = [month['income'] for month in monthly_data]
            
            if not income_values:
                return {
                    'volatility_level': 'unknown',
                    'max_income': 0.0,
                    'min_income': 0.0,
                    'income_range': 0.0,
                    'outlier_months': []
                }
            
            max_income = max(income_values)
            min_income = min(income_values)
            income_range = max_income - min_income
            avg_income = sum(income_values) / len(income_values)
            
            # 计算波动性等级
            cv = self.calculation_service.calculate_coefficient_of_variation(income_values)
            
            if cv < 10:
                volatility_level = 'low'
            elif cv < 25:
                volatility_level = 'moderate'
            elif cv < 50:
                volatility_level = 'high'
            else:
                volatility_level = 'very_high'
            
            # 识别异常月份（收入偏离平均值超过1个标准差）
            std_dev = self.calculation_service.calculate_variance(income_values) ** 0.5
            outlier_months = []
            
            for i, (month_data, income) in enumerate(zip(monthly_data, income_values)):
                if abs(income - avg_income) > std_dev:
                    outlier_months.append({
                        'year': month_data['year'],
                        'month': month_data['month'],
                        'income': income,
                        'deviation': abs(income - avg_income)
                    })
            
            result = {
                'volatility_level': volatility_level,
                'max_income': max_income,
                'min_income': min_income,
                'income_range': income_range,
                'avg_income': avg_income,
                'outlier_months': outlier_months,
                'outlier_count': len(outlier_months)
            }
            
            # 缓存结果
            self.set_cached_result('analyze_volatility', result, ttl_minutes=60)
            
            return result
            
        except Exception as e:
            self.logger.error(f"分析波动性失败: {e}")
            return {
                'volatility_level': 'unknown',
                'max_income': 0.0,
                'min_income': 0.0,
                'income_range': 0.0,
                'outlier_months': []
            }
    
    def assess_predictability(self) -> Dict[str, Any]:
        """评估收入可预测性
        
        Returns:
            可预测性评估结果
        """
        try:
            # 检查缓存
            cached_result = self.get_cached_result('assess_predictability')
            if cached_result:
                return cached_result
            
            # 获取月度收入数据
            monthly_data = self.data_service.get_monthly_breakdown(
                start_date=self.start_date,
                end_date=self.end_date,
                account_id=self.account_id
            )
            
            if len(monthly_data) < 3:
                return {
                    'predictability_score': 0.0,
                    'trend_consistency': 'insufficient_data',
                    'seasonal_pattern': False,
                    'prediction_confidence': 'low'
                }
            
            income_values = [month['income'] for month in monthly_data]
            
            # 计算趋势一致性
            trend = self.calculation_service.calculate_trend(income_values)
            
            # 计算可预测性得分（基于变异系数的倒数）
            cv = self.calculation_service.calculate_coefficient_of_variation(income_values)
            predictability_score = max(0, 100 - cv) if cv > 0 else 100
            
            # 评估预测信心
            if predictability_score >= 80:
                prediction_confidence = 'high'
            elif predictability_score >= 60:
                prediction_confidence = 'moderate'
            elif predictability_score >= 40:
                prediction_confidence = 'low'
            else:
                prediction_confidence = 'very_low'
            
            # 简单的季节性模式检测（需要至少12个月的数据）
            seasonal_pattern = False
            if len(monthly_data) >= 12:
                # 这里可以实现更复杂的季节性检测算法
                # 暂时基于简单的方差分析
                seasonal_pattern = cv < 30  # 如果变异系数较小，可能存在季节性模式
            
            result = {
                'predictability_score': predictability_score,
                'trend_consistency': trend,
                'seasonal_pattern': seasonal_pattern,
                'prediction_confidence': prediction_confidence,
                'data_points': len(income_values)
            }
            
            # 缓存结果
            self.set_cached_result('assess_predictability', result, ttl_minutes=60)
            
            return result
            
        except Exception as e:
            self.logger.error(f"评估可预测性失败: {e}")
            return {
                'predictability_score': 0.0,
                'trend_consistency': 'unknown',
                'seasonal_pattern': False,
                'prediction_confidence': 'low'
            }
    
    def get_stability_level(self) -> str:
        """获取稳定性等级
        
        Returns:
            稳定性等级字符串
        """
        try:
            metrics = self.calculate_stability_metrics()
            stability_score = metrics.get('stability_score', 0)
            
            if stability_score >= 80:
                return 'excellent'
            elif stability_score >= 60:
                return 'good'
            elif stability_score >= 40:
                return 'fair'
            elif stability_score >= 20:
                return 'poor'
            else:
                return 'very_poor'
                
        except Exception as e:
            self.logger.error(f"获取稳定性等级失败: {e}")
            return 'unknown'
    
    def generate_recommendations(self) -> List[str]:
        """生成改善建议
        
        Returns:
            建议列表
        """
        try:
            recommendations = []
            
            stability_level = self.get_stability_level()
            volatility = self.analyze_volatility()
            predictability = self.assess_predictability()
            
            # 基于稳定性等级的建议
            if stability_level in ['poor', 'very_poor']:
                recommendations.append("建议寻找更稳定的收入来源或增加收入来源的多样性")
                recommendations.append("考虑建立应急基金以应对收入波动")
            
            # 基于波动性的建议
            if volatility.get('volatility_level') in ['high', 'very_high']:
                recommendations.append("收入波动较大，建议制定更保守的支出计划")
                recommendations.append("考虑平滑收入的方法，如签订长期合同")
            
            # 基于可预测性的建议
            if predictability.get('prediction_confidence') in ['low', 'very_low']:
                recommendations.append("收入可预测性较低，建议加强财务规划和预算管理")
                recommendations.append("考虑增加被动收入来源以提高收入稳定性")
            
            # 基于异常值的建议
            outlier_count = volatility.get('outlier_count', 0)
            if outlier_count > len(volatility.get('outlier_months', [])) * 0.3:
                recommendations.append("存在较多收入异常月份，建议分析原因并制定应对策略")
            
            return recommendations
            
        except Exception as e:
            self.logger.error(f"生成建议失败: {e}")
            return ["无法生成改善建议"]
    
    def get_summary(self) -> str:
        """获取分析摘要
        
        Returns:
            分析摘要文本
        """
        try:
            stability_level = self.get_stability_level()
            metrics = self.calculate_stability_metrics()
            volatility = self.analyze_volatility()
            
            stability_score = metrics.get('stability_score', 0)
            cv = metrics.get('coefficient_of_variation', 0)
            volatility_level = volatility.get('volatility_level', 'unknown')
            
            # 稳定性等级描述
            level_descriptions = {
                'excellent': '优秀',
                'good': '良好',
                'fair': '一般',
                'poor': '较差',
                'very_poor': '很差',
                'unknown': '未知'
            }
            
            # 波动性等级描述
            volatility_descriptions = {
                'low': '低',
                'moderate': '中等',
                'high': '高',
                'very_high': '很高',
                'unknown': '未知'
            }
            
            summary = (
                f"收入稳定性等级为{level_descriptions.get(stability_level, '未知')}，"
                f"稳定性得分 {stability_score:.1f} 分（满分100分）。"
                f"收入变异系数为 {cv:.1f}%，波动性水平为{volatility_descriptions.get(volatility_level, '未知')}。"
            )
            
            return summary
            
        except Exception as e:
            self.logger.error(f"生成摘要失败: {e}")
            return "无法生成分析摘要。"