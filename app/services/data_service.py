"""统一数据服务

合并了原来的 AccountService、BankService 和 TransactionService 的核心功能，
提供统一的数据访问接口，简化服务依赖关系。

主要功能:
- 银行的创建、查询、更新、删除
- 账户的创建、查询、更新、删除  
- 交易记录的CRUD操作
- 基础的数据查询和过滤
- 去重检查和数据验证
"""

from typing import List, Optional, Dict, Any
from decimal import Decimal
from datetime import date
import logging

from app.models import Bank, Account, Transaction, db
from flask_sqlalchemy.pagination import Pagination
from sqlalchemy import func, and_
from app.utils.query_cache import invalidate_cache_on_change

logger = logging.getLogger(__name__)

class DataService:
    """统一数据管理服务
    
    提供银行、账户、交易记录的统一数据访问接口。
    """
    
    def __init__(self, db_session=None):
        """初始化数据服务
        
        Args:
            db_session: 数据库会话，如果为None则使用默认会话
        """
        self.db = db_session or db.session
        self.logger = logging.getLogger(__name__)
    
    # ==================== 银行管理 ====================
    
    def get_or_create_bank(self, name: str, code: str = None) -> Bank:
        """获取或创建银行

        Args:
            name: 银行名称
            code: 银行代码，可选

        Returns:
            Bank: 银行实例

        Raises:
            Exception: 当银行创建或查询失败时抛出异常
        """
        try:
            bank = self.get_bank_by_name(name)
            if not bank:
                bank = Bank.create(name=name, code=code)
                self.logger.info(f"创建新银行: {name}")
            return bank
        except Exception as e:
            self.logger.error(f"获取或创建银行 '{name}' 失败: {e}")
            raise

    def get_bank_by_name(self, name: str) -> Optional[Bank]:
        """根据名称获取银行"""
        try:
            return Bank.query.filter_by(name=name.strip()).first()
        except Exception as e:
            self.logger.error(f"Error getting bank by name '{name}': {e}")
            raise

    def get_bank_by_code(self, code: str) -> Optional[Bank]:
        """根据代码获取银行"""
        try:
            if not code:
                return None
            return Bank.query.filter_by(code=code.strip().upper()).first()
        except Exception as e:
            self.logger.error(f"Error getting bank by code '{code}': {e}")
            raise

    def get_all_banks(self) -> List[Bank]:
        """获取所有银行"""
        try:
            return Bank.query.order_by(Bank.name).all()
        except Exception as e:
            self.logger.error(f"Error getting all banks: {e}")
            raise

    def update_bank(self, bank_id: int, **kwargs) -> bool:
        """更新银行信息"""
        try:
            bank = Bank.get_by_id(bank_id)
            if bank:
                bank.update(**kwargs)
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error updating bank {bank_id}: {e}")
            raise

    def delete_bank(self, bank_id: int) -> bool:
        """删除银行"""
        try:
            bank = Bank.get_by_id(bank_id)
            if bank:
                bank.delete()
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error deleting bank {bank_id}: {e}")
            raise
    
    # ==================== 账户管理 ====================
    
    def get_or_create_account(self, bank_id: int, account_number: str, account_name: str = None, 
                            currency: str = 'CNY', account_type: str = 'checking') -> Account:
        """获取或创建账户

        Args:
            bank_id: 银行ID
            account_number: 账户号码
            account_name: 账户名称，可选
            currency: 货币类型，默认为CNY
            account_type: 账户类型，默认为checking

        Returns:
            Account: 账户实例

        Raises:
            Exception: 当账户创建或查询失败时抛出异常
        """
        try:
            account = self.get_account_by_bank_and_number(bank_id, account_number)
            if not account:
                account = Account.create(
                    bank_id=bank_id,
                    account_number=account_number,
                    account_name=account_name,
                    currency=currency,
                    account_type=account_type
                )
                self.logger.info(f"创建新账户: {account_number}")
            return account
        except Exception as e:
            self.logger.error(f"获取或创建账户 '{account_number}' 失败: {e}")
            raise

    def get_account_by_bank_and_number(self, bank_id: int, account_number: str) -> Optional[Account]:
        """根据银行ID和账户号码获取账户"""
        try:
            if not account_number:
                return None
            return Account.query.filter_by(bank_id=bank_id, account_number=account_number.strip()).first()
        except Exception as e:
            self.logger.error(f"Error getting account by bank_id={bank_id}, account_number={account_number}: {e}")
            raise

    def get_account_by_id(self, account_id: int) -> Optional[Account]:
        """根据ID获取账户"""
        try:
            return Account.get_by_id(account_id)
        except Exception as e:
            self.logger.error(f"Error getting account by id {account_id}: {e}")
            return None

    def get_all_accounts(self) -> List[Account]:
        """获取所有账户"""
        try:
            return Account.query.order_by(Account.account_name, Account.account_number).all()
        except Exception as e:
            self.logger.error(f"Error getting all accounts: {e}")
            raise

    def update_account(self, account_id: int, **kwargs) -> bool:
        """更新账户信息"""
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
        """删除账户"""
        try:
            account = Account.get_by_id(account_id)
            if account:
                account.delete()
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error deleting account {account_id}: {e}")
            raise
    
    # ==================== 交易记录管理 ====================
    
    @invalidate_cache_on_change(['get_expense_composition', 'get_income_composition', 'get_monthly_trend', 'get_dashboard_data'])
    def create_transaction(self, account_id: int, date: date,
                         amount: Decimal, currency: str = 'CNY', description: str = None,
                         counterparty: str = None, **kwargs) -> Transaction:
        """创建交易记录"""
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
            self.logger.error(f"Error creating transaction: {e}")
            raise

    def is_duplicate_transaction(self, transaction_data: Dict[str, Any]) -> bool:
        """检查交易是否重复"""
        try:
            account_id = transaction_data.get('account_id')
            date = transaction_data.get('date')
            amount = transaction_data.get('amount')
            balance_after = transaction_data.get('balance_after')

            if account_id is None or date is None or amount is None or balance_after is None:
                self.logger.warning("重复检查失败：缺少必需字段")
                return True

            try:
                normalized_amount = Transaction._normalize_decimal(amount)
                normalized_balance = Transaction._normalize_decimal(balance_after)
            except (ValueError, TypeError):
                self.logger.warning(f"重复检查失败：无效的数值格式 {amount} {balance_after}")
                return True

            # 使用 exists() 查询替代 first()，提高性能
            # exists() 只检查是否存在，不需要返回完整记录
            query_conditions = [
                Transaction.account_id == account_id,
                Transaction.date == date,
                Transaction.amount == normalized_amount,
                Transaction.balance_after == normalized_balance
            ]

            return self.db.query(Transaction.query.filter(and_(*query_conditions)).exists()).scalar()

        except Exception as e:
            self.logger.error(f"重复检查异常: {e}")
            return True

    def batch_check_duplicates(self, transactions_data: List[Dict[str, Any]]) -> List[bool]:
        """批量检查交易重复 - 新增方法，提高批量导入性能"""
        try:
            if not transactions_data:
                return []

            # 构建批量查询条件
            conditions = []
            for transaction_data in transactions_data:
                account_id = transaction_data.get('account_id')
                date = transaction_data.get('date')
                amount = transaction_data.get('amount')
                balance_after = transaction_data.get('balance_after')

                if all(x is not None for x in [account_id, date, amount, balance_after]):
                    try:
                        normalized_amount = Transaction._normalize_decimal(amount)
                        normalized_balance = Transaction._normalize_decimal(balance_after)
                        conditions.append(and_(
                            Transaction.account_id == account_id,
                            Transaction.date == date,
                            Transaction.amount == normalized_amount,
                            Transaction.balance_after == normalized_balance
                        ))
                    except (ValueError, TypeError):
                        continue

            if not conditions:
                return [True] * len(transactions_data)

            # 单次查询获取所有重复记录
            from sqlalchemy import or_
            existing_transactions = Transaction.query.filter(or_(*conditions)).all()

            # 构建重复记录的快速查找集合
            existing_set = set()
            for t in existing_transactions:
                key = (t.account_id, t.date, t.amount, t.balance_after)
                existing_set.add(key)

            # 检查每个交易是否重复
            results = []
            for transaction_data in transactions_data:
                account_id = transaction_data.get('account_id')
                date = transaction_data.get('date')
                amount = transaction_data.get('amount')
                balance_after = transaction_data.get('balance_after')

                if any(x is None for x in [account_id, date, amount, balance_after]):
                    results.append(True)
                    continue

                try:
                    normalized_amount = Transaction._normalize_decimal(amount)
                    normalized_balance = Transaction._normalize_decimal(balance_after)
                    key = (account_id, date, normalized_amount, normalized_balance)
                    results.append(key in existing_set)
                except (ValueError, TypeError):
                    results.append(True)

            return results

        except Exception as e:
            self.logger.error(f"批量重复检查异常: {e}")
            return [True] * len(transactions_data)

    def get_transactions(self, account_id: int = None, start_date: date = None, 
                        end_date: date = None, transaction_type: str = None,
                        limit: int = None, offset: int = None) -> List[Transaction]:
        """获取交易记录"""
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

    def get_transactions_by_type(self, transaction_type: str, start_date: date, end_date: date, 
                               account_id: Optional[int] = None) -> List[Transaction]:
        """根据交易类型获取交易记录"""
        try:
            query = Transaction.query.join(Account)
            
            if transaction_type == 'income':
                query = query.filter(Transaction.amount > 0)
            elif transaction_type == 'expense':
                query = query.filter(Transaction.amount < 0)
            
            if start_date:
                query = query.filter(Transaction.date >= start_date)
            if end_date:
                query = query.filter(Transaction.date <= end_date)
            if account_id:
                query = query.filter(Transaction.account_id == account_id)
                
            return query.order_by(Transaction.date.desc()).all()
        except Exception as e:
            self.logger.error(f"Error getting {transaction_type} transactions: {e}")
            return []

    def update_transaction(self, transaction_id: int, **kwargs) -> bool:
        """更新交易记录"""
        try:
            transaction = Transaction.get_by_id(transaction_id)
            if transaction:
                transaction.update(**kwargs)
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error updating transaction {transaction_id}: {e}")
            raise

    def delete_transaction(self, transaction_id: int) -> bool:
        """删除交易记录"""
        try:
            transaction = Transaction.get_by_id(transaction_id)
            if transaction:
                transaction.delete()
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error deleting transaction {transaction_id}: {e}")
            raise

    def get_all_currencies(self) -> List[str]:
        """获取所有货币类型"""
        try:
            currencies = self.db.query(Transaction.currency).distinct().all()
            all_currencies = {currency for (currency,) in currencies if currency}
            return sorted(list(all_currencies))
        except Exception as e:
            self.logger.error(f"Error getting all currencies: {e}")
            return ['CNY']

    def get_distinct_counterparties(self) -> List[str]:
        """获取所有不同的交易对手"""
        try:
            counterparties = self.db.query(Transaction.counterparty).distinct().all()
            return [c[0] for c in counterparties if c[0]]
        except Exception as e:
            self.logger.error(f"Error getting distinct counterparties: {e}")
            return []

    def get_transactions_paginated(self, filters: Dict[str, Any] = None,
                                 page: int = 1,
                                 per_page: int = 20,
                                 transaction_type_filter: str = None) -> Pagination:
        """分页获取交易记录"""
        try:
            from app.models import Account

            query = self.db.query(Transaction).join(Account)

            # 应用交易类型过滤器
            if transaction_type_filter == 'income':
                query = query.filter(Transaction.amount > 0)
            elif transaction_type_filter == 'expense':
                query = query.filter(Transaction.amount < 0)

            if filters:
                # Account number filter
                if 'account_number' in filters and filters['account_number']:
                    query = query.filter(Account.account_number.like(f"%{filters['account_number']}%"))

                # Account name filter
                if 'account_name' in filters and filters['account_name']:
                    query = query.filter(Account.account_name.like(f"%{filters['account_name']}%"))

                # Date range filters
                if 'start_date' in filters and filters['start_date']:
                    from datetime import datetime
                    start_date = datetime.strptime(filters['start_date'], '%Y-%m-%d').date()
                    query = query.filter(Transaction.date >= start_date)

                if 'end_date' in filters and filters['end_date']:
                    from datetime import datetime
                    end_date = datetime.strptime(filters['end_date'], '%Y-%m-%d').date()
                    query = query.filter(Transaction.date <= end_date)

                # Amount range filters
                if 'min_amount' in filters and filters['min_amount'] is not None:
                    if transaction_type_filter == 'expense':
                        query = query.filter(func.abs(Transaction.amount) >= filters['min_amount'])
                    else:
                        query = query.filter(Transaction.amount >= filters['min_amount'])

                if 'max_amount' in filters and filters['max_amount'] is not None:
                    if transaction_type_filter == 'expense':
                        query = query.filter(func.abs(Transaction.amount) <= filters['max_amount'])
                    else:
                        query = query.filter(Transaction.amount <= filters['max_amount'])

                # Counterparty filter
                if 'counterparty' in filters and filters['counterparty']:
                    query = query.filter(Transaction.counterparty.like(f"%{filters['counterparty']}%"))

                # Search filter
                if 'search' in filters and filters['search']:
                    search_term = filters['search']
                    query = query.filter(Transaction.counterparty.like(f"%{search_term}%"))

                # Currency filter
                if 'currency' in filters and filters['currency']:
                    query = query.filter(Transaction.currency == filters['currency'])

            # Order by date descending
            query = query.order_by(Transaction.date.desc(), Transaction.created_at.desc())

            # 使用Flask-SQLAlchemy的分页功能
            return query.paginate(
                page=page,
                per_page=per_page,
                error_out=False
            )

        except Exception as e:
            self.logger.error(f"Error getting transactions with pagination: {e}")
            # 返回空的分页对象
            return self.db.query(Transaction).filter(Transaction.id == -1).paginate(
                page=1, per_page=per_page, error_out=False
            )