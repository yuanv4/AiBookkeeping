"""账户管理服务

专门负责账户相关的CRUD操作，从DataService中拆分出来。
遵循单一职责原则，只处理账户相关的业务逻辑。
"""

from typing import List, Optional
import logging

from app.models import Account, Bank
from app.utils.decorators import cached_query
from .base_service import BaseService
from .bank_service import BankService

logger = logging.getLogger(__name__)


class AccountService(BaseService):
    """账户管理服务
    
    提供账户的创建、查询、更新、删除等功能。
    依赖BankService来处理银行相关操作。
    """
    
    def __init__(self, bank_service: BankService = None, db_session=None):
        """初始化账户服务

        Args:
            bank_service: 银行服务实例
            db_session: 数据库会话，如果为None则使用默认会话
        """
        super().__init__(db_session)
        self.bank_service = bank_service or BankService(db_session)
    
    def get_or_create_account(self, bank_id: int, account_number: str, account_name: str = None) -> Account:
        """获取或创建账户

        Args:
            bank_id: 银行ID
            account_number: 账户号码
            account_name: 账户名称，可选

        Returns:
            Account: 账户实例

        Raises:
            Exception: 当账户创建或查询失败时抛出异常
        """
        try:
            account = self.get_account_by_number(account_number)
            if not account:
                account = Account.create(
                    bank_id=bank_id,
                    account_number=account_number,
                    account_name=account_name or f"账户{account_number}"
                )
                self.logger.info(f"创建新账户: {account_number}")
            return account
        except Exception as e:
            self.logger.error(f"获取或创建账户 '{account_number}' 失败: {e}")
            raise

    def get_account_by_number(self, account_number: str) -> Optional[Account]:
        """根据账户号码获取账户"""
        try:
            return Account.query.filter_by(account_number=account_number.strip()).first()
        except Exception as e:
            self.logger.error(f"Error getting account by number '{account_number}': {e}")
            raise

    def get_account_by_id(self, account_id: int) -> Optional[Account]:
        """根据ID获取账户"""
        try:
            return Account.get_by_id(account_id)
        except Exception as e:
            self.logger.error(f"Error getting account by id {account_id}: {e}")
            raise

    @cached_query()
    def get_all_accounts(self) -> List[Account]:
        """获取所有账户"""
        try:
            return Account.query.order_by(Account.account_name).all()
        except Exception as e:
            self.logger.error(f"Error getting all accounts: {e}")
            raise

    def get_accounts_by_bank(self, bank_id: int) -> List[Account]:
        """根据银行ID获取账户列表"""
        try:
            return Account.query.filter_by(bank_id=bank_id).order_by(Account.account_name).all()
        except Exception as e:
            self.logger.error(f"Error getting accounts by bank {bank_id}: {e}")
            raise

    def get_accounts_by_bank_name(self, bank_name: str) -> List[Account]:
        """根据银行名称获取账户列表"""
        try:
            bank = self.bank_service.get_bank_by_name(bank_name)
            if not bank:
                return []
            return self.get_accounts_by_bank(bank.id)
        except Exception as e:
            self.logger.error(f"Error getting accounts by bank name '{bank_name}': {e}")
            raise

    def update_account(self, account_id: int, **kwargs) -> bool:
        """更新账户信息"""
        try:
            account = Account.get_by_id(account_id)
            if account:
                account.update(**kwargs)
                self.logger.info(f"更新账户信息: {account_id}")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error updating account {account_id}: {e}")
            raise

    def delete_account(self, account_id: int) -> bool:
        """删除账户"""
        try:
            account = Account.get_by_id(account_id)
            if account:
                account.delete()
                self.logger.info(f"删除账户: {account_id}")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error deleting account {account_id}: {e}")
            raise

    def account_exists(self, account_number: str) -> bool:
        """检查账户是否存在"""
        try:
            return self.get_account_by_number(account_number) is not None
        except Exception as e:
            self.logger.error(f"Error checking account existence '{account_number}': {e}")
            return False

    def get_accounts_count(self) -> int:
        """获取账户总数"""
        try:
            return Account.query.count()
        except Exception as e:
            self.logger.error(f"Error getting accounts count: {e}")
            return 0

    def get_accounts_by_bank_code(self, bank_code: str) -> List[Account]:
        """根据银行代码获取账户列表"""
        try:
            bank = self.bank_service.get_bank_by_code(bank_code)
            if not bank:
                return []
            return self.get_accounts_by_bank(bank.id)
        except Exception as e:
            self.logger.error(f"Error getting accounts by bank code '{bank_code}': {e}")
            raise

    def get_by_id(self, id: int) -> Optional[Account]:
        """根据ID获取账户（实现BaseService抽象方法）"""
        try:
            if not self._validate_id(id):
                return None
            return Account.get_by_id(id)
        except Exception as e:
            self._handle_service_error(f"获取账户 ID={id}", e)

    def get_all(self) -> List[Account]:
        """获取所有账户（实现BaseService抽象方法）"""
        try:
            return Account.query.order_by(Account.account_name).all()
        except Exception as e:
            self._handle_service_error("获取所有账户", e)
