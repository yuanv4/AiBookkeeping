"""Database service for the Flask application.

This module provides database operations and management functionality.
"""

from flask import current_app
from app.models import db, Bank, Account, TransactionType, Transaction
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
            
            # 创建默认交易类型
            created_count = TransactionType.create_default_types()
            if created_count > 0:
                logger.info(f"Created {created_count} default transaction types")
            
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
            {'name': '工商银行', 'code': 'ICBC'},
            {'name': '农业银行', 'code': 'ABC'},
            {'name': '中国银行', 'code': 'BOC'},
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
    def get_bank_by_id(bank_id: int) -> Optional[Bank]:
        """Get bank by ID."""
        return Bank.get_by_id(bank_id)
    
    @staticmethod
    def get_bank_by_name(name: str) -> Optional[Bank]:
        """Get bank by name."""
        return Bank.get_by_name(name)
    
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
    def get_account_by_id(account_id: int) -> Optional[Account]:
        """Get account by ID."""
        return Account.get_by_id(account_id)
    
    @staticmethod
    def get_accounts_by_bank_id(bank_id: int) -> List[Account]:
        """Get all accounts for a specific bank."""
        return Account.get_by_bank_id(bank_id)
    
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
    
    # Transaction Type operations
    @staticmethod
    def get_or_create_transaction_type(name: str, is_income: bool = False, 
                                     description: str = None, color: str = None, 
                                     icon: str = None) -> TransactionType:
        """Get existing transaction type or create new one."""
        try:
            return TransactionType.get_or_create(
                name=name,
                is_income=is_income,
                description=description,
                color=color,
                icon=icon
            )
        except Exception as e:
            logger.error(f"Error getting or creating transaction type '{name}': {e}")
            raise
    
    @staticmethod
    def get_transaction_type_by_id(type_id: int) -> Optional[TransactionType]:
        """Get transaction type by ID."""
        return TransactionType.get_by_id(type_id)
    
    @staticmethod
    def get_transaction_type_by_name(name: str) -> Optional[TransactionType]:
        """Get transaction type by name."""
        return TransactionType.get_by_name(name)
    
    @staticmethod
    def get_all_transaction_types(active_only: bool = True, is_income: bool = None) -> List[TransactionType]:
        """Get all transaction types."""
        if active_only:
            return TransactionType.get_active_types(is_income=is_income)
        return TransactionType.get_all()
    
    @staticmethod
    def get_income_types() -> List[TransactionType]:
        """Get all income transaction types."""
        return TransactionType.get_income_types()
    
    @staticmethod
    def get_expense_types() -> List[TransactionType]:
        """Get all expense transaction types."""
        return TransactionType.get_expense_types()
    
    @staticmethod
    def update_transaction_type(type_id: int, **kwargs) -> bool:
        """Update transaction type information."""
        try:
            transaction_type = TransactionType.get_by_id(type_id)
            if transaction_type:
                transaction_type.update(**kwargs)
                return True
            return False
        except Exception as e:
            logger.error(f"Error updating transaction type {type_id}: {e}")
            raise
    
    @staticmethod
    def delete_transaction_type(type_id: int, soft_delete: bool = True) -> bool:
        """Delete transaction type (soft delete by default)."""
        try:
            transaction_type = TransactionType.get_by_id(type_id)
            if transaction_type:
                if soft_delete:
                    transaction_type.deactivate()
                else:
                    transaction_type.delete()
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting transaction type {type_id}: {e}")
            raise
    
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
    def import_transactions(transactions_data: List[Dict[str, Any]]) -> Tuple[int, int]:
        """Import multiple transactions.
        
        Returns:
            Tuple of (successful_imports, failed_imports)
        """
        successful = 0
        failed = 0
        
        for transaction_data in transactions_data:
            try:
                DatabaseService.create_transaction(**transaction_data)
                successful += 1
            except Exception as e:
                logger.error(f"Failed to import transaction: {transaction_data}, error: {e}")
                failed += 1
        
        logger.info(f"Transaction import completed: {successful} successful, {failed} failed")
        return successful, failed
    
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
    def get_transaction_by_id(transaction_id: int) -> Optional[Transaction]:
        """Get transaction by ID."""
        return Transaction.get_by_id(transaction_id)
    
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
                'transaction_types_count': TransactionType.query.count(),
                'active_transaction_types_count': TransactionType.query.filter_by(is_active=True).count(),
                'transactions_count': Transaction.query.count(),
                'income_transactions_count': Transaction.query.filter(Transaction.amount > 0).count(),
                'expense_transactions_count': Transaction.query.filter(Transaction.amount < 0).count(),
            }
            return stats
        except Exception as e:
            logger.error(f"Error getting database stats: {e}")
            return {}
    
    @staticmethod
    def backup_database(backup_path: str) -> bool:
        """Backup database (implementation depends on database type)."""
        # This would be implemented based on the specific database being used
        # For SQLite, we could copy the file
        # For PostgreSQL/MySQL, we could use pg_dump/mysqldump
        logger.warning("Database backup not implemented yet")
        return False
    
    @staticmethod
    def restore_database(backup_path: str) -> bool:
        """Restore database from backup."""
        # This would be implemented based on the specific database being used
        logger.warning("Database restore not implemented yet")
        return False