"""数据库工具模块

提供常用的数据库查询工具和方法，减少重复代码。
"""

from typing import List, Optional, Dict, Any, Type
from sqlalchemy import func, and_, or_
from sqlalchemy.orm import Query
from app.models.base import db
from datetime import date, datetime
from decimal import Decimal


class QueryBuilder:
    """通用查询构建器"""
    
    def __init__(self, model_class: Type):
        self.model_class = model_class
        self.query = db.session.query(model_class)
        self._joins = []
        self._filters = []
        self._order_by = []
    
    def join(self, *args, **kwargs):
        """添加JOIN子句"""
        self.query = self.query.join(*args, **kwargs)
        return self
    
    def filter(self, *criterion):
        """添加WHERE条件"""
        self.query = self.query.filter(*criterion)
        return self
    
    def filter_by(self, **kwargs):
        """添加WHERE条件（字段=值）"""
        self.query = self.query.filter_by(**kwargs)
        return self
    
    def order_by(self, *criterion):
        """添加ORDER BY子句"""
        self.query = self.query.order_by(*criterion)
        return self
    
    def limit(self, limit: int):
        """添加LIMIT子句"""
        self.query = self.query.limit(limit)
        return self
    
    def offset(self, offset: int):
        """添加OFFSET子句"""
        self.query = self.query.offset(offset)
        return self
    
    def count(self) -> int:
        """获取记录数量"""
        return self.query.count()
    
    def all(self) -> List:
        """获取所有记录"""
        return self.query.all()
    
    def first(self):
        """获取第一条记录"""
        return self.query.first()
    
    def get(self, id):
        """根据ID获取记录"""
        return self.query.get(id)


