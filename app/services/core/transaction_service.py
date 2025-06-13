"""Transaction service for handling transaction-related business logic.

This module provides transaction processing, validation, and analysis functionality.
"""

from typing import List, Dict, Any, Optional, Tuple
from decimal import Decimal
from datetime import date, datetime
import logging
from collections import defaultdict

from app.models import Transaction, Account, db

from sqlalchemy import func, and_

logger = logging.getLogger(__name__)

class TransactionService:
    """Service for handling transaction operations and business logic."""

    @staticmethod
    def get_transactions_with_filters(filters: Dict[str, Any] = None, 
                                    limit: int = None, offset: int = None) -> List[Transaction]:
        """Get transactions with complex filtering options."""
        try:
            from app.models import Account, Bank
            
            query = db.session.query(Transaction).join(Account)
            
            if filters:
                # Account number filter
                if 'account_number' in filters and filters['account_number']:
                    query = query.filter(Account.account_number.like(f"%{filters['account_number']}%"))
                
                # Account name filter
                if 'account_name' in filters and filters['account_name']:
                    query = query.filter(Account.account_name.like(f"%{filters['account_name']}%"))
                
                # Date range filters
                if 'start_date' in filters and filters['start_date']:
                    start_date = datetime.strptime(filters['start_date'], '%Y-%m-%d').date()
                    query = query.filter(Transaction.date >= start_date)
                
                if 'end_date' in filters and filters['end_date']:
                    end_date = datetime.strptime(filters['end_date'], '%Y-%m-%d').date()
                    query = query.filter(Transaction.date <= end_date)
                
                # Amount range filters
                if 'min_amount' in filters and filters['min_amount'] is not None:
                    query = query.filter(Transaction.amount >= filters['min_amount'])
                
                if 'max_amount' in filters and filters['max_amount'] is not None:
                    query = query.filter(Transaction.amount <= filters['max_amount'])
                
                # Transaction type filter
                if 'transaction_type' in filters and filters['transaction_type']:
                    filter_type = filters['transaction_type']
                    if filter_type == 'income':
                        query = query.filter(Transaction.amount > 0)
                    elif filter_type == 'expense':
                        query = query.filter(Transaction.amount < 0)
                    elif filter_type == 'transfer':
                        query = query.filter(Transaction.amount == 0)
                
                # Counterparty filter
                if 'counterparty' in filters and filters['counterparty']:
                    query = query.filter(Transaction.counterparty.like(f"%{filters['counterparty']}%"))
                
                # Currency filter
                if 'currency' in filters and filters['currency']:
                    query = query.filter(Transaction.currency == filters['currency'])
            
            # Order by date descending
            query = query.order_by(Transaction.date.desc(), Transaction.created_at.desc())
            
            # Apply pagination
            if offset:
                query = query.offset(offset)
            if limit:
                query = query.limit(limit)
            
            return query.all()
            
        except Exception as e:
            logger.error(f"Error getting transactions with filters: {e}")
            return []
    
    @staticmethod
    def count_transactions_with_filters(filters: Dict[str, Any] = None) -> int:
        """Count transactions with filtering options."""
        try:
            from app.models import Account, Bank
            
            query = db.session.query(func.count(Transaction.id)).join(Account)
            
            if filters:
                # Account number filter
                if 'account_number' in filters and filters['account_number']:
                    query = query.filter(Account.account_number.like(f"%{filters['account_number']}%"))
                
                # Account name filter
                if 'account_name' in filters and filters['account_name']:
                    query = query.filter(Account.account_name.like(f"%{filters['account_name']}%"))
                
                # Date range filters
                if 'start_date' in filters and filters['start_date']:
                    start_date = datetime.strptime(filters['start_date'], '%Y-%m-%d').date()
                    query = query.filter(Transaction.date >= start_date)
                
                if 'end_date' in filters and filters['end_date']:
                    end_date = datetime.strptime(filters['end_date'], '%Y-%m-%d').date()
                    query = query.filter(Transaction.date <= end_date)
                
                # Amount range filters
                if 'min_amount' in filters and filters['min_amount'] is not None:
                    query = query.filter(Transaction.amount >= filters['min_amount'])
                
                if 'max_amount' in filters and filters['max_amount'] is not None:
                    query = query.filter(Transaction.amount <= filters['max_amount'])
                
                # Transaction type filter
                if 'transaction_type' in filters and filters['transaction_type']:
                    filter_type = filters['transaction_type']
                    if filter_type == 'income':
                        query = query.filter(Transaction.amount > 0)
                    elif filter_type == 'expense':
                        query = query.filter(Transaction.amount < 0)
                    elif filter_type == 'transfer':
                        query = query.filter(Transaction.amount == 0)
                
                # Counterparty filter
                if 'counterparty' in filters and filters['counterparty']:
                    query = query.filter(Transaction.counterparty.like(f"%{filters['counterparty']}%"))
                
                # Currency filter
                if 'currency' in filters and filters['currency']:
                    query = query.filter(Transaction.currency == filters['currency'])
            
            return query.scalar() or 0
            
        except Exception as e:
            logger.error(f"Error counting transactions with filters: {e}")
            return 0
    
    @staticmethod
    def is_duplicate_transaction(transaction_data: Dict[str, Any]) -> bool:
        """Check if transaction is a duplicate."""
        try:
            existing = Transaction.query.filter(
                and_(
                    Transaction.account_id == transaction_data.get('account_id'),
                    Transaction.date == transaction_data.get('date'),
                    Transaction.amount == transaction_data.get('amount'),
                    Transaction.balance_after == transaction_data.get('balance_after')
                )
            ).first()
            return existing is not None
        except Exception:
            return False
    
    # Database transaction operations (migrated from DatabaseService)
    @staticmethod
    def create_transaction(account_id: int, date: date, 
                         amount: Decimal, currency: str = 'CNY', description: str = None,
                         counterparty: str = None, **kwargs) -> Transaction:
        """Create a new transaction."""
        try:
            return Transaction.create(
                account_id=account_id,
                date=date,
                amount=amount,
                currency=currency,
                description=description,
                counterparty=counterparty,
                **kwargs
            )
        except Exception as e:
            logger.error(f"Error creating transaction: {e}")
            raise
    
    @staticmethod
    def get_transactions(account_id: int = None, start_date: date = None, 
                        end_date: date = None, transaction_type: str = None,
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
        if transaction_type:
            query = query.filter_by(transaction_type=transaction_type)
        
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
    
    @staticmethod
    def get_all_transaction_types() -> List[str]:
        """Get all transaction types.
        
        Returns:
            List[str]: List of available transaction types ['income', 'expense', 'transfer']
        """
        return ['income', 'expense', 'transfer']