"""Statistics service for handling database statistics and reporting.

This module provides statistical analysis functionality including balance summaries,
historical data, and database metrics.
"""

from typing import List, Dict, Any
from decimal import Decimal
from datetime import datetime, timedelta
import logging

from app.models import Bank, Account, Transaction, db
from sqlalchemy import func
from dateutil.relativedelta import relativedelta

logger = logging.getLogger(__name__)

class StatisticsService:
    """Service for handling statistics and reporting operations."""

    @staticmethod
    def get_database_stats() -> Dict[str, Any]:
        """Get database statistics."""
        try:
            stats = {
                'banks_count': Bank.query.count(),
                'active_banks_count': Bank.query.filter_by(is_active=True).count(),
                'accounts_count': Account.query.count(),
                'active_accounts_count': Account.query.filter_by(is_active=True).count(),
                'transactions_count': Transaction.query.count(),
                'income_transactions_count': Transaction.query.filter(Transaction.amount > 0).count(),
                'expense_transactions_count': Transaction.query.filter(Transaction.amount < 0).count(),
            }
            return stats
        except Exception as e:
            logger.error(f"Error getting database stats: {e}")
            return {}

    @staticmethod
    def get_balance_range() -> Dict[str, Any]:
        """Get balance range (min and max) across all accounts."""
        try:
            accounts = Account.query.filter_by(is_active=True).all()
            if not accounts:
                return {'min_balance': 0, 'max_balance': 0, 'range': 0}
            
            balances = [float(account.get_current_balance()) for account in accounts]
            min_balance = min(balances)
            max_balance = max(balances)
            
            return {
                'min_balance': min_balance,
                'max_balance': max_balance,
                'range': max_balance - min_balance
            }
            
        except Exception as e:
            logger.error(f"Error getting balance range: {e}")
            return {'min_balance': 0, 'max_balance': 0, 'range': 0}

    @staticmethod
    def get_monthly_balance_history(months: int = 12) -> List[Dict[str, Any]]:
        """Get monthly balance history for the specified number of months."""
        try:
            # Calculate start date
            end_date = datetime.now().date()
            start_date = end_date - relativedelta(months=months-1)
            start_date = start_date.replace(day=1)  # First day of the month
            
            # Get all active accounts
            accounts = Account.query.filter_by(is_active=True).all()
            if not accounts:
                return []
            
            history = []
            current_date = start_date
            
            while current_date <= end_date:
                month_end = (current_date + relativedelta(months=1)) - timedelta(days=1)
                if month_end > end_date:
                    month_end = end_date
                
                total_balance = Decimal('0')
                for account in accounts:
                    # Calculate balance at the end of this month
                    # Get opening balance + sum of transactions up to month_end
                    transactions_sum = db.session.query(func.sum(Transaction.amount)).filter(
                        Transaction.account_id == account.id,
                        Transaction.date <= month_end
                    ).scalar() or Decimal('0')
                    
                    balance = account.opening_balance + transactions_sum
                    total_balance += balance
                
                history.append({
                    'year': current_date.year,
                    'month': current_date.month,
                    'date': current_date.strftime('%Y-%m'),
                    'balance': float(total_balance)
                })
                
                current_date = current_date + relativedelta(months=1)
            
            return history
            
        except Exception as e:
            logger.error(f"Error getting monthly balance history: {e}")
            return []

    @staticmethod
    def get_balance_summary() -> Dict[str, Any]:
        """Get balance summary for all accounts."""
        try:
            accounts = Account.query.filter_by(is_active=True).all()
            summary = {
                'total_accounts': len(accounts),
                'total_balance': Decimal('0'),
                'accounts': [],
                'by_bank': {},
                'by_currency': {}
            }
            
            for account in accounts:
                current_balance = account.get_current_balance()
                account_info = {
                    'id': account.id,
                    'name': account.account_name,
                    'number': account.account_number,
                    'bank_name': account.bank.name if account.bank else 'Unknown',
                    'currency': account.currency,
                    'balance': float(current_balance),
                    'account_type': account.account_type
                }
                
                summary['accounts'].append(account_info)
                summary['total_balance'] += current_balance
                
                # Group by bank
                bank_name = account.bank.name if account.bank else 'Unknown'
                if bank_name not in summary['by_bank']:
                    summary['by_bank'][bank_name] = {'count': 0, 'balance': Decimal('0')}
                summary['by_bank'][bank_name]['count'] += 1
                summary['by_bank'][bank_name]['balance'] += current_balance
                
                # Group by currency
                if account.currency not in summary['by_currency']:
                    summary['by_currency'][account.currency] = {'count': 0, 'balance': Decimal('0')}
                summary['by_currency'][account.currency]['count'] += 1
                summary['by_currency'][account.currency]['balance'] += current_balance
            
            # Convert Decimal to float for JSON serialization
            summary['total_balance'] = float(summary['total_balance'])
            for bank_data in summary['by_bank'].values():
                bank_data['balance'] = float(bank_data['balance'])
            for currency_data in summary['by_currency'].values():
                currency_data['balance'] = float(currency_data['balance'])
            
            return summary
            
        except Exception as e:
            logger.error(f"Error getting balance summary: {e}")
            return {
                'total_accounts': 0,
                'total_balance': 0,
                'accounts': [],
                'by_bank': {},
                'by_currency': {}
            }