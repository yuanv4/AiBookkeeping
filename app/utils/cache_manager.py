"""优化后的缓存管理器。

实现分层缓存策略，包括内存缓存、持久化缓存和智能失效机制。
"""

import hashlib
import threading
import pickle
import os
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Callable, Tuple, Set
from functools import wraps
from collections import OrderedDict
import weakref
import gc
import json
from pathlib import Path

logger = logging.getLogger(__name__)

class CacheStats:
    """缓存统计信息"""
    def __init__(self):
        self.hits = 0
        self.misses = 0
        self.evictions = 0
        self.total_size = 0
        self.max_size_reached = 0
        self.l1_hits = 0  # L1缓存命中
        self.l2_hits = 0  # L2缓存命中
        self.disk_hits = 0  # 磁盘缓存命中
        
    @property
    def hit_rate(self) -> float:
        """缓存命中率"""
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0
    
    @property
    def l1_hit_rate(self) -> float:
        """L1缓存命中率"""
        total_hits = self.l1_hits + self.l2_hits + self.disk_hits
        return self.l1_hits / total_hits if total_hits > 0 else 0.0
        
    def reset(self):
        """重置统计信息"""
        self.hits = 0
        self.misses = 0
        self.evictions = 0
        self.total_size = 0
        self.max_size_reached = 0
        self.l1_hits = 0
        self.l2_hits = 0
        self.disk_hits = 0

class CacheEntry:
    """缓存条目"""
    def __init__(self, value: Any, expire_time: datetime, access_count: int = 0, priority: int = 1):
        self.value = value
        self.expire_time = expire_time
        self.access_count = access_count
        self.last_access = datetime.now()
        self.priority = priority  # 优先级：1=低，2=中，3=高
        self.size = self._calculate_size(value)
        
    def is_expired(self) -> bool:
        """检查是否过期"""
        return datetime.now() > self.expire_time
        
    def touch(self):
        """更新访问时间和次数"""
        self.last_access = datetime.now()
        self.access_count += 1
    
    def _calculate_size(self, value: Any) -> int:
        """估算对象大小"""
        try:
            return len(pickle.dumps(value))
        except:
            return 1024  # 默认大小

