"""Transaction service for handling transaction-related logic."""

from typing import List, Dict, Any, Optional
from decimal import Decimal
from datetime import date, datetime
import logging
from collections import defaultdict
import decimal

from app.models import Transaction, Account, db
from flask_sqlalchemy.pagination import Pagination

from sqlalchemy import func, and_

logger = logging.getLogger(__name__)

class TransactionService:
    """Service for handling transaction operations."""
    
    def __init__(self, db_session=None):
        """初始化交易服务
        
        Args:
            db_session: 数据库会话，如果为None则使用默认会话
        """
        self.db = db_session or db.session
        self.logger = logging.getLogger(__name__)
    def get_transactions_paginated(self, filters: Dict[str, Any] = None, 
                                 page: int = 1, 
                                 per_page: int = 20) -> Pagination:
        """使用Flask-SQLAlchemy分页获取交易记录"""
        try:
            from app.models import Account, Bank
            
            query = self.db.query(Transaction).join(Account)
            
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
                    filter_type = filters['transaction_type']
                    if filter_type == 'income':
                        query = query.filter(Transaction.amount > 0)
                    elif filter_type == 'expense':
                        query = query.filter(Transaction.amount < 0)
                    elif filter_type == 'transfer':
                        query = query.filter(Transaction.amount == 0)
                
                # Counterparty filter
                if 'counterparty' in filters and filters['counterparty']:
                    query = query.filter(Transaction.counterparty.like(f"%{filters['counterparty']}%"))
                
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

    def is_duplicate_transaction(self, transaction_data: Dict[str, Any]) -> bool:
        """Check if transaction is a duplicate."""
        try:
            # 基本字段检查
            account_id = transaction_data.get('account_id')
            date = transaction_data.get('date')
            amount = transaction_data.get('amount')
            balance_after = transaction_data.get('balance_after')
            
            if account_id is None or date is None or amount is None or balance_after is None:
                self.logger.warning("重复检查失败：缺少必需字段")
                return True
            
            # 简单类型转换（主要处理pandas数值类型）
            try:
                normalized_amount = Transaction._normalize_decimal(amount)
                normalized_balance = Transaction._normalize_decimal(balance_after)
            except (ValueError, TypeError, decimal.InvalidOperation):
                self.logger.warning(f"重复检查失败：无效的amount格式或者balance_after格式 {amount} {balance_after}")
                return True
            
            # 执行查询
            query_conditions = [
                Transaction.account_id == account_id,
                Transaction.date == date,
                Transaction.amount == normalized_amount,
                Transaction.balance_after == normalized_balance
            ]
            
            existing = Transaction.query.filter(and_(*query_conditions)).first()
            return existing is not None
            
        except Exception as e:
            self.logger.error(f"重复检查异常: {e}")
            return True
    
    # Database transaction operations (migrated from DatabaseService)
    def create_transaction(self, account_id: int, date: date, 
                         amount: Decimal, currency: str = 'CNY', description: str = None,
                         counterparty: str = None, **kwargs) -> Transaction:
        """Create a new transaction."""
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
    

    
    def get_transactions(self, account_id: int = None, start_date: date = None, 
                        end_date: date = None, transaction_type: str = None,
                        limit: int = None, offset: int = None) -> List[Transaction]:
        """Get transactions with filtering options."""
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
    
    def search_transactions(self, keyword: str, account_id: int = None, 
                          start_date: date = None, end_date: date = None) -> List[Transaction]:
        """Search transactions by keyword."""
        return Transaction.search(
            keyword=keyword,
            account_id=account_id,
            start_date=start_date,
            end_date=end_date
        )
    
    def update_transaction(self, transaction_id: int, **kwargs) -> bool:
        """Update transaction information."""
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
        """Delete transaction."""
        try:
            transaction = Transaction.get_by_id(transaction_id)
            if transaction:
                transaction.delete()
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error deleting transaction {transaction_id}: {e}")
            raise
    
    def get_all_transaction_types(self) -> List[str]:
        """Get all transaction types.
        
        Returns:
            List[str]: List of available transaction types ['income', 'expense', 'transfer']
        """
        return ['income', 'expense', 'transfer']

    def get_all_currencies(self) -> List[str]:
        """Get all distinct currencies from transactions.
        
        Returns:
            List[str]: A sorted list of unique currency codes used in transactions.
            Returns ['CNY'] if any error occurs.
        """
        try:
            # 只从交易记录获取货币类型
            currencies = self.db.query(Transaction.currency).distinct().all()
            
            # 处理结果并去重
            all_currencies = {currency for (currency,) in currencies if currency}
            
            # 转换为排序列表
            return sorted(list(all_currencies))
            
        except Exception as e:
            self.logger.error(f"Error getting all currencies: {e}")
            return ['CNY']

    # ==================== 新增查询方法 (从db_utils迁移) ====================
    
    def get_by_date_range(self, start_date: date, end_date: date, 
                         account_id: Optional[int] = None) -> List[Transaction]:
        """根据日期范围获取交易记录"""
        try:
            query = Transaction.query.join(Account)
            
            if start_date:
                query = query.filter(Transaction.date >= start_date)
            if end_date:
                query = query.filter(Transaction.date <= end_date)
            if account_id:
                query = query.filter(Transaction.account_id == account_id)
                
            return query.order_by(Transaction.date.desc()).all()
        except Exception as e:
            self.logger.error(f"Error getting transactions by date range: {e}")
            return []
    
    def get_income_transactions(self, start_date: date, end_date: date, 
                              account_id: Optional[int] = None) -> List[Transaction]:
        """获取收入交易记录"""
        try:
            query = Transaction.query.join(Account).filter(Transaction.amount > 0)
            
            if start_date:
                query = query.filter(Transaction.date >= start_date)
            if end_date:
                query = query.filter(Transaction.date <= end_date)
            if account_id:
                query = query.filter(Transaction.account_id == account_id)
                
            return query.order_by(Transaction.date.desc()).all()
        except Exception as e:
            self.logger.error(f"Error getting income transactions: {e}")
            return []
    
    def get_expense_transactions(self, start_date: date, end_date: date, 
                               account_id: Optional[int] = None) -> List[Transaction]:
        """获取支出交易记录"""
        try:
            query = Transaction.query.join(Account).filter(Transaction.amount < 0)
            
            if start_date:
                query = query.filter(Transaction.date >= start_date)
            if end_date:
                query = query.filter(Transaction.date <= end_date)
            if account_id:
                query = query.filter(Transaction.account_id == account_id)
                
            return query.order_by(Transaction.date.desc()).all()
        except Exception as e:
            self.logger.error(f"Error getting expense transactions: {e}")
            return []
    
    def get_distinct_currencies(self) -> List[str]:
        """获取所有不同的货币类型"""
        try:
            currencies = self.db.query(Transaction.currency).distinct().all()
            return [c[0] for c in currencies if c[0]]
        except Exception as e:
            self.logger.error(f"Error getting distinct currencies: {e}")
            return ['CNY']
    
    def get_distinct_counterparties(self) -> List[str]:
        """获取所有不同的交易对手"""
        try:
            counterparties = self.db.query(Transaction.counterparty).distinct().all()
            return [c[0] for c in counterparties if c[0]]
        except Exception as e:
            self.logger.error(f"Error getting distinct counterparties: {e}")
            return []
    
