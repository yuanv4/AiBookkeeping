"""统一财务服务
"""

from typing import List, Dict, Any, Optional
from decimal import Decimal
from datetime import date, datetime
import logging
from functools import wraps

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
    
    # ==================== 分析方法 ====================
    
    def analyze_income(self, start_date: date, end_date: date, 
                      account_id: Optional[int] = None) -> Dict[str, Any]:
        """分析收入情况"""

        # 获取收入数据
        income_sources = self.get_income_data(start_date, end_date, account_id)
        
        total_income = sum(source['total'] for source in income_sources)
        
        # 计算百分比
        for source in income_sources:
            source['percentage'] = (source['total'] / total_income * 100) if total_income > 0 else 0
        
        return {
            'total_income': total_income,
            'income_sources': income_sources,
            'primary_source': income_sources[0] if income_sources else None,
            'source_diversity': len(income_sources),
            'transaction_count': sum(source['count'] for source in income_sources),
            'average_amount': total_income / sum(source['count'] for source in income_sources) if income_sources else 0
        }
    
    def analyze_overview(self) -> Dict[str, Any]:
        """分析总览情况
        
        Args:
            months: 分析月份数，默认12个月
            
        Returns:
            Dict[str, Any]: 包含总览数据的字典
        """
        return {
            'balance': self.get_all_accounts_balance(),
            'monthly_trends': self.get_monthly_balance_trends(12),
        }
        
    # ==================== 计算方法 ====================

    def get_income_data(self, start_date: date, end_date: date, 
                       account_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """获取收入交易数据
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            account_id: 账户ID，可选
            
        Returns:
            List[Dict[str, Any]]: 包含收入统计信息的字典列表
        """
        try:
            # 使用优化的聚合查询
            query = self.db.query(
                case(
                    (Transaction.amount > 0, 'income'),
                    (Transaction.amount < 0, 'expense'),
                    else_='transfer'
                ).label('type_enum'),
                func.count(Transaction.id).label('transaction_count'),
                func.sum(Transaction.amount).label('total_amount'),
                func.avg(Transaction.amount).label('avg_amount'),
                func.max(Transaction.amount).label('max_amount'),
                func.min(Transaction.amount).label('min_amount')
            )
            
            # 添加过滤条件
            if account_id:
                query = query.filter(Transaction.account_id == account_id)
            if start_date:
                query = query.filter(Transaction.date >= start_date)
            if end_date:
                query = query.filter(Transaction.date <= end_date)
            
            # 只查询收入
            query = query.filter(Transaction.amount > 0)
            
            # 分组和排序
            query = query.group_by(
                case(
                    (Transaction.amount > 0, 'income'),
                    (Transaction.amount < 0, 'expense'),
                    else_='transfer'
                )
            ).order_by(
                func.sum(Transaction.amount).desc()
            )
            
            results = query.all()
            
            # 格式化结果
            income_sources = []
            for result in results:
                income_sources.append({
                    'category': result.type_enum,
                    'total': float(result.total_amount or 0),
                    'count': result.transaction_count,
                    'average': float(result.avg_amount or 0),
                    'maximum': float(result.max_amount or 0),
                    'minimum': float(result.min_amount or 0)
                })
            
            return income_sources
            
        except Exception as e:
            self.logger.error(f"获取收入数据失败: {e}")
            return []

    def get_all_accounts_balance(self) -> Decimal:
        """获取所有账户的当前余额总和
        
        使用SQLAlchemy ORM窗口函数实现，替代原有的原生SQL查询。
        为每个账户获取最新的交易记录，然后计算所有账户余额的总和。
        
        Returns:
            Decimal: 所有账户当前余额的总和
            
        Raises:
            SQLAlchemyError: 数据库查询异常时抛出
        """
        try:
            # 使用SQLAlchemy ORM窗口函数查询
            # 为每个账户的交易按日期和创建时间排序，获取最新的交易记录
            window_func = over(
                func.row_number(),
                partition_by=Transaction.account_id,
                order_by=[Transaction.date.desc(), Transaction.created_at.desc()]
            )
            
            # 子查询：获取每个账户的最新交易记录
            latest_transactions = self.db.query(
                Transaction.account_id,
                Transaction.balance_after
            ).add_columns(
                window_func.label('rn')
            ).subquery()
            
            # 主查询：筛选最新记录并计算总和
            result = self.db.query(
                func.sum(latest_transactions.c.balance_after)
            ).filter(
                latest_transactions.c.rn == 1
            ).scalar()
            
            return Decimal(str(result)) if result else Decimal('0.00')
            
        except SQLAlchemyError as e:
            self.logger.error(f"数据库查询异常 - ORM窗口函数获取余额失败: {e}")
            return Decimal('0.00')
        except Exception as e:
            self.logger.error(f"ORM窗口函数获取余额失败: {e}")
            return Decimal('0.00')
    
    def get_monthly_balance_trends(self, months: int = 12) -> List[Dict[str, Any]]:
        """获取所有账户的月度余额趋势"""
        try:
            monthly_trends = self.db.query(
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
                'balance': float(balance)
            } for month, balance in monthly_trends]
        except Exception as e:
            self.logger.error(f"获取月度余额趋势失败: {e}")
            return []