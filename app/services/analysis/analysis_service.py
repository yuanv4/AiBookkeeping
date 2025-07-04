"""核心分析服务

精简的现金流分析服务，只包含当前实际使用的核心功能。
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

from .query_helpers import DatabaseQueryHelper
from .validators import normalize_decimal

logger = logging.getLogger(__name__)

class AnalysisService:
    """核心分析服务
    
    提供现金流分析的核心功能，专注于当前实际使用的计算。
    """
    
    def __init__(self, db_session: Optional[Session] = None):
        """初始化核心分析服务
        
        Args:
            db_session: 数据库会话，如果为None则使用默认会话
        """
        self.db = db_session or db.session
        self.logger = logging.getLogger(__name__)
    
    def get_current_total_assets(self) -> float:
        """获取当前总现金（所有账户最新余额之和）
        
        Returns:
            float: 当前总现金
        """
        try:
            # 使用DatabaseQueryHelper获取每个账户的最新余额
            balance_dict = DatabaseQueryHelper.get_latest_balance_by_account(self.db)
            
            # 计算总现金
            total_assets = sum(balance_dict.values())
            
            result = float(total_assets)
            self.logger.debug(f"计算总现金: {result}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"获取当前总现金失败: {e}")
            raise
    
    def get_total_assets_at_date(self, target_date: date) -> float:
        """获取截至指定日期的总现金
        
        Args:
            target_date: 目标日期
            
        Returns:
            float: 截至指定日期的总现金
        """
        try:
            # 使用DatabaseQueryHelper获取指定日期前每个账户的最新余额
            balance_dict = DatabaseQueryHelper.get_latest_balance_by_account(self.db, target_date)
            
            # 计算总现金
            total_assets = sum(balance_dict.values())
            
            result = float(total_assets)
            self.logger.debug(f"计算截至{target_date}的总现金: {result}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"获取指定日期总现金失败: {e}")
            raise
    
    def get_all_time_net_income(self) -> float:
        """计算所有时间范围内的总净收入
        
        Returns:
            float: 总净收入
        """
        try:
            total_net_income = self.db.query(func.sum(Transaction.amount)).scalar() or 0
            return float(total_net_income)
        except SQLAlchemyError as e:
            self.logger.error(f"数据库查询异常 - 计算总净收入失败: {e}")
            raise
        except Exception as e:
            self.logger.error(f"计算总净收入失败: {e}")
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

    def calculate_daily_average_expense(self, start_date: date, end_date: date) -> float:
        """计算指定时间范围内的日均支出
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            float: 日均支出金额（正数）
        """
        try:
            # 计算时间范围内的总支出（负数金额的绝对值）
            total_expense = self.db.query(
                func.sum(func.abs(Transaction.amount))
            ).filter(
                Transaction.amount < 0,
                Transaction.date >= start_date,
                Transaction.date <= end_date
            ).scalar() or 0
            
            # 计算天数
            days = (end_date - start_date).days + 1  # 包含结束日期
            
            if days <= 0:
                return 0.0
                
            daily_average = float(total_expense) / days
            self.logger.debug(f"计算日均支出: 总支出={total_expense}, 天数={days}, 日均={daily_average}")
            
            return daily_average
            
        except SQLAlchemyError as e:
            self.logger.error(f"数据库查询异常 - 计算日均支出失败: {e}")
            raise
        except Exception as e:
            self.logger.error(f"计算日均支出失败: {e}")
            raise

    def calculate_emergency_reserve_months(self, daily_average_expense: float = None, 
                                        calculation_period_days: int = None) -> float:
        """计算应急储备月数
        
        Args:
            daily_average_expense: 日均支出，如果为None则自动计算
            calculation_period_days: 用于计算日均支出的天数。如果为None，则使用全部历史数据。
            
        Returns:
            float: 应急储备月数，如果日均支出为0则返回-1表示无限
        """
        try:
            # 获取当前总现金作为应急储备资金
            current_assets = self.get_current_total_assets()
            
            # 如果没有提供日均支出，则进行计算
            if daily_average_expense is None:
                end_date = date.today()
                if calculation_period_days:
                    start_date = end_date - timedelta(days=calculation_period_days - 1)
                else:
                    # 如果未指定天数，则从第一笔交易开始计算
                    first_transaction_date = self.db.query(func.min(Transaction.date)).scalar()
                    if not first_transaction_date:
                        return -1.0 # 没有交易，无法计算
                    start_date = first_transaction_date
                
                daily_average_expense = self.calculate_daily_average_expense(start_date, end_date)
            
            # 处理日均支出为0的情况
            if daily_average_expense <= 0:
                self.logger.debug("日均支出为0，应急储备月数设为无限")
                return -1.0  # 返回-1表示无限月数
            
            # 计算应急储备月数（按30天/月计算）
            reserve_months = current_assets / (daily_average_expense * 30)
            self.logger.debug(f"计算应急储备月数: 总现金={current_assets}, 日均支出={daily_average_expense}, 储备月数={reserve_months}")
            
            return reserve_months
            
        except Exception as e:
            self.logger.error(f"计算应急储备月数失败: {e}")
            raise 