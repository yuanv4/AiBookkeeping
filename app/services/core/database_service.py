"""Database service for the Flask application.

This module provides database operations and management functionality.
"""

from app.models import db, Bank, Account, TransactionType, Transaction
from sqlalchemy.exc import SQLAlchemyError
from typing import List, Dict, Any, Optional, Tuple
from decimal import Decimal
from datetime import date, datetime
import logging

logger = logging.getLogger(__name__)

class DatabaseService:
    """Database service for managing all database operations."""
    
    # Account operations
    
    @staticmethod
    def get_account_by_id(account_id: int) -> Optional[Account]:
        """Get account by ID."""
        return Account.get_by_id(account_id)
    
    # Transaction Type operations
    
    @staticmethod
    def get_transaction_type_by_id(type_id: int) -> Optional[TransactionType]:
        """Get transaction type by ID."""
        return TransactionType.get_by_id(type_id)
    
    @staticmethod
    def get_transaction_type_by_name(name: str) -> Optional[TransactionType]:
        """Get transaction type by name."""
        return TransactionType.get_by_name(name)
    

    
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