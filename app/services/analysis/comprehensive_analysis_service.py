"""Comprehensive Analysis Service Module.

包含综合分析服务。
优化版本：使用优化后的分析器和缓存策略。
"""

from typing import List, Dict, Any, Optional, Tuple
from decimal import Decimal
from datetime import date, datetime, timedelta
import logging
from collections import defaultdict
import calendar

from app.models import Transaction, Account, TransactionType, Bank, db
from app.models.analysis_models import ComprehensiveAnalysisData
from app.services.analysis.analyzers.income_analyzer import IncomeExpenseAnalyzer, IncomeStabilityAnalyzer
from app.services.analysis.analyzers.cash_flow_analyzer import CashFlowAnalyzer
from app.services.analysis.analyzers.diversity_analyzer import IncomeDiversityAnalyzer
from app.services.analysis.analyzers.growth_analyzer import IncomeGrowthAnalyzer
from app.services.analysis.analyzers.resilience_analyzer import FinancialResilienceAnalyzer
from app.utils.query_builder import OptimizedQueryBuilder, AnalysisException
from app.utils.cache_manager import optimized_cache
from app.utils.performance_monitor import monitor_performance
from sqlalchemy import func, and_, or_, extract, case
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)

class ComprehensiveService:
    """优化的综合分析服务。"""
    
    @staticmethod
    @monitor_performance("comprehensive_analysis")
    @optimized_cache('comprehensive_income_analysis', expire_minutes=45, priority=1)
    def get_comprehensive_income_analysis(account_id: Optional[int] = None) -> Dict[str, Any]:
        """获取综合收入分析数据，返回模板所需的完整data结构
        
        Args:
            account_id: 可选的账户ID，用于分析特定账户
            
        Returns:
            Dict[str, Any]: 包含所有分析模块数据的字典
        """
        try:
            # 获取基础数据
            today = date.today()
            start_date = today.replace(year=today.year - 1, month=1, day=1)  # 过去一年
            end_date = today
            
            # 创建优化后的分析器
            analyzers = ComprehensiveService._create_analyzers(start_date, end_date, account_id)
            
            # 并行执行分析（如果可能）
            analysis_results = ComprehensiveService._execute_parallel_analysis(analyzers)
            
            # 构建综合分析数据结构
            # 将IncomeExpenseAnalysis转换为IncomeExpenseBalance以保持模板兼容性
            from app.models.analysis_models import IncomeExpenseBalance
            income_expense_result = analysis_results['income_expense']
            income_expense_balance = IncomeExpenseBalance(
                overall_stats=income_expense_result.overall_stats,
                monthly_data=income_expense_result.monthly_data
            )
            
            comprehensive_data = ComprehensiveAnalysisData(
                income_expense_balance=income_expense_balance,
                income_stability=analysis_results['stability'],
                cash_flow_health=analysis_results['cash_flow'],
                income_diversity=analysis_results['diversity'],
                income_growth=analysis_results['growth'],
                financial_resilience=analysis_results['resilience']
            )
            
            # 返回对象以支持属性访问
            return comprehensive_data
            
        except Exception as e:
            logger.error(f"Error getting comprehensive income analysis: {e}")
            # 返回默认对象以防止模板错误
            return ComprehensiveAnalysisData()
    
    @staticmethod
    def _create_analyzers(start_date: date, end_date: date, account_id: Optional[int]) -> Dict[str, Any]:
        """创建分析器实例。"""
        return {
            'income_expense': IncomeExpenseAnalyzer(start_date, end_date, account_id),
            'stability': IncomeStabilityAnalyzer(start_date, end_date, account_id),
            'cash_flow': CashFlowAnalyzer(start_date, end_date, account_id),
            'diversity': IncomeDiversityAnalyzer(start_date, end_date, account_id),
            'growth': IncomeGrowthAnalyzer(start_date, end_date, account_id),
            'resilience': FinancialResilienceAnalyzer(start_date, end_date, account_id)
        }
    
    @staticmethod
    def _execute_parallel_analysis(analyzers: Dict[str, Any]) -> Dict[str, Any]:
        """执行并行分析（当前为顺序执行，可扩展为真正的并行）。"""
        results = {}
        
        try:
            # 顺序执行各个分析器
            results['income_expense'] = analyzers['income_expense'].analyze()
            results['stability'] = analyzers['stability'].analyze()
            results['cash_flow'] = analyzers['cash_flow'].analyze()
            results['diversity'] = analyzers['diversity'].analyze()
            results['growth'] = analyzers['growth'].analyze()
            results['resilience'] = analyzers['resilience'].analyze()
            
            return results
            
        except Exception as e:
            logger.error(f"并行分析执行失败: {e}")
            # 返回默认结果对象
            from ..analysis.analyzers.income_analyzer import IncomeExpenseAnalysis
            from ..analysis.analyzers.income_stability_analyzer import IncomeStability
            from ..analysis.analyzers.cash_flow_analyzer import CashFlowHealth
            from ..analysis.analyzers.income_diversity_analyzer import IncomeDiversity
            from ..analysis.analyzers.income_growth_analyzer import IncomeGrowth
            from ..analysis.analyzers.financial_resilience_analyzer import FinancialResilience
            
            return {
                'income_expense': IncomeExpenseAnalysis(),
                'stability': IncomeStability(),
                'cash_flow': CashFlowHealth(),
                'diversity': IncomeDiversity(),
                'growth': IncomeGrowth(),
                'resilience': FinancialResilience()
            }
    
    @staticmethod
    def _get_default_analysis_data() -> Dict[str, Any]:
        """获取默认的分析数据结构"""
        return {
            'income_expense_balance': {
                'overall_stats': {
                    'total_income': 0.0,
                    'total_expense': 0.0,
                    'net_saving': 0.0,
                    'avg_monthly_income': 0.0,
                    'avg_monthly_expense': 0.0,
                    'avg_monthly_saving_rate': 0.0,
                    'avg_monthly_ratio': 0.0,
                    'avg_necessary_expense_coverage': 0.0
                },
                'monthly_data': []
            },
            'income_stability': {
                'stability_metrics': {
                    'coefficient_of_variation': 0,
                    'stability_score': 0,
                    'trend_direction': 'stable',
                    'volatility_level': 'low'
                },
                'monthly_variance': {
                    'variance': 0,
                    'standard_deviation': 0,
                    'mean_income': 0
                }
            },
            'cash_flow_health': {
                'cash_flow_metrics': {
                    'average_monthly_flow': 0,
                    'positive_months': 0,
                    'negative_months': 0,
                    'flow_consistency': 0
                },
                'monthly_flow': [],
                'cash_flow_health': {
                    'emergency_fund_months': 0,
                    'gap_frequency': 0,
                    'average_gap': 0
                }
            },
            'income_diversity': {
                'diversity_metrics': {
                    'source_count': 0,
                    'concentration_ratio': 0,
                    'passive_income_ratio': 0,
                    'diversity_index': 0,
                    'risk_level': 'low'
                },
                'source_breakdown': []
            },
            'income_growth': {
                'growth_metrics': {
                    'annual_growth_rate': 0,
                    'quarterly_growth_rate': 0,
                    'growth_trend': 'stable',
                    'growth_consistency': 0
                },
                'historical_growth': []
            },
            'financial_resilience': {
                'resilience_metrics': {
                    'resilience_score': 0,
                    'stress_test_score': 0,
                    'recovery_capacity': 0,
                    'risk_tolerance': 'medium'
                },
                'scenario_analysis': {
                    'best_case': {'income': 0, 'probability': 0},
                    'worst_case': {'income': 0, 'probability': 0},
                    'most_likely': {'income': 0, 'probability': 0}
                }
            }
        }
    
    @staticmethod
    def get_monthly_income_summary() -> Dict[str, Any]:
        """获取月度收入汇总"""
        try:
            # 获取当前月份的开始和结束日期
            today = date.today()
            start_date = today.replace(day=1)
            
            # 计算月末日期
            if today.month == 12:
                end_date = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
            else:
                end_date = today.replace(month=today.month + 1, day=1) - timedelta(days=1)
            
            # 查询当月收入交易
            income_query = db.session.query(
                func.sum(Transaction.amount).label('total_income'),
                func.count(Transaction.id).label('transaction_count'),
                func.avg(Transaction.amount).label('average_income')
            ).filter(
                Transaction.amount > 0,
                Transaction.date >= start_date,
                Transaction.date <= end_date
            )
            
            result = income_query.first()
            
            return {
                'period': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat(),
                    'month': today.strftime('%Y-%m')
                },
                'total_income': float(result.total_income or 0),
                'transaction_count': result.transaction_count or 0,
                'average_income': float(result.average_income or 0)
            }
            
        except Exception as e:
            logger.error(f"Error getting monthly income summary: {e}")
            return {
                'period': {'start_date': '', 'end_date': '', 'month': ''},
                'total_income': 0,
                'transaction_count': 0,
                'average_income': 0
            }
    
    @staticmethod
    def get_yearly_income_summary() -> Dict[str, Any]:
        """获取年度收入汇总"""
        try:
            # 获取当前年份的开始和结束日期
            today = date.today()
            start_date = today.replace(month=1, day=1)
            end_date = today.replace(month=12, day=31)
            
            # 查询当年收入交易
            income_query = db.session.query(
                func.sum(Transaction.amount).label('total_income'),
                func.count(Transaction.id).label('transaction_count'),
                func.avg(Transaction.amount).label('average_income')
            ).filter(
                Transaction.amount > 0,
                Transaction.date >= start_date,
                Transaction.date <= end_date
            )
            
            result = income_query.first()
            
            # 按月份分组的收入数据
            monthly_query = db.session.query(
                extract('month', Transaction.date).label('month'),
                func.sum(Transaction.amount).label('monthly_income')
            ).filter(
                Transaction.amount > 0,
                Transaction.date >= start_date,
                Transaction.date <= end_date
            ).group_by(extract('month', Transaction.date)).order_by('month')
            
            monthly_results = monthly_query.all()
            monthly_breakdown = []
            for month_result in monthly_results:
                monthly_breakdown.append({
                    'month': int(month_result.month),
                    'month_name': calendar.month_name[int(month_result.month)],
                    'income': float(month_result.monthly_income or 0)
                })
            
            return {
                'period': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat(),
                    'year': today.year
                },
                'total_income': float(result.total_income or 0),
                'transaction_count': result.transaction_count or 0,
                'average_income': float(result.average_income or 0),
                'monthly_breakdown': monthly_breakdown
            }
            
        except Exception as e:
            logger.error(f"Error getting yearly income summary: {e}")
            return {
                'period': {'start_date': '', 'end_date': '', 'year': 0},
                'total_income': 0,
                'transaction_count': 0,
                'average_income': 0,
                'monthly_breakdown': []
            }
    
    @staticmethod
    def get_income_by_account() -> Dict[str, Any]:
        """获取按账户分组的收入数据"""
        try:
            # 查询按账户分组的收入数据
            from app.models.bank import Bank
            account_query = db.session.query(
                Account.id,
                Account.account_name,
                Bank.name.label('bank_name'),
                func.sum(Transaction.amount).label('total_income'),
                func.count(Transaction.id).label('transaction_count')
            ).join(Transaction).join(Bank, Account.bank_id == Bank.id).filter(
                Transaction.amount > 0
            ).group_by(
                Account.id, Account.account_name, Bank.name
            ).order_by(func.sum(Transaction.amount).desc())
            
            results = account_query.all()
            
            accounts = []
            total_income = 0
            
            for result in results:
                income = float(result.total_income or 0)
                total_income += income
                accounts.append({
                    'account_id': result.id,
                    'account_name': result.account_name,
                    'bank_name': result.bank_name,
                    'total_income': income,
                    'transaction_count': result.transaction_count or 0
                })
            
            # 计算百分比
            for account in accounts:
                account['percentage'] = (account['total_income'] / total_income * 100) if total_income > 0 else 0
            
            return {
                'accounts': accounts,
                'total_income': total_income,
                'account_count': len(accounts)
            }
            
        except Exception as e:
            logger.error(f"Error getting income by account: {e}")
            return {
                'accounts': [],
                'total_income': 0,
                'account_count': 0
            }
    
    @staticmethod
    def get_income_trends() -> Dict[str, Any]:
        """获取收入趋势数据"""
        try:
            # 获取最近12个月的收入趋势
            today = date.today()
            start_date = today.replace(day=1) - timedelta(days=365)
            
            # 按月份分组的收入趋势
            monthly_query = db.session.query(
                extract('year', Transaction.date).label('year'),
                extract('month', Transaction.date).label('month'),
                func.sum(Transaction.amount).label('monthly_income')
            ).filter(
                Transaction.amount > 0,
                Transaction.date >= start_date
            ).group_by(
                extract('year', Transaction.date),
                extract('month', Transaction.date)
            ).order_by('year', 'month')
            
            monthly_results = monthly_query.all()
            monthly_trends = []
            
            for result in monthly_results:
                monthly_trends.append({
                    'year': int(result.year),
                    'month': int(result.month),
                    'month_name': calendar.month_name[int(result.month)],
                    'period': f"{int(result.year)}-{int(result.month):02d}",
                    'income': float(result.monthly_income or 0)
                })
            
            # 计算增长率
            for i in range(1, len(monthly_trends)):
                current = monthly_trends[i]['income']
                previous = monthly_trends[i-1]['income']
                if previous > 0:
                    growth_rate = ((current - previous) / previous) * 100
                else:
                    growth_rate = 0
                monthly_trends[i]['growth_rate'] = growth_rate
            
            # 如果有数据，第一个月的增长率设为0
            if monthly_trends:
                monthly_trends[0]['growth_rate'] = 0
            
            return {
                'monthly_trends': monthly_trends,
                'trend_period': {
                    'start_date': start_date.isoformat(),
                    'end_date': today.isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting income trends: {e}")
            return {
                'monthly_trends': [],
                'trend_period': {'start_date': '', 'end_date': ''}
            }
    
    @staticmethod
    def compare_periods(account_id: int = None, current_start: date = None, 
                       current_end: date = None, previous_start: date = None, 
                       previous_end: date = None) -> Dict[str, Any]:
        """Compare financial data between two periods."""
        try:
            from app.services.reporting.financial_report_service import FinancialReportService
            
            current_summary = FinancialReportService._get_period_summary(account_id, current_start, current_end)
            previous_summary = FinancialReportService._get_period_summary(account_id, previous_start, previous_end)
            
            comparison = {
                'current_period': {
                    'start_date': current_start.isoformat() if current_start else None,
                    'end_date': current_end.isoformat() if current_end else None,
                    'summary': current_summary
                },
                'previous_period': {
                    'start_date': previous_start.isoformat() if previous_start else None,
                    'end_date': previous_end.isoformat() if previous_end else None,
                    'summary': previous_summary
                },
                'changes': {}
            }
            
            # Calculate changes
            for key in ['total_income', 'total_expense', 'net_income', 'total_transactions']:
                current_val = current_summary.get(key, 0)
                previous_val = previous_summary.get(key, 0)
                
                if previous_val != 0:
                    change_percent = ((current_val - previous_val) / previous_val) * 100
                else:
                    change_percent = 100 if current_val > 0 else 0
                
                comparison['changes'][key] = {
                    'absolute': current_val - previous_val,
                    'percentage': change_percent,
                    'trend': 'up' if current_val > previous_val else 'down' if current_val < previous_val else 'stable'
                }
            
            return comparison
            
        except Exception as e:
            logger.error(f"Error comparing periods: {e}")
            raise
    
    @staticmethod
    def get_budget_analysis(account_id: int = None, budget_limits: Dict[str, float] = None,
                          start_date: date = None, end_date: date = None) -> Dict[str, Any]:
        """Analyze spending against budget limits."""
        try:
            if not budget_limits:
                return {'error': 'No budget limits provided'}
            
            from app.services.reporting.financial_report_service import FinancialReportService
            expense_analysis = FinancialReportService._get_expense_analysis(account_id, start_date, end_date)
            
            budget_analysis = {
                'total_budget': sum(budget_limits.values()),
                'total_spent': expense_analysis['total_expense'],
                'categories': [],
                'overall_status': 'within_budget'
            }
            
            total_over_budget = 0
            
            for category in expense_analysis['expense_categories']:
                category_name = category['category']
                spent = category['total']
                budget = budget_limits.get(category_name, 0)
                
                if budget > 0:
                    percentage_used = (spent / budget) * 100
                    over_budget = max(0, spent - budget)
                    total_over_budget += over_budget
                    
                    status = 'over_budget' if spent > budget else 'within_budget'
                    if percentage_used > 80 and status == 'within_budget':
                        status = 'near_limit'
                    
                    budget_analysis['categories'].append({
                        'category': category_name,
                        'budget': budget,
                        'spent': spent,
                        'remaining': max(0, budget - spent),
                        'percentage_used': percentage_used,
                        'over_budget': over_budget,
                        'status': status
                    })
            
            # Overall status
            if total_over_budget > 0:
                budget_analysis['overall_status'] = 'over_budget'
            elif budget_analysis['total_spent'] > budget_analysis['total_budget'] * 0.9:
                budget_analysis['overall_status'] = 'near_limit'
            
            budget_analysis['total_over_budget'] = total_over_budget
            budget_analysis['budget_utilization'] = (
                budget_analysis['total_spent'] / budget_analysis['total_budget'] * 100
                if budget_analysis['total_budget'] > 0 else 0
            )
            
            return budget_analysis
            
        except Exception as e:
            logger.error(f"Error analyzing budget: {e}")
            raise
    
    @staticmethod
    def export_financial_data(account_id: int = None, start_date: date = None, 
                            end_date: date = None, format: str = 'json') -> Dict[str, Any]:
        """Export financial data in specified format."""
        try:
            query = Transaction.query
            
            if account_id:
                query = query.filter_by(account_id=account_id)
            if start_date:
                query = query.filter(Transaction.date >= start_date)
            if end_date:
                query = query.filter(Transaction.date <= end_date)
            
            transactions = query.order_by(Transaction.date.desc()).all()
            
            export_data = {
                'metadata': {
                    'export_date': datetime.now().isoformat(),
                    'period_start': start_date.isoformat() if start_date else None,
                    'period_end': end_date.isoformat() if end_date else None,
                    'account_id': account_id,
                    'total_records': len(transactions),
                    'format': format
                },
                'transactions': []
            }
            
            for transaction in transactions:
                export_data['transactions'].append({
                    'id': transaction.id,
                    'date': transaction.date.isoformat(),
                    'amount': float(transaction.amount),
                    'currency': transaction.currency,
                    'description': transaction.description,
                    'counterparty': transaction.counterparty,
                    'category': transaction.transaction_type.name if transaction.transaction_type else None,
                    'account_number': transaction.account.account_number if transaction.account else None,
                    'bank_name': transaction.account.bank.name if transaction.account and transaction.account.bank else None,
                    'notes': transaction.notes,
                    'reference_number': transaction.reference_number,
                    'is_verified': transaction.is_verified,
                    'created_at': transaction.created_at.isoformat() if transaction.created_at else None
                })
            
            return export_data
            
        except Exception as e:
            logger.error(f"Error exporting financial data: {e}")
            raise