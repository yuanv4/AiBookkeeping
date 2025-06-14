"""简化的工具函数模块

将原有分散的工具函数整合到单一模块中，提供核心的缓存、错误处理和计算功能。
消除了过度模块化的复杂性，保持功能完整性。

Created: 2024-12-19
Author: AI Assistant
"""

import json
import hashlib
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Callable, Union
from functools import wraps
from decimal import Decimal


# ==================== 缓存功能 ====================

class SimpleCache:
    """简单内存缓存"""
    
    def __init__(self):
        self._cache: Dict[str, Dict[str, Any]] = {}
        self.logger = logging.getLogger(__name__)
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        if key not in self._cache:
            return None
        
        cache_item = self._cache[key]
        if cache_item['expires_at'] and datetime.now() > cache_item['expires_at']:
            del self._cache[key]
            return None
        
        return cache_item['value']
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """设置缓存值"""
        expires_at = None
        if ttl is not None:
            expires_at = datetime.now() + timedelta(seconds=ttl)
        
        self._cache[key] = {
            'value': value,
            'expires_at': expires_at,
            'created_at': datetime.now()
        }
    
    def clear(self) -> None:
        """清空缓存"""
        self._cache.clear()


# 全局缓存实例
_global_cache = SimpleCache()


def cache_result(ttl: int = 300):
    """缓存结果装饰器
    
    Args:
        ttl: 缓存生存时间（秒）
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 生成缓存键
            cache_key = _generate_cache_key(func.__name__, args, kwargs)
            
            # 尝试从缓存获取
            cached_result = _global_cache.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # 执行函数并缓存结果
            result = func(*args, **kwargs)
            _global_cache.set(cache_key, result, ttl)
            return result
        
        return wrapper
    return decorator


def _generate_cache_key(func_name: str, args: tuple, kwargs: dict) -> str:
    """生成缓存键"""
    # 将参数转换为可序列化的格式
    serializable_args = []
    for arg in args:
        if hasattr(arg, '__dict__'):
            serializable_args.append(str(type(arg).__name__))
        else:
            serializable_args.append(str(arg))
    
    key_data = {
        'func': func_name,
        'args': serializable_args,
        'kwargs': {k: str(v) for k, v in kwargs.items()}
    }
    
    key_str = json.dumps(key_data, sort_keys=True)
    return hashlib.md5(key_str.encode()).hexdigest()


# ==================== 错误处理 ====================

class AnalysisError(Exception):
    """分析错误基类"""
    pass


class DataValidationError(AnalysisError):
    """数据验证错误"""
    pass


class CalculationError(AnalysisError):
    """计算错误"""
    pass


class InsufficientDataError(AnalysisError):
    """数据不足错误"""
    pass


def handle_analysis_errors(func: Callable) -> Callable:
    """分析错误处理装饰器"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        logger = logging.getLogger(__name__)
        
        try:
            return func(*args, **kwargs)
        except (DataValidationError, CalculationError, InsufficientDataError) as e:
            logger.warning(f"Analysis error in {func.__name__}: {str(e)}")
            return _get_default_result(func)
        except Exception as e:
            logger.error(f"Unexpected error in {func.__name__}: {str(e)}", exc_info=True)
            return _get_default_result(func)
    
    return wrapper


def _get_default_result(func: Callable) -> Any:
    """获取默认返回值"""
    func_name = func.__name__.lower()
    
    if 'analyze' in func_name:
        # 导入简化的数据模型
        try:
            from .data_models import AnalysisResult
            return AnalysisResult()
        except ImportError:
            return {
                'total_amount': 0.0,
                'by_category': {},
                'by_month': {},
                'transaction_count': 0,
                'average_amount': 0.0
            }
    elif 'trends' in func_name or 'monthly' in func_name:
        return []
    elif 'health' in func_name:
        return {
            'health_score': 0,
            'health_level': 'unknown',
            'savings_rate': 0.0,
            'expense_ratio': 0.0,
            'cash_flow_stability': 0.0
        }
    else:
        return {}


