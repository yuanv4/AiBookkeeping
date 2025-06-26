"""财务分析服务

专门负责财务数据的分析和计算，包括余额趋势、支出模式分析等。
"""

from typing import List, Dict, Any, Optional
from decimal import Decimal
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
import logging

from app.models import Transaction, db
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from sqlalchemy.sql.expression import over

logger = logging.getLogger(__name__)

class FinancialAnalysisService:
    """财务分析服务
    
    提供各种财务分析和计算功能，专注于数据分析而不涉及数据获取。
    """
    
    def __init__(self, db_session: Optional[Session] = None):
        """初始化财务分析服务
        
        Args:
            db_session: 数据库会话，如果为None则使用默认会话
        """
        self.db = db_session or db.session
        self.logger = logging.getLogger(__name__)
    
    # ==================== 余额和趋势分析 ====================
    
    def get_balance_trend(self, months: int = 12) -> List[Dict[str, Any]]:
        """获取余额趋势数据
        
        Args:
            months: 查询月数，默认12个月
            
        Returns:
            List[Dict[str, Any]]: 余额趋势数据
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
            return [{
                'month': result.month,
                'balance': float(result.balance or 0)
            } for result in results]
            
        except SQLAlchemyError as e:
            self.logger.error(f"余额趋势查询失败: {e}")
            return []
        except Exception as e:
            self.logger.error(f"余额趋势分析失败: {e}")
            return []
    
    def get_net_worth_trend(self, start_date: date, end_date: date) -> List[Dict[str, Any]]:
        """获取净资产趋势数据
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            List[Dict[str, Any]]: 净资产趋势数据
        """
        try:
            # 使用窗口函数获取每日最终余额
            window_func = over(
                func.row_number(),
                partition_by=[Transaction.account_id, func.date(Transaction.date)],
                order_by=[Transaction.date.desc(), Transaction.created_at.desc()]
            )
            
            # 子查询：获取每个账户每日的最终交易记录
            daily_balances = self.db.query(
                Transaction.account_id,
                func.date(Transaction.date).label('date'),
                Transaction.balance_after
            ).add_columns(
                window_func.label('rn')
            ).filter(
                Transaction.date >= start_date,
                Transaction.date <= end_date
            ).subquery()
            
            # 主查询：筛选最终记录并按日期分组
            query = self.db.query(
                daily_balances.c.date,
                func.sum(daily_balances.c.balance_after).label('total_balance')
            ).filter(
                daily_balances.c.rn == 1
            ).group_by(
                daily_balances.c.date
            ).order_by(
                daily_balances.c.date
            )
            
            results = query.all()
            
            if not results:
                # 如果没有数据，返回当前总资产
                current_assets = self.get_current_total_assets()
                return [{
                    'date': start_date.isoformat(),
                    'balance': current_assets
                }, {
                    'date': end_date.isoformat(),
                    'balance': current_assets
                }]
            
            trend_data = []
            for result in results:
                date_str = result.date.isoformat() if hasattr(result.date, 'isoformat') else str(result.date)
                trend_data.append({
                    'date': date_str,
                    'balance': float(result.total_balance or 0)
                })
            
            return trend_data
            
        except Exception as e:
            self.logger.error(f"净资产趋势分析失败: {e}")
            return []
    
    def get_current_total_assets(self) -> float:
        """获取当前总资产（所有账户最新余额之和）
        
        Returns:
            float: 当前总资产
        """
        try:
            # 使用窗口函数获取每个账户的最新余额
            window_func = over(
                func.row_number(),
                partition_by=Transaction.account_id,
                order_by=[Transaction.date.desc(), Transaction.created_at.desc()]
            )
            
            # 子查询：获取每个账户的最新交易记录
            latest_balances = self.db.query(
                Transaction.account_id,
                Transaction.balance_after
            ).add_columns(
                window_func.label('rn')
            ).subquery()
            
            # 主查询：获取每个账户的最新余额并求和
            total_assets = self.db.query(
                func.sum(latest_balances.c.balance_after)
            ).filter(
                latest_balances.c.rn == 1
            ).scalar() or 0
            
            return float(total_assets)
            
        except Exception as e:
            self.logger.error(f"获取当前总资产失败: {e}")
            return 0.0
    
    # ==================== 支出分析 ====================
    
    def analyze_expense_patterns(self, transactions: List[Transaction]) -> Dict[str, Any]:
        """分析支出模式
        
        Args:
            transactions: 交易记录列表（应为支出交易）
            
        Returns:
            Dict[str, Any]: 支出模式分析结果
        """
        try:
            # 分析固定支出
            fixed_expenses = self._analyze_fixed_expenses(transactions)
            
            # 分析异常支出
            abnormal_expenses = self._analyze_abnormal_expenses(transactions)
            
            # 分析支出集中度（按周分布）
            weekly_distribution = self._analyze_weekly_distribution(transactions)
            
            return {
                'fixed_expenses': fixed_expenses,
                'abnormal_expenses': abnormal_expenses,
                'weekly_distribution': weekly_distribution
            }
            
        except Exception as e:
            self.logger.error(f"支出模式分析失败: {e}")
            return {}
    
    def _analyze_fixed_expenses(self, transactions: List[Transaction]) -> List[Dict[str, Any]]:
        """分析固定支出模式
        
        Args:
            transactions: 交易记录列表
            
        Returns:
            List[Dict[str, Any]]: 固定支出列表
        """
        # 按对手方分组
        counterparty_groups = {}
        for transaction in transactions:
            counterparty = transaction.counterparty or '未知'
            if counterparty not in counterparty_groups:
                counterparty_groups[counterparty] = []
            counterparty_groups[counterparty].append(transaction)
        
        # 识别固定支出（相同对手方、金额相似的重复交易）
        fixed_expenses = []
        for counterparty, group_transactions in counterparty_groups.items():
            if len(group_transactions) >= 2:  # 至少2次交易
                amounts = [abs(t.amount) for t in group_transactions]
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
        """分析异常支出
        
        Args:
            transactions: 交易记录列表
            
        Returns:
            List[Dict[str, Any]]: 异常支出列表
        """
        if not transactions:
            return []
        
        amounts = [abs(t.amount) for t in transactions]
        avg_amount = sum(amounts) / Decimal(str(len(amounts)))
        
        # 计算标准差
        variance = sum((amount - avg_amount) ** 2 for amount in amounts) / Decimal(str(len(amounts)))
        std_dev = variance.sqrt()
        
        # 识别异常支出（超过平均值2个标准差）
        threshold = avg_amount + Decimal('2') * std_dev
        abnormal_expenses = []
        
        for transaction in transactions:
            if abs(transaction.amount) > threshold:
                abnormal_expenses.append({
                    'date': transaction.date.isoformat(),
                    'counterparty': transaction.counterparty or '未知',
                    'amount': float(abs(transaction.amount)),
                    'description': transaction.description or ''
                })
        
        return abnormal_expenses
    
    def _analyze_weekly_distribution(self, transactions: List[Transaction]) -> Dict[str, int]:
        """分析周度支出分布
        
        Args:
            transactions: 交易记录列表
            
        Returns:
            Dict[str, int]: 周度支出分布
        """
        weekly_counts = {}
        weekday_names = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
        
        for transaction in transactions:
            weekday = transaction.date.weekday()
            weekday_name = weekday_names[weekday]
            
            if weekday_name not in weekly_counts:
                weekly_counts[weekday_name] = 0
            weekly_counts[weekday_name] += 1
        
        return weekly_counts
    
    # ==================== 周期指标计算 ====================
    
    def calculate_period_metrics(self, start_date: date, end_date: date) -> Dict[str, Any]:
        """计算指定周期的核心指标
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            Dict[str, Any]: 周期指标
        """
        try:
            # 计算总收入
            income_query = self.db.query(
                func.sum(Transaction.amount)
            ).filter(
                Transaction.amount > 0,
                Transaction.date >= start_date,
                Transaction.date <= end_date
            ).scalar() or Decimal('0')
            
            # 计算总支出
            expense_query = self.db.query(
                func.sum(func.abs(Transaction.amount))
            ).filter(
                Transaction.amount < 0,
                Transaction.date >= start_date,
                Transaction.date <= end_date
            ).scalar() or Decimal('0')
            
            # 获取当前总资产
            current_assets = self.get_current_total_assets()
            
            total_income = float(income_query)
            total_expense = float(expense_query)
            
            return {
                'current_total_assets': current_assets,
                'total_income': total_income,
                'total_expense': total_expense,
                'net_income': total_income - total_expense
            }
            
        except Exception as e:
            self.logger.error(f"计算周期指标失败: {e}")
            return {
                'current_total_assets': 0.0,
                'total_income': 0.0,
                'total_expense': 0.0,
                'net_income': 0.0
            }
    
    def calculate_change_percentage(self, current: float, previous: float) -> float:
        """计算变化百分比
        
        Args:
            current: 当前值
            previous: 之前值
            
        Returns:
            float: 变化百分比
        """
        if previous == 0:
            return 100.0 if current > 0 else 0.0
        return ((current - previous) / previous) * 100.0 