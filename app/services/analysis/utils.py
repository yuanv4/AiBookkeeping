"""分析工具函数

提供分析服务的通用工具函数、异常类和配置常量。
"""

from typing import List, Dict, Any
from decimal import Decimal

# ==================== 异常类 ====================
# 已移除自定义异常类，改用标准Python异常

# ==================== 配置常量 ====================

# 缓存配置
CACHE_TIMEOUT_MINUTES = 5

# 数据验证配置
MAX_DATE_RANGE_DAYS = 365 * 2  # 最大查询范围2年

# 数据处理配置
DEFAULT_DECIMAL_PLACES = 2
PERCENTAGE_PRECISION = 1

# ==================== 数据聚合工具 ====================

# 已移除 aggregate_by_field 和 calculate_percentage_distribution 函数
# 这些功能现在直接在数据库查询中实现，提高了效率

def format_currency(amount: float, currency_symbol: str = '¥') -> str:
    """格式化货币显示
    
    Args:
        amount: 金额
        currency_symbol: 货币符号
        
    Returns:
        str: 格式化后的货币字符串
    """
    return f"{currency_symbol}{amount:,.{DEFAULT_DECIMAL_PLACES}f}"

def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """安全除法，处理除零情况
    
    Args:
        numerator: 分子
        denominator: 分母
        default: 除零时的默认值
        
    Returns:
        float: 除法结果
    """
    if denominator == 0:
        return default
    return numerator / denominator

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

def validate_amount(amount: float) -> None:
    """验证金额
    
    Args:
        amount: 金额
        
    Raises:
        ValueError: 金额无效时抛出
    """
    if not isinstance(amount, (int, float, Decimal)):
        raise ValueError("金额必须是数字类型")
    
    if amount < 0:
        raise ValueError("金额不能为负数")

# ==================== 查询构建器辅助函数 ====================

def build_date_filter_conditions(query, date_field, start_date=None, end_date=None):
    """构建日期过滤条件
    
    Args:
        query: SQLAlchemy查询对象
        date_field: 日期字段
        start_date: 开始日期
        end_date: 结束日期
        
    Returns:
        查询对象: 添加了日期过滤条件的查询
    """
    if start_date:
        query = query.filter(date_field >= start_date)
    if end_date:
        query = query.filter(date_field <= end_date)
    return query 