# ==================== 计算工具函数 ====================

def calculate_growth_rate(current_value: float, previous_value: float) -> float:
    """计算增长率
    
    Args:
        current_value: 当前值
        previous_value: 之前值
        
    Returns:
        增长率（百分比）
    """
    if previous_value == 0:
        return 0.0 if current_value == 0 else 100.0
    
    return ((current_value - previous_value) / previous_value) * 100


def calculate_percentage(part: float, total: float) -> float:
    """计算百分比
    
    Args:
        part: 部分值
        total: 总值
        
    Returns:
        百分比
    """
    return (part / total * 100) if total > 0 else 0.0


def calculate_average(values: List[float]) -> float:
    """计算平均值
    
    Args:
        values: 数值列表
        
    Returns:
        平均值
    """
    return sum(values) / len(values) if values else 0.0


def calculate_variance(values: List[float]) -> float:
    """计算方差
    
    Args:
        values: 数值列表
        
    Returns:
        方差
    """
    if not values:
        return 0.0
    
    avg = calculate_average(values)
    return sum((x - avg) ** 2 for x in values) / len(values)


def calculate_stability_score(values: List[float]) -> float:
    """计算稳定性评分
    
    Args:
        values: 数值列表
        
    Returns:
        稳定性评分（0-1之间，1表示最稳定）
    """
    if not values or len(values) < 2:
        return 0.0
    
    avg = calculate_average(values)
    if avg == 0:
        return 0.0
    
    variance = calculate_variance(values)
    coefficient_of_variation = (variance ** 0.5) / avg
    
    # 将变异系数转换为稳定性评分
    return max(0.0, 1.0 - coefficient_of_variation)


# ==================== 数据格式化 ====================

def format_currency(amount: float, currency: str = '¥') -> str:
    """格式化货币
    
    Args:
        amount: 金额
        currency: 货币符号
        
    Returns:
        格式化的货币字符串
    """
    return f"{currency}{amount:,.2f}"


def format_percentage(value: float, decimal_places: int = 1) -> str:
    """格式化百分比
    
    Args:
        value: 百分比值
        decimal_places: 小数位数
        
    Returns:
        格式化的百分比字符串
    """
    return f"{value:.{decimal_places}f}%"


def format_number(value: float, decimal_places: int = 2) -> str:
    """格式化数字
    
    Args:
        value: 数值
        decimal_places: 小数位数
        
    Returns:
        格式化的数字字符串
    """
    return f"{value:,.{decimal_places}f}"


# ==================== 数据验证 ====================

def validate_date_range(start_date, end_date) -> bool:
    """验证日期范围
    
    Args:
        start_date: 开始日期
        end_date: 结束日期
        
    Returns:
        是否有效
    """
    if not start_date or not end_date:
        return False
    
    return start_date <= end_date


def validate_amount(amount: Any) -> bool:
    """验证金额
    
    Args:
        amount: 金额值
        
    Returns:
        是否有效
    """
    try:
        float(amount)
        return True
    except (ValueError, TypeError):
        return False


def validate_account_id(account_id: Any) -> bool:
    """验证账户ID
    
    Args:
        account_id: 账户ID
        
    Returns:
        是否有效
    """
    if account_id is None:
        return True  # None是有效的（表示所有账户）
    
    try:
        int(account_id)
        return True
    except (ValueError, TypeError):
        return False


# ==================== 导出的公共接口 ====================

__all__ = [
    # 缓存
    'SimpleCache',
    'cache_result',
    
    # 错误处理
    'AnalysisError',
    'DataValidationError', 
    'CalculationError',
    'InsufficientDataError',
    'handle_analysis_errors',
    
    # 计算函数
    'calculate_growth_rate',
    'calculate_percentage',
    'calculate_average',
    'calculate_variance',
    'calculate_stability_score',
    
    # 格式化函数
    'format_currency',
    'format_percentage',
    'format_number',
    
    # 验证函数
    'validate_date_range',
    'validate_amount',
    'validate_account_id'
]