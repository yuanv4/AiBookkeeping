"""现金流分析器

专门负责现金流相关的财务分析功能。
从综合分析器中提取出来，遵循单一职责原则。

Created: 2024-12-19
Author: AI Assistant
"""

from datetime import date, datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from decimal import Decimal

from .base_analyzer import BaseAnalyzer
from .analyzer_context import AnalyzerContext


class CashFlowAnalyzer(BaseAnalyzer):
    """现金流分析器
    
    专门负责现金流相关的分析，包括：
    - 现金流量计算
    - 现金流趋势分析
    - 现金流预测
    - 流动性分析
    """
    
    def __init__(
        self,
        start_date: date,
        end_date: date,
        context: AnalyzerContext,
        account_id: Optional[int] = None
    ):
        """初始化现金流分析器
        
        Args:
            start_date: 分析开始日期
            end_date: 分析结束日期
            context: 分析器上下文
            account_id: 可选的账户ID
        """
        super().__init__(start_date, end_date, context, account_id)
    
    def _perform_analysis(self) -> Dict[str, Any]:
        """执行现金流分析的具体逻辑
        
        Returns:
            包含现金流分析结果的字典
        """
        return {
            'cash_flow_summary': self.get_cash_flow_summary(),
            'monthly_cash_flow': self.get_monthly_cash_flow(),
            'cash_flow_trends': self.analyze_cash_flow_trends(),
            'liquidity_analysis': self.analyze_liquidity(),
            'cash_flow_forecast': self.forecast_cash_flow(),
            'recommendations': self.generate_recommendations(),
            'summary': self.get_summary()
        }
    
    def get_cash_flow_summary(self) -> Dict[str, float]:
        """获取现金流汇总
        
        Returns:
            现金流汇总数据
        """
        try:
            # 检查缓存
            cached_result = self.get_cached_result('get_cash_flow_summary')
            if cached_result:
                return cached_result
            
            # 获取收入和支出总额
            totals = self.data_service.get_income_expense_totals(
                start_date=self.start_date,
                end_date=self.end_date,
                account_id=self.account_id
            )
            
            total_income = totals.get('total_income', 0.0)
            total_expense = totals.get('total_expense', 0.0)
            net_cash_flow = total_income - total_expense
            
            # 计算现金流比率
            cash_flow_ratio = (total_income / total_expense) if total_expense > 0 else float('inf')
            
            # 计算分析期间天数
            analysis_days = self.get_analysis_period_days()
            
            # 计算日均现金流
            daily_avg_income = total_income / analysis_days if analysis_days > 0 else 0
            daily_avg_expense = total_expense / analysis_days if analysis_days > 0 else 0
            daily_avg_net_flow = net_cash_flow / analysis_days if analysis_days > 0 else 0
            
            result = {
                'total_income': total_income,
                'total_expense': total_expense,
                'net_cash_flow': net_cash_flow,
                'cash_flow_ratio': cash_flow_ratio,
                'daily_avg_income': daily_avg_income,
                'daily_avg_expense': daily_avg_expense,
                'daily_avg_net_flow': daily_avg_net_flow,
                'analysis_period_days': analysis_days
            }
            
            # 缓存结果
            self.set_cached_result('get_cash_flow_summary', result, ttl_minutes=60)
            
            return result
            
        except Exception as e:
            self.logger.error(f"获取现金流汇总失败: {e}")
            return {
                'total_income': 0.0,
                'total_expense': 0.0,
                'net_cash_flow': 0.0,
                'cash_flow_ratio': 0.0,
                'daily_avg_income': 0.0,
                'daily_avg_expense': 0.0,
                'daily_avg_net_flow': 0.0,
                'analysis_period_days': 0
            }
    
    def get_monthly_cash_flow(self) -> List[Dict[str, Any]]:
        """获取月度现金流数据
        
        Returns:
            月度现金流数据列表
        """
        try:
            # 检查缓存
            cached_result = self.get_cached_result('get_monthly_cash_flow')
            if cached_result:
                return cached_result
            
            # 获取月度数据
            monthly_data = self.data_service.get_monthly_breakdown(
                start_date=self.start_date,
                end_date=self.end_date,
                account_id=self.account_id
            )
            
            result = []
            cumulative_cash_flow = 0.0
            
            for month_data in monthly_data:
                income = month_data.get('income', 0.0)
                expense = month_data.get('expense', 0.0)
                net_flow = income - expense
                cumulative_cash_flow += net_flow
                
                # 计算现金流比率
                flow_ratio = (income / expense) if expense > 0 else float('inf')
                
                month_result = {
                    'year': month_data.get('year'),
                    'month': month_data.get('month'),
                    'income': income,
                    'expense': expense,
                    'net_cash_flow': net_flow,
                    'cumulative_cash_flow': cumulative_cash_flow,
                    'cash_flow_ratio': flow_ratio,
                    'transaction_count': month_data.get('transaction_count', 0)
                }
                
                result.append(month_result)
            
            # 缓存结果
            self.set_cached_result('get_monthly_cash_flow', result, ttl_minutes=60)
            
            return result
            
        except Exception as e:
            self.logger.error(f"获取月度现金流失败: {e}")
            return []
    
    def analyze_cash_flow_trends(self) -> Dict[str, Any]:
        """分析现金流趋势
        
        Returns:
            现金流趋势分析结果
        """
        try:
            # 检查缓存
            cached_result = self.get_cached_result('analyze_cash_flow_trends')
            if cached_result:
                return cached_result
            
            monthly_data = self.get_monthly_cash_flow()
            
            if len(monthly_data) < 2:
                return {
                    'trend_direction': 'insufficient_data',
                    'trend_strength': 0.0,
                    'income_trend': 'stable',
                    'expense_trend': 'stable',
                    'net_flow_trend': 'stable',
                    'volatility': 'low'
                }
            
            # 提取数据序列
            income_values = [month['income'] for month in monthly_data]
            expense_values = [month['expense'] for month in monthly_data]
            net_flow_values = [month['net_cash_flow'] for month in monthly_data]
            
            # 计算趋势
            income_trend = self.calculation_service.calculate_trend(income_values)
            expense_trend = self.calculation_service.calculate_trend(expense_values)
            net_flow_trend = self.calculation_service.calculate_trend(net_flow_values)
            
            # 计算波动性
            net_flow_cv = self.calculation_service.calculate_coefficient_of_variation(net_flow_values)
            
            if net_flow_cv < 20:
                volatility = 'low'
            elif net_flow_cv < 50:
                volatility = 'moderate'
            elif net_flow_cv < 100:
                volatility = 'high'
            else:
                volatility = 'very_high'
            
            # 计算趋势强度（基于最近3个月与前面月份的比较）
            trend_strength = 0.0
            if len(monthly_data) >= 6:
                recent_avg = sum(net_flow_values[-3:]) / 3
                earlier_avg = sum(net_flow_values[:-3]) / (len(net_flow_values) - 3)
                if earlier_avg != 0:
                    trend_strength = abs((recent_avg - earlier_avg) / earlier_avg) * 100
            
            # 确定总体趋势方向
            if net_flow_trend == 'increasing':
                trend_direction = 'improving'
            elif net_flow_trend == 'decreasing':
                trend_direction = 'deteriorating'
            else:
                trend_direction = 'stable'
            
            result = {
                'trend_direction': trend_direction,
                'trend_strength': trend_strength,
                'income_trend': income_trend,
                'expense_trend': expense_trend,
                'net_flow_trend': net_flow_trend,
                'volatility': volatility,
                'data_points': len(monthly_data)
            }
            
            # 缓存结果
            self.set_cached_result('analyze_cash_flow_trends', result, ttl_minutes=60)
            
            return result
            
        except Exception as e:
            self.logger.error(f"分析现金流趋势失败: {e}")
            return {
                'trend_direction': 'unknown',
                'trend_strength': 0.0,
                'income_trend': 'unknown',
                'expense_trend': 'unknown',
                'net_flow_trend': 'unknown',
                'volatility': 'unknown'
            }
    
    def analyze_liquidity(self) -> Dict[str, Any]:
        """分析流动性
        
        Returns:
            流动性分析结果
        """
        try:
            # 检查缓存
            cached_result = self.get_cached_result('analyze_liquidity')
            if cached_result:
                return cached_result
            
            monthly_data = self.get_monthly_cash_flow()
            
            if not monthly_data:
                return {
                    'liquidity_status': 'unknown',
                    'months_with_negative_flow': 0,
                    'consecutive_negative_months': 0,
                    'worst_month': {},
                    'best_month': {},
                    'cash_burn_rate': 0.0
                }
            
            # 统计负现金流月份
            negative_flow_months = [month for month in monthly_data if month['net_cash_flow'] < 0]
            months_with_negative_flow = len(negative_flow_months)
            
            # 计算连续负现金流月份
            consecutive_negative = 0
            max_consecutive_negative = 0
            
            for month in monthly_data:
                if month['net_cash_flow'] < 0:
                    consecutive_negative += 1
                    max_consecutive_negative = max(max_consecutive_negative, consecutive_negative)
                else:
                    consecutive_negative = 0
            
            # 找出最差和最好的月份
            worst_month = min(monthly_data, key=lambda x: x['net_cash_flow'])
            best_month = max(monthly_data, key=lambda x: x['net_cash_flow'])
            
            # 计算现金消耗率（负现金流月份的平均支出）
            cash_burn_rate = 0.0
            if negative_flow_months:
                total_negative_expense = sum(month['expense'] for month in negative_flow_months)
                cash_burn_rate = total_negative_expense / len(negative_flow_months)
            
            # 评估流动性状态
            negative_ratio = months_with_negative_flow / len(monthly_data)
            
            if negative_ratio == 0:
                liquidity_status = 'excellent'
            elif negative_ratio < 0.2:
                liquidity_status = 'good'
            elif negative_ratio < 0.4:
                liquidity_status = 'fair'
            elif negative_ratio < 0.6:
                liquidity_status = 'poor'
            else:
                liquidity_status = 'critical'
            
            result = {
                'liquidity_status': liquidity_status,
                'months_with_negative_flow': months_with_negative_flow,
                'consecutive_negative_months': max_consecutive_negative,
                'negative_flow_ratio': negative_ratio,
                'worst_month': {
                    'year': worst_month['year'],
                    'month': worst_month['month'],
                    'net_cash_flow': worst_month['net_cash_flow']
                },
                'best_month': {
                    'year': best_month['year'],
                    'month': best_month['month'],
                    'net_cash_flow': best_month['net_cash_flow']
                },
                'cash_burn_rate': cash_burn_rate,
                'total_months_analyzed': len(monthly_data)
            }
            
            # 缓存结果
            self.set_cached_result('analyze_liquidity', result, ttl_minutes=60)
            
            return result
            
        except Exception as e:
            self.logger.error(f"分析流动性失败: {e}")
            return {
                'liquidity_status': 'unknown',
                'months_with_negative_flow': 0,
                'consecutive_negative_months': 0,
                'worst_month': {},
                'best_month': {},
                'cash_burn_rate': 0.0
            }
    
    def forecast_cash_flow(self, forecast_months: int = 3) -> Dict[str, Any]:
        """预测现金流
        
        Args:
            forecast_months: 预测月数
            
        Returns:
            现金流预测结果
        """
        try:
            # 检查缓存
            cache_key = f'forecast_cash_flow_{forecast_months}'
            cached_result = self.get_cached_result(cache_key)
            if cached_result:
                return cached_result
            
            monthly_data = self.get_monthly_cash_flow()
            
            if len(monthly_data) < 3:
                return {
                    'forecast_available': False,
                    'reason': 'insufficient_historical_data',
                    'forecasts': [],
                    'confidence_level': 'low'
                }
            
            # 提取最近的数据用于预测
            recent_data = monthly_data[-6:] if len(monthly_data) >= 6 else monthly_data
            
            income_values = [month['income'] for month in recent_data]
            expense_values = [month['expense'] for month in recent_data]
            
            # 计算平均值和趋势
            avg_income = sum(income_values) / len(income_values)
            avg_expense = sum(expense_values) / len(expense_values)
            
            income_trend = self.calculation_service.calculate_trend(income_values)
            expense_trend = self.calculation_service.calculate_trend(expense_values)
            
            # 计算趋势调整因子
            income_adjustment = 0.0
            expense_adjustment = 0.0
            
            if income_trend == 'increasing':
                income_adjustment = 0.05  # 5% 增长
            elif income_trend == 'decreasing':
                income_adjustment = -0.05  # 5% 下降
            
            if expense_trend == 'increasing':
                expense_adjustment = 0.05
            elif expense_trend == 'decreasing':
                expense_adjustment = -0.05
            
            # 生成预测
            forecasts = []
            current_date = datetime.now().date()
            
            for i in range(forecast_months):
                # 计算预测月份
                forecast_month = current_date.month + i + 1
                forecast_year = current_date.year
                
                while forecast_month > 12:
                    forecast_month -= 12
                    forecast_year += 1
                
                # 应用趋势调整
                predicted_income = avg_income * (1 + income_adjustment * (i + 1))
                predicted_expense = avg_expense * (1 + expense_adjustment * (i + 1))
                predicted_net_flow = predicted_income - predicted_expense
                
                forecasts.append({
                    'year': forecast_year,
                    'month': forecast_month,
                    'predicted_income': predicted_income,
                    'predicted_expense': predicted_expense,
                    'predicted_net_flow': predicted_net_flow
                })
            
            # 评估预测信心
            income_cv = self.calculation_service.calculate_coefficient_of_variation(income_values)
            expense_cv = self.calculation_service.calculate_coefficient_of_variation(expense_values)
            avg_cv = (income_cv + expense_cv) / 2
            
            if avg_cv < 20:
                confidence_level = 'high'
            elif avg_cv < 40:
                confidence_level = 'moderate'
            else:
                confidence_level = 'low'
            
            result = {
                'forecast_available': True,
                'forecasts': forecasts,
                'confidence_level': confidence_level,
                'based_on_months': len(recent_data),
                'methodology': 'trend_adjusted_average'
            }
            
            # 缓存结果
            self.set_cached_result(cache_key, result, ttl_minutes=30)
            
            return result
            
        except Exception as e:
            self.logger.error(f"预测现金流失败: {e}")
            return {
                'forecast_available': False,
                'reason': 'calculation_error',
                'forecasts': [],
                'confidence_level': 'low'
            }
    
    def generate_recommendations(self) -> List[str]:
        """生成现金流改善建议
        
        Returns:
            建议列表
        """
        try:
            recommendations = []
            
            summary = self.get_cash_flow_summary()
            trends = self.analyze_cash_flow_trends()
            liquidity = self.analyze_liquidity()
            
            # 基于净现金流的建议
            net_flow = summary.get('net_cash_flow', 0)
            if net_flow < 0:
                recommendations.append("当前净现金流为负，建议立即审查和削减非必要支出")
                recommendations.append("考虑增加收入来源或提高现有收入")
            
            # 基于现金流比率的建议
            flow_ratio = summary.get('cash_flow_ratio', 0)
            if flow_ratio < 1.2:
                recommendations.append("现金流比率偏低，建议建立应急资金储备")
            
            # 基于趋势的建议
            trend_direction = trends.get('trend_direction')
            if trend_direction == 'deteriorating':
                recommendations.append("现金流呈恶化趋势，建议制定现金流改善计划")
                recommendations.append("考虑延长应收账款回收期或缩短应付账款支付期")
            
            # 基于流动性的建议
            liquidity_status = liquidity.get('liquidity_status')
            if liquidity_status in ['poor', 'critical']:
                recommendations.append("流动性状况不佳，建议优先改善现金流管理")
                recommendations.append("考虑申请信用额度以应对现金流短缺")
            
            consecutive_negative = liquidity.get('consecutive_negative_months', 0)
            if consecutive_negative >= 3:
                recommendations.append("连续多月现金流为负，建议寻求专业财务咨询")
            
            # 基于波动性的建议
            volatility = trends.get('volatility')
            if volatility in ['high', 'very_high']:
                recommendations.append("现金流波动较大，建议制定现金流平滑策略")
                recommendations.append("考虑建立现金流缓冲基金")
            
            return recommendations
            
        except Exception as e:
            self.logger.error(f"生成建议失败: {e}")
            return ["无法生成现金流改善建议"]
    
    def get_summary(self) -> str:
        """获取现金流分析摘要
        
        Returns:
            分析摘要文本
        """
        try:
            summary = self.get_cash_flow_summary()
            trends = self.analyze_cash_flow_trends()
            liquidity = self.analyze_liquidity()
            
            net_flow = summary.get('net_cash_flow', 0)
            flow_ratio = summary.get('cash_flow_ratio', 0)
            trend_direction = trends.get('trend_direction', 'unknown')
            liquidity_status = liquidity.get('liquidity_status', 'unknown')
            
            # 状态描述
            trend_descriptions = {
                'improving': '改善',
                'deteriorating': '恶化',
                'stable': '稳定',
                'unknown': '未知'
            }
            
            liquidity_descriptions = {
                'excellent': '优秀',
                'good': '良好',
                'fair': '一般',
                'poor': '较差',
                'critical': '危险',
                'unknown': '未知'
            }
            
            flow_status = "正现金流" if net_flow > 0 else "负现金流"
            
            summary_text = (
                f"分析期间净现金流为 {net_flow:,.2f} 元（{flow_status}），"
                f"现金流比率为 {flow_ratio:.2f}。"
                f"现金流趋势呈{trend_descriptions.get(trend_direction, '未知')}态势，"
                f"流动性状况为{liquidity_descriptions.get(liquidity_status, '未知')}。"
            )
            
            return summary_text
            
        except Exception as e:
            self.logger.error(f"生成摘要失败: {e}")
            return "无法生成现金流分析摘要。"