class TieredCache:
    """分层缓存实现"""
    
    def __init__(self, 
                 l1_max_size: int = 100,  # L1缓存最大条目数
                 l2_max_size: int = 500,  # L2缓存最大条目数
                 disk_cache_dir: str = None,  # 磁盘缓存目录
                 default_ttl_minutes: int = 30):
        
        self.l1_max_size = l1_max_size
        self.l2_max_size = l2_max_size
        self.default_ttl_minutes = default_ttl_minutes
        
        # L1缓存：最热数据，最快访问
        self._l1_cache: OrderedDict[str, CacheEntry] = OrderedDict()
        
        # L2缓存：次热数据
        self._l2_cache: OrderedDict[str, CacheEntry] = OrderedDict()
        
        # 磁盘缓存目录
        self.disk_cache_dir = Path(disk_cache_dir) if disk_cache_dir else Path.cwd() / '.cache'
        self.disk_cache_dir.mkdir(exist_ok=True)
        
        self._lock = threading.RLock()
        self.stats = CacheStats()
        
        # 依赖关系跟踪
        self._dependencies: Dict[str, Set[str]] = {}
        
    def _generate_key(self, func_name: str, args: tuple, kwargs: dict) -> str:
        """生成缓存键"""
        key_data = f"{func_name}_{args}_{sorted(kwargs.items())}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def _get_disk_cache_path(self, key: str) -> Path:
        """获取磁盘缓存文件路径"""
        return self.disk_cache_dir / f"{key}.cache"
    
    def _load_from_disk(self, key: str) -> Optional[Any]:
        """从磁盘加载缓存"""
        try:
            cache_file = self._get_disk_cache_path(key)
            if cache_file.exists():
                with open(cache_file, 'rb') as f:
                    entry_data = pickle.load(f)
                    entry = CacheEntry(**entry_data)
                    if not entry.is_expired():
                        self.stats.disk_hits += 1
                        return entry.value
                    else:
                        cache_file.unlink()  # 删除过期文件
        except Exception as e:
            logger.warning(f"从磁盘加载缓存失败 {key}: {e}")
        return None
    
    def _save_to_disk(self, key: str, entry: CacheEntry):
        """保存到磁盘缓存"""
        try:
            cache_file = self._get_disk_cache_path(key)
            entry_data = {
                'value': entry.value,
                'expire_time': entry.expire_time,
                'access_count': entry.access_count,
                'priority': entry.priority
            }
            with open(cache_file, 'wb') as f:
                pickle.dump(entry_data, f)
        except Exception as e:
            logger.warning(f"保存到磁盘缓存失败 {key}: {e}")
    
    def _promote_to_l1(self, key: str, entry: CacheEntry):
        """提升到L1缓存"""
        # 如果L1已满，移除最少使用的
        if len(self._l1_cache) >= self.l1_max_size:
            lru_key, lru_entry = self._l1_cache.popitem(last=False)
            # 降级到L2
            self._demote_to_l2(lru_key, lru_entry)
        
        self._l1_cache[key] = entry
        self._l1_cache.move_to_end(key)
    
    def _demote_to_l2(self, key: str, entry: CacheEntry):
        """降级到L2缓存"""
        # 如果L2已满，移除最少使用的并保存到磁盘
        if len(self._l2_cache) >= self.l2_max_size:
            lru_key, lru_entry = self._l2_cache.popitem(last=False)
            if lru_entry.priority >= 2:  # 中高优先级保存到磁盘
                self._save_to_disk(lru_key, lru_entry)
        
        self._l2_cache[key] = entry
        self._l2_cache.move_to_end(key)
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        with self._lock:
            # 检查L1缓存
            if key in self._l1_cache:
                entry = self._l1_cache[key]
                if not entry.is_expired():
                    self._l1_cache.move_to_end(key)
                    entry.touch()
                    self.stats.hits += 1
                    self.stats.l1_hits += 1
                    return entry.value
                else:
                    del self._l1_cache[key]
            
            # 检查L2缓存
            if key in self._l2_cache:
                entry = self._l2_cache[key]
                if not entry.is_expired():
                    # 提升到L1
                    del self._l2_cache[key]
                    entry.touch()
                    self._promote_to_l1(key, entry)
                    self.stats.hits += 1
                    self.stats.l2_hits += 1
                    return entry.value
                else:
                    del self._l2_cache[key]
            
            # 检查磁盘缓存
            disk_value = self._load_from_disk(key)
            if disk_value is not None:
                # 重新加载到L2缓存
                expire_time = datetime.now() + timedelta(minutes=self.default_ttl_minutes)
                entry = CacheEntry(disk_value, expire_time, priority=2)
                self._demote_to_l2(key, entry)
                self.stats.hits += 1
                return disk_value
            
            self.stats.misses += 1
            return None
    
    def set(self, key: str, value: Any, ttl_minutes: Optional[int] = None, priority: int = 1) -> None:
        """设置缓存值"""
        with self._lock:
            ttl = ttl_minutes or self.default_ttl_minutes
            expire_time = datetime.now() + timedelta(minutes=ttl)
            entry = CacheEntry(value, expire_time, priority=priority)
            
            # 根据优先级决定存储位置
            if priority >= 3:  # 高优先级直接进L1
                self._promote_to_l1(key, entry)
            elif priority >= 2:  # 中优先级进L2
                self._demote_to_l2(key, entry)
            else:  # 低优先级直接保存到磁盘
                self._save_to_disk(key, entry)
    
    def invalidate_by_pattern(self, pattern: str):
        """按模式失效缓存"""
        with self._lock:
            keys_to_remove = []
            
            # 检查L1缓存
            for key in self._l1_cache:
                if pattern in key:
                    keys_to_remove.append(('l1', key))
            
            # 检查L2缓存
            for key in self._l2_cache:
                if pattern in key:
                    keys_to_remove.append(('l2', key))
            
            # 删除匹配的键
            for cache_type, key in keys_to_remove:
                if cache_type == 'l1' and key in self._l1_cache:
                    del self._l1_cache[key]
                elif cache_type == 'l2' and key in self._l2_cache:
                    del self._l2_cache[key]
            
            # 检查磁盘缓存
            for cache_file in self.disk_cache_dir.glob('*.cache'):
                if pattern in cache_file.stem:
                    try:
                        cache_file.unlink()
                    except Exception as e:
                        logger.warning(f"删除磁盘缓存文件失败 {cache_file}: {e}")
    
    def add_dependency(self, key: str, depends_on: str):
        """添加缓存依赖关系"""
        if depends_on not in self._dependencies:
            self._dependencies[depends_on] = set()
        self._dependencies[depends_on].add(key)
    
    def invalidate_dependents(self, key: str):
        """失效依赖的缓存"""
        if key in self._dependencies:
            for dependent_key in self._dependencies[key]:
                self.invalidate_by_pattern(dependent_key)
            del self._dependencies[key]
    
    def clear(self):
        """清空所有缓存"""
        with self._lock:
            self._l1_cache.clear()
            self._l2_cache.clear()
            self._dependencies.clear()
            
            # 清理磁盘缓存
            for cache_file in self.disk_cache_dir.glob('*.cache'):
                try:
                    cache_file.unlink()
                except Exception as e:
                    logger.warning(f"删除磁盘缓存文件失败 {cache_file}: {e}")
            
            self.stats.reset()
    
    def cleanup_expired(self):
        """清理过期条目"""
        with self._lock:
            # 清理L1缓存
            expired_keys = [key for key, entry in self._l1_cache.items() if entry.is_expired()]
            for key in expired_keys:
                del self._l1_cache[key]
                self.stats.evictions += 1
            
            # 清理L2缓存
            expired_keys = [key for key, entry in self._l2_cache.items() if entry.is_expired()]
            for key in expired_keys:
                del self._l2_cache[key]
                self.stats.evictions += 1
            
            # 清理磁盘缓存
            for cache_file in self.disk_cache_dir.glob('*.cache'):
                try:
                    with open(cache_file, 'rb') as f:
                        entry_data = pickle.load(f)
                        entry = CacheEntry(**entry_data)
                        if entry.is_expired():
                            cache_file.unlink()
                            self.stats.evictions += 1
                except Exception:
                    # 如果文件损坏，直接删除
                    cache_file.unlink()
    
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        return {
            'hits': self.stats.hits,
            'misses': self.stats.misses,
            'hit_rate': self.stats.hit_rate,
            'l1_hit_rate': self.stats.l1_hit_rate,
            'l1_size': len(self._l1_cache),
            'l2_size': len(self._l2_cache),
            'l1_hits': self.stats.l1_hits,
            'l2_hits': self.stats.l2_hits,
            'disk_hits': self.stats.disk_hits,
            'evictions': self.stats.evictions
        }

# 全局缓存实例
_tiered_cache = TieredCache()

def optimized_cache(cache_name: str, expire_minutes: int = 30, priority: int = 1):
    """优化的缓存装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 生成缓存键
            cache_key = f"{cache_name}_{_tiered_cache._generate_key(func.__name__, args, kwargs)}"
            
            # 尝试从缓存获取
            cached_result = _tiered_cache.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # 执行函数并缓存结果
            result = func(*args, **kwargs)
            _tiered_cache.set(cache_key, result, expire_minutes, priority)
            
            return result
        return wrapper
    return decorator

def invalidate_cache_pattern(pattern: str):
    """按模式失效缓存"""
    _tiered_cache.invalidate_by_pattern(pattern)

def get_cache_stats() -> Dict[str, Any]:
    """获取缓存统计信息"""
    return _tiered_cache.get_stats()

def cleanup_cache():
    """清理过期缓存"""
    _tiered_cache.cleanup_expired()