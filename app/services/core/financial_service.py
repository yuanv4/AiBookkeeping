"""统一财务服务
"""

from typing import List, Dict, Any, Optional, Union
from decimal import Decimal
from datetime import date
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