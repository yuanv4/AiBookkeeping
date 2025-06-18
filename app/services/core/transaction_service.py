"""Transaction service for handling transaction-related logic."""

from typing import List, Dict, Any, Optional
from decimal import Decimal
from datetime import date, datetime
import logging
from collections import defaultdict

from app.models import Transaction, Account, db
from flask_sqlalchemy.pagination import Pagination

from sqlalchemy import func, and_

logger = logging.getLogger(__name__)

class TransactionService:
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

    # ==================== 支出分析专用方法 ====================

    @staticmethod
    def get_expense_statistics(start_date: Optional[date] = None, 
                             end_date: Optional[date] = None, 
                             account_id: Optional[int] = None) -> Dict[str, Any]:
        """获取支出统计信息
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            account_id: 账户ID，None表示所有账户
            
        Returns:
            Dict[str, Any]: 支出统计信息
        """
        try:
            # 设置默认日期范围
            if not end_date:
                end_date = date.today()
            if not start_date:
                start_date = date(end_date.year - 1, end_date.month, end_date.day)
            
            # 构建基础查询
            query = db.session.query(Transaction).filter(
                Transaction.amount < 0,  # 只查询支出
                Transaction.date >= start_date,
                Transaction.date <= end_date
            )
            
            # 添加账户过滤
            if account_id:
                query = query.filter(Transaction.account_id == account_id)
            
            # 计算总支出金额
            total_expense = query.with_entities(
                func.sum(func.abs(Transaction.amount))
            ).scalar() or Decimal('0.00')
            
            # 计算支出交易笔数
            expense_count = query.count()
            
            # 计算最大单笔支出
            max_expense = query.with_entities(
                func.max(func.abs(Transaction.amount))
            ).scalar() or Decimal('0.00')
            
            # 计算平均每笔支出
            avg_expense = total_expense / expense_count if expense_count > 0 else Decimal('0.00')
            
            # 计算支出占收入比例
            income_query = db.session.query(Transaction).filter(
                Transaction.amount > 0,  # 只查询收入
                Transaction.date >= start_date,
                Transaction.date <= end_date
            )
            if account_id:
                income_query = income_query.filter(Transaction.account_id == account_id)
            
            total_income = income_query.with_entities(
                func.sum(Transaction.amount)
            ).scalar() or Decimal('0.00')
            
            expense_ratio = (total_expense / total_income * 100) if total_income > 0 else 0
            
            return {
                'total_expense': float(total_expense),
                'expense_count': expense_count,
                'max_expense': float(max_expense),
                'avg_expense': float(avg_expense),
                'total_income': float(total_income),
                'expense_ratio': float(expense_ratio),
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting expense statistics: {e}")
            return {}

    @staticmethod
    def get_top_expense_counterparties(start_date: Optional[date] = None, 
                                     end_date: Optional[date] = None, 
                                     account_id: Optional[int] = None, 
                                     limit: int = 10, 
                                     sort_by: str = 'amount') -> List[Dict[str, Any]]:
        """获取支出对手方排名
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            account_id: 账户ID，None表示所有账户
            limit: 返回结果数量限制
            sort_by: 排序方式，'amount'按金额，'frequency'按频次
            
        Returns:
            List[Dict[str, Any]]: 支出对手方排名数据
        """
        try:
            # 设置默认日期范围
            if not end_date:
                end_date = date.today()
            if not start_date:
                start_date = date(end_date.year - 1, end_date.month, end_date.day)
            
            # 构建查询
            query = db.session.query(
                Transaction.counterparty,
                func.sum(func.abs(Transaction.amount)).label('total_amount'),
                func.count(Transaction.id).label('transaction_count'),
                func.avg(func.abs(Transaction.amount)).label('avg_amount')
            ).filter(
                Transaction.amount < 0,  # 只查询支出
                Transaction.date >= start_date,
                Transaction.date <= end_date,
                Transaction.counterparty.isnot(None),
                Transaction.counterparty != ''
            )
            
            # 添加账户过滤
            if account_id:
                query = query.filter(Transaction.account_id == account_id)
            
            # 分组
            query = query.group_by(Transaction.counterparty)
            
            # 排序
            if sort_by == 'frequency':
                query = query.order_by(func.count(Transaction.id).desc())
            else:  # 默认按金额排序
                query = query.order_by(func.sum(func.abs(Transaction.amount)).desc())
            
            # 限制结果数量
            results = query.limit(limit).all()
            
            # 格式化结果
            counterparty_data = [{
                'counterparty': result.counterparty,
                'total_amount': float(result.total_amount or 0),
                'transaction_count': result.transaction_count or 0,
                'avg_amount': float(result.avg_amount or 0)
            } for result in results]
            
            return counterparty_data
            
        except Exception as e:
            logger.error(f"Error getting top expense counterparties: {e}")
            return []

    @staticmethod
    def get_expense_transactions_paginated(filters: Dict[str, Any] = None, 
                                         page: int = 1, 
                                         per_page: int = 20) -> Pagination:
        """获取支出交易记录（分页）
        
        Args:
            filters: 过滤条件
            page: 页码
            per_page: 每页数量
            
        Returns:
            Pagination: 分页结果
        """
        try:
            from app.models import Account, Bank
            
            # 构建基础查询，只查询支出
            query = db.session.query(Transaction).join(Account).filter(
                Transaction.amount < 0  # 只查询支出
            )
            
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
                    query = query.filter(func.abs(Transaction.amount) >= filters['min_amount'])
                
                if 'max_amount' in filters and filters['max_amount'] is not None:
                    query = query.filter(func.abs(Transaction.amount) <= filters['max_amount'])
                
                # Counterparty filter
                if 'counterparty' in filters and filters['counterparty']:
                    query = query.filter(Transaction.counterparty.like(f"%{filters['counterparty']}%"))
                
                # Currency filter
                if 'currency' in filters and filters['currency']:
                    query = query.filter(Transaction.currency == filters['currency'])
            
            # 按日期降序排序
            query = query.order_by(Transaction.date.desc(), Transaction.created_at.desc())
            
            # 使用Flask-SQLAlchemy的分页功能
            return query.paginate(
                page=page,
                per_page=per_page,
                error_out=False
            )
            
        except Exception as e:
            logger.error(f"Error getting expense transactions with pagination: {e}")
            # 返回空的分页对象
            return db.session.query(Transaction).filter(Transaction.id == -1).paginate(
                page=1, per_page=per_page, error_out=False
            )