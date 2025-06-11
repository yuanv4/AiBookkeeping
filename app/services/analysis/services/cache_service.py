"""缓存服务层 - 统一管理分析结果缓存

该模块提供统一的缓存管理接口，支持多种缓存策略和失效机制，
提高分析性能和用户体验。

Created: 2024-12-19
Author: AI Assistant
"""

import json
import hashlib
from datetime import datetime, timedelta, date
from typing import Any, Dict, Optional, Union, List
from decimal import Decimal
import pickle
import os
from pathlib import Path


class DecimalEncoder(json.JSONEncoder):
    """自定义JSON编码器，支持Decimal类型"""
    
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        elif isinstance(obj, (date, datetime)):
            return obj.isoformat()
        return super().default(obj)


class CacheService:
    """缓存服务
    
    提供内存缓存和文件缓存功能，支持TTL（生存时间）和LRU（最近最少使用）策略。
    """
    
    def __init__(
        self, 
        cache_dir: Optional[str] = None,
        max_memory_items: int = 100,
        default_ttl_minutes: int = 30
    ):
        """初始化缓存服务
        
        Args:
            cache_dir: 文件缓存目录，如果为None则只使用内存缓存
            max_memory_items: 内存缓存最大项目数
            default_ttl_minutes: 默认TTL（分钟）
        """
        self.cache_dir = Path(cache_dir) if cache_dir else None
        self.max_memory_items = max_memory_items
        self.default_ttl_minutes = default_ttl_minutes
        
        # 内存缓存
        self._memory_cache: Dict[str, Dict[str, Any]] = {}
        self._access_order: List[str] = []  # LRU跟踪
        
        # 确保缓存目录存在
        if self.cache_dir:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_cache_key(
        self, 
        analyzer_type: str,
        method_name: str,
        start_date: date,
        end_date: date,
        account_id: Optional[int] = None,
        **kwargs
    ) -> str:
        """生成缓存键
        
        Args:
            analyzer_type: 分析器类型
            method_name: 方法名
            start_date: 开始日期
            end_date: 结束日期
            account_id: 账户ID
            **kwargs: 其他参数
            
        Returns:
            缓存键
        """
        # 构建键值字符串
        key_parts = [
            analyzer_type,
            method_name,
            start_date.isoformat(),
            end_date.isoformat(),
            str(account_id) if account_id else 'all'
        ]
        
        # 添加其他参数
        if kwargs:
            sorted_kwargs = sorted(kwargs.items())
            for key, value in sorted_kwargs:
                key_parts.append(f"{key}:{value}")
        
        # 生成哈希
        key_string = "|".join(key_parts)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def get_cached_data(
        self, 
        cache_key: str,
        use_file_cache: bool = True
    ) -> Optional[Any]:
        """获取缓存数据
        
        Args:
            cache_key: 缓存键
            use_file_cache: 是否使用文件缓存
            
        Returns:
            缓存的数据，如果不存在或已过期则返回None
        """
        # 首先检查内存缓存
        if cache_key in self._memory_cache:
            cache_item = self._memory_cache[cache_key]
            
            # 检查是否过期
            if self._is_expired(cache_item['expires_at']):
                self._remove_from_memory_cache(cache_key)
            else:
                # 更新访问顺序（LRU）
                self._update_access_order(cache_key)
                return cache_item['data']
        
        # 如果内存缓存中没有，检查文件缓存
        if use_file_cache and self.cache_dir:
            return self._get_from_file_cache(cache_key)
        
        return None
    
    def set_cached_data(
        self, 
        cache_key: str,
        data: Any,
        ttl_minutes: Optional[int] = None,
        use_file_cache: bool = True
    ) -> None:
        """设置缓存数据
        
        Args:
            cache_key: 缓存键
            data: 要缓存的数据
            ttl_minutes: TTL（分钟），如果为None则使用默认值
            use_file_cache: 是否同时保存到文件缓存
        """
        if ttl_minutes is None:
            ttl_minutes = self.default_ttl_minutes
        
        expires_at = datetime.now() + timedelta(minutes=ttl_minutes)
        
        # 保存到内存缓存
        self._set_to_memory_cache(cache_key, data, expires_at)
        
        # 保存到文件缓存
        if use_file_cache and self.cache_dir:
            self._set_to_file_cache(cache_key, data, expires_at)
    
    def clear_cache(
        self, 
        pattern: Optional[str] = None,
        clear_file_cache: bool = True
    ) -> None:
        """清除缓存
        
        Args:
            pattern: 缓存键模式，如果为None则清除所有缓存
            clear_file_cache: 是否同时清除文件缓存
        """
        if pattern is None:
            # 清除所有内存缓存
            self._memory_cache.clear()
            self._access_order.clear()
            
            # 清除所有文件缓存
            if clear_file_cache and self.cache_dir:
                for cache_file in self.cache_dir.glob("*.cache"):
                    try:
                        cache_file.unlink()
                    except OSError:
                        pass
        else:
            # 清除匹配模式的缓存
            keys_to_remove = [
                key for key in self._memory_cache.keys() 
                if pattern in key
            ]
            
            for key in keys_to_remove:
                self._remove_from_memory_cache(key)
            
            # 清除匹配的文件缓存
            if clear_file_cache and self.cache_dir:
                for cache_file in self.cache_dir.glob("*.cache"):
                    if pattern in cache_file.stem:
                        try:
                            cache_file.unlink()
                        except OSError:
                            pass
    
    def clear_expired_cache(self) -> None:
        """清除过期的缓存"""
        current_time = datetime.now()
        
        # 清除过期的内存缓存
        expired_keys = [
            key for key, item in self._memory_cache.items()
            if self._is_expired(item['expires_at'])
        ]
        
        for key in expired_keys:
            self._remove_from_memory_cache(key)
        
        # 清除过期的文件缓存
        if self.cache_dir:
            for cache_file in self.cache_dir.glob("*.cache"):
                try:
                    with open(cache_file, 'rb') as f:
                        cache_data = pickle.load(f)
                        if self._is_expired(cache_data.get('expires_at')):
                            cache_file.unlink()
                except (OSError, pickle.PickleError):
                    # 如果文件损坏，删除它
                    try:
                        cache_file.unlink()
                    except OSError:
                        pass
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息
        
        Returns:
            缓存统计信息
        """
        memory_count = len(self._memory_cache)
        file_count = 0
        
        if self.cache_dir:
            file_count = len(list(self.cache_dir.glob("*.cache")))
        
        return {
            'memory_cache_count': memory_count,
            'file_cache_count': file_count,
            'max_memory_items': self.max_memory_items,
            'memory_usage_ratio': memory_count / self.max_memory_items,
            'cache_directory': str(self.cache_dir) if self.cache_dir else None
        }
    
    def _set_to_memory_cache(
        self, 
        cache_key: str, 
        data: Any, 
        expires_at: datetime
    ) -> None:
        """设置内存缓存"""
        # 如果缓存已满，移除最少使用的项目
        if len(self._memory_cache) >= self.max_memory_items:
            if cache_key not in self._memory_cache:
                # 移除最少使用的项目
                lru_key = self._access_order[0]
                self._remove_from_memory_cache(lru_key)
        
        self._memory_cache[cache_key] = {
            'data': data,
            'expires_at': expires_at,
            'created_at': datetime.now()
        }
        
        self._update_access_order(cache_key)
    
    def _remove_from_memory_cache(self, cache_key: str) -> None:
        """从内存缓存中移除项目"""
        if cache_key in self._memory_cache:
            del self._memory_cache[cache_key]
        
        if cache_key in self._access_order:
            self._access_order.remove(cache_key)
    
    def _update_access_order(self, cache_key: str) -> None:
        """更新访问顺序（LRU）"""
        if cache_key in self._access_order:
            self._access_order.remove(cache_key)
        self._access_order.append(cache_key)
    
    def _set_to_file_cache(
        self, 
        cache_key: str, 
        data: Any, 
        expires_at: datetime
    ) -> None:
        """设置文件缓存"""
        if not self.cache_dir:
            return
        
        cache_file = self.cache_dir / f"{cache_key}.cache"
        
        try:
            cache_data = {
                'data': data,
                'expires_at': expires_at,
                'created_at': datetime.now()
            }
            
            with open(cache_file, 'wb') as f:
                pickle.dump(cache_data, f)
                
        except (OSError, pickle.PickleError) as e:
            # 记录错误但不抛出异常
            print(f"Error saving to file cache: {e}")
    
    def _get_from_file_cache(self, cache_key: str) -> Optional[Any]:
        """从文件缓存获取数据"""
        if not self.cache_dir:
            return None
        
        cache_file = self.cache_dir / f"{cache_key}.cache"
        
        if not cache_file.exists():
            return None
        
        try:
            with open(cache_file, 'rb') as f:
                cache_data = pickle.load(f)
            
            # 检查是否过期
            if self._is_expired(cache_data.get('expires_at')):
                cache_file.unlink()  # 删除过期文件
                return None
            
            # 将数据加载到内存缓存中
            self._set_to_memory_cache(
                cache_key, 
                cache_data['data'], 
                cache_data['expires_at']
            )
            
            return cache_data['data']
            
        except (OSError, pickle.PickleError) as e:
            # 如果文件损坏，删除它
            try:
                cache_file.unlink()
            except OSError:
                pass
            print(f"Error reading from file cache: {e}")
            return None
    
    def _is_expired(self, expires_at: Optional[datetime]) -> bool:
        """检查是否过期"""
        if expires_at is None:
            return True
        return datetime.now() > expires_at
    
    def invalidate_date_range_cache(
        self, 
        start_date: date, 
        end_date: date
    ) -> None:
        """使特定日期范围的缓存失效
        
        当数据发生变化时，需要清除相关的缓存。
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
        """
        # 构建日期模式
        date_patterns = [
            start_date.isoformat(),
            end_date.isoformat()
        ]
        
        # 清除包含这些日期的缓存
        for pattern in date_patterns:
            self.clear_cache(pattern=pattern)
    
    def __del__(self):
        """析构函数，清理资源"""
        # 清理过期缓存
        try:
            self.clear_expired_cache()
        except Exception:
            pass