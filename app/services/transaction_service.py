"""交易管理服务 - 提供交易相关的CRUD操作"""

from typing import List, Optional, Dict, Any
from decimal import Decimal
from datetime import date
import logging

from app.models import Transaction, Account, Bank
from flask_sqlalchemy.pagination import Pagination
from sqlalchemy import func, and_, or_
from sqlalchemy.orm import joinedload, selectinload
from app.utils.decorators import cached_query

from .base_service import BaseService
from .account_service import AccountService

logger = logging.getLogger(__name__)


class TransactionService(BaseService):
    """交易管理服务 - 提供交易的创建、查询、更新、删除等功能"""

    def __init__(self, account_service: AccountService = None, db_session=None):
        """初始化交易服务"""
        super().__init__(db_session)
        self.account_service = account_service or AccountService(db_session=db_session)
    
    def create_transaction(self, **kwargs) -> Transaction:
        """创建交易记录"""
        try:
            transaction = Transaction.create(**kwargs)
            self.logger.info(f"创建交易记录: {transaction.id}")
            return transaction
        except Exception as e:
            self.logger.error(f"创建交易记录失败: {e}")
            raise

    def get_by_id(self, id: int) -> Optional[Transaction]:
        """根据ID获取交易"""
        try:
            if not self._validate_id(id):
                return None
            return Transaction.get_by_id(id)
        except Exception as e:
            self._handle_service_error(f"获取交易 ID={id}", e)

    def get_transaction_by_id(self, transaction_id: int) -> Optional[Transaction]:
        """根据ID获取交易（向后兼容）"""
        return self.get_by_id(transaction_id)

    def get_transactions_with_relations(self, filters: dict = None, page: int = None, per_page: int = None) -> List[Transaction]:
        """获取交易记录，预加载关联数据避免N+1问题"""
        try:
            query = Transaction.query.options(
                joinedload(Transaction.account).joinedload(Account.bank)
            )

            if filters:
                query = self._apply_filters(query, filters)

            # 默认按日期降序排列
            query = query.order_by(Transaction.date.desc(), Transaction.id.desc())

            if page and per_page:
                pagination = query.paginate(page=page, per_page=per_page, error_out=False)
                transactions = pagination.items
            else:
                transactions = query.all()

            # 标记关联数据已加载，供to_dict方法使用
            for transaction in transactions:
                transaction._account_loaded = True
                if transaction.account:
                    transaction.account._bank_loaded = True

            return transactions
        except Exception as e:
            self.logger.error(f"Error getting transactions with relations: {e}")
            raise

    def get_transactions_filtered(self, filters: dict = None, page: int = None, per_page: int = None) -> List[Transaction]:
        """根据过滤条件获取交易记录"""
        try:
            query = Transaction.query
            
            if filters:
                query = self._apply_filters(query, filters)
            
            # 默认按日期降序排列
            query = query.order_by(Transaction.date.desc(), Transaction.id.desc())
            
            if page and per_page:
                pagination = query.paginate(page=page, per_page=per_page, error_out=False)
                return pagination.items
            else:
                return query.all()
        except Exception as e:
            self.logger.error(f"Error getting filtered transactions: {e}")
            raise

    def _apply_filters(self, query, filters: dict):
        """应用过滤条件到查询"""
        try:
            if 'account_id' in filters and filters['account_id']:
                query = query.filter(Transaction.account_id == filters['account_id'])
            
            if 'account_number' in filters and filters['account_number']:
                account = self.account_service.get_account_by_number(filters['account_number'])
                if account:
                    query = query.filter(Transaction.account_id == account.id)
            
            if 'start_date' in filters and filters['start_date']:
                if isinstance(filters['start_date'], str):
                    from datetime import datetime
                    start_date = datetime.strptime(filters['start_date'], '%Y-%m-%d').date()
                else:
                    start_date = filters['start_date']
                query = query.filter(Transaction.date >= start_date)
            
            if 'end_date' in filters and filters['end_date']:
                if isinstance(filters['end_date'], str):
                    from datetime import datetime
                    end_date = datetime.strptime(filters['end_date'], '%Y-%m-%d').date()
                else:
                    end_date = filters['end_date']
                query = query.filter(Transaction.date <= end_date)
            
            if 'min_amount' in filters and filters['min_amount'] is not None:
                query = query.filter(Transaction.amount >= filters['min_amount'])
            
            if 'max_amount' in filters and filters['max_amount'] is not None:
                query = query.filter(Transaction.amount <= filters['max_amount'])
            
            if 'transaction_type' in filters and filters['transaction_type']:
                if filters['transaction_type'] == 'income':
                    query = query.filter(Transaction.amount > 0)
                elif filters['transaction_type'] == 'expense':
                    query = query.filter(Transaction.amount < 0)
            
            if 'counterparty' in filters and filters['counterparty']:
                query = query.filter(Transaction.counterparty.ilike(f"%{filters['counterparty']}%"))
            
            if 'currency' in filters and filters['currency']:
                query = query.filter(Transaction.currency == filters['currency'])
            
            if 'category' in filters and filters['category']:
                query = query.filter(Transaction.category == filters['category'])
            
            return query
        except Exception as e:
            self.logger.error(f"Error applying filters: {e}")
            raise

    def check_duplicate_transaction(self, account_id: int, date: date, amount: Decimal, balance_after: Decimal = None) -> bool:
        """检查交易是否重复"""
        try:
            # 标准化金额
            from app.utils import DataUtils
            normalized_amount = DataUtils.normalize_decimal(amount)
            normalized_balance = DataUtils.normalize_decimal(balance_after) if balance_after is not None else None

            # 使用 exists() 查询替代 first()，提高性能
            query_conditions = [
                Transaction.account_id == account_id,
                Transaction.date == date,
                Transaction.amount == normalized_amount,
            ]
            
            if normalized_balance is not None:
                query_conditions.append(Transaction.balance_after == normalized_balance)

            return self.db.query(Transaction.query.filter(and_(*query_conditions)).exists()).scalar()

        except Exception as e:
            self.logger.error(f"重复检查异常: {e}")
            return True

    def batch_check_duplicates(self, transactions_data: List[Dict[str, Any]]) -> List[bool]:
        """批量检查交易重复 - 提高批量导入性能"""
        try:
            if not transactions_data:
                return []

            # 构建查询条件
            conditions = []
            for data in transactions_data:
                account_id = data.get('account_id')
                date_val = data.get('date')
                from app.utils import DataUtils
                amount = DataUtils.normalize_decimal(data.get('amount'))
                balance_after = data.get('balance_after')

                if balance_after is not None:
                    balance_after = DataUtils.normalize_decimal(balance_after)

                condition = and_(
                    Transaction.account_id == account_id,
                    Transaction.date == date_val,
                    Transaction.amount == amount,
                    Transaction.balance_after == balance_after
                )
                conditions.append(condition)

            # 单次查询获取所有重复记录
            existing_transactions = Transaction.query.filter(or_(*conditions)).all()

            # 构建重复记录的快速查找集合
            existing_set = set()
            for t in existing_transactions:
                key = (t.account_id, t.date, t.amount, t.balance_after)
                existing_set.add(key)

            # 检查每个交易是否重复
            results = []
            for data in transactions_data:
                from app.utils import DataUtils
                key = (
                    data.get('account_id'),
                    data.get('date'),
                    DataUtils.normalize_decimal(data.get('amount')),
                    DataUtils.normalize_decimal(data.get('balance_after')) if data.get('balance_after') is not None else None
                )
                results.append(key in existing_set)

            return results

        except Exception as e:
            self.logger.error(f"批量重复检查异常: {e}")
            return [True] * len(transactions_data)  # 出错时假设都重复，避免重复导入

    def batch_create_transactions(self, transactions_data: List[Dict[str, Any]]) -> List[Transaction]:
        """批量创建交易记录"""
        try:
            transactions = []
            for data in transactions_data:
                # 直接使用Transaction模型，模型内部会进行验证
                transaction = Transaction(**data)
                self.db.add(transaction)
                transactions.append(transaction)

            self.db.commit()
            self.logger.info(f"批量创建 {len(transactions)} 条交易记录")
            return transactions
        except Exception as e:
            self.db.rollback()
            self.logger.error(f"批量创建交易记录失败: {e}")
            raise

    def update_transaction(self, transaction_id: int, **kwargs) -> bool:
        """更新交易记录"""
        try:
            transaction = Transaction.get_by_id(transaction_id)
            if transaction:
                transaction.update(**kwargs)
                self.logger.info(f"更新交易记录: {transaction_id}")
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
                self.logger.info(f"删除交易记录: {transaction_id}")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error deleting transaction {transaction_id}: {e}")
            raise

    def get_transactions_count(self, filters: dict = None) -> int:
        """获取交易记录总数"""
        try:
            query = Transaction.query
            if filters:
                query = self._apply_filters(query, filters)
            return query.count()
        except Exception as e:
            self.logger.error(f"Error getting transactions count: {e}")
            return 0

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

    def get_transactions_by_date_range(self, start_date: date, end_date: date) -> List[Transaction]:
        """根据日期范围获取交易记录"""
        try:
            return Transaction.query.filter(
                Transaction.date >= start_date,
                Transaction.date <= end_date
            ).order_by(Transaction.date.desc()).all()
        except Exception as e:
            self.logger.error(f"Error getting transactions by date range: {e}")
            raise

    def get_transactions_by_category(self, category: str) -> List[Transaction]:
        """根据分类获取交易记录"""
        try:
            return Transaction.query.filter(
                Transaction.category == category
            ).order_by(Transaction.date.desc()).all()
        except Exception as e:
            self.logger.error(f"Error getting transactions by category '{category}': {e}")
            raise

    @cached_query()
    def get_transactions_summary(self) -> Dict[str, Any]:
        """获取交易汇总信息"""
        try:
            total_count = Transaction.query.count()
            income_sum = self.db.query(func.sum(Transaction.amount)).filter(Transaction.amount > 0).scalar() or 0
            expense_sum = self.db.query(func.sum(Transaction.amount)).filter(Transaction.amount < 0).scalar() or 0

            return {
                'total_count': total_count,
                'income_sum': float(income_sum),
                'expense_sum': float(expense_sum),
                'net_amount': float(income_sum + expense_sum)
            }
        except Exception as e:
            self.logger.error(f"Error getting transactions summary: {e}")
            return {'total_count': 0, 'income_sum': 0, 'expense_sum': 0, 'net_amount': 0}

    def get_all(self) -> List[Transaction]:
        """获取所有交易（实现BaseService抽象方法）"""
        try:
            return Transaction.query.order_by(Transaction.date.desc(), Transaction.id.desc()).all()
        except Exception as e:
            self._handle_service_error("获取所有交易", e)
