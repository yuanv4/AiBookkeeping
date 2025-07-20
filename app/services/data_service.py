"""数据服务协调层

重构后的DataService作为协调层，委托具体操作给专门的服务类。
这样既保持了向后兼容性，又实现了职责分离。

主要功能:
- 作为BankService、AccountService、TransactionService的协调层
- 提供统一的数据访问接口
- 保持向后兼容性
"""

from typing import List, Optional, Dict, Any
from decimal import Decimal
from datetime import date
import logging

from app.models import Bank, Account, Transaction, db
from .bank_service import BankService
from .account_service import AccountService
from .transaction_service import TransactionService

logger = logging.getLogger(__name__)

class DataService:
    """数据服务协调层
    
    委托具体操作给专门的服务类，保持向后兼容性。
    """
    
    def __init__(self, db_session=None):
        """初始化数据服务
        
        Args:
            db_session: 数据库会话，如果为None则使用默认会话
        """
        self.db = db_session or db.session
        self.logger = logging.getLogger(__name__)
        
        # 初始化专门的服务
        self.bank_service = BankService(db_session)
        self.account_service = AccountService(self.bank_service, db_session)
        self.transaction_service = TransactionService(self.account_service, db_session)

    # ==================== 银行管理 (委托给BankService) ====================
    
    def get_or_create_bank(self, name: str, code: str = None) -> Bank:
        """获取或创建银行"""
        return self.bank_service.get_or_create_bank(name, code)

    def get_bank_by_name(self, name: str) -> Optional[Bank]:
        """根据名称获取银行"""
        return self.bank_service.get_bank_by_name(name)

    def get_bank_by_code(self, code: str) -> Optional[Bank]:
        """根据代码获取银行"""
        return self.bank_service.get_bank_by_code(code)

    def get_all_banks(self) -> List[Bank]:
        """获取所有银行"""
        return self.bank_service.get_all_banks()

    def update_bank(self, bank_id: int, **kwargs) -> bool:
        """更新银行信息"""
        return self.bank_service.update_bank(bank_id, **kwargs)

    def delete_bank(self, bank_id: int) -> bool:
        """删除银行"""
        return self.bank_service.delete_bank(bank_id)

    def get_bank_by_id(self, bank_id: int) -> Optional[Bank]:
        """根据ID获取银行"""
        return self.bank_service.get_bank_by_id(bank_id)

    # ==================== 账户管理 (委托给AccountService) ====================
    
    def get_or_create_account(self, bank_id: int, account_number: str, account_name: str = None) -> Account:
        """获取或创建账户"""
        return self.account_service.get_or_create_account(bank_id, account_number, account_name)

    def get_account_by_number(self, account_number: str) -> Optional[Account]:
        """根据账户号码获取账户"""
        return self.account_service.get_account_by_number(account_number)

    def get_account_by_id(self, account_id: int) -> Optional[Account]:
        """根据ID获取账户"""
        return self.account_service.get_account_by_id(account_id)

    def get_all_accounts(self) -> List[Account]:
        """获取所有账户"""
        return self.account_service.get_all_accounts()

    def get_accounts_by_bank(self, bank_id: int) -> List[Account]:
        """根据银行ID获取账户列表"""
        return self.account_service.get_accounts_by_bank(bank_id)

    def update_account(self, account_id: int, **kwargs) -> bool:
        """更新账户信息"""
        return self.account_service.update_account(account_id, **kwargs)

    def delete_account(self, account_id: int) -> bool:
        """删除账户"""
        return self.account_service.delete_account(account_id)

    # ==================== 交易管理 (委托给TransactionService) ====================
    
    def create_transaction(self, **kwargs) -> Transaction:
        """创建交易记录"""
        return self.transaction_service.create_transaction(**kwargs)

    def get_transaction_by_id(self, transaction_id: int) -> Optional[Transaction]:
        """根据ID获取交易"""
        return self.transaction_service.get_transaction_by_id(transaction_id)

    def get_transactions_filtered(self, filters: dict = None, page: int = None, per_page: int = None) -> List[Transaction]:
        """根据过滤条件获取交易记录"""
        return self.transaction_service.get_transactions_filtered(filters, page, per_page)

    def check_duplicate_transaction(self, account_id: int, date: date, amount: Decimal, balance_after: Decimal = None) -> bool:
        """检查交易是否重复"""
        return self.transaction_service.check_duplicate_transaction(account_id, date, amount, balance_after)

    def batch_check_duplicates(self, transactions_data: List[Dict[str, Any]]) -> List[bool]:
        """批量检查交易重复"""
        return self.transaction_service.batch_check_duplicates(transactions_data)

    def batch_create_transactions(self, transactions_data: List[Dict[str, Any]]) -> List[Transaction]:
        """批量创建交易记录"""
        return self.transaction_service.batch_create_transactions(transactions_data)

    def update_transaction(self, transaction_id: int, **kwargs) -> bool:
        """更新交易记录"""
        return self.transaction_service.update_transaction(transaction_id, **kwargs)

    def delete_transaction(self, transaction_id: int) -> bool:
        """删除交易记录"""
        return self.transaction_service.delete_transaction(transaction_id)

    def get_transactions_count(self, filters: dict = None) -> int:
        """获取交易记录总数"""
        return self.transaction_service.get_transactions_count(filters)

    def get_all_currencies(self) -> List[str]:
        """获取所有货币类型"""
        return self.transaction_service.get_all_currencies()

    def get_distinct_counterparties(self) -> List[str]:
        """获取所有不同的交易对手"""
        return self.transaction_service.get_distinct_counterparties()

    def get_transactions_by_date_range(self, start_date: date, end_date: date) -> List[Transaction]:
        """根据日期范围获取交易记录"""
        return self.transaction_service.get_transactions_by_date_range(start_date, end_date)

    def get_transactions_by_category(self, category: str) -> List[Transaction]:
        """根据分类获取交易记录"""
        return self.transaction_service.get_transactions_by_category(category)

    # ==================== 兼容性方法 ====================
    
    def is_duplicate_transaction(self, transaction_data: Dict[str, Any]) -> bool:
        """检查交易是否重复（兼容性方法）"""
        account_id = transaction_data.get('account_id')
        date_val = transaction_data.get('date')
        amount = transaction_data.get('amount')
        balance_after = transaction_data.get('balance_after')
        
        if any(x is None for x in [account_id, date_val, amount]):
            return True
            
        return self.check_duplicate_transaction(account_id, date_val, amount, balance_after)

    def get_account_by_bank_and_number(self, bank_id: int, account_number: str) -> Optional[Account]:
        """根据银行ID和账户号码获取账户（兼容性方法）"""
        account = self.get_account_by_number(account_number)
        if account and account.bank_id == bank_id:
            return account
        return None
