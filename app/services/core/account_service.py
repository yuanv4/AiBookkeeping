"""Account service for handling account-related operations.

This module provides account management functionality including CRUD operations
and account-specific business logic.
"""

from typing import List, Optional, Dict, Any
import logging
from decimal import Decimal
from datetime import date
from sqlalchemy import func

from app.models import Account, Transaction, db

logger = logging.getLogger(__name__)

class AccountService:
    """Service for handling account operations."""

    @staticmethod
    def get_or_create_account(bank_id: int, account_number: str, account_name: str = None, 
                            currency: str = 'CNY', account_type: str = 'checking') -> Account:
        """Get existing account or create new one."""
        try:
            # 首先尝试根据银行ID和账户号码查找现有账户
            account = AccountService.get_by_bank_and_number(bank_id, account_number)
            if not account:
                # 如果不存在，创建新账户
                account = Account.create(
                    bank_id=bank_id,
                    account_number=account_number,
                    account_name=account_name,
                    currency=currency,
                    account_type=account_type
                )
                logger.info(f"Created new account: {account_number}")
            return account
        except Exception as e:
            logger.error(f"Error getting or creating account '{account_number}': {e}")
            raise

    @staticmethod
    def get_by_bank_and_number(bank_id: int, account_number: str) -> Optional[Account]:
        """Get account by bank ID and account number."""
        try:
            if not account_number:
                return None
            return Account.query.filter_by(bank_id=bank_id, account_number=account_number.strip()).first()
        except Exception as e:
            logger.error(f"Error getting account by bank_id={bank_id}, account_number={account_number}: {e}")
            raise

    @staticmethod
    def get_all_accounts() -> List[Account]:
        """Get all accounts."""
        try:
            return Account.query.order_by(Account.account_name, Account.account_number).all()
        except Exception as e:
            logger.error(f"Error getting all accounts: {e}")
            raise

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

    @staticmethod
    def get_by_id(account_id: int) -> Optional[Account]:
        """根据ID获取账户"""
        try:
            return Account.get_by_id(account_id)
        except Exception as e:
            logger.error(f"Error getting account by id {account_id}: {e}")
            return None