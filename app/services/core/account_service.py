"""Account service for handling account-related operations.

This module provides account management functionality including CRUD operations
and account-specific business logic.
"""

from typing import List
import logging

from app.models import Account, db

logger = logging.getLogger(__name__)

class AccountService:
    """Service for handling account operations."""

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
            from app.models import Transaction
            
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