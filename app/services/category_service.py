#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
简化的商户分类服务模块

提供基于配置文件的商户分类功能。
"""

import logging
import yaml
from pathlib import Path
from typing import Dict, Optional, List
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
        if config_path:
            self.config_path = Path(config_path)
        else:
            # 使用相对于项目根目录的配置文件路径
            project_root = Path(__file__).parent.parent.parent
            self.config_path = project_root / "config" / "merchant_categories.yaml"
        self._merchant_lookup: Dict[str, str] = {}
        self._categories: Dict[str, Dict[str, str]] = {}

        # 加载配置
        self._load_config()

    def _load_config(self) -> None:
        """加载配置文件"""
        try:
            if not self.config_path.exists():
                raise FileNotFoundError(f"分类配置文件不存在: {self.config_path}，应用无法启动")

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
                        logger.warning(f"商户'{merchant}'重复定义")
                    merchant_lookup[merchant] = category

            self._categories = config_data.get('categories', {})
            self._merchant_lookup = merchant_lookup

            logger.info(f"配置加载成功: {len(self._categories)}个分类, {len(merchant_lookup)}个商户")

        except Exception as e:
            logger.error(f"配置加载失败: {e}")
            raise RuntimeError(f"分类配置加载失败，应用无法启动: {e}") from e

    @lru_cache(maxsize=1000)
    def classify_merchant(self, merchant_name: str) -> str:
        """对商户进行分类

        Args:
            merchant_name: 商户名称

        Returns:
            商户分类标识，如果未找到匹配则返回'other'
        """
        # 验证并标准化商户名称
        if not merchant_name or not isinstance(merchant_name, str):
            return 'other'

        normalized_name = merchant_name.strip()
        return self._merchant_lookup.get(normalized_name, 'other') if normalized_name else 'other'
    
    def get_category_display_info(self, category: str) -> Dict[str, str]:
        """获取分类的显示信息

        Args:
            category: 分类标识

        Returns:
            包含名称、颜色、描述、图标的字典
        """
        if category not in self._categories:
            raise ValueError(f"未知的分类代码: {category}")
        return self._categories[category]

    def get_all_categories(self) -> Dict[str, Dict[str, str]]:
        """获取所有分类信息"""
        return self._categories

    def get_valid_category_codes(self) -> List[str]:
        """获取所有有效的分类代码列表"""
        return list(self._categories.keys())

    def classify_merchant_with_info(self, merchant_name: str) -> Dict[str, str]:
        """对商户进行分类并返回完整的分类信息

        Args:
            merchant_name: 商户名称

        Returns:
            包含分类代码和显示信息的字典
        """
        category = self.classify_merchant(merchant_name)
        category_info = self.get_category_display_info(category)
        return {
            'code': category,
            **category_info
        }

    def clear_cache(self) -> None:
        """清除分类缓存"""
        self.classify_merchant.cache_clear()
        logger.info("分类缓存已清除")
