#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
简化的商户分类服务模块

提供基于混合配置的商户分类功能：
- 分类元数据：硬编码在Python常量中
- 商户映射：从YAML配置文件加载
"""

import logging
import yaml
from pathlib import Path
from typing import Dict, Optional, List
from functools import lru_cache

class CategoryService:
    """简化的商户分类服务

    提供基于混合配置的商户分类功能：
    - 分类元数据：使用硬编码的CATEGORIES常量
    - 商户映射：从YAML配置文件加载
    """

    def __init__(self, config_path: Optional[str] = None):
        """初始化分类服务

        Args:
            config_path: 配置文件路径，如果为None则使用默认路径
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        if config_path:
            self.config_path = Path(config_path)
        else:
            # 使用相对于项目根目录的配置文件路径
            project_root = Path(__file__).parent.parent.parent
            self.config_path = project_root / "config" / "merchant_categories.yaml"
        self._merchant_lookup: Dict[str, str] = {}

        # 直接使用硬编码的分类数据
        self._categories = {
            'dining': {
                'name': '餐饮支出',
                'icon': 'coffee',
                'color': 'primary',
                'description': '餐厅、咖啡、外卖等饮食消费'
            },
            'transport': {
                'name': '交通支出',
                'icon': 'car',
                'color': 'success',
                'description': '地铁、打车、加油等出行费用'
            },
            'shopping': {
                'name': '购物支出',
                'icon': 'shopping-bag',
                'color': 'info',
                'description': '网购、超市、商场等购物消费'
            },
            'services': {
                'name': '生活服务',
                'icon': 'settings',
                'color': 'warning',
                'description': '通信、快递、美容等服务费用'
            },
            'healthcare': {
                'name': '医疗健康',
                'icon': 'heart',
                'color': 'danger',
                'description': '医院、药店、体检等医疗支出'
            },
            'finance': {
                'name': '金融保险',
                'icon': 'credit-card',
                'color': 'secondary',
                'description': '保险、转账等金融相关支出'
            },
            'other': {
                'name': '其他支出',
                'icon': 'more-horizontal',
                'color': 'dark',
                'description': '未分类的其他支出'
            }
        }

        # 加载商户映射配置
        self._load_config()

    def _load_config(self) -> None:
        """加载商户映射配置文件"""
        self._merchant_lookup = {}

        try:
            if self.config_path.exists():
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config_data = yaml.safe_load(f) or {}

                # 直接处理merchants数据
                for category, merchants in config_data.get('merchants', {}).items():
                    if category in self._categories:
                        for merchant in merchants or []:
                            self._merchant_lookup[merchant] = category

                self.logger.info(f"加载了 {len(self._merchant_lookup)} 个商户映射")
            else:
                self.logger.info("配置文件不存在，使用空的商户映射")

        except Exception as e:
            self.logger.warning(f"配置加载失败: {e}")
            self._merchant_lookup = {}

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
        self.logger.info("分类缓存已清除")
