#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
简化的商户分类服务模块

提供基于配置文件的商户分类功能。
"""

import logging
import yaml
from pathlib import Path
from typing import Dict, Optional
from functools import lru_cache

logger = logging.getLogger(__name__)


class CategoryService:
    """简化的商户分类服务

    提供基于配置文件的商户分类功能。
    """

    def __init__(self, config_path: Optional[str] = None):
        """初始化分类服务

        Args:
            config_path: 配置文件路径，如果为None则使用默认路径
        """
        self.logger = logging.getLogger(__name__)
        self.config_path = Path(config_path) if config_path else self._get_default_config_path()
        self._merchant_lookup: Dict[str, str] = {}
        self._categories: Dict[str, Dict[str, str]] = {}

        # 加载配置
        self._load_config()
    
    def _get_default_config_path(self) -> Path:
        """获取默认配置文件路径"""
        project_root = Path(__file__).parent.parent.parent
        return project_root / "config" / "merchant_categories.yaml"

    def _load_config(self) -> None:
        """加载配置文件"""
        try:
            if not self.config_path.exists():
                self.logger.warning(f"配置文件不存在: {self.config_path}，使用默认配置")
                self._load_default_config()
                return

            with open(self.config_path, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)

            # 基本验证
            if not config_data or 'categories' not in config_data or 'merchants' not in config_data:
                raise ValueError("配置文件格式错误")

            # 构建商户查找表
            merchant_lookup = {}
            for category, merchant_list in config_data.get('merchants', {}).items():
                for merchant in merchant_list:
                    if merchant in merchant_lookup:
                        self.logger.warning(f"商户'{merchant}'重复定义")
                    merchant_lookup[merchant] = category

            self._categories = config_data.get('categories', {})
            self._merchant_lookup = merchant_lookup

            self.logger.info(f"配置加载成功: {len(self._categories)}个分类, {len(merchant_lookup)}个商户")

        except Exception as e:
            self.logger.error(f"配置加载失败: {e}")
            self._load_default_config()
    
    def _load_default_config(self) -> None:
        """加载默认配置"""
        self.logger.warning("使用默认配置")

        self._categories = {
            'other': {
                'name': '其他支出',
                'icon': 'more-horizontal',
                'color': 'dark',
                'description': '未分类的其他支出'
            }
        }
        self._merchant_lookup = {}

    @lru_cache(maxsize=1000)
    def classify_merchant(self, merchant_name: str) -> str:
        """对商户进行分类

        Args:
            merchant_name: 商户名称

        Returns:
            商户分类标识，如果未找到匹配则返回'other'
        """
        if not merchant_name or not isinstance(merchant_name, str):
            return 'other'

        normalized_name = merchant_name.strip()
        if not normalized_name:
            return 'other'

        return self._merchant_lookup.get(normalized_name, 'other')
    
    def get_category_display_info(self, category: str) -> Dict[str, str]:
        """获取分类的显示信息

        Args:
            category: 分类标识

        Returns:
            包含名称、颜色、描述、图标的字典
        """
        return self._categories.get(category, self._get_default_category_info())

    def _get_default_category_info(self) -> Dict[str, str]:
        """获取默认分类信息"""
        return {
            'name': '其他支出',
            'icon': 'more-horizontal',
            'color': 'dark',
            'description': '未分类的其他支出'
        }

    def get_all_categories(self) -> Dict[str, Dict[str, str]]:
        """获取所有分类信息"""
        return self._categories or {'other': self._get_default_category_info()}

    def clear_cache(self) -> None:
        """清除分类缓存"""
        self.classify_merchant.cache_clear()
        self.logger.info("分类缓存已清除")

    def reload_config(self) -> bool:
        """重新加载配置"""
        try:
            self._load_config()
            self.classify_merchant.cache_clear()
            self.logger.info("配置重新加载成功，缓存已清除")
            return True
        except Exception as e:
            self.logger.error(f"重新加载配置失败: {e}")
            return False