class TransactionQueries:
    """交易记录查询工具"""
    
    @staticmethod
    def get_by_date_range(start_date: date, end_date: date, 
                         account_id: Optional[int] = None) -> Query:
        """根据日期范围获取交易记录"""
        query = QueryBuilder(Transaction).join(Account)
        
        if start_date:
            query.filter(Transaction.date >= start_date)
        if end_date:
            query.filter(Transaction.date <= end_date)
        if account_id:
            query.filter(Transaction.account_id == account_id)
            
        return query.order_by(Transaction.date.desc())
    
    @staticmethod
    def get_income_transactions(start_date: date, end_date: date, 
                              account_id: Optional[int] = None) -> Query:
        """获取收入交易记录"""
        query = TransactionQueries.get_by_date_range(start_date, end_date, account_id)
        return query.filter(Transaction.amount > 0)
    
    @staticmethod
    def get_expense_transactions(start_date: date, end_date: date, 
                               account_id: Optional[int] = None) -> Query:
        """获取支出交易记录"""
        query = TransactionQueries.get_by_date_range(start_date, end_date, account_id)
        return query.filter(Transaction.amount < 0)
    
    @staticmethod
    def get_total_amount(start_date: date, end_date: date, 
                        account_id: Optional[int] = None, 
                        transaction_type: str = 'all') -> float:
        """获取指定条件下的交易总额"""
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
    
    @staticmethod
    def get_distinct_currencies() -> List[str]:
        """获取所有不同的货币类型"""
        currencies = db.session.query(Transaction.currency).distinct().all()
        return [c[0] for c in currencies if c[0]]
    
    @staticmethod
    def get_distinct_counterparties() -> List[str]:
        """获取所有不同的交易对手"""
        counterparties = db.session.query(Transaction.counterparty).distinct().all()
        return [c[0] for c in counterparties if c[0]]
    
    @staticmethod
    def get_by_account(account_id, start_date=None, end_date=None, limit=None, offset=None):
        """Get transactions by account with optional date filtering."""
        from app.models.transaction import Transaction
        query = Transaction.query.filter_by(account_id=account_id)
        
        if start_date:
            query = query.filter(Transaction.date >= start_date)
        if end_date:
            query = query.filter(Transaction.date <= end_date)
        
        query = query.order_by(Transaction.date.desc(), Transaction.created_at.desc())
        
        if offset:
            query = query.offset(offset)
        if limit:
            query = query.limit(limit)
        
        return query.all()
    
    @staticmethod
    def get_by_type(transaction_type, start_date=None, end_date=None):
        """Get transactions by type with optional date filtering."""
        from app.models.transaction import Transaction
        if transaction_type == 'income':
            query = Transaction.query.filter(Transaction.amount > 0)
        elif transaction_type == 'expense':
            query = Transaction.query.filter(Transaction.amount < 0)
        elif transaction_type == 'transfer':
            query = Transaction.query.filter(Transaction.amount == 0)
        else:
            raise ValueError(f"Invalid transaction type: {transaction_type}")
        
        if start_date:
            query = query.filter(Transaction.date >= start_date)
        if end_date:
            query = query.filter(Transaction.date <= end_date)
        
        return query.order_by(Transaction.date.desc()).all()
    
    @staticmethod
    def search(keyword, account_id=None, start_date=None, end_date=None):
        """Search transactions by keyword in description or counterparty."""
        from app.models.transaction import Transaction
        query = Transaction.query
        
        if account_id:
            query = query.filter_by(account_id=account_id)
        
        if start_date:
            query = query.filter(Transaction.date >= start_date)
        if end_date:
            query = query.filter(Transaction.date <= end_date)
        
        search_filter = db.or_(
            Transaction.description.ilike(f'%{keyword}%'),
            Transaction.counterparty.ilike(f'%{keyword}%')
        )
        query = query.filter(search_filter)
        
        return query.order_by(Transaction.date.desc()).all()
    
    @staticmethod
    def get_income_transactions(account_id=None, start_date=None, end_date=None):
        """Get income transactions (positive amounts)."""
        from app.models.transaction import Transaction
        query = Transaction.query.filter(Transaction.amount > 0)
        
        if account_id:
            query = query.filter_by(account_id=account_id)
        if start_date:
            query = query.filter(Transaction.date >= start_date)
        if end_date:
            query = query.filter(Transaction.date <= end_date)
        
        return query.order_by(Transaction.date.desc()).all()
    
    @staticmethod
    def get_expense_transactions(account_id=None, start_date=None, end_date=None):
        """Get expense transactions (negative amounts)."""
        from app.models.transaction import Transaction
        query = Transaction.query.filter(Transaction.amount < 0)
        
        if account_id:
            query = query.filter_by(account_id=account_id)
        if start_date:
            query = query.filter(Transaction.date >= start_date)
        if end_date:
            query = query.filter(Transaction.date <= end_date)
        
        return query.order_by(Transaction.date.desc()).all()
    
    @staticmethod
    def get_summary_by_type(account_id=None, start_date=None, end_date=None):
        """Get transaction summary grouped by type."""
        from app.models.transaction import Transaction
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
    
    @staticmethod
    def get_monthly_summary(account_id=None, year=None):
        """Get monthly transaction summary."""
        from app.models.transaction import Transaction
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
        
        return query.group_by(db.extract('month', Transaction.date)).order_by('month').all()


class AccountQueries:
    """账户查询工具"""
    
    @staticmethod
    def get_all_with_banks() -> List['Account']:
        """Get all accounts with their associated banks."""
        from app.models.account import Account
        return Account.query.join(Account.bank).order_by(Account.account_name).all()
    
    @staticmethod
    def get_by_number(account_number: str) -> Optional[Account]:
        """根据账户号码获取账户"""
        return QueryBuilder(Account).filter_by(account_number=account_number).first()
    
    @staticmethod
    def get_account_balance(account_id: int) -> float:
        """获取账户余额"""
        result = db.session.query(func.sum(Transaction.amount)).filter_by(account_id=account_id).scalar()
        return float(result) if result else 0.0
    
    @staticmethod
    def get_by_id(account_id: int) -> Optional[Account]:
        """根据ID获取账户"""
        return QueryBuilder(Account).get(account_id)
    
    @staticmethod
    def get_by_bank_and_number(bank_id, account_number):
        """Get account by bank ID and account number."""
        from app.models.account import Account
        if not account_number:
            return None
        return Account.query.filter_by(bank_id=bank_id, account_number=account_number.strip()).first()
    
    @staticmethod
    def get_or_create(bank_id, account_number, account_name=None, currency='CNY', account_type='checking'):
        """Get existing account or create new one."""
        from app.models.account import Account
        account = AccountQueries.get_by_bank_and_number(bank_id, account_number)
        if not account:
            account = Account.create(
                bank_id=bank_id,
                account_number=account_number,
                account_name=account_name,
                currency=currency,
                account_type=account_type
            )
        return account
    
    @staticmethod
    def get_all_accounts(bank_id=None):
        """Get all accounts, optionally filtered by bank."""
        from app.models.account import Account
        query = Account.query
        if bank_id:
            query = query.filter_by(bank_id=bank_id)
        return query.order_by(Account.account_name, Account.account_number).all()
    
    @staticmethod
    def get_all_accounts_balance():
        """Get the sum of current balances for all accounts."""
        from app.models.transaction import Transaction
        from app.models.account import Account
        account_balances = db.session.query(
            Transaction.account_id,
            Transaction.balance_after
        ).distinct(
            Transaction.account_id
        ).order_by(
            Transaction.account_id,
            Transaction.date.desc(),
            Transaction.created_at.desc()
        ).all()
        
        return sum(Decimal(str(balance)) for _, balance in account_balances) if account_balances else Decimal('0.00')
    
    @staticmethod
    def get_monthly_balance_trends(months=12):
        """Get monthly balance trends for all accounts."""
        from app.models.transaction import Transaction
        from app.models.account import Account
        monthly_trends = db.session.query(
            func.strftime('%Y-%m', Transaction.date).label('month'),
            func.sum(Transaction.balance_after).label('balance')
        ).filter(
            Transaction.date >= func.date('now', f'-{months} months')
        ).group_by(
            func.strftime('%Y-%m', Transaction.date)
        ).order_by(
            func.strftime('%Y-%m', Transaction.date)
        ).all()
        
        return [{
            'month': month,
            'balance': Decimal(str(balance))
        } for month, balance in monthly_trends]


