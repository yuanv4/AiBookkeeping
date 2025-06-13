"""数据服务层 - 统一处理所有财务数据访问逻辑

该模块提供统一的数据访问接口，将数据库查询逻辑从分析器中分离出来，
提高代码复用性和可维护性。

Created: 2024-12-19
Author: AI Assistant
"""

from datetime import datetime, date
from typing import Dict, List, Optional, Tuple, Any
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, extract

from app.models.transaction import Transaction
from app.models.account import Account
from app.database import get_db


class DataService:
    """财务数据访问服务
    
    提供统一的数据访问接口，封装所有与数据库交询相关的逻辑。
    """
    
    def __init__(self, db_session: Optional[Session] = None):
        """初始化数据服务
        
        Args:
            db_session: 数据库会话，如果为None则使用默认会话
        """
        self.db = db_session or next(get_db())
    
    def get_income_expense_totals(
        self, 
        start_date: date, 
        end_date: date, 
        account_id: Optional[int] = None
    ) -> Dict[str, Decimal]:
        """获取收入和支出总额
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            account_id: 可选的账户ID，用于过滤特定账户
            
        Returns:
            包含收入和支出总额的字典
        """
        try:
            query = self.db.query(
                func.sum(
                    func.case(
                        (Transaction.amount > 0, Transaction.amount),
                        else_=0
                    )
                ).label('total_income'),
                func.sum(
                    func.case(
                        (Transaction.amount < 0, func.abs(Transaction.amount)),
                        else_=0
                    )
                ).label('total_expense')
            ).filter(
                and_(
                    Transaction.date >= start_date,
                    Transaction.date <= end_date
                )
            )
            
            if account_id:
                query = query.filter(Transaction.account_id == account_id)
            
            result = query.first()
            
            return {
                'total_income': result.total_income or Decimal('0'),
                'total_expense': result.total_expense or Decimal('0')
            }
            
        except Exception as e:
            # 记录错误并返回默认值
            print(f"Error in get_income_expense_totals: {e}")
            return {
                'total_income': Decimal('0'),
                'total_expense': Decimal('0')
            }
    
    def get_monthly_breakdown(
        self, 
        start_date: date, 
        end_date: date, 
        account_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """获取按月分解的收入支出数据
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            account_id: 可选的账户ID
            
        Returns:
            按月分组的收入支出数据列表
        """
        try:
            query = self.db.query(
                extract('year', Transaction.date).label('year'),
                extract('month', Transaction.date).label('month'),
                func.sum(
                    func.case(
                        (Transaction.amount > 0, Transaction.amount),
                        else_=0
                    )
                ).label('income'),
                func.sum(
                    func.case(
                        (Transaction.amount < 0, func.abs(Transaction.amount)),
                        else_=0
                    )
                ).label('expense'),
                func.count(Transaction.id).label('transaction_count')
            ).filter(
                and_(
                    Transaction.date >= start_date,
                    Transaction.date <= end_date
                )
            )
            
            if account_id:
                query = query.filter(Transaction.account_id == account_id)
            
            query = query.group_by(
                extract('year', Transaction.date),
                extract('month', Transaction.date)
            ).order_by(
                extract('year', Transaction.date),
                extract('month', Transaction.date)
            )
            
            results = query.all()
            
            monthly_data = []
            for result in results:
                monthly_data.append({
                    'year': int(result.year),
                    'month': int(result.month),
                    'income': result.income or Decimal('0'),
                    'expense': result.expense or Decimal('0'),
                    'net': (result.income or Decimal('0')) - (result.expense or Decimal('0')),
                    'transaction_count': result.transaction_count
                })
            
            return monthly_data
            
        except Exception as e:
            print(f"Error in get_monthly_breakdown: {e}")
            return []
    
    def get_transaction_categories(
        self, 
        start_date: date, 
        end_date: date, 
        account_id: Optional[int] = None,
        transaction_type: Optional[str] = None  # 'income' or 'expense'
    ) -> List[Dict[str, Any]]:
        """获取交易分类统计
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            account_id: 可选的账户ID
            transaction_type: 交易类型过滤 ('income' 或 'expense')
            
        Returns:
            分类统计数据列表
        """
        try:
            query = self.db.query(
                Category.name.label('category_name'),
                Category.id.label('category_id'),
                func.sum(func.abs(Transaction.amount)).label('total_amount'),
                func.count(Transaction.id).label('transaction_count'),
                func.avg(func.abs(Transaction.amount)).label('avg_amount')
            ).join(
                Transaction, Transaction.category_id == Category.id
            ).filter(
                and_(
                    Transaction.date >= start_date,
                    Transaction.date <= end_date
                )
            )
            
            if account_id:
                query = query.filter(Transaction.account_id == account_id)
            
            if transaction_type == 'income':
                query = query.filter(Transaction.amount > 0)
            elif transaction_type == 'expense':
                query = query.filter(Transaction.amount < 0)
            
            query = query.group_by(
                Category.id, Category.name
            ).order_by(
                func.sum(func.abs(Transaction.amount)).desc()
            )
            
            results = query.all()
            
            categories = []
            for result in results:
                categories.append({
                    'category_id': result.category_id,
                    'category_name': result.category_name,
                    'total_amount': result.total_amount or Decimal('0'),
                    'transaction_count': result.transaction_count,
                    'avg_amount': result.avg_amount or Decimal('0')
                })
            
            return categories
            
        except Exception as e:
            print(f"Error in get_transaction_categories: {e}")
            return []
    
    def get_cash_flow_data(
        self, 
        start_date: date, 
        end_date: date, 
        account_id: Optional[int] = None,
        group_by: str = 'month'  # 'day', 'week', 'month'
    ) -> List[Dict[str, Any]]:
        """获取现金流数据
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            account_id: 可选的账户ID
            group_by: 分组方式 ('day', 'week', 'month')
            
        Returns:
            现金流数据列表
        """
        try:
            # 根据分组方式选择不同的时间提取函数
            if group_by == 'day':
                time_group = func.date(Transaction.date)
                time_label = 'date'
            elif group_by == 'week':
                time_group = func.date_trunc('week', Transaction.date)
                time_label = 'week_start'
            else:  # month
                time_group = func.date_trunc('month', Transaction.date)
                time_label = 'month_start'
            
            query = self.db.query(
                time_group.label(time_label),
                func.sum(Transaction.amount).label('net_flow'),
                func.sum(
                    func.case(
                        (Transaction.amount > 0, Transaction.amount),
                        else_=0
                    )
                ).label('inflow'),
                func.sum(
                    func.case(
                        (Transaction.amount < 0, func.abs(Transaction.amount)),
                        else_=0
                    )
                ).label('outflow'),
                func.count(Transaction.id).label('transaction_count')
            ).filter(
                and_(
                    Transaction.date >= start_date,
                    Transaction.date <= end_date
                )
            )
            
            if account_id:
                query = query.filter(Transaction.account_id == account_id)
            
            query = query.group_by(time_group).order_by(time_group)
            
            results = query.all()
            
            cash_flow_data = []
            for result in results:
                data_point = {
                    time_label: result[0],
                    'net_flow': result.net_flow or Decimal('0'),
                    'inflow': result.inflow or Decimal('0'),
                    'outflow': result.outflow or Decimal('0'),
                    'transaction_count': result.transaction_count
                }
                cash_flow_data.append(data_point)
            
            return cash_flow_data
            
        except Exception as e:
            print(f"Error in get_cash_flow_data: {e}")
            return []
    
    def get_account_balances(
        self, 
        as_of_date: Optional[date] = None,
        account_ids: Optional[List[int]] = None
    ) -> List[Dict[str, Any]]:
        """获取账户余额
        
        Args:
            as_of_date: 截止日期，如果为None则使用当前日期
            account_ids: 账户ID列表，如果为None则获取所有账户
            
        Returns:
            账户余额数据列表
        """
        try:
            if as_of_date is None:
                as_of_date = date.today()
            
            query = self.db.query(
                Account.id.label('account_id'),
                Account.name.label('account_name'),
                Account.account_type.label('account_type'),
                func.coalesce(
                    func.sum(Transaction.amount), 
                    Decimal('0')
                ).label('balance')
            ).outerjoin(
                Transaction, 
                and_(
                    Transaction.account_id == Account.id,
                    Transaction.date <= as_of_date
                )
            )
            
            if account_ids:
                query = query.filter(Account.id.in_(account_ids))
            
            query = query.group_by(
                Account.id, Account.name, Account.account_type
            ).order_by(Account.name)
            
            results = query.all()
            
            balances = []
            for result in results:
                balances.append({
                    'account_id': result.account_id,
                    'account_name': result.account_name,
                    'account_type': result.account_type,
                    'balance': result.balance
                })
            
            return balances
            
        except Exception as e:
            print(f"Error in get_account_balances: {e}")
            return []
    
    def get_transaction_count(
        self, 
        start_date: date, 
        end_date: date, 
        account_id: Optional[int] = None
    ) -> int:
        """获取交易数量
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            account_id: 可选的账户ID
            
        Returns:
            交易数量
        """
        try:
            query = self.db.query(func.count(Transaction.id)).filter(
                and_(
                    Transaction.date >= start_date,
                    Transaction.date <= end_date
                )
            )
            
            if account_id:
                query = query.filter(Transaction.account_id == account_id)
            
            return query.scalar() or 0
            
        except Exception as e:
            print(f"Error in get_transaction_count: {e}")
            return 0
    
    def close(self):
        """关闭数据库连接"""
        if self.db:
            self.db.close()