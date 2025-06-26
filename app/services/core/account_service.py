"""Account service for handling account-related operations."""

from typing import List, Optional, Dict, Any
import logging
from app.models import Account

logger = logging.getLogger(__name__)

class AccountService:
    """Service for handling account operations."""
    
    def __init__(self, db_session=None):
        """初始化账户服务
        
        Args:
            db_session: 数据库会话，如果为None则使用默认会话
        """
        from app.models import db
        self.db = db_session or db.session
        self.logger = logging.getLogger(__name__)

    def get_or_create_account(self, bank_id: int, account_number: str, account_name: str = None, 
                            currency: str = 'CNY', account_type: str = 'checking') -> Account:
        """Get existing account or create new one."""
        try:
            # 首先尝试根据银行ID和账户号码查找现有账户
            account = self.get_by_bank_and_number(bank_id, account_number)
            if not account:
                # 如果不存在，创建新账户
                account = Account.create(
                    bank_id=bank_id,
                    account_number=account_number,
                    account_name=account_name,
                    currency=currency,
                    account_type=account_type
                )
                self.logger.info(f"Created new account: {account_number}")
            return account
        except Exception as e:
            self.logger.error(f"Error getting or creating account '{account_number}': {e}")
            raise

    def get_by_bank_and_number(self, bank_id: int, account_number: str) -> Optional[Account]:
        """Get account by bank ID and account number."""
        try:
            if not account_number:
                return None
            return Account.query.filter_by(bank_id=bank_id, account_number=account_number.strip()).first()
        except Exception as e:
            self.logger.error(f"Error getting account by bank_id={bank_id}, account_number={account_number}: {e}")
            raise

    def get_all_accounts(self) -> List[Account]:
        """Get all accounts."""
        try:
            return Account.query.order_by(Account.account_name, Account.account_number).all()
        except Exception as e:
            self.logger.error(f"Error getting all accounts: {e}")
            raise

    def update_account(self, account_id: int, **kwargs) -> bool:
        """Update account information."""
        try:
            account = Account.get_by_id(account_id)
            if account:
                account.update(**kwargs)
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error updating account {account_id}: {e}")
            raise

    def delete_account(self, account_id: int) -> bool:
        """Delete account."""
        try:
            account = Account.get_by_id(account_id)
            if account:
                account.delete()
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error deleting account {account_id}: {e}")
            raise

    def get_by_id(self, account_id: int) -> Optional[Account]:
        """根据ID获取账户"""
        try:
            return Account.get_by_id(account_id)
        except Exception as e:
            self.logger.error(f"Error getting account by id {account_id}: {e}")
            return None