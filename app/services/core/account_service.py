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
    def get_all_accounts() -> List[Account]:
        """Get all accounts."""
        return Account.get_all_accounts()

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
    def delete_account(account_id: int) -> bool:
        """Delete account."""
        try:
            account = Account.get_by_id(account_id)
            if account:
                account.delete()
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting account {account_id}: {e}")
            raise