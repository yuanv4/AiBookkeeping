"""Transaction service for handling transaction-related business logic.

This module provides transaction processing, validation, and analysis functionality.
"""

from typing import List, Dict, Any, Optional, Tuple
from decimal import Decimal
from datetime import date, datetime
import logging
from collections import defaultdict

from app.models import Transaction, Account, db
from .database_service import DatabaseService
from sqlalchemy import func, and_

logger = logging.getLogger(__name__)

class TransactionService:
    """Service for handling transaction operations and business logic."""
    
    @staticmethod
    def process_transaction(account_id: int, transaction_type: str, date: date,
                          amount: Decimal, currency: str = 'CNY', description: str = None,
                          counterparty: str = None, notes: str = None,
                          original_description: str = None, auto_categorize: bool = True,
                          **kwargs) -> Tuple[Transaction, bool]:
        """Process a new transaction with validation and auto-categorization.
        
        Returns:
            Tuple of (transaction, is_new_transaction)
        """
        try:
            # Validate account
            account = DatabaseService.get_account_by_id(account_id)
            if not account:
                raise ValueError(f"Account with ID {account_id} not found")
            
            # Auto-categorize if enabled and no type specified
            if auto_categorize and not transaction_type:
                suggested_type = TransactionService._auto_categorize_transaction(
                    description or original_description, counterparty, amount
                )
                if suggested_type:
                    transaction_type = suggested_type
            
            # Use default type if still not specified
            if not transaction_type:
                transaction_type = 'OTHER_INCOME' if amount > 0 else 'OTHER_EXPENSE'
            
            # Adjust amount based on transaction type
            adjusted_amount = TransactionService._adjust_amount_by_type(amount, transaction_type)
            
            # Create transaction
            transaction = DatabaseService.create_transaction(
                account_id=account_id,
                transaction_type=transaction_type,
                date=date,
                amount=adjusted_amount,
                currency=currency,
                description=description,
                counterparty=counterparty,
                notes=notes,
                original_description=original_description,
                **kwargs
            )
            
            # Update account balance if needed
            TransactionService._update_account_balance(account, adjusted_amount)
            
            logger.info(f"Transaction processed successfully: {transaction.id}")
            return transaction, True
            
        except Exception as e:
            logger.error(f"Error processing transaction: {e}")
            db.session.rollback()
            raise
    
    @staticmethod
    def _auto_categorize_transaction(description: str, counterparty: str, amount: Decimal) -> Optional[str]:
        """Auto-categorize transaction based on description and counterparty."""
        if not description and not counterparty:
            return None
        
        search_text = f"{description or ''} {counterparty or ''}".lower()
        
        # Define categorization rules mapping to string values
        categorization_rules = {
            # Income categories
            'SALARY': ['salary', 'wage', '工资', '薪水', '薪资'],
            'BONUS': ['bonus', '奖金', '年终奖', '绩效'],
            'INVESTMENT': ['dividend', 'interest', '股息', '利息', '投资', '理财'],
            
            # Expense categories
            'FOOD': ['restaurant', 'food', '餐厅', '外卖', '美团', '饿了么', 'mcdonald', 'kfc'],
            'TRANSPORT': ['transport', 'taxi', 'uber', '滴滴', '地铁', '公交', '加油', 'gas'],
            'SHOPPING': ['shopping', 'mall', '淘宝', '京东', '超市', 'walmart', '沃尔玛'],
            'ENTERTAINMENT': ['entertainment', 'movie', 'game', '电影', '游戏', '娱乐'],
            'HEALTHCARE': ['hospital', 'pharmacy', 'medical', '医院', '药店', '医疗'],
            'EDUCATION': ['education', 'school', 'course', '学校', '培训', '教育'],
            'RENT': ['rent', 'housing', '房租', '租金', '物业'],
            'UTILITIES': ['utility', 'electric', 'water', '水费', '电费', '燃气'],
        }
        
        # Find matching category
        for transaction_type, keywords in categorization_rules.items():
            for keyword in keywords:
                if keyword in search_text:
                    return transaction_type
        
        # Default categorization based on amount
        if amount > 0:
            return 'OTHER_INCOME'
        else:
            return 'OTHER_EXPENSE'
    
    @staticmethod
    def _adjust_amount_by_type(amount: Decimal, transaction_type: str) -> Decimal:
        """Adjust amount sign based on transaction type."""
        # Define income types
        income_types = {'SALARY', 'BONUS', 'INVESTMENT', 'OTHER_INCOME'}
        
        is_income = transaction_type in income_types
        
        if is_income and amount < 0:
            return abs(amount)
        elif not is_income and amount > 0:
            return -abs(amount)
        return amount
    
    @staticmethod
    def _update_account_balance(account: Account, amount: Decimal):
        """Update account balance after transaction."""
        try:
            # Note: Account balance is calculated dynamically via get_current_balance()
            # No need to update a balance field as it doesn't exist
            db.session.commit()
        except Exception as e:
            logger.error(f"Error updating account balance: {e}")
            db.session.rollback()
            raise
    
    @staticmethod
    def bulk_import_transactions(transactions_data: List[Dict[str, Any]], 
                               account_id: int = None, auto_categorize: bool = True) -> Dict[str, Any]:
        """Import multiple transactions in bulk.
        
        Returns:
            Dictionary with import statistics
        """
        results = {
            'total': len(transactions_data),
            'successful': 0,
            'failed': 0,
            'errors': [],
            'duplicates': 0
        }
        
        for i, transaction_data in enumerate(transactions_data):
            try:
                # Use provided account_id if not in data
                if account_id and 'account_id' not in transaction_data:
                    transaction_data['account_id'] = account_id
                
                # Check for duplicates
                if TransactionService.is_duplicate_transaction(transaction_data):
                    results['duplicates'] += 1
                    continue
                
                # Process transaction
                TransactionService.process_transaction(
                    auto_categorize=auto_categorize,
                    **transaction_data
                )
                results['successful'] += 1
                
            except Exception as e:
                error_msg = f"Row {i+1}: {str(e)}"
                results['errors'].append(error_msg)
                results['failed'] += 1
                logger.error(f"Failed to import transaction at row {i+1}: {e}")
        
        logger.info(f"Bulk import completed: {results['successful']} successful, "
                   f"{results['failed']} failed, {results['duplicates']} duplicates")
        return results
    
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
                    # 如果过滤器中的transaction_type是字符串，尝试匹配枚举的display_name
                    filter_type = filters['transaction_type']
                    matching_types = [t for t in TransactionTypeEnum if filter_type.lower() in t.display_name.lower()]
                    if matching_types:
                        query = query.filter(Transaction.transaction_type.in_(matching_types))
                
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
                    # 如果过滤器中的transaction_type是字符串，尝试匹配枚举的display_name
                    filter_type = filters['transaction_type']
                    matching_types = [t for t in TransactionTypeEnum if filter_type.lower() in t.display_name.lower()]
                    if matching_types:
                        query = query.filter(Transaction.transaction_type.in_(matching_types))
                
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