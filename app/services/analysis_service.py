"""Analysis service for financial data analysis and reporting.

This module provides comprehensive financial analysis, reporting, and insights.
"""

from typing import List, Dict, Any, Optional, Tuple
from decimal import Decimal
from datetime import date, datetime, timedelta
import logging
from collections import defaultdict
import calendar

from app.models import Transaction, Account, TransactionType, Bank, db
from app.models.analysis_models import ComprehensiveAnalysisData
from app.services.specialized_analyzers import (
    IncomeExpenseAnalyzer, IncomeStabilityAnalyzer, CashFlowAnalyzer,
    IncomeDiversityAnalyzer, IncomeGrowthAnalyzer, FinancialResilienceAnalyzer
)
from sqlalchemy import func, and_, or_, extract, case
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)

class AnalysisService:
    """Service for financial analysis and reporting."""
    
    @staticmethod
    def generate_financial_report(account_id: int = None, start_date: date = None, 
                                end_date: date = None) -> Dict[str, Any]:
        """Generate comprehensive financial report."""
        try:
            if not start_date:
                start_date = date.today().replace(day=1)  # First day of current month
            if not end_date:
                end_date = date.today()
            
            report = {
                'period': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat(),
                    'days': (end_date - start_date).days + 1
                },
                'summary': AnalysisService._get_period_summary(account_id, start_date, end_date),
                'income_analysis': AnalysisService._get_income_analysis(account_id, start_date, end_date),
                'expense_analysis': AnalysisService._get_expense_analysis(account_id, start_date, end_date),
                'category_breakdown': AnalysisService._get_category_breakdown(account_id, start_date, end_date),
                'trends': AnalysisService._get_trend_analysis(account_id, start_date, end_date),
                'insights': AnalysisService._generate_insights(account_id, start_date, end_date)
            }
            
            if account_id:
                account = Account.query.get(account_id)
                if account:
                    report['account_info'] = {
                        'id': account.id,
                        'name': account.account_name,
                        'number': account.account_number,
                        'bank': account.bank.name if account.bank else None,
                        'current_balance': float(account.balance or 0)
                    }
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating financial report: {e}")
            raise
    
    @staticmethod
    def _get_period_summary(account_id: int = None, start_date: date = None, 
                          end_date: date = None) -> Dict[str, Any]:
        """Get summary statistics for the period."""
        query = Transaction.query
        
        if account_id:
            query = query.filter_by(account_id=account_id)
        if start_date:
            query = query.filter(Transaction.date >= start_date)
        if end_date:
            query = query.filter(Transaction.date <= end_date)
        
        transactions = query.all()
        
        total_income = sum(t.amount for t in transactions if t.amount > 0)
        total_expense = sum(abs(t.amount) for t in transactions if t.amount < 0)
        
        return {
            'total_transactions': len(transactions),
            'total_income': float(total_income),
            'total_expense': float(total_expense),
            'net_income': float(total_income - total_expense),
            'average_transaction': float(sum(abs(t.amount) for t in transactions) / len(transactions)) if transactions else 0,
            'income_transactions': len([t for t in transactions if t.amount > 0]),
            'expense_transactions': len([t for t in transactions if t.amount < 0])
        }
    
    @staticmethod
    def _get_income_analysis(account_id: int = None, start_date: date = None, 
                           end_date: date = None) -> Dict[str, Any]:
        """Analyze income patterns."""
        query = db.session.query(
            TransactionType.name,
            func.count(Transaction.id).label('count'),
            func.sum(Transaction.amount).label('total'),
            func.avg(Transaction.amount).label('average'),
            func.max(Transaction.amount).label('maximum'),
            func.min(Transaction.amount).label('minimum')
        ).join(Transaction).filter(Transaction.amount > 0)
        
        if account_id:
            query = query.filter(Transaction.account_id == account_id)
        if start_date:
            query = query.filter(Transaction.date >= start_date)
        if end_date:
            query = query.filter(Transaction.date <= end_date)
        
        results = query.group_by(TransactionType.name).order_by(
            func.sum(Transaction.amount).desc()
        ).all()
        
        income_sources = []
        total_income = 0
        
        for result in results:
            amount = float(result.total)
            total_income += amount
            income_sources.append({
                'category': result.name,
                'count': result.count,
                'total': amount,
                'average': float(result.average),
                'maximum': float(result.maximum),
                'minimum': float(result.minimum)
            })
        
        # Calculate percentages
        for source in income_sources:
            source['percentage'] = (source['total'] / total_income * 100) if total_income > 0 else 0
        
        return {
            'total_income': total_income,
            'income_sources': income_sources,
            'primary_source': income_sources[0] if income_sources else None,
            'source_diversity': len(income_sources)
        }
    
    @staticmethod
    def _get_expense_analysis(account_id: int = None, start_date: date = None, 
                            end_date: date = None) -> Dict[str, Any]:
        """Analyze expense patterns."""
        query = db.session.query(
            TransactionType.name,
            func.count(Transaction.id).label('count'),
            func.sum(func.abs(Transaction.amount)).label('total'),
            func.avg(func.abs(Transaction.amount)).label('average'),
            func.max(func.abs(Transaction.amount)).label('maximum'),
            func.min(func.abs(Transaction.amount)).label('minimum')
        ).join(Transaction).filter(Transaction.amount < 0)
        
        if account_id:
            query = query.filter(Transaction.account_id == account_id)
        if start_date:
            query = query.filter(Transaction.date >= start_date)
        if end_date:
            query = query.filter(Transaction.date <= end_date)
        
        results = query.group_by(TransactionType.name).order_by(
            func.sum(func.abs(Transaction.amount)).desc()
        ).all()
        
        expense_categories = []
        total_expense = 0
        
        for result in results:
            amount = float(result.total)
            total_expense += amount
            expense_categories.append({
                'category': result.name,
                'count': result.count,
                'total': amount,
                'average': float(result.average),
                'maximum': float(result.maximum),
                'minimum': float(result.minimum)
            })
        
        # Calculate percentages
        for category in expense_categories:
            category['percentage'] = (category['total'] / total_expense * 100) if total_expense > 0 else 0
        
        return {
            'total_expense': total_expense,
            'expense_categories': expense_categories,
            'largest_category': expense_categories[0] if expense_categories else None,
            'category_count': len(expense_categories)
        }
    
    @staticmethod
    def _get_category_breakdown(account_id: int = None, start_date: date = None, 
                              end_date: date = None) -> Dict[str, Any]:
        """Get detailed category breakdown."""
        query = db.session.query(
            TransactionType.name,
            TransactionType.is_income,
            TransactionType.color,
            TransactionType.icon,
            func.count(Transaction.id).label('count'),
            func.sum(Transaction.amount).label('total')
        ).join(Transaction)
        
        if account_id:
            query = query.filter(Transaction.account_id == account_id)
        if start_date:
            query = query.filter(Transaction.date >= start_date)
        if end_date:
            query = query.filter(Transaction.date <= end_date)
        
        results = query.group_by(
            TransactionType.id, TransactionType.name, TransactionType.is_income,
            TransactionType.color, TransactionType.icon
        ).order_by(func.sum(func.abs(Transaction.amount)).desc()).all()
        
        categories = []
        for result in results:
            categories.append({
                'name': result.name,
                'is_income': result.is_income,
                'color': result.color,
                'icon': result.icon,
                'transaction_count': result.count,
                'total_amount': float(result.total),
                'absolute_amount': float(abs(result.total))
            })
        
        return {
            'categories': categories,
            'total_categories': len(categories)
        }
    
    @staticmethod
    def _get_trend_analysis(account_id: int = None, start_date: date = None, 
                          end_date: date = None) -> Dict[str, Any]:
        """Analyze trends over time."""
        # Daily trends
        daily_query = db.session.query(
            Transaction.date,
            func.sum(case((Transaction.amount > 0, Transaction.amount), else_=0)).label('daily_income'),
            func.sum(case((Transaction.amount < 0, func.abs(Transaction.amount)), else_=0)).label('daily_expense')
        )
        
        if account_id:
            daily_query = daily_query.filter(Transaction.account_id == account_id)
        if start_date:
            daily_query = daily_query.filter(Transaction.date >= start_date)
        if end_date:
            daily_query = daily_query.filter(Transaction.date <= end_date)
        
        daily_results = daily_query.group_by(Transaction.date).order_by(Transaction.date).all()
        
        daily_trends = []
        for result in daily_results:
            income = float(result.daily_income or 0)
            expense = float(result.daily_expense or 0)
            daily_trends.append({
                'date': result.date.isoformat(),
                'income': income,
                'expense': expense,
                'net': income - expense
            })
        
        # Weekly trends
        weekly_trends = AnalysisService._aggregate_by_week(daily_trends)
        
        # Monthly trends (if period is long enough)
        monthly_trends = AnalysisService._aggregate_by_month(daily_trends)
        
        return {
            'daily': daily_trends,
            'weekly': weekly_trends,
            'monthly': monthly_trends
        }
    
    @staticmethod
    def _aggregate_by_week(daily_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Aggregate daily data by week."""
        weekly_data = defaultdict(lambda: {'income': 0, 'expense': 0, 'net': 0})
        
        for day in daily_data:
            date_obj = datetime.fromisoformat(day['date']).date()
            # Get Monday of the week
            monday = date_obj - timedelta(days=date_obj.weekday())
            week_key = monday.isoformat()
            
            weekly_data[week_key]['income'] += day['income']
            weekly_data[week_key]['expense'] += day['expense']
            weekly_data[week_key]['net'] += day['net']
        
        return [
            {'week_start': week, **data}
            for week, data in sorted(weekly_data.items())
        ]
    
    @staticmethod
    def _aggregate_by_month(daily_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Aggregate daily data by month."""
        monthly_data = defaultdict(lambda: {'income': 0, 'expense': 0, 'net': 0})
        
        for day in daily_data:
            date_obj = datetime.fromisoformat(day['date']).date()
            month_key = date_obj.strftime('%Y-%m')
            
            monthly_data[month_key]['income'] += day['income']
            monthly_data[month_key]['expense'] += day['expense']
            monthly_data[month_key]['net'] += day['net']
        
        return [
            {'month': month, **data}
            for month, data in sorted(monthly_data.items())
        ]
    
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
            account_query = db.session.query(
                Account.id,
                Account.account_name,
                Account.bank_name,
                func.sum(Transaction.amount).label('total_income'),
                func.count(Transaction.id).label('transaction_count')
            ).join(Transaction).filter(
                Transaction.amount > 0
            ).group_by(
                Account.id, Account.account_name, Account.bank_name
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
    def _generate_insights(account_id: int = None, start_date: date = None, 
                         end_date: date = None) -> List[Dict[str, Any]]:
        """Generate financial insights and recommendations."""
        insights = []
        
        try:
            # Get summary data
            summary = AnalysisService._get_period_summary(account_id, start_date, end_date)
            income_analysis = AnalysisService._get_income_analysis(account_id, start_date, end_date)
            expense_analysis = AnalysisService._get_expense_analysis(account_id, start_date, end_date)
            
            # Savings rate insight
            if summary['total_income'] > 0:
                savings_rate = (summary['net_income'] / summary['total_income']) * 100
                if savings_rate > 20:
                    insights.append({
                        'type': 'positive',
                        'title': '储蓄率良好',
                        'message': f'您的储蓄率为 {savings_rate:.1f}%，这是一个很好的理财习惯！',
                        'value': savings_rate
                    })
                elif savings_rate < 0:
                    insights.append({
                        'type': 'warning',
                        'title': '支出超过收入',
                        'message': f'本期支出超过收入 {abs(savings_rate):.1f}%，建议控制支出。',
                        'value': savings_rate
                    })
                else:
                    insights.append({
                        'type': 'info',
                        'title': '储蓄率偏低',
                        'message': f'您的储蓄率为 {savings_rate:.1f}%，建议提高到20%以上。',
                        'value': savings_rate
                    })
            
            # Expense concentration insight
            if expense_analysis['expense_categories']:
                largest_category = expense_analysis['largest_category']
                if largest_category['percentage'] > 40:
                    insights.append({
                        'type': 'warning',
                        'title': '支出过于集中',
                        'message': f'{largest_category["category"]}占总支出的{largest_category["percentage"]:.1f}%，建议分散支出。',
                        'category': largest_category['category'],
                        'percentage': largest_category['percentage']
                    })
            
            # Income diversity insight
            if income_analysis['source_diversity'] == 1:
                insights.append({
                    'type': 'info',
                    'title': '收入来源单一',
                    'message': '建议考虑多元化收入来源，降低财务风险。',
                    'source_count': income_analysis['source_diversity']
                })
            elif income_analysis['source_diversity'] >= 3:
                insights.append({
                    'type': 'positive',
                    'title': '收入来源多样化',
                    'message': f'您有{income_analysis["source_diversity"]}个收入来源，财务风险较低。',
                    'source_count': income_analysis['source_diversity']
                })
            
            # Transaction frequency insight
            if summary['total_transactions'] > 0:
                period_days = (end_date - start_date).days + 1 if start_date and end_date else 30
                daily_avg = summary['total_transactions'] / period_days
                
                if daily_avg > 5:
                    insights.append({
                        'type': 'info',
                        'title': '交易频率较高',
                        'message': f'平均每天{daily_avg:.1f}笔交易，建议定期整理财务记录。',
                        'daily_average': daily_avg
                    })
            
            # Average transaction size insight
            if summary['average_transaction'] > 1000:
                insights.append({
                    'type': 'info',
                    'title': '大额交易较多',
                    'message': f'平均交易金额为¥{summary["average_transaction"]:.0f}，建议关注大额支出。',
                    'average_amount': summary['average_transaction']
                })
            
        except Exception as e:
            logger.error(f"Error generating insights: {e}")
            insights.append({
                'type': 'error',
                'title': '分析出错',
                'message': '无法生成财务洞察，请稍后重试。'
            })
        
        return insights
    
    @staticmethod
    def compare_periods(account_id: int = None, current_start: date = None, 
                       current_end: date = None, previous_start: date = None, 
                       previous_end: date = None) -> Dict[str, Any]:
        """Compare financial data between two periods."""
        try:
            current_summary = AnalysisService._get_period_summary(account_id, current_start, current_end)
            previous_summary = AnalysisService._get_period_summary(account_id, previous_start, previous_end)
            
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
            
            expense_analysis = AnalysisService._get_expense_analysis(account_id, start_date, end_date)
            
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
    
    @staticmethod
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
            
            # 使用专门的分析器进行分析
            income_expense_analyzer = IncomeExpenseAnalyzer(start_date, end_date, account_id)
            stability_analyzer = IncomeStabilityAnalyzer(start_date, end_date, account_id)
            cash_flow_analyzer = CashFlowAnalyzer(start_date, end_date, account_id)
            diversity_analyzer = IncomeDiversityAnalyzer(start_date, end_date, account_id)
            growth_analyzer = IncomeGrowthAnalyzer(start_date, end_date, account_id)
            resilience_analyzer = FinancialResilienceAnalyzer(start_date, end_date, account_id)
            
            # 构建综合分析数据结构
            comprehensive_data = ComprehensiveAnalysisData(
                income_expense_balance=income_expense_analyzer.analyze(),
                income_stability=stability_analyzer.analyze(),
                cash_flow_health=cash_flow_analyzer.analyze(),
                income_diversity=diversity_analyzer.analyze(),
                income_growth=growth_analyzer.analyze(),
                financial_resilience=resilience_analyzer.analyze()
            )
            
            # 返回字典格式以保持模板兼容性
            return comprehensive_data.to_dict()
            
        except Exception as e:
            logger.error(f"Error getting comprehensive income analysis: {e}")
            # 返回默认数据结构以防止模板错误
            return AnalysisService._get_default_analysis_data()
    
    @staticmethod
    def _get_income_expense_balance(start_date: date, end_date: date) -> Dict[str, Any]:
        """获取收入支出平衡分析"""
        try:
            # 查询收入和支出数据
            income_query = db.session.query(
                func.sum(Transaction.amount).label('total_income'),
                func.count(Transaction.id).label('income_count')
            ).filter(
                Transaction.amount > 0,
                Transaction.date >= start_date,
                Transaction.date <= end_date
            ).first()
            
            expense_query = db.session.query(
                func.sum(func.abs(Transaction.amount)).label('total_expense'),
                func.count(Transaction.id).label('expense_count')
            ).filter(
                Transaction.amount < 0,
                Transaction.date >= start_date,
                Transaction.date <= end_date
            ).first()
            
            total_income = float(income_query.total_income or 0)
            total_expense = float(expense_query.total_expense or 0)
            
            # 计算月度数据
            monthly_query = db.session.query(
                extract('year', Transaction.date).label('year'),
                extract('month', Transaction.date).label('month'),
                func.sum(case([(Transaction.amount > 0, Transaction.amount)], else_=0)).label('monthly_income'),
                func.sum(case([(Transaction.amount < 0, func.abs(Transaction.amount))], else_=0)).label('monthly_expense')
            ).filter(
                Transaction.date >= start_date,
                Transaction.date <= end_date
            ).group_by(
                extract('year', Transaction.date),
                extract('month', Transaction.date)
            ).order_by('year', 'month')
            
            monthly_results = monthly_query.all()
            monthly_data = []
            total_months = len(monthly_results) if monthly_results else 1
            
            for result in monthly_results:
                month_income = float(result.monthly_income or 0)
                month_expense = float(result.monthly_expense or 0)
                monthly_data.append({
                    'year': int(result.year),
                    'month': int(result.month),
                    'income': month_income,
                    'expense': month_expense,
                    'balance': month_income - month_expense,
                    'saving_rate': (month_income - month_expense) / month_income if month_income > 0 else 0
                })
            
            # 计算整体统计
            avg_monthly_income = total_income / total_months
            avg_monthly_expense = total_expense / total_months
            avg_monthly_saving = avg_monthly_income - avg_monthly_expense
            avg_monthly_saving_rate = avg_monthly_saving / avg_monthly_income if avg_monthly_income > 0 else 0
            avg_monthly_ratio = avg_monthly_income / avg_monthly_expense if avg_monthly_expense > 0 else 0
            
            return {
                'overall_stats': {
                    'total_income': total_income,
                    'total_expense': total_expense,
                    'net_saving': total_income - total_expense,
                    'avg_monthly_income': avg_monthly_income,
                    'avg_monthly_expense': avg_monthly_expense,
                    'avg_monthly_saving_rate': avg_monthly_saving_rate,
                    'avg_monthly_ratio': avg_monthly_ratio,
                    'avg_necessary_expense_coverage': avg_monthly_ratio  # 简化处理
                },
                'monthly_data': monthly_data
            }
            
        except Exception as e:
            logger.error(f"Error getting income expense balance: {e}")
            return {
                'overall_stats': {
                    'total_income': 0,
                    'total_expense': 0,
                    'net_saving': 0,
                    'avg_monthly_income': 0,
                    'avg_monthly_expense': 0,
                    'avg_monthly_saving_rate': 0,
                    'avg_monthly_ratio': 0,
                    'avg_necessary_expense_coverage': 0
                },
                'monthly_data': []
             }
    
    @staticmethod
    def _get_income_stability(start_date: date, end_date: date) -> Dict[str, Any]:
        """获取收入稳定性分析"""
        try:
            # 查询收入数据按类型分组
            income_by_type = db.session.query(
                TransactionType.name,
                func.sum(Transaction.amount).label('total_amount'),
                func.count(Transaction.id).label('transaction_count')
            ).join(Transaction.transaction_type).filter(
                Transaction.amount > 0,
                Transaction.date >= start_date,
                Transaction.date <= end_date
            ).group_by(TransactionType.name).all()
            
            total_income = sum(float(item.total_amount) for item in income_by_type)
            
            # 计算工资收入比例（假设包含"工资"、"薪资"等关键词的为工资收入）
            salary_keywords = ['工资', '薪资', '薪水', '月薪', 'salary']
            salary_income = 0
            for item in income_by_type:
                if any(keyword in item.name.lower() for keyword in salary_keywords):
                    salary_income += float(item.total_amount)
            
            salary_income_ratio = salary_income / total_income if total_income > 0 else 0
            
            # 计算月度收入数据
            monthly_income_query = db.session.query(
                extract('year', Transaction.date).label('year'),
                extract('month', Transaction.date).label('month'),
                func.sum(Transaction.amount).label('monthly_income')
            ).filter(
                Transaction.amount > 0,
                Transaction.date >= start_date,
                Transaction.date <= end_date
            ).group_by(
                extract('year', Transaction.date),
                extract('month', Transaction.date)
            ).order_by('year', 'month')
            
            monthly_results = monthly_income_query.all()
            monthly_income = []
            income_values = []
            
            for result in monthly_results:
                income_amount = float(result.monthly_income or 0)
                monthly_income.append({
                    'year': int(result.year),
                    'month': int(result.month),
                    'income': income_amount
                })
                income_values.append(income_amount)
            
            # 计算收入统计指标
            if income_values:
                mean_income = sum(income_values) / len(income_values)
                variance = sum((x - mean_income) ** 2 for x in income_values) / len(income_values)
                std_dev = variance ** 0.5
                coefficient_of_variation = std_dev / mean_income if mean_income > 0 else 0
            else:
                mean_income = 0
                coefficient_of_variation = 0
            
            # 计算最长无收入期间（简化处理）
            max_no_income_period = {
                'days': 0,
                'start': '',
                'end': ''
            }
            
            return {
                'salary_income_ratio': salary_income_ratio,
                'income_stats': {
                    'mean_income': mean_income,
                    'coefficient_of_variation': coefficient_of_variation
                },
                'max_no_income_period': max_no_income_period,
                'monthly_income': monthly_income
            }
            
        except Exception as e:
            logger.error(f"Error getting income stability: {e}")
            return {
                'salary_income_ratio': 0,
                'income_stats': {
                    'mean_income': 0,
                    'coefficient_of_variation': 0
                },
                'max_no_income_period': {
                    'days': 0,
                    'start': '',
                    'end': ''
                },
                'monthly_income': []
             }
    
    @staticmethod
    def _get_cash_flow_health(start_date: date, end_date: date) -> Dict[str, Any]:
        """获取现金流健康分析"""
        try:
            # 获取账户总余额
            total_balance_query = db.session.query(
                func.sum(Account.balance).label('total_balance')
            ).first()
            
            total_balance = float(total_balance_query.total_balance or 0)
            
            # 计算月度现金流
            monthly_cashflow_query = db.session.query(
                extract('year', Transaction.date).label('year'),
                extract('month', Transaction.date).label('month'),
                func.sum(case([(Transaction.amount > 0, Transaction.amount)], else_=0)).label('monthly_income'),
                func.sum(case([(Transaction.amount < 0, func.abs(Transaction.amount))], else_=0)).label('monthly_expense')
            ).filter(
                Transaction.date >= start_date,
                Transaction.date <= end_date
            ).group_by(
                extract('year', Transaction.date),
                extract('month', Transaction.date)
            ).order_by('year', 'month')
            
            monthly_results = monthly_cashflow_query.all()
            monthly_cash_flow = []
            monthly_expenses = []
            gap_months = 0
            total_gaps = 0
            
            for result in monthly_results:
                month_income = float(result.monthly_income or 0)
                month_expense = float(result.monthly_expense or 0)
                cash_flow = month_income - month_expense
                
                monthly_cash_flow.append({
                    'year': int(result.year),
                    'month': int(result.month),
                    'income': month_income,
                    'expense': month_expense,
                    'cash_flow': cash_flow
                })
                
                monthly_expenses.append(month_expense)
                
                # 统计现金流缺口
                if cash_flow < 0:
                    gap_months += 1
                    total_gaps += abs(cash_flow)
            
            # 计算应急基金月数（基于平均月支出）
            avg_monthly_expense = sum(monthly_expenses) / len(monthly_expenses) if monthly_expenses else 1
            emergency_fund_months = total_balance / avg_monthly_expense if avg_monthly_expense > 0 else 0
            
            # 计算缺口频率
            total_months = len(monthly_results) if monthly_results else 1
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
            
        except Exception as e:
            logger.error(f"Error getting cash flow health: {e}")
            return {
                'emergency_fund_months': 0,
                'gap_frequency': 0,
                'avg_gap': 0,
                'total_balance': 0,
                'monthly_cash_flow': []
             }
    
    @staticmethod
    def _get_income_diversity(start_date: date, end_date: date) -> Dict[str, Any]:
        """获取收入多样性分析"""
        try:
            # 按收入类型分组统计
            income_sources_query = db.session.query(
                TransactionType.name,
                func.sum(Transaction.amount).label('total_amount'),
                func.count(Transaction.id).label('transaction_count')
            ).join(Transaction.transaction_type).filter(
                Transaction.amount > 0,
                Transaction.date >= start_date,
                Transaction.date <= end_date
            ).group_by(TransactionType.name).all()
            
            sources = []
            total_income = 0
            passive_income_keywords = ['利息', '分红', '投资', '理财', '租金', 'dividend', 'interest']
            passive_income = 0
            
            for source in income_sources_query:
                amount = float(source.total_amount)
                total_income += amount
                
                # 判断是否为被动收入
                is_passive = any(keyword in source.name.lower() for keyword in passive_income_keywords)
                if is_passive:
                    passive_income += amount
                
                sources.append({
                    'name': source.name,
                    'amount': amount,
                    'count': source.transaction_count,
                    'is_passive': is_passive
                })
            
            # 计算收入来源数量
            source_count = len(sources)
            
            # 计算收入集中度（最大收入来源占比）
            if sources:
                max_source_amount = max(source['amount'] for source in sources)
                concentration = max_source_amount / total_income if total_income > 0 else 0
            else:
                concentration = 0
            
            # 计算被动收入比例
            passive_income_ratio = passive_income / total_income if total_income > 0 else 0
            
            # 计算月度收入来源分布
            monthly_sources_query = db.session.query(
                extract('year', Transaction.date).label('year'),
                extract('month', Transaction.date).label('month'),
                TransactionType.name,
                func.sum(Transaction.amount).label('monthly_amount')
            ).join(Transaction.transaction_type).filter(
                Transaction.amount > 0,
                Transaction.date >= start_date,
                Transaction.date <= end_date
            ).group_by(
                extract('year', Transaction.date),
                extract('month', Transaction.date),
                TransactionType.name
            ).order_by('year', 'month')
            
            monthly_sources_results = monthly_sources_query.all()
            monthly_sources = defaultdict(lambda: defaultdict(float))
            
            for result in monthly_sources_results:
                year_month = f"{int(result.year)}-{int(result.month):02d}"
                monthly_sources[year_month][result.name] = float(result.monthly_amount)
            
            # 转换为列表格式
            monthly_sources_list = []
            for year_month, sources_data in sorted(monthly_sources.items()):
                monthly_sources_list.append({
                    'period': year_month,
                    'sources': dict(sources_data)
                })
            
            return {
                'source_count': source_count,
                'concentration': concentration,
                'passive_income_ratio': passive_income_ratio,
                'sources': sources,
                'monthly_sources': monthly_sources_list
            }
            
        except Exception as e:
            logger.error(f"Error getting income diversity: {e}")
            return {
                'source_count': 0,
                'concentration': 0,
                'passive_income_ratio': 0,
                'sources': [],
                'monthly_sources': []
             }
    
    @staticmethod
    def _get_income_growth(start_date: date, end_date: date) -> Dict[str, Any]:
        """获取收入增长分析"""
        try:
            # 按年度统计收入
            yearly_income_query = db.session.query(
                extract('year', Transaction.date).label('year'),
                func.sum(Transaction.amount).label('yearly_income')
            ).filter(
                Transaction.amount > 0,
                Transaction.date >= start_date,
                Transaction.date <= end_date
            ).group_by(extract('year', Transaction.date)).order_by('year')
            
            yearly_results = yearly_income_query.all()
            yearly_income = []
            
            for result in yearly_results:
                yearly_income.append({
                    'year': int(result.year),
                    'income': float(result.yearly_income or 0)
                })
            
            # 计算年度增长率
            annual_growth_rate = 0
            if len(yearly_income) >= 2:
                first_year_income = yearly_income[0]['income']
                last_year_income = yearly_income[-1]['income']
                years_span = yearly_income[-1]['year'] - yearly_income[0]['year']
                if first_year_income > 0 and years_span > 0:
                    annual_growth_rate = ((last_year_income / first_year_income) ** (1/years_span)) - 1
            
            # 找出收入最高的月份
            monthly_income_query = db.session.query(
                extract('year', Transaction.date).label('year'),
                extract('month', Transaction.date).label('month'),
                func.sum(Transaction.amount).label('monthly_income')
            ).filter(
                Transaction.amount > 0,
                Transaction.date >= start_date,
                Transaction.date <= end_date
            ).group_by(
                extract('year', Transaction.date),
                extract('month', Transaction.date)
            ).order_by(func.sum(Transaction.amount).desc())
            
            peak_month_result = monthly_income_query.first()
            peak_month = '未知'
            if peak_month_result:
                peak_month = f"{int(peak_month_result.year)}-{int(peak_month_result.month):02d}"
            
            # 计算预计年度增长金额
            projected_annual_increase = 0
            if len(yearly_income) >= 2:
                recent_income = yearly_income[-1]['income']
                projected_annual_increase = recent_income * annual_growth_rate
            
            # 收入与通胀对比（简化处理，假设通胀率3%）
            inflation_rate = 0.03
            income_vs_inflation = []
            for year_data in yearly_income:
                real_growth = annual_growth_rate - inflation_rate
                income_vs_inflation.append({
                    'year': year_data['year'],
                    'nominal_income': year_data['income'],
                    'real_growth': real_growth,
                    'inflation_adjusted': year_data['income'] / ((1 + inflation_rate) ** (year_data['year'] - yearly_income[0]['year'])) if yearly_income else year_data['income']
                })
            
            return {
                'annual_growth_rate': annual_growth_rate,
                'peak_month': peak_month,
                'projected_annual_increase': projected_annual_increase,
                'yearly_income': yearly_income,
                'income_vs_inflation': income_vs_inflation
            }
            
        except Exception as e:
            logger.error(f"Error getting income growth: {e}")
            return {
                'annual_growth_rate': 0,
                'peak_month': '未知',
                'projected_annual_increase': 0,
                'yearly_income': [],
                 'income_vs_inflation': []
             }
    
    @staticmethod
    def _get_financial_resilience(start_date: date, end_date: date) -> Dict[str, Any]:
        """获取财务韧性分析"""
        try:
            # 获取所有账户余额
            accounts = Account.query.all()
            total_balance = sum(account.balance for account in accounts)
            
            # 计算月平均支出
            monthly_expense_query = db.session.query(
                func.avg(func.abs(Transaction.amount)).label('avg_expense')
            ).filter(
                Transaction.amount < 0,
                Transaction.date >= start_date,
                Transaction.date <= end_date
            )
            
            avg_monthly_expense = monthly_expense_query.scalar() or 0
            
            # 计算应急基金月数
            emergency_fund_months = 0
            if avg_monthly_expense > 0:
                emergency_fund_months = total_balance / avg_monthly_expense
            
            # 计算收入稳定性（收入变异系数）
            monthly_income_query = db.session.query(
                extract('year', Transaction.date).label('year'),
                extract('month', Transaction.date).label('month'),
                func.sum(Transaction.amount).label('monthly_income')
            ).filter(
                Transaction.amount > 0,
                Transaction.date >= start_date,
                Transaction.date <= end_date
            ).group_by(
                extract('year', Transaction.date),
                extract('month', Transaction.date)
            )
            
            monthly_incomes = [float(result.monthly_income or 0) for result in monthly_income_query.all()]
            
            income_stability_score = 0
            if len(monthly_incomes) > 1:
                mean_income = sum(monthly_incomes) / len(monthly_incomes)
                if mean_income > 0:
                    variance = sum((x - mean_income) ** 2 for x in monthly_incomes) / len(monthly_incomes)
                    std_dev = variance ** 0.5
                    coefficient_of_variation = std_dev / mean_income
                    # 稳定性评分：变异系数越小，稳定性越高
                    income_stability_score = max(0, 1 - coefficient_of_variation)
            
            # 计算债务收入比（简化处理，假设负余额账户为债务）
            debt_accounts = [account for account in accounts if account.balance < 0]
            total_debt = sum(abs(account.balance) for account in debt_accounts)
            
            # 计算月平均收入
            avg_monthly_income = sum(monthly_incomes) / len(monthly_incomes) if monthly_incomes else 0
            
            debt_to_income_ratio = 0
            if avg_monthly_income > 0:
                debt_to_income_ratio = total_debt / avg_monthly_income
            
            # 计算流动性比率（现金及现金等价物/月支出）
            cash_accounts = [account for account in accounts if account.account_type in ['现金', '储蓄', '支票']]
            liquid_assets = sum(account.balance for account in cash_accounts if account.balance > 0)
            
            liquidity_ratio = 0
            if avg_monthly_expense > 0:
                liquidity_ratio = liquid_assets / avg_monthly_expense
            
            # 风险承受能力评估
            risk_tolerance = 'low'
            if emergency_fund_months >= 6 and income_stability_score >= 0.7 and debt_to_income_ratio <= 0.3:
                risk_tolerance = 'high'
            elif emergency_fund_months >= 3 and income_stability_score >= 0.5 and debt_to_income_ratio <= 0.5:
                risk_tolerance = 'medium'
            
            # 财务健康度评分（0-100）
            health_score = 0
            # 应急基金权重30%
            emergency_score = min(100, (emergency_fund_months / 6) * 30)
            # 收入稳定性权重25%
            stability_score = income_stability_score * 25
            # 债务比率权重25%（债务越少分数越高）
            debt_score = max(0, (1 - min(1, debt_to_income_ratio)) * 25)
            # 流动性权重20%
            liquidity_score = min(20, (liquidity_ratio / 3) * 20)
            
            health_score = emergency_score + stability_score + debt_score + liquidity_score
            
            return {
                'emergency_fund_months': emergency_fund_months,
                'income_stability_score': income_stability_score,
                'debt_to_income_ratio': debt_to_income_ratio,
                'liquidity_ratio': liquidity_ratio,
                'risk_tolerance': risk_tolerance,
                'financial_health_score': health_score,
                'total_balance': total_balance,
                'total_debt': total_debt,
                'liquid_assets': liquid_assets
            }
            
        except Exception as e:
            logger.error(f"Error getting financial resilience: {e}")
            return {
                'emergency_fund_months': 0,
                'income_stability_score': 0,
                'debt_to_income_ratio': 0,
                'liquidity_ratio': 0,
                'risk_tolerance': 'low',
                'financial_health_score': 0,
                'total_balance': 0,
                'total_debt': 0,
                'liquid_assets': 0
            }
    
    @staticmethod
    def _get_default_analysis_data() -> Dict[str, Any]:
        """获取默认分析数据结构，使用新的数据模型"""
        # 使用新的数据模型创建默认结构
        default_data = ComprehensiveAnalysisData()
        return default_data.to_dict()