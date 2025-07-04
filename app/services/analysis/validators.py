"""分析工具函数

提供分析服务的通用工具函数和配置常量。
"""

from typing import List, Dict, Any, Union, Optional
from decimal import Decimal, InvalidOperation
from datetime import date, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models import Transaction

# ==================== 配置常量 ====================

# 数据验证配置
MAX_DATE_RANGE_DAYS = 365 * 2  # 最大查询范围2年

# 数据处理配置
DEFAULT_DECIMAL_PLACES = 2

# ==================== 数据类型转换工具 ====================

def normalize_decimal(value: Union[int, float, str, Decimal]) -> Decimal:
    """统一Decimal转换逻辑
    
    Args:
        value: 需要转换的数值
        
    Returns:
        Decimal: 转换后的Decimal对象
        
    Raises:
        ValueError: 转换失败时抛出
    """
    try:
        if value is None:
            return Decimal('0.00')
        
        if isinstance(value, Decimal):
            return value.quantize(Decimal('0.01'))
        
        # 转换为Decimal并保留2位小数
        decimal_value = Decimal(str(value))
        return decimal_value.quantize(Decimal('0.01'))
        
    except (InvalidOperation, ValueError, TypeError) as e:
        raise ValueError(f"无法转换为Decimal类型: {value}, 错误: {e}")

def validate_decimal_precision(value: Decimal, max_digits: int = 15, decimal_places: int = 2) -> None:
    """验证Decimal精度
    
    Args:
        value: 需要验证的Decimal值
        max_digits: 最大总位数
        decimal_places: 小数位数
        
    Raises:
        ValueError: 精度验证失败时抛出
    """
    if not isinstance(value, Decimal):
        raise ValueError("值必须是Decimal类型")
    
    # 获取数值的符号、数字和指数
    sign, digits, exponent = value.as_tuple()
    
    # 检查总位数
    if len(digits) > max_digits:
        raise ValueError(f"总位数不能超过{max_digits}位")
    
    # 检查小数位数
    if exponent < -decimal_places:
        raise ValueError(f"小数位数不能超过{decimal_places}位")

# ==================== 数据验证工具 ====================

def validate_date_range(start_date, end_date) -> None:
    """验证日期范围
    
    Args:
        start_date: 开始日期
        end_date: 结束日期
        
    Raises:
        ValueError: 日期范围无效时抛出
    """
    if start_date > end_date:
        raise ValueError("开始日期不能晚于结束日期")
    
    date_diff = (end_date - start_date).days
    if date_diff > MAX_DATE_RANGE_DAYS:
        raise ValueError(f"查询范围不能超过{MAX_DATE_RANGE_DAYS}天")

# ==================== 公共计算工具 ====================

def get_month_date_range(target_month: date) -> tuple[date, date]:
    """获取指定月份的开始和结束日期
    
    Args:
        target_month: 目标月份
        
    Returns:
        tuple[date, date]: (月份开始日期, 月份结束日期)
    """
    month_start = target_month.replace(day=1)
    if target_month.month == 12:
        month_end = target_month.replace(year=target_month.year + 1, month=1, day=1) - timedelta(days=1)
    else:
        month_end = target_month.replace(month=target_month.month + 1, day=1) - timedelta(days=1)
    
    return month_start, month_end

def get_expense_transactions(db: Session, start_date: Optional[date] = None, 
                           end_date: Optional[date] = None, 
                           counterparty: Optional[str] = None) -> List[Transaction]:
    """获取支出交易记录
    
    Args:
        db: 数据库会话
        start_date: 开始日期，可选
        end_date: 结束日期，可选
        counterparty: 交易对方，可选
        
    Returns:
        List[Transaction]: 支出交易记录列表
    """
    query = db.query(Transaction).filter(Transaction.amount < 0)
    
    if start_date:
        query = query.filter(Transaction.date >= start_date)
    
    if end_date:
        query = query.filter(Transaction.date <= end_date)
    
    if counterparty:
        query = query.filter(Transaction.counterparty == counterparty)
    
    return query.order_by(Transaction.date).all()