"""分析工具函数

提供分析服务的通用工具函数和配置常量。
"""

from typing import List, Dict, Any
from decimal import Decimal

# ==================== 配置常量 ====================

# 数据验证配置
MAX_DATE_RANGE_DAYS = 365 * 2  # 最大查询范围2年

# 数据处理配置
DEFAULT_DECIMAL_PLACES = 2

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