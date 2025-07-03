"""分析工具函数

提供分析服务的通用工具函数和配置常量。
"""

from typing import List, Dict, Any, Union
from decimal import Decimal, InvalidOperation

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