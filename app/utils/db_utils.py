"""数据库工具模块

提供常用的数据库查询工具和方法，减少重复代码。
"""

from typing import List, Optional, Dict, Any, Type
from sqlalchemy import func, and_, or_
from sqlalchemy.orm import Query
from app.models.base import db
from app.models import Transaction, Account, Bank
from datetime import date


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


class AccountQueries:
    """账户查询工具"""
    
    @staticmethod
    def get_all_with_banks() -> List[Account]:
        """获取所有账户及其银行信息"""
        return QueryBuilder(Account).join(Bank).all()
    
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


class BankQueries:
    """银行查询工具"""
    
    @staticmethod
    def get_or_create(name: str, code: Optional[str] = None) -> Bank:
        """获取或创建银行"""
        bank = QueryBuilder(Bank).filter_by(name=name).first()
        if not bank:
            bank = Bank(name=name, code=code)
            db.session.add(bank)
            db.session.commit()
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