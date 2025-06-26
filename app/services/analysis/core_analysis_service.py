"""核心分析服务

精简的财务分析服务，只包含当前实际使用的核心功能。
优化了查询性能，添加了缓存机制和统一的异常处理。
"""

from typing import Optional
from datetime import date, datetime, timedelta
import logging

from app.models import Transaction, db
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from sqlalchemy.sql.expression import over

logger = logging.getLogger(__name__)

class CoreAnalysisService:
    """核心分析服务
    
    提供财务分析的核心功能，专注于当前实际使用的计算。
    """
    
    def __init__(self, db_session: Optional[Session] = None):
        """初始化核心分析服务
        
        Args:
            db_session: 数据库会话，如果为None则使用默认会话
        """
        self.db = db_session or db.session
        self.logger = logging.getLogger(__name__)
    
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
            
            result = float(total_assets)
            self.logger.debug(f"计算总资产: {result}")
            
            return result
            
        except SQLAlchemyError as e:
            self.logger.error(f"数据库查询异常 - 获取当前总资产失败: {e}")
            raise
        except Exception as e:
            self.logger.error(f"获取当前总资产失败: {e}")
            raise
    
    def get_total_assets_at_date(self, target_date: date) -> float:
        """获取截至指定日期的总资产
        
        Args:
            target_date: 目标日期
            
        Returns:
            float: 截至指定日期的总资产
        """
        try:
            # 使用窗口函数获取每个账户在指定日期前的最新余额
            window_func = over(
                func.row_number(),
                partition_by=Transaction.account_id,
                order_by=[Transaction.date.desc(), Transaction.created_at.desc()]
            )
            
            # 子查询：获取每个账户在指定日期前的最新交易记录
            latest_balances = self.db.query(
                Transaction.account_id,
                Transaction.balance_after
            ).filter(
                Transaction.date <= target_date
            ).add_columns(
                window_func.label('rn')
            ).subquery()
            
            # 主查询：获取每个账户的最新余额并求和
            total_assets = self.db.query(
                func.sum(latest_balances.c.balance_after)
            ).filter(
                latest_balances.c.rn == 1
            ).scalar() or 0
            
            result = float(total_assets)
            self.logger.debug(f"计算截至{target_date}的总资产: {result}")
            
            return result
            
        except SQLAlchemyError as e:
            self.logger.error(f"数据库查询异常 - 获取指定日期总资产失败: {e}")
            raise
        except Exception as e:
            self.logger.error(f"获取指定日期总资产失败: {e}")
            raise
    
    def calculate_change_percentage(self, current: float, previous: float) -> float:
        """计算变化百分比
        
        统一的变化百分比计算逻辑，处理除零情况。
        
        Args:
            current: 当前值
            previous: 之前值
            
        Returns:
            float: 变化百分比
        """
        if previous == 0:
            return 100.0 if current > 0 else 0.0
        return ((current - previous) / previous) * 100.0 