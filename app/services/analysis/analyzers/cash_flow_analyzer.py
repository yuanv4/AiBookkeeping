"""Cash Flow Analysis Module.

包含现金流健康状况分析器。
优化版本：使用新的基类和缓存策略。"""

from typing import Dict, List, Any
import logging
from datetime import datetime, timedelta
from sqlalchemy import func

from app.models import Transaction, db
from app.models.analysis_models import CashFlowHealth, CashFlowMetrics
from app.utils.query_builder import OptimizedQueryBuilder, AnalysisException
from app.utils.cache_manager import optimized_cache
from .base_analyzer import BaseAnalyzer
from app.utils.performance_monitor import performance_monitor

logger = logging.getLogger(__name__)


class CashFlowAnalyzer(BaseAnalyzer):
    """优化的现金流健康状况分析器。"""
    
    @performance_monitor("cash_flow_analysis")
    def analyze(self) -> CashFlowHealth:
        """分析现金流健康状况。"""
        try:
            # 使用优化的现金流分析
            cash_flow_data = self._analyze_cash_flow_patterns()
            metrics = self._build_cash_flow_metrics(cash_flow_data)
            
            return CashFlowHealth(
                metrics=metrics,
                monthly_flow=cash_flow_data.get('monthly_flow', []),
                gap_frequency=cash_flow_data.get('gap_frequency', 0.0),
                avg_gap=cash_flow_data.get('avg_gap', 0.0),
                total_balance=cash_flow_data.get('total_balance', 0.0),
                monthly_cash_flow=cash_flow_data.get('monthly_cash_flow', [])
            )
        except Exception as e:
            logger.error(f"现金流分析失败: {e}")
            return CashFlowHealth()
    
    @optimized_cache('cash_flow_analysis', expire_minutes=20, priority=2)
    def _analyze_cash_flow_patterns(self) -> Dict[str, Any]:
        """分析现金流模式。"""
        try:
            # 使用优化的查询构建器获取现金流数据
            query_builder = OptimizedQueryBuilder()
            
            # 获取现金流分析查询
            cash_flow_query = query_builder.build_cash_flow_analysis_query(
                account_id=self.account_id,
                start_date=self.start_date,
                end_date=self.end_date
            )
            
            # 执行查询
            results = query_builder.execute_with_error_handling(
                cash_flow_query, "现金流分析查询"
            )
            
            # 处理结果
            daily_balances = []
            monthly_flows = {}
            
            for result in results:
                daily_balances.append({
                    'date': result.date,
                    'amount': float(result.amount),
                    'running_balance': float(result.running_balance),
                    'daily_net': float(result.daily_net),
                    'daily_income': float(result.daily_income),
                    'daily_expense': float(result.daily_expense)
                })
                
                # 按月汇总
                month_key = f"{result.date.year}-{result.date.month:02d}"
                if month_key not in monthly_flows:
                    monthly_flows[month_key] = {
                        'income': 0.0,
                        'expense': 0.0,
                        'net': 0.0
                    }
                
                monthly_flows[month_key]['income'] += float(result.daily_income)
                monthly_flows[month_key]['expense'] += float(result.daily_expense)
                monthly_flows[month_key]['net'] += float(result.daily_net)
            
            # 计算统计指标
            monthly_nets = [flow['net'] for flow in monthly_flows.values()]
            positive_months = sum(1 for net in monthly_nets if net > 0)
            negative_months = sum(1 for net in monthly_nets if net < 0)
            
            # 计算波动性
            volatility = self._calculate_coefficient_of_variation(monthly_nets)
            
            # 计算缺口频率和平均缺口
            gaps = [net for net in monthly_nets if net < 0]
            gap_frequency = len(gaps) / len(monthly_nets) if monthly_nets else 0.0
            avg_gap = abs(sum(gaps) / len(gaps)) if gaps else 0.0
            
            # 计算总余额
            total_balance = daily_balances[-1]['running_balance'] if daily_balances else 0.0
            
            return {
                'monthly_flow': list(monthly_flows.values()),
                'monthly_cash_flow': monthly_nets,
                'avg_monthly_income': sum(flow['income'] for flow in monthly_flows.values()) / len(monthly_flows) if monthly_flows else 0.0,
                'avg_monthly_expense': sum(flow['expense'] for flow in monthly_flows.values()) / len(monthly_flows) if monthly_flows else 0.0,
                'volatility': volatility,
                'positive_months': positive_months,
                'negative_months': negative_months,
                'gap_frequency': gap_frequency,
                'avg_gap': avg_gap,
                'total_balance': total_balance,
                'daily_balances': daily_balances
            }
            
        except Exception as e:
            logger.error(f"现金流模式分析失败: {e}")
            return {}
    
    def _build_cash_flow_metrics(self, cash_flow_data: Dict[str, Any]) -> CashFlowMetrics:
        """构建现金流指标。"""
        return CashFlowMetrics(
            total_inflow=cash_flow_data.get('total_inflow', 0.0),
            total_outflow=cash_flow_data.get('total_outflow', 0.0),
            net_cash_flow=cash_flow_data.get('net_cash_flow', 0.0),
            average_monthly_inflow=cash_flow_data.get('avg_monthly_income', 0.0),
            average_monthly_outflow=cash_flow_data.get('avg_monthly_expense', 0.0),
            cash_flow_volatility=cash_flow_data.get('volatility', 0.0),
            positive_months=cash_flow_data.get('positive_months', 0),
            negative_months=cash_flow_data.get('negative_months', 0)
        )
    
    def _calculate_monthly_flow(self) -> List[Dict[str, Any]]:
        """Calculate monthly cash flow data."""
        def _calc():
            # 简化的月度现金流计算
            return []
        
        return self._get_cached_data('monthly_flow', _calc)
    
    @optimized_cache(cache_name='cash_flow_health', expire_minutes=30)
    def _calculate_cash_flow_health(self) -> Dict[str, Any]:
        """Calculate cash flow health indicators."""
        try:
            from app.models.account import Account
            
            query_builder = OptimizedQueryBuilder()
            
            # 获取总余额
            balance_query = db.session.query(
                func.sum(Account.balance).label('total_balance')
            )
            balance_result = query_builder.execute_with_error_handling(balance_query)
            total_balance = float(balance_result[0].total_balance or 0) if balance_result else 0
            
            # 获取最近12个月的月度现金流数据
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=365)
            
            monthly_query = query_builder.build_aggregated_analysis_query(
                start_date=start_date,
                end_date=end_date,
                account_id=self.account_id,
                group_by='month'
            )
            
            monthly_results = query_builder.execute_with_error_handling(monthly_query, 'monthly_cash_flow_analysis')
            
            # 计算现金流指标
            gap_months = 0
            total_gaps = 0
            monthly_expenses = []
            monthly_cash_flow = []
            
            for result in monthly_results:
                income = float(getattr(result, 'total_income', 0) or 0)
                expense = float(getattr(result, 'total_expense', 0) or 0)
                cash_flow = income - expense
                
                # 构建月份标识
                year = getattr(result, 'year', '')
                month = getattr(result, 'month', '')
                month_str = f"{year}-{month:02d}" if year and month else ''
                
                monthly_cash_flow.append({
                    'month': month_str,
                    'income': income,
                    'expense': expense,
                    'cash_flow': cash_flow
                })
                
                monthly_expenses.append(expense)
                
                # 统计现金流缺口
                if cash_flow < 0:
                    gap_months += 1
                    total_gaps += abs(cash_flow)
            
            # 计算应急基金月数（基于平均月支出）
            avg_monthly_expense = sum(monthly_expenses) / len(monthly_expenses) if monthly_expenses else 1
            emergency_fund_months = total_balance / avg_monthly_expense if avg_monthly_expense > 0 else 0
            
            # 计算缺口频率
            total_months = len(formatted_results) if formatted_results else 1
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
            
        except AnalysisException:
            raise
        except Exception as e:
            logger.error(f"Error calculating cash flow health: {e}")
            raise AnalysisException(f"Failed to calculate cash flow health: {str(e)}")