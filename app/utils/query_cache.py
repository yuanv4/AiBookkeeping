"""查询缓存工具

提供简单的内存缓存机制，用于缓存频繁查询的结果。
"""

import time
import hashlib
import json
import logging
from typing import Any, Optional, Dict, Callable
from functools import wraps
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class QueryCache:
    """查询结果缓存器"""
    
    def __init__(self, default_ttl: int = 300):
        """初始化缓存器
        
        Args:
            default_ttl: 默认缓存过期时间（秒），默认5分钟
        """
        self.cache: Dict[str, Dict] = {}
        self.default_ttl = default_ttl
        self.hit_count = 0
        self.miss_count = 0
    
    def _generate_key(self, func_name: str, args: tuple, kwargs: dict) -> str:
        """生成缓存键
        
        Args:
            func_name: 函数名
            args: 位置参数
            kwargs: 关键字参数
            
        Returns:
            str: 缓存键
        """
        # 创建参数的哈希值
        key_data = {
            'func': func_name,
            'args': str(args),
            'kwargs': sorted(kwargs.items())
        }
        key_str = json.dumps(key_data, sort_keys=True, default=str)
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存值
        
        Args:
            key: 缓存键
            
        Returns:
            Optional[Any]: 缓存值，如果不存在或已过期则返回None
        """
        if key not in self.cache:
            self.miss_count += 1
            return None
        
        cache_item = self.cache[key]
        
        # 检查是否过期
        if time.time() > cache_item['expires_at']:
            del self.cache[key]
            self.miss_count += 1
            return None
        
        self.hit_count += 1
        cache_item['last_accessed'] = time.time()
        return cache_item['value']
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """设置缓存值
        
        Args:
            key: 缓存键
            value: 缓存值
            ttl: 过期时间（秒），如果为None则使用默认值
        """
        ttl = ttl or self.default_ttl
        expires_at = time.time() + ttl
        
        self.cache[key] = {
            'value': value,
            'expires_at': expires_at,
            'created_at': time.time(),
            'last_accessed': time.time()
        }
    
    def delete(self, key: str) -> bool:
        """删除缓存项
        
        Args:
            key: 缓存键
            
        Returns:
            bool: 是否成功删除
        """
        if key in self.cache:
            del self.cache[key]
            return True
        return False
    
    def clear(self) -> None:
        """清空所有缓存"""
        self.cache.clear()
        self.hit_count = 0
        self.miss_count = 0
        logger.info("查询缓存已清空")
    
    def cleanup_expired(self) -> int:
        """清理过期缓存项
        
        Returns:
            int: 清理的项目数量
        """
        current_time = time.time()
        expired_keys = [
            key for key, item in self.cache.items()
            if current_time > item['expires_at']
        ]
        
        for key in expired_keys:
            del self.cache[key]
        
        if expired_keys:
            logger.info(f"清理了 {len(expired_keys)} 个过期缓存项")
        
        return len(expired_keys)
    
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        total_requests = self.hit_count + self.miss_count
        hit_rate = (self.hit_count / total_requests * 100) if total_requests > 0 else 0
        
        return {
            'cache_size': len(self.cache),
            'hit_count': self.hit_count,
            'miss_count': self.miss_count,
            'hit_rate': round(hit_rate, 2),
            'total_requests': total_requests
        }


# 全局缓存实例
query_cache = QueryCache()


def cached_query(ttl: Optional[int] = None, cache_key_prefix: str = ""):
    """查询缓存装饰器
    
    Args:
        ttl: 缓存过期时间（秒）
        cache_key_prefix: 缓存键前缀
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 生成缓存键
            func_name = f"{cache_key_prefix}{func.__name__}" if cache_key_prefix else func.__name__
            cache_key = query_cache._generate_key(func_name, args, kwargs)
            
            # 尝试从缓存获取
            cached_result = query_cache.get(cache_key)
            if cached_result is not None:
                logger.debug(f"缓存命中: {func_name}")
                return cached_result
            
            # 执行函数并缓存结果
            logger.debug(f"缓存未命中，执行查询: {func_name}")
            result = func(*args, **kwargs)
            query_cache.set(cache_key, result, ttl)
            
            return result
        return wrapper
    return decorator


class CacheManager:
    """缓存管理器"""
    
    @staticmethod
    def invalidate_pattern(pattern: str) -> int:
        """根据模式失效缓存
        
        Args:
            pattern: 匹配模式
            
        Returns:
            int: 失效的缓存项数量
        """
        invalidated_count = 0
        keys_to_delete = []
        
        for key in query_cache.cache.keys():
            if pattern in key:
                keys_to_delete.append(key)
        
        for key in keys_to_delete:
            query_cache.delete(key)
            invalidated_count += 1
        
        if invalidated_count > 0:
            logger.info(f"根据模式 '{pattern}' 失效了 {invalidated_count} 个缓存项")
        
        return invalidated_count
    
    @staticmethod
    def invalidate_transaction_related_cache():
        """失效与交易相关的缓存"""
        patterns = [
            'get_expense_composition',
            'get_income_composition', 
            'get_monthly_trend',
            'expense_analysis_by_category',
            'get_dashboard_data'
        ]
        
        total_invalidated = 0
        for pattern in patterns:
            total_invalidated += CacheManager.invalidate_pattern(pattern)
        
        logger.info(f"失效交易相关缓存，共 {total_invalidated} 项")
        return total_invalidated
    
    @staticmethod
    def get_cache_report() -> str:
        """生成缓存报告
        
        Returns:
            str: 缓存报告
        """
        stats = query_cache.get_stats()
        
        report = []
        report.append("=== 查询缓存报告 ===")
        report.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        report.append(f"缓存大小: {stats['cache_size']} 项")
        report.append(f"命中次数: {stats['hit_count']}")
        report.append(f"未命中次数: {stats['miss_count']}")
        report.append(f"命中率: {stats['hit_rate']}%")
        report.append(f"总请求数: {stats['total_requests']}")
        
        # 清理过期项
        expired_count = query_cache.cleanup_expired()
        if expired_count > 0:
            report.append(f"清理过期项: {expired_count} 项")
        
        return "\n".join(report)
    
    @staticmethod
    def schedule_cleanup():
        """定期清理任务"""
        query_cache.cleanup_expired()


def log_cache_stats():
    """记录缓存统计信息到日志"""
    report = CacheManager.get_cache_report()
    logger.info(f"缓存统计报告:\n{report}")


# 在数据变更时自动失效相关缓存的装饰器
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
                CacheManager.invalidate_pattern(pattern)
            
            return result
        return wrapper
    return decorator