class BankQueries:
    """银行查询工具"""
    
    @staticmethod
    def get_by_name(name):
        """Get bank by name."""
        from app.models.bank import Bank
        return Bank.query.filter_by(name=name.strip()).first()
    
    @staticmethod
    def get_by_code(code):
        """Get bank by code."""
        from app.models.bank import Bank
        if not code:
            return None
        return Bank.query.filter_by(code=code.strip().upper()).first()
    
    @staticmethod
    def get_or_create(name, code=None):
        """Get existing bank or create new one."""
        from app.models.bank import Bank
        bank = BankQueries.get_by_name(name)
        if not bank:
            bank = Bank.create(name=name, code=code)
        return bank
    
    @staticmethod
    def get_all() -> List[Bank]:
        """获取所有银行"""
        return QueryBuilder(Bank).order_by(Bank.name).all()


class AggregationQueries:
    """聚合查询工具"""
    
    @staticmethod
    def group_by_category(start_date: date, end_date: date, 
                         account_id: Optional[int] = None, 
                         abs_amount: bool = False) -> Dict[str, float]:
        """按类别分组统计"""
        query = db.session.query(
            Transaction.counterparty,
            func.sum(func.abs(Transaction.amount) if abs_amount else Transaction.amount)
        )
        
        if account_id:
            query = query.filter(Transaction.account_id == account_id)
        if start_date:
            query = query.filter(Transaction.date >= start_date)
        if end_date:
            query = query.filter(Transaction.date <= end_date)
        
        query = query.group_by(Transaction.counterparty)
        
        result = {}
        for counterparty, amount in query.all():
            if counterparty:
                result[counterparty] = float(amount) if amount else 0.0
        
        return result
    
    @staticmethod
    def group_by_month(start_date: date, end_date: date, 
                      account_id: Optional[int] = None, 
                      abs_amount: bool = False) -> Dict[str, float]:
        """按月份分组统计"""
        query = db.session.query(
            func.date_format(Transaction.date, '%Y-%m').label('month'),
            func.sum(func.abs(Transaction.amount) if abs_amount else Transaction.amount)
        )
        
        if account_id:
            query = query.filter(Transaction.account_id == account_id)
        if start_date:
            query = query.filter(Transaction.date >= start_date)
        if end_date:
            query = query.filter(Transaction.date <= end_date)
        
        query = query.group_by('month').order_by('month')
        
        result = {}
        for month, amount in query.all():
            if month:
                result[month] = float(amount) if amount else 0.0
        
        return result


def safe_query_execute(query_func, default_value=None, log_error=True):
    """安全执行查询，处理异常"""
    try:
        return query_func()
    except Exception as e:
        if log_error:
            from flask import current_app
            current_app.logger.error(f"数据库查询执行失败: {e}")
        return default_value