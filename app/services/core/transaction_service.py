"""Transaction service for handling transaction-related business logic.

This module provides transaction processing, validation, and analysis functionality.
"""

from typing import List, Dict, Any, Optional, Tuple
from decimal import Decimal
from datetime import date, datetime
import logging
from collections import defaultdict

from app.models import Transaction, Account, db
from flask_sqlalchemy.pagination import Pagination

from sqlalchemy import func, and_

logger = logging.getLogger(__name__)

class TransactionService:
    """Service for handling transaction operations and business logic."""

    @staticmethod
    def get_transactions_paginated(filters: Dict[str, Any] = None, 
                                 page: int = 1, 
                                 per_page: int = 20) -> Pagination:
        """使用Flask-SQLAlchemy分页获取交易记录"""
        try:
            from app.models import Account, Bank
            
            query = db.session.query(Transaction).join(Account)
            
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
            logger.error(f"Error getting transactions with pagination: {e}")
            # 返回空的分页对象
            return db.session.query(Transaction).filter(Transaction.id == -1).paginate(
                page=1, per_page=per_page, error_out=False
            )

    @staticmethod
    def is_duplicate_transaction(transaction_data: Dict[str, Any]) -> bool:
        """Check if transaction is a duplicate."""
        try:
            existing = Transaction.query.filter(
                and_(
                    Transaction.account_id == transaction_data.get('account_id'),
                    Transaction.date == transaction_data.get('date'),
                    Transaction.amount == transaction_data.get('amount'),
                    Transaction.balance_after == transaction_data.get('balance_after')
                )
            ).first()
            return existing is not None
        except Exception:
            return False
    
    # Database transaction operations (migrated from DatabaseService)
    @staticmethod
    def create_transaction(account_id: int, date: date, 
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
            logger.error(f"Error creating transaction: {e}")
            raise
    
    @staticmethod
    def get_transactions(account_id: int = None, start_date: date = None, 
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
    
    @staticmethod
    def search_transactions(keyword: str, account_id: int = None, 
                          start_date: date = None, end_date: date = None) -> List[Transaction]:
        """Search transactions by keyword."""
        return Transaction.search(
            keyword=keyword,
            account_id=account_id,
            start_date=start_date,
            end_date=end_date
        )
    
    @staticmethod
    def update_transaction(transaction_id: int, **kwargs) -> bool:
        """Update transaction information."""
        try:
            transaction = Transaction.get_by_id(transaction_id)
            if transaction:
                transaction.update(**kwargs)
                return True
            return False
        except Exception as e:
            logger.error(f"Error updating transaction {transaction_id}: {e}")
            raise
    
    @staticmethod
    def delete_transaction(transaction_id: int) -> bool:
        """Delete transaction."""
        try:
            transaction = Transaction.get_by_id(transaction_id)
            if transaction:
                transaction.delete()
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting transaction {transaction_id}: {e}")
            raise
    
    @staticmethod
    def get_all_transaction_types() -> List[str]:
        """Get all transaction types.
        
        Returns:
            List[str]: List of available transaction types ['income', 'expense', 'transfer']
        """
        return ['income', 'expense', 'transfer']

    @staticmethod
    def get_all_currencies() -> List[str]:
        """Get all distinct currencies from transactions.
        
        Returns:
            List[str]: A sorted list of unique currency codes used in transactions.
            Returns ['CNY'] if any error occurs.
        """
        try:
            # 只从交易记录获取货币类型
            currencies = db.session.query(Transaction.currency).distinct().all()
            
            # 处理结果并去重
            all_currencies = {currency for (currency,) in currencies if currency}
            
            # 转换为排序列表
            return sorted(list(all_currencies))
            
        except Exception as e:
            logger.error(f"Error getting all currencies: {e}")
            return ['CNY']

    # ==================== 新增查询方法 (从db_utils迁移) ====================
    
    @staticmethod
    def get_by_date_range(start_date: date, end_date: date, 
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
            logger.error(f"Error getting transactions by date range: {e}")
            return []
    
    @staticmethod
    def get_income_transactions(start_date: date, end_date: date, 
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
            logger.error(f"Error getting income transactions: {e}")
            return []
    
    @staticmethod
    def get_expense_transactions(start_date: date, end_date: date, 
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
            logger.error(f"Error getting expense transactions: {e}")
            return []
    
    @staticmethod
    def get_total_amount(start_date: date, end_date: date, 
                        account_id: Optional[int] = None, 
                        transaction_type: str = 'all') -> float:
        """获取指定条件下的交易总额"""
        try:
            query = db.session.query(func.sum(Transaction.amount))
            
            if account_id:
                query = query.filter(Transaction.account_id == account_id)
            if start_date:
                query = query.filter(Transaction.date >= start_date)
            if end_date:
                query = query.filter(Transaction.date <= end_date)
            
            if transaction_type == 'income':
                query = query.filter(Transaction.amount > 0)
            elif transaction_type == 'expense':
                query = query.filter(Transaction.amount < 0)
            
            result = query.scalar()
            return float(result) if result else 0.0
        except Exception as e:
            logger.error(f"Error getting total amount: {e}")
            return 0.0
    
    @staticmethod
    def get_distinct_currencies() -> List[str]:
        """获取所有不同的货币类型"""
        try:
            currencies = db.session.query(Transaction.currency).distinct().all()
            return [c[0] for c in currencies if c[0]]
        except Exception as e:
            logger.error(f"Error getting distinct currencies: {e}")
            return ['CNY']
    
    @staticmethod
    def get_distinct_counterparties() -> List[str]:
        """获取所有不同的交易对手"""
        try:
            counterparties = db.session.query(Transaction.counterparty).distinct().all()
            return [c[0] for c in counterparties if c[0]]
        except Exception as e:
            logger.error(f"Error getting distinct counterparties: {e}")
            return []
    
    @staticmethod
    def get_summary_by_type(account_id: Optional[int] = None, 
                           start_date: Optional[date] = None, 
                           end_date: Optional[date] = None) -> List[Dict[str, Any]]:
        """Get transaction summary grouped by type."""
        try:
            income_query = db.session.query(
                db.literal('income').label('type'),
                db.func.count(Transaction.id).label('count'),
                db.func.sum(Transaction.amount).label('total')
            ).filter(Transaction.amount > 0)
            
            expense_query = db.session.query(
                db.literal('expense').label('type'),
                db.func.count(Transaction.id).label('count'),
                db.func.sum(Transaction.amount).label('total')
            ).filter(Transaction.amount < 0)
            
            transfer_query = db.session.query(
                db.literal('transfer').label('type'),
                db.func.count(Transaction.id).label('count'),
                db.func.sum(Transaction.amount).label('total')
            ).filter(Transaction.amount == 0)
            
            for query in [income_query, expense_query, transfer_query]:
                if account_id:
                    query = query.filter(Transaction.account_id == account_id)
                if start_date:
                    query = query.filter(Transaction.date >= start_date)
                if end_date:
                    query = query.filter(Transaction.date <= end_date)
            
            results = income_query.union_all(expense_query).union_all(transfer_query).all()
            
            formatted_results = []
            for type_name, count, total in results:
                formatted_results.append({
                    'name': type_name,
                    'is_income': type_name == 'income',
                    'count': count,
                    'total': total
                })
            
            return sorted(formatted_results, key=lambda x: x['name'])
        except Exception as e:
            logger.error(f"Error getting summary by type: {e}")
            return []
    
    @staticmethod
    def get_monthly_summary(account_id: Optional[int] = None, year: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get monthly transaction summary."""
        try:
            if not year:
                year = date.today().year
            
            query = db.session.query(
                db.extract('month', Transaction.date).label('month'),
                db.func.sum(db.case((Transaction.amount > 0, Transaction.amount), else_=0)).label('income'),
                db.func.sum(db.case((Transaction.amount < 0, Transaction.amount), else_=0)).label('expense'),
                db.func.count(Transaction.id).label('count')
            ).filter(db.extract('year', Transaction.date) == year)
            
            if account_id:
                query = query.filter(Transaction.account_id == account_id)
            
            results = query.group_by(db.extract('month', Transaction.date)).order_by('month').all()
            
            return [{
                'month': int(month),
                'income': float(income) if income else 0.0,
                'expense': float(expense) if expense else 0.0,
                'count': count
            } for month, income, expense, count in results]
        except Exception as e:
            logger.error(f"Error getting monthly summary: {e}")
            return []