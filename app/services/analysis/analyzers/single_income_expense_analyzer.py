"""收入支出分析器

专门负责收入支出相关的财务分析功能。
从综合分析器中提取出来，遵循单一职责原则。

Created: 2024-12-19
Author: AI Assistant
"""

from datetime import date
from typing import Dict, List, Optional, Any
from decimal import Decimal

from .base_analyzer import BaseAnalyzer
from .analyzer_context import AnalyzerContext


class IncomeExpenseAnalyzer(BaseAnalyzer):
    """收入支出分析器
    
    专门负责收入支出相关的分析，包括：
    - 收入支出总额分析
    - 月度收支分解
    - 收支趋势分析
    - 收支比例分析
    """
    
    def __init__(
        self,
        start_date: date,
        end_date: date,
        context: AnalyzerContext,
        account_id: Optional[int] = None
    ):
        """初始化收入支出分析器
        
        Args:
            start_date: 分析开始日期
            end_date: 分析结束日期
            context: 分析器上下文
            account_id: 可选的账户ID
        """
        super().__init__(start_date, end_date, context, account_id)
    
    def _perform_analysis(self) -> Dict[str, Any]:
        """执行收入支出分析的具体逻辑
        
        Returns:
            包含收入支出分析结果的字典
        """
        return {
            'totals': self.get_income_expense_totals(),
            'monthly_breakdown': self.get_monthly_breakdown(),
            'trends': self.analyze_trends(),
            'ratios': self.calculate_ratios(),
            'summary': self.get_summary()
        }
    
    def get_income_expense_totals(self) -> Dict[str, float]:
        """获取收入支出总额
        
        Returns:
            包含总收入、总支出和净收入的字典
        """
        try:
            # 检查缓存
            cached_result = self.get_cached_result('get_income_expense_totals')
            if cached_result:
                return cached_result
            
            # 使用数据服务获取数据
            totals = self.data_service.get_income_expense_totals(
                start_date=self.start_date,
                end_date=self.end_date,
                account_id=self.account_id
            )
            
            result = {
                'total_income': float(totals.get('total_income', 0)),
                'total_expense': float(totals.get('total_expense', 0)),
                'net_income': float(totals.get('net_income', 0)),
                'transaction_count': totals.get('transaction_count', 0)
            }
            
            # 缓存结果
            self.set_cached_result('get_income_expense_totals', result, ttl_minutes=60)
            
            return result
            
        except Exception as e:
            self.logger.error(f"获取收入支出总额失败: {e}")
            return {
                'total_income': 0.0,
                'total_expense': 0.0,
                'net_income': 0.0,
                'transaction_count': 0
            }
    
    def get_monthly_breakdown(self) -> List[Dict[str, Any]]:
        """获取月度收支分解
        
        Returns:
            月度收支数据列表
        """
        try:
            # 检查缓存
            cached_result = self.get_cached_result('get_monthly_breakdown')
            if cached_result:
                return cached_result
            
            # 使用数据服务获取月度数据
            monthly_data = self.data_service.get_monthly_breakdown(
                start_date=self.start_date,
                end_date=self.end_date,
                account_id=self.account_id
            )
            
            # 缓存结果
            self.set_cached_result('get_monthly_breakdown', monthly_data, ttl_minutes=60)
            
            return monthly_data
            
        except Exception as e:
            self.logger.error(f"获取月度分解数据失败: {e}")
            return []
    
    def analyze_trends(self) -> Dict[str, Any]:
        """分析收支趋势
        
        Returns:
            趋势分析结果
        """
        try:
            # 检查缓存
            cached_result = self.get_cached_result('analyze_trends')
            if cached_result:
                return cached_result
            
            # 获取月度数据
            monthly_data = self.get_monthly_breakdown()
            
            if not monthly_data:
                return {
                    'income_trend': 'stable',
                    'expense_trend': 'stable',
                    'net_trend': 'stable',
                    'income_growth_rate': 0.0,
                    'expense_growth_rate': 0.0
                }
            
            # 提取数值序列
            income_values = [month['income'] for month in monthly_data]
            expense_values = [month['expense'] for month in monthly_data]
            net_values = [month['net'] for month in monthly_data]
            
            # 使用计算服务分析趋势
            result = {
                'income_trend': self.calculation_service.calculate_trend(income_values),
                'expense_trend': self.calculation_service.calculate_trend(expense_values),
                'net_trend': self.calculation_service.calculate_trend(net_values),
                'income_volatility': self.calculation_service.calculate_coefficient_of_variation(income_values),
                'expense_volatility': self.calculation_service.calculate_coefficient_of_variation(expense_values)
            }
            
            # 计算增长率（如果有足够数据）
            if len(monthly_data) >= 2:
                first_month = monthly_data[0]
                last_month = monthly_data[-1]
                
                result['income_growth_rate'] = self.calculation_service.calculate_growth_rate(
                    last_month['income'], first_month['income']
                )
                result['expense_growth_rate'] = self.calculation_service.calculate_growth_rate(
                    last_month['expense'], first_month['expense']
                )
            else:
                result['income_growth_rate'] = 0.0
                result['expense_growth_rate'] = 0.0
            
            # 缓存结果
            self.set_cached_result('analyze_trends', result, ttl_minutes=30)
            
            return result
            
        except Exception as e:
            self.logger.error(f"分析趋势失败: {e}")
            return {
                'income_trend': 'stable',
                'expense_trend': 'stable',
                'net_trend': 'stable',
                'income_growth_rate': 0.0,
                'expense_growth_rate': 0.0,
                'income_volatility': 0.0,
                'expense_volatility': 0.0
            }
    
    def calculate_ratios(self) -> Dict[str, float]:
        """计算收支比例
        
        Returns:
            各种比例指标
        """
        try:
            # 检查缓存
            cached_result = self.get_cached_result('calculate_ratios')
            if cached_result:
                return cached_result
            
            # 获取总额数据
            totals = self.get_income_expense_totals()
            
            total_income = totals['total_income']
            total_expense = totals['total_expense']
            
            result = {
                'expense_ratio': (total_expense / total_income * 100) if total_income > 0 else 0.0,
                'savings_ratio': ((total_income - total_expense) / total_income * 100) if total_income > 0 else 0.0,
                'expense_income_ratio': (total_expense / total_income) if total_income > 0 else 0.0
            }
            
            # 缓存结果
            self.set_cached_result('calculate_ratios', result, ttl_minutes=60)
            
            return result
            
        except Exception as e:
            self.logger.error(f"计算比例失败: {e}")
            return {
                'expense_ratio': 0.0,
                'savings_ratio': 0.0,
                'expense_income_ratio': 0.0
            }
    
    def get_summary(self) -> str:
        """获取分析摘要
        
        Returns:
            分析摘要文本
        """
        try:
            totals = self.get_income_expense_totals()
            trends = self.analyze_trends()
            ratios = self.calculate_ratios()
            
            total_income = totals['total_income']
            total_expense = totals['total_expense']
            net_income = totals['net_income']
            
            # 构建摘要
            summary_parts = []
            
            # 基本情况
            summary_parts.append(
                f"分析期间总收入 {total_income:.2f} 元，总支出 {total_expense:.2f} 元，"
                f"净收入 {net_income:.2f} 元。"
            )
            
            # 收支比例
            if total_income > 0:
                expense_ratio = ratios['expense_ratio']
                savings_ratio = ratios['savings_ratio']
                summary_parts.append(
                    f"支出占收入的 {expense_ratio:.1f}%，储蓄率为 {savings_ratio:.1f}%。"
                )
            
            # 趋势分析
            income_trend = trends['income_trend']
            expense_trend = trends['expense_trend']
            
            if income_trend == 'increasing':
                summary_parts.append("收入呈上升趋势。")
            elif income_trend == 'decreasing':
                summary_parts.append("收入呈下降趋势。")
            else:
                summary_parts.append("收入相对稳定。")
            
            if expense_trend == 'increasing':
                summary_parts.append("支出呈上升趋势。")
            elif expense_trend == 'decreasing':
                summary_parts.append("支出呈下降趋势。")
            else:
                summary_parts.append("支出相对稳定。")
            
            return ' '.join(summary_parts)
            
        except Exception as e:
            self.logger.error(f"生成摘要失败: {e}")
            return "无法生成分析摘要。"