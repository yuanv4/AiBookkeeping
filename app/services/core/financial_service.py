"""统一财务服务
"""

from typing import List, Dict, Any, Optional, Union
from decimal import Decimal
from datetime import date, datetime
import logging

from app.models import Transaction, db
from sqlalchemy import func, case
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from sqlalchemy.sql.expression import over

logger = logging.getLogger(__name__)

class FinancialService:
    """统一财务服务
    
    整合了财务分析和报告生成功能，提供一站式的财务数据处理服务。
    消除了原有架构中的功能重复和接口复杂性。
    """
    def __init__(self, db_session: Optional[Session] = None):
        """初始化财务服务
        
        Args:
            db_session: 数据库会话，如果为None则使用默认会话
        """
        self.db = db_session or db.session
        self.logger = logging.getLogger(__name__)
    
    # ==================== 计算方法 ====================

    def get_income_data(self, months: int = 12) -> List[Dict[str, Any]]:
        """获取收入交易数据
        
        Args:
            months: 查询月数，默认12个月
            
        Returns:
            List[Dict[str, Any]]: 返回相应格式的数据
        """
        try:
            
            # 格式化结果
            result_data = []

            # TODO
            
            return result_data
            
        except Exception as e:
            self.logger.error(f"获取收入数据失败: {e}")
            return []

    def get_balance_data(self, months: int = 12) -> List[Dict[str, Any]]:
        """获取余额趋势
        
        Args:
            months: 查询月数，默认12个月

        Returns:
            List[Dict[str, Any]]: 返回相应格式的数据
            
        Raises:
            SQLAlchemyError: 数据库查询异常时抛出
        """
        try:
            # 使用窗口函数查询每个账户每个月的最终余额
            window_func = over(
                func.row_number(),
                partition_by=[Transaction.account_id, func.strftime('%Y-%m', Transaction.date)],
                order_by=[Transaction.date.desc(), Transaction.created_at.desc()]
            )
            
            # 子查询：获取每个账户每个月的最终交易记录
            monthly_balances = self.db.query(
                Transaction.account_id,
                func.strftime('%Y-%m', Transaction.date).label('month'),
                Transaction.balance_after
            ).add_columns(
                window_func.label('rn')
            ).filter(
                Transaction.date >= func.date('now', f'-{months} months')
            ).subquery()
            
            # 主查询：筛选最终记录并按月分组
            query = self.db.query(
                monthly_balances.c.month,
                func.sum(monthly_balances.c.balance_after).label('balance')
            ).filter(
                monthly_balances.c.rn == 1
            ).group_by(
                monthly_balances.c.month
            ).order_by(
                monthly_balances.c.month
            )
            
            results = query.all()
            
            # 返回历史趋势数据
            result_data = [{
                'month': result.month,
                'balance': float(result.balance or 0)
            } for result in results]
            
            return result_data
            
        except SQLAlchemyError as e:
            self.logger.error(f"数据库查询异常 - 统一余额查询失败: {e}")
            return []
        except Exception as e:
            self.logger.error(f"统一余额查询失败: {e}")
            return []

    # ==================== 支出分析方法 ====================

    def get_expense_overview(self, start_date: Optional[date] = None, 
                           end_date: Optional[date] = None, 
                           account_id: Optional[int] = None) -> Dict[str, Any]:
        """获取支出概览统计
        
        Args:
            start_date: 开始日期，None表示查询所有历史数据
            end_date: 结束日期，默认为今天
            account_id: 账户ID，None表示所有账户
            
        Returns:
            Dict[str, Any]: 支出概览数据
        """
        try:
            # 设置默认日期范围
            if not end_date:
                end_date = date.today()
            # 移除默认的12个月限制，当start_date为None时查询所有历史数据
            
            # 构建基础查询
            query = self.db.query(Transaction).filter(
                Transaction.amount < 0  # 只查询支出
            )
            
            # 添加时间范围过滤（如果指定了start_date）
            if start_date:
                query = query.filter(Transaction.date >= start_date)
            query = query.filter(Transaction.date <= end_date)
            
            # 添加账户过滤
            if account_id:
                query = query.filter(Transaction.account_id == account_id)
            
            # 计算总支出金额
            total_expense = query.with_entities(
                func.sum(func.abs(Transaction.amount))
            ).scalar() or Decimal('0.00')
            
            # 计算支出交易笔数
            expense_count = query.count()
            
            # 计算平均每月支出
            if start_date:
                months_diff = (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month)
                if months_diff == 0:
                    months_diff = 1
            else:
                # 查询所有历史数据时，计算从最早交易到现在的月数
                earliest_date = self.db.query(func.min(Transaction.date)).filter(
                    Transaction.amount < 0
                ).scalar()
                if earliest_date:
                    months_diff = (end_date.year - earliest_date.year) * 12 + (end_date.month - earliest_date.month)
                    if months_diff == 0:
                        months_diff = 1
                else:
                    months_diff = 1
            
            avg_monthly_expense = total_expense / months_diff
            
            return {
                'total_expense': float(total_expense),
                'expense_count': expense_count,
                'avg_monthly_expense': float(avg_monthly_expense),
                'start_date': start_date.isoformat() if start_date else None,
                'end_date': end_date.isoformat(),
                'months': months_diff
            }
            
        except SQLAlchemyError as e:
            self.logger.error(f"数据库查询异常 - 支出概览查询失败: {e}")
            return {}
        except Exception as e:
            self.logger.error(f"支出概览查询失败: {e}")
            return {}

    def get_expense_trends(self, months: int = 12, 
                          account_id: Optional[int] = None,
                          all_history: bool = False) -> List[Dict[str, Any]]:
        """获取支出趋势数据
        
        Args:
            months: 查询月数，默认12个月（仅在all_history=False时使用）
            account_id: 账户ID，None表示所有账户
            all_history: 是否查询所有历史数据，True时忽略months参数
            
        Returns:
            List[Dict[str, Any]]: 支出趋势数据
        """
        try:
            # 构建查询
            query = self.db.query(
                func.strftime('%Y-%m', Transaction.date).label('month'),
                func.sum(func.abs(Transaction.amount)).label('expense_amount'),
                func.count(Transaction.id).label('expense_count')
            ).filter(
                Transaction.amount < 0  # 只查询支出
            )
            
            # 添加时间范围过滤
            if not all_history:
                query = query.filter(Transaction.date >= func.date('now', f'-{months} months'))
            
            # 添加账户过滤
            if account_id:
                query = query.filter(Transaction.account_id == account_id)
            
            # 分组和排序
            results = query.group_by(
                func.strftime('%Y-%m', Transaction.date)
            ).order_by(
                func.strftime('%Y-%m', Transaction.date)
            ).all()
            
            # 格式化结果
            trend_data = [{
                'month': result.month,
                'expense_amount': float(result.expense_amount or 0),
                'expense_count': result.expense_count or 0
            } for result in results]
            
            return trend_data
            
        except SQLAlchemyError as e:
            self.logger.error(f"数据库查询异常 - 支出趋势查询失败: {e}")
            return []
        except Exception as e:
            self.logger.error(f"支出趋势查询失败: {e}")
            return []

    def get_expense_patterns(self, start_date: Optional[date] = None, 
                           end_date: Optional[date] = None, 
                           account_id: Optional[int] = None) -> Dict[str, Any]:
        """获取支出模式分析
        
        Args:
            start_date: 开始日期，None表示查询所有历史数据
            end_date: 结束日期，默认为今天
            account_id: 账户ID，None表示所有账户
            
        Returns:
            Dict[str, Any]: 支出模式数据
        """
        try:
            # 设置默认日期范围
            if not end_date:
                end_date = date.today()
            # 移除默认的12个月限制，当start_date为None时查询所有历史数据
            
            # 构建基础查询
            query = self.db.query(Transaction).filter(
                Transaction.amount < 0  # 只查询支出
            )
            
            # 添加时间范围过滤（如果指定了start_date）
            if start_date:
                query = query.filter(Transaction.date >= start_date)
            query = query.filter(Transaction.date <= end_date)
            
            # 添加账户过滤
            if account_id:
                query = query.filter(Transaction.account_id == account_id)
            
            # 获取所有支出交易
            transactions = query.all()
            
            # 分析固定支出（相同对手方、相似金额的重复交易）
            fixed_expenses = self._analyze_fixed_expenses(transactions)
            
            # 分析异常支出（超过平均值的2倍标准差）
            abnormal_expenses = self._analyze_abnormal_expenses(transactions)
            
            # 分析支出集中度（按周分布）
            weekly_distribution = self._analyze_weekly_distribution(transactions)
            
            return {
                'fixed_expenses': fixed_expenses,
                'abnormal_expenses': abnormal_expenses,
                'weekly_distribution': weekly_distribution
            }
            
        except SQLAlchemyError as e:
            self.logger.error(f"数据库查询异常 - 支出模式查询失败: {e}")
            return {}
        except Exception as e:
            self.logger.error(f"支出模式查询失败: {e}")
            return {}

    def get_expense_categories(self, start_date: Optional[date] = None, 
                             end_date: Optional[date] = None, 
                             account_id: Optional[int] = None, 
                             limit: int = 10) -> List[Dict[str, Any]]:
        """获取支出分类数据（按对手方）
        
        Args:
            start_date: 开始日期，None表示查询所有历史数据
            end_date: 结束日期，默认为今天
            account_id: 账户ID，None表示所有账户
            limit: 返回结果数量限制
            
        Returns:
            List[Dict[str, Any]]: 支出分类数据
        """
        try:
            # 设置默认日期范围
            if not end_date:
                end_date = date.today()
            # 移除默认的12个月限制，当start_date为None时查询所有历史数据
            
            # 构建查询
            query = self.db.query(
                Transaction.counterparty,
                func.sum(func.abs(Transaction.amount)).label('total_amount'),
                func.count(Transaction.id).label('transaction_count'),
                func.avg(func.abs(Transaction.amount)).label('avg_amount')
            ).filter(
                Transaction.amount < 0,  # 只查询支出
                Transaction.counterparty.isnot(None),
                Transaction.counterparty != ''
            )
            
            # 添加时间范围过滤（如果指定了start_date）
            if start_date:
                query = query.filter(Transaction.date >= start_date)
            query = query.filter(Transaction.date <= end_date)
            
            # 添加账户过滤
            if account_id:
                query = query.filter(Transaction.account_id == account_id)
            
            # 分组、排序和限制
            results = query.group_by(
                Transaction.counterparty
            ).order_by(
                func.sum(func.abs(Transaction.amount)).desc()
            ).limit(limit).all()
            
            # 格式化结果
            category_data = [{
                'counterparty': result.counterparty,
                'total_amount': float(result.total_amount or 0),
                'transaction_count': result.transaction_count or 0,
                'avg_amount': float(result.avg_amount or 0)
            } for result in results]
            
            return category_data
            
        except SQLAlchemyError as e:
            self.logger.error(f"数据库查询异常 - 支出分类查询失败: {e}")
            return []
        except Exception as e:
            self.logger.error(f"支出分类查询失败: {e}")
            return []

    # ==================== 私有辅助方法 ====================

    def _analyze_fixed_expenses(self, transactions: List[Transaction]) -> List[Dict[str, Any]]:
        """分析固定支出模式"""
        # 按对手方分组
        counterparty_groups = {}
        for transaction in transactions:
            if transaction.counterparty not in counterparty_groups:
                counterparty_groups[transaction.counterparty] = []
            counterparty_groups[transaction.counterparty].append(transaction)
        
        # 识别固定支出（相同对手方、金额相似的重复交易）
        fixed_expenses = []
        for counterparty, group_transactions in counterparty_groups.items():
            if len(group_transactions) >= 2:  # 至少2次交易
                amounts = [abs(t.amount) for t in group_transactions]
                # 确保平均值为Decimal类型
                avg_amount = sum(amounts) / Decimal(str(len(amounts)))
                # 如果所有金额都在平均值的10%范围内，认为是固定支出
                if all(abs(amount - avg_amount) / avg_amount <= Decimal('0.1') for amount in amounts):
                    fixed_expenses.append({
                        'counterparty': counterparty,
                        'amount': float(avg_amount),
                        'frequency': len(group_transactions),
                        'transactions': [{
                            'date': t.date.isoformat(),
                            'amount': float(abs(t.amount))
                        } for t in group_transactions]
                    })
        
        return fixed_expenses

    def _analyze_abnormal_expenses(self, transactions: List[Transaction]) -> List[Dict[str, Any]]:
        """分析异常支出"""
        if not transactions:
            return []
        
        amounts = [abs(t.amount) for t in transactions]
        # 确保平均值为Decimal类型
        avg_amount = sum(amounts) / Decimal(str(len(amounts)))
        
        # 计算标准差，使用Decimal运算
        variance = sum((amount - avg_amount) ** 2 for amount in amounts) / Decimal(str(len(amounts)))
        std_dev = variance.sqrt()
        
        # 识别异常支出（超过平均值2个标准差）
        threshold = avg_amount + Decimal('2') * std_dev
        abnormal_expenses = []
        
        for transaction in transactions:
            if abs(transaction.amount) > threshold:
                abnormal_expenses.append({
                    'date': transaction.date.isoformat(),
                    'counterparty': transaction.counterparty,
                    'amount': float(abs(transaction.amount)),
                    'description': transaction.description
                })
        
        return abnormal_expenses

    def _analyze_weekly_distribution(self, transactions: List[Transaction]) -> Dict[str, int]:
        """分析周度支出分布"""
        weekly_counts = {}
        for transaction in transactions:
            # 获取星期几（0=周一，6=周日）
            weekday = transaction.date.weekday()
            weekday_name = ['周一', '周二', '周三', '周四', '周五', '周六', '周日'][weekday]
            
            if weekday_name not in weekly_counts:
                weekly_counts[weekday_name] = 0
            weekly_counts[weekday_name] += 1
        
        return weekly_counts