"""Database service for the Flask application.

This module provides database operations and management functionality.
"""

from flask import current_app
from app.models import db, Bank, Account, Transaction
from sqlalchemy.exc import SQLAlchemyError
from typing import List, Dict, Any, Optional, Tuple
from decimal import Decimal
from datetime import date, datetime
import logging

logger = logging.getLogger(__name__)

class DatabaseService:
    """Database service for managing all database operations."""
    
    @staticmethod
    def init_database():
        """Initialize database with tables and default data."""
        try:
            # 创建所有表
            db.create_all()
            logger.info("Database tables created successfully")
            
            # 创建默认银行（如果需要）
            DatabaseService._create_default_banks()
            
            return True
            
        except SQLAlchemyError as e:
            logger.error(f"Database initialization error: {e}")
            db.session.rollback()
            return False
        except Exception as e:
            logger.error(f"Unexpected error during database initialization: {e}")
            db.session.rollback()
            return False
    
    @staticmethod
    def _create_default_banks():
        """Create some common default banks."""
        default_banks = [
            {'name': '招商银行', 'code': 'CMB'},
            {'name': '建设银行', 'code': 'CCB'},
        ]
        
        created_count = 0
        for bank_data in default_banks:
            if not Bank.get_by_name(bank_data['name']):
                Bank.create(**bank_data)
                created_count += 1
        
        if created_count > 0:
            logger.info(f"Created {created_count} default banks")
    
    # Bank operations
    @staticmethod
    def get_or_create_bank(name: str, code: str = None, country: str = 'CN') -> Bank:
        """Get existing bank or create new one."""
        try:
            return Bank.get_or_create(name=name, code=code, country=country)
        except Exception as e:
            logger.error(f"Error getting or creating bank '{name}': {e}")
            raise
    
    @staticmethod
    def get_all_banks(active_only: bool = True) -> List[Bank]:
        """Get all banks."""
        if active_only:
            return Bank.get_active_banks()
        return Bank.get_all()
    
    @staticmethod
    def update_bank(bank_id: int, **kwargs) -> bool:
        """Update bank information."""
        try:
            bank = Bank.get_by_id(bank_id)
            if bank:
                bank.update(**kwargs)
                return True
            return False
        except Exception as e:
            logger.error(f"Error updating bank {bank_id}: {e}")
            raise
    
    @staticmethod
    def delete_bank(bank_id: int, soft_delete: bool = True) -> bool:
        """Delete bank (soft delete by default)."""
        try:
            bank = Bank.get_by_id(bank_id)
            if bank:
                if soft_delete:
                    bank.deactivate()
                else:
                    bank.delete()
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting bank {bank_id}: {e}")
            raise
    
    # Account operations
    @staticmethod
    def get_or_create_account(bank_id: int, account_number: str, account_name: str = None, 
                            currency: str = 'CNY', account_type: str = 'checking') -> Account:
        """Get existing account or create new one."""
        try:
            return Account.get_or_create(
                bank_id=bank_id,
                account_number=account_number,
                account_name=account_name,
                currency=currency,
                account_type=account_type
            )
        except Exception as e:
            logger.error(f"Error getting or creating account '{account_number}': {e}")
            raise
    
    @staticmethod
    def get_all_accounts(active_only: bool = True) -> List[Account]:
        """Get all accounts."""
        if active_only:
            return Account.get_active_accounts()
        return Account.get_all()
    
    @staticmethod
    def update_account(account_id: int, **kwargs) -> bool:
        """Update account information."""
        try:
            account = Account.get_by_id(account_id)
            if account:
                account.update(**kwargs)
                return True
            return False
        except Exception as e:
            logger.error(f"Error updating account {account_id}: {e}")
            raise
    
    @staticmethod
    def delete_account(account_id: int, soft_delete: bool = True) -> bool:
        """Delete account (soft delete by default)."""
        try:
            account = Account.get_by_id(account_id)
            if account:
                if soft_delete:
                    account.deactivate()
                else:
                    account.delete()
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting account {account_id}: {e}")
            raise
    
    @staticmethod
    def get_all_currencies() -> List[str]:
        """Get all distinct currencies from transactions and accounts."""
        try:
            # Get currencies from transactions
            transaction_currencies = db.session.query(Transaction.currency).distinct().all()
            # Get currencies from accounts
            account_currencies = db.session.query(Account.currency).distinct().all()
            
            # Combine and deduplicate
            all_currencies = set()
            for (currency,) in transaction_currencies:
                if currency:
                    all_currencies.add(currency)
            for (currency,) in account_currencies:
                if currency:
                    all_currencies.add(currency)
            
            # Convert to sorted list
            return sorted(list(all_currencies))
            
        except Exception as e:
            logger.error(f"Error getting all currencies: {e}")
            # Return default currency if error occurs
            return ['CNY']
    
    @staticmethod
    def get_all_transaction_types() -> List[str]:
        """Get all distinct transaction types from transactions."""
        try:
            # Get transaction types from transactions
            transaction_types = db.session.query(Transaction.transaction_type).distinct().all()
            
            # Filter out None and empty values, then convert to set for deduplication
            all_types = set()
            for (transaction_type,) in transaction_types:
                if transaction_type and transaction_type.strip():
                    all_types.add(transaction_type.strip())
            
            # Convert to sorted list
            return sorted(list(all_types))
            
        except Exception as e:
            logger.error(f"Error getting all transaction types: {e}")
            # Return empty list if error occurs
            return []
    
    # Transaction operations
    @staticmethod
    def create_transaction(account_id: int, transaction_type_id: int, date: date, 
                         amount: Decimal, currency: str = 'CNY', description: str = None,
                         counterparty: str = None, notes: str = None, 
                         original_description: str = None, **kwargs) -> Transaction:
        """Create a new transaction."""
        try:
            return Transaction.create(
                account_id=account_id,
                transaction_type_id=transaction_type_id,
                date=date,
                amount=amount,
                currency=currency,
                description=description,
                counterparty=counterparty,
                notes=notes,
                original_description=original_description,
                **kwargs
            )
        except Exception as e:
            logger.error(f"Error creating transaction: {e}")
            raise
    
    @staticmethod
    def get_transactions(account_id: int = None, start_date: date = None, 
                        end_date: date = None, transaction_type_id: int = None,
                        limit: int = None, offset: int = None) -> List[Transaction]:
        """Get transactions with filtering options."""
        if account_id:
            return Transaction.get_by_account(
                account_id=account_id,
                start_date=start_date,
                end_date=end_date,
                limit=limit,
                offset=offset
            )
        
        query = Transaction.query
        
        if start_date:
            query = query.filter(Transaction.date >= start_date)
        if end_date:
            query = query.filter(Transaction.date <= end_date)
        if transaction_type_id:
            query = query.filter_by(transaction_type_id=transaction_type_id)
        
        query = query.order_by(Transaction.date.desc(), Transaction.created_at.desc())
        
        if offset:
            query = query.offset(offset)
        if limit:
            query = query.limit(limit)
        
        return query.all()
    
    @staticmethod
    def search_transactions(keyword: str, account_id: int = None, 
                          start_date: date = None, end_date: date = None) -> List[Transaction]:
        """Search transactions by keyword."""
        return Transaction.search(
            keyword=keyword,
            account_id=account_id,
            start_date=start_date,
            end_date=end_date
        )
    
    @staticmethod
    def update_transaction(transaction_id: int, **kwargs) -> bool:
        """Update transaction information."""
        try:
            transaction = Transaction.get_by_id(transaction_id)
            if transaction:
                transaction.update(**kwargs)
                return True
            return False
        except Exception as e:
            logger.error(f"Error updating transaction {transaction_id}: {e}")
            raise
    
    @staticmethod
    def delete_transaction(transaction_id: int) -> bool:
        """Delete transaction."""
        try:
            transaction = Transaction.get_by_id(transaction_id)
            if transaction:
                transaction.delete()
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting transaction {transaction_id}: {e}")
            raise
    
    # Utility methods
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
            from datetime import datetime, timedelta
            from dateutil.relativedelta import relativedelta
            from sqlalchemy import func, extract
            
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