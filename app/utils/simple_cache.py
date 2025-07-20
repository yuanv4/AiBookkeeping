"""简化的缓存工具

基于functools.lru_cache提供简单实用的缓存功能，替代复杂的QueryCache实现。
"""

import time
import logging
from functools import lru_cache, wraps
from typing import Callable, Any, Optional, Dict
from threading import Lock

logger = logging.getLogger(__name__)


class SimpleCacheManager:
    """简化的缓存管理器
    
    使用functools.lru_cache作为底层实现，提供缓存失效和统计功能。
    """
    
    def __init__(self):
        self._cached_functions: Dict[str, Callable] = {}
        self._lock = Lock()
    
    def register_cached_function(self, name: str, func: Callable):
        """注册缓存函数"""
        with self._lock:
            self._cached_functions[name] = func
    
    def clear_cache(self, pattern: Optional[str] = None):
        """清除缓存
        
        Args:
            pattern: 匹配模式，如果为None则清除所有缓存
        """
        cleared_count = 0
        with self._lock:
            for name, func in self._cached_functions.items():
                if pattern is None or pattern in name:
                    if hasattr(func, 'cache_clear'):
                        func.cache_clear()
                        cleared_count += 1
                        logger.debug(f"清除缓存: {name}")
        
        if cleared_count > 0:
            logger.info(f"清除了 {cleared_count} 个缓存函数")
        
        return cleared_count
    
    def get_cache_info(self) -> Dict[str, Any]:
        """获取缓存信息"""
        info = {}
        with self._lock:
            for name, func in self._cached_functions.items():
                if hasattr(func, 'cache_info'):
                    cache_info = func.cache_info()
                    info[name] = {
                        'hits': cache_info.hits,
                        'misses': cache_info.misses,
                        'maxsize': cache_info.maxsize,
                        'currsize': cache_info.currsize,
                        'hit_rate': round(cache_info.hits / (cache_info.hits + cache_info.misses) * 100, 2) if (cache_info.hits + cache_info.misses) > 0 else 0
                    }
        return info
    
    def invalidate_transaction_cache(self):
        """失效与交易相关的缓存"""
        patterns = [
            'expense_composition',
            'income_composition', 
            'monthly_trend',
            'dashboard_data',
            'period_summary'
        ]
        
        total_cleared = 0
        for pattern in patterns:
            total_cleared += self.clear_cache(pattern)
        
        logger.info(f"失效交易相关缓存，共清除 {total_cleared} 个函数缓存")
        return total_cleared


# 全局缓存管理器实例
cache_manager = SimpleCacheManager()


def simple_cache(maxsize: int = 128, ttl: Optional[int] = None):
    """简化的缓存装饰器
    
    基于functools.lru_cache，支持TTL（生存时间）。
    
    Args:
        maxsize: 最大缓存条目数，默认128
        ttl: 缓存生存时间（秒），如果为None则不过期
        
    Usage:
        @simple_cache(maxsize=256, ttl=300)  # 缓存5分钟
        def expensive_function(arg1, arg2):
            return some_expensive_operation(arg1, arg2)
    """
    def decorator(func: Callable) -> Callable:
        # 如果不需要TTL，直接使用lru_cache
        if ttl is None:
            cached_func = lru_cache(maxsize=maxsize)(func)
            cache_manager.register_cached_function(func.__name__, cached_func)
            return cached_func
        
        # 需要TTL的情况，添加时间检查
        cached_func = lru_cache(maxsize=maxsize)(func)
        cache_times = {}
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 生成缓存键
            key = str(args) + str(sorted(kwargs.items()))
            current_time = time.time()
            
            # 检查是否过期
            if key in cache_times:
                if current_time - cache_times[key] > ttl:
                    # 过期了，清除缓存并重新计算
                    cached_func.cache_clear()
                    cache_times.clear()
            
            # 调用缓存函数
            result = cached_func(*args, **kwargs)
            cache_times[key] = current_time
            
            return result
        
        # 保持lru_cache的接口
        wrapper.cache_info = cached_func.cache_info
        wrapper.cache_clear = lambda: (cached_func.cache_clear(), cache_times.clear())
        
        cache_manager.register_cached_function(func.__name__, wrapper)
        return wrapper
    
    return decorator


def invalidate_cache_on_change(cache_patterns: list):
    """数据变更时失效缓存的装饰器
    
    Args:
        cache_patterns: 需要失效的缓存模式列表
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            
            # 失效相关缓存
            for pattern in cache_patterns:
                cache_manager.clear_cache(pattern)
            
            return result
        return wrapper
    return decorator


# 为了兼容性，提供与原QueryCache相同的接口
def cached_query(ttl: Optional[int] = None, cache_key_prefix: str = ""):
    """查询缓存装饰器（兼容接口）
    
    Args:
        ttl: 缓存过期时间（秒）
        cache_key_prefix: 缓存键前缀（忽略，仅为兼容性）
    """
    return simple_cache(maxsize=128, ttl=ttl)


class CacheManager:
    """缓存管理器（兼容接口）"""
    
    @staticmethod
    def invalidate_pattern(pattern: str) -> int:
        """根据模式失效缓存"""
        return cache_manager.clear_cache(pattern)
    
    @staticmethod
    def invalidate_transaction_related_cache():
        """失效与交易相关的缓存"""
        return cache_manager.invalidate_transaction_cache()
    
    @staticmethod
    def get_cache_report() -> str:
        """生成缓存报告"""
        info = cache_manager.get_cache_info()
        
        report = []
        report.append("=== 简化缓存报告 ===")
        report.append(f"生成时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        for name, stats in info.items():
            report.append(f"函数: {name}")
            report.append(f"  命中: {stats['hits']}, 未命中: {stats['misses']}")
            report.append(f"  命中率: {stats['hit_rate']}%")
            report.append(f"  缓存大小: {stats['currsize']}/{stats['maxsize']}")
            report.append("")
        
        return "\n".join(report)


def log_cache_stats():
    """记录缓存统计信息到日志"""
    report = CacheManager.get_cache_report()
    logger.info(f"缓存统计报告:\n{report}")
