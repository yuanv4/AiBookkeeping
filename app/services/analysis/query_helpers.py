"""数据库查询辅助工具

提供统一的数据库查询逻辑，消除重复的窗口函数查询和通用交易查询。
"""

from typing import Dict, List, Any, Optional
from datetime import date
from decimal import Decimal
import logging

from app.models import Transaction, db
from sqlalchemy import func, and_
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from sqlalchemy.sql.expression import over

from .validators import normalize_decimal
from .validators import get_expense_transactions

logger = logging.getLogger(__name__)

class DatabaseQueryHelper:
    """数据库查询辅助工具类
    
    提供统一的数据库查询逻辑，专门处理分析服务中的重复查询模式。
    """
    
    @staticmethod
    def get_latest_balance_by_account(db: Session, target_date: Optional[date] = None) -> Dict[int, Decimal]:
        """获取每个账户的最新余额
        
        使用窗口函数获取每个账户的最新余额，避免重复的查询逻辑。
        
        Args:
            db: 数据库会话
            target_date: 目标日期，如果为None则获取最新余额
            
        Returns:
            Dict[int, Decimal]: 账户ID到余额的映射
        """
        try:
            # 构建基础查询
            query = db.query(
                Transaction.account_id,
                Transaction.balance_after
            )
            
            # 如果指定了目标日期，则过滤日期
            if target_date:
                query = query.filter(Transaction.date <= target_date)
            
            # 使用窗口函数获取每个账户的最新余额
            window_func = over(
                func.row_number(),
                partition_by=Transaction.account_id,
                order_by=[Transaction.date.desc(), Transaction.created_at.desc()]
            )
            
            # 子查询：获取每个账户的最新交易记录
            latest_balances = query.add_columns(
                window_func.label('rn')
            ).subquery()
            
            # 主查询：获取每个账户的最新余额
            results = db.query(
                latest_balances.c.account_id,
                latest_balances.c.balance_after
            ).filter(
                latest_balances.c.rn == 1
            ).all()
            
            # 转换为字典格式，确保余额为Decimal类型
            balance_dict = {}
            for account_id, balance_after in results:
                balance_dict[account_id] = normalize_decimal(balance_after)
            
            logger.debug(f"获取最新余额完成，账户数量: {len(balance_dict)}")
            return balance_dict
            
        except SQLAlchemyError as e:
            logger.error(f"数据库查询异常 - 获取最新余额失败: {e}")
            raise
        except Exception as e:
            logger.error(f"获取最新余额失败: {e}")
            raise
    
    @staticmethod
    def get_transactions_by_criteria(db: Session, filters: Dict[str, Any]) -> List[Transaction]:
        """通用交易查询
        
        根据提供的过滤条件查询交易记录。
        
        Args:
            db: 数据库会话
            filters: 过滤条件字典，支持的键：
                - start_date: 开始日期
                - end_date: 结束日期
                - account_id: 账户ID
                - amount_min: 最小金额
                - amount_max: 最大金额
                - counterparty: 交易对方
                - description: 交易描述
                
        Returns:
            List[Transaction]: 符合条件的交易记录列表
        """
        try:
            query = db.query(Transaction)
            
            # 应用过滤条件
            if 'start_date' in filters and filters['start_date']:
                query = query.filter(Transaction.date >= filters['start_date'])
            
            if 'end_date' in filters and filters['end_date']:
                query = query.filter(Transaction.date <= filters['end_date'])
            
            if 'account_id' in filters and filters['account_id']:
                query = query.filter(Transaction.account_id == filters['account_id'])
            
            if 'amount_min' in filters and filters['amount_min'] is not None:
                query = query.filter(Transaction.amount >= filters['amount_min'])
            
            if 'amount_max' in filters and filters['amount_max'] is not None:
                query = query.filter(Transaction.amount <= filters['amount_max'])
            
            if 'counterparty' in filters and filters['counterparty']:
                query = query.filter(Transaction.counterparty == filters['counterparty'])
            
            if 'description' in filters and filters['description']:
                query = query.filter(Transaction.description == filters['description'])
            
            # 按日期排序
            query = query.order_by(Transaction.date.desc(), Transaction.created_at.desc())
            
            results = query.all()
            logger.debug(f"通用查询完成，结果数量: {len(results)}")
            
            return results
            
        except SQLAlchemyError as e:
            logger.error(f"数据库查询异常 - 通用交易查询失败: {e}")
            raise
        except Exception as e:
            logger.error(f"通用交易查询失败: {e}")
            raise
    
    @staticmethod
    def calculate_period_aggregation(db: Session, start_date: date, end_date: date, 
                                   group_by: str = 'month') -> List[Dict[str, Any]]:
        """计算时间段聚合数据
        
        按指定的时间粒度聚合交易数据。
        
        Args:
            db: 数据库会话
            start_date: 开始日期
            end_date: 结束日期
            group_by: 聚合粒度，支持 'day', 'week', 'month'
            
        Returns:
            List[Dict[str, Any]]: 聚合结果列表
        """
        try:
            # 根据聚合粒度构建不同的查询
            if group_by == 'day':
                date_group = func.date(Transaction.date)
                date_format = '%Y-%m-%d'
            elif group_by == 'week':
                date_group = func.strftime('%Y-%W', Transaction.date)
                date_format = '%Y-%W'
            elif group_by == 'month':
                date_group = func.strftime('%Y-%m', Transaction.date)
                date_format = '%Y-%m'
            else:
                raise ValueError(f"不支持的聚合粒度: {group_by}")
            
            # 聚合查询
            results = db.query(
                date_group.label('period'),
                func.sum(Transaction.amount).label('total_amount'),
                func.count(Transaction.id).label('transaction_count')
            ).filter(
                and_(
                    Transaction.date >= start_date,
                    Transaction.date <= end_date
                )
            ).group_by(
                date_group
            ).order_by(
                date_group
            ).all()
            
            # 转换为字典格式
            aggregated_data = []
            for period, total_amount, transaction_count in results:
                aggregated_data.append({
                    'period': period,
                    'total_amount': normalize_decimal(total_amount or 0),
                    'transaction_count': transaction_count
                })
            
            logger.debug(f"时间段聚合完成，结果数量: {len(aggregated_data)}")
            return aggregated_data
            
        except SQLAlchemyError as e:
            logger.error(f"数据库查询异常 - 时间段聚合失败: {e}")
            raise
        except Exception as e:
            logger.error(f"时间段聚合失败: {e}")
            raise 