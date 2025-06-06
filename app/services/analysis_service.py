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
from sqlalchemy import func, and_, or_, extract
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
            func.sum(func.case([(Transaction.amount > 0, Transaction.amount)], else_=0)).label('daily_income'),
            func.sum(func.case([(Transaction.amount < 0, func.abs(Transaction.amount))], else_=0)).label('daily_expense')
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