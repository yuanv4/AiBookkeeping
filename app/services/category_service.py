#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
智能商户分类服务模块

提供基于智能匹配的商户分类功能：
- 分类元数据：硬编码在Python常量中
- 商户映射：支持精确匹配、关键词匹配、模式匹配
"""

import logging
import re
from typing import Dict, Optional, List

# 分类元数据定义（硬编码）
CATEGORIES = {
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
    },
    'uncategorized': {
        'name': '未分类',
        'icon': 'help-circle',
        'color': 'secondary',
        'description': '尚未分类的交易，需要手动处理'
    }
}


class SmartMerchantMatcher:
    """智能商户匹配器

    支持多种匹配策略：
    1. 精确匹配 - 完全相同的商户名称
    2. 关键词匹配 - 包含特定关键词
    3. 模式匹配 - 正则表达式匹配
    """

    def __init__(self):
        from .merchant_config import MERCHANT_CATEGORIES
        self.exact_rules = MERCHANT_CATEGORIES.get('exact_match', {})
        self.keyword_rules = MERCHANT_CATEGORIES.get('keyword_match', {})
        self.pattern_rules = MERCHANT_CATEGORIES.get('pattern_match', [])

    def classify(self, merchant_name: str) -> tuple[str, float]:
        """分类商户并返回置信度

        Returns:
            tuple: (category, confidence) 分类结果和置信度(0-1)
        """
        if not merchant_name:
            return 'other', 0.0

        normalized_name = self.normalize_merchant_name(merchant_name)

        # 1. 精确匹配 (置信度: 1.0)
        if normalized_name in self.exact_rules:
            return self.exact_rules[normalized_name], 1.0

        # 2. 关键词匹配 (置信度: 0.8)
        for keyword, category in self.keyword_rules.items():
            if keyword in normalized_name:
                return category, 0.8

        # 3. 模式匹配 (置信度: 0.6)
        for rule in self.pattern_rules:
            if re.match(rule['pattern'], normalized_name):
                return rule['category'], 0.6

        return 'other', 0.0

    def normalize_merchant_name(self, name: str) -> str:
        """标准化商户名称"""
        if not name:
            return ''
        # 去除多余空格，转换为小写，移除特殊字符
        normalized = re.sub(r'\s+', '', name.strip().lower())
        normalized = re.sub(r'[^\w\u4e00-\u9fff]', '', normalized)
        return normalized


class CategoryService:
    """简化的商户分类服务

    提供基于混合配置的商户分类功能：
    - 分类元数据：使用硬编码的CATEGORIES常量
    - 商户映射：从YAML配置文件加载
    """

    def __init__(self):
        """初始化分类服务"""
        self.logger = logging.getLogger(self.__class__.__name__)

        # 直接使用硬编码的分类数据
        self._categories = CATEGORIES.copy()

        # 初始化智能匹配器
        self.matcher = SmartMerchantMatcher()

        # 初始化用户规则管理器
        from .user_rules import SimpleUserRules
        self.user_rules = SimpleUserRules()

        self.logger.info(f"分类服务初始化完成: {len(self._categories)}个分类, 智能匹配器已就绪")

    def classify_merchant(self, merchant_name: str) -> str:
        """智能分类商户

        优先级：用户自定义规则 > 智能匹配规则

        Args:
            merchant_name: 商户名称

        Returns:
            str: 分类代码
        """
        if not merchant_name:
            return 'other'

        # 1. 优先查询用户自定义规则
        user_category = self.user_rules.get_rule(merchant_name)
        if user_category and user_category in self._categories:
            return user_category

        # 2. 使用智能匹配
        category, confidence = self.matcher.classify(merchant_name)

        # 记录低置信度分类用于后续优化
        if confidence < 0.8:
            self.logger.debug(f"低置信度分类: {merchant_name} -> {category} (置信度: {confidence:.2f})")

        return category

    def update_merchant_category(self, merchant_name: str, category: str) -> bool:
        """更新商户分类规则

        Args:
            merchant_name: 商户名称
            category: 新的分类代码

        Returns:
            bool: 是否更新成功
        """
        if category not in self._categories:
            self.logger.warning(f"无效的分类代码: {category}")
            return False

        return self.user_rules.set_rule(merchant_name, category)

    def get_user_rules_count(self) -> int:
        """获取用户自定义规则数量"""
        return self.user_rules.get_rules_count()

    def classify_merchants_batch(self, merchant_names: List[str]) -> Dict[str, str]:
        """批量分类商户

        Args:
            merchant_names: 商户名称列表

        Returns:
            dict: 商户名称到分类的映射
        """
        return {name: self.classify_merchant(name) for name in merchant_names}

    def get_classification_info(self, merchant_name: str) -> Dict:
        """获取分类详细信息

        Args:
            merchant_name: 商户名称

        Returns:
            dict: 包含分类、置信度等信息
        """
        if not merchant_name:
            return {'category': 'other', 'confidence': 0.0, 'method': 'default'}

        category, confidence = self.matcher.classify(merchant_name)

        # 确定匹配方法
        normalized_name = self.matcher.normalize_merchant_name(merchant_name)
        if normalized_name in self.matcher.exact_rules:
            method = 'exact_match'
        elif any(keyword in normalized_name for keyword in self.matcher.keyword_rules):
            method = 'keyword_match'
        elif any(re.match(rule['pattern'], normalized_name) for rule in self.matcher.pattern_rules):
            method = 'pattern_match'
        else:
            method = 'default'

        return {
            'category': category,
            'confidence': confidence,
            'method': method,
            'normalized_name': normalized_name
        }
    
    def get_category_display_info(self, category: str) -> Dict[str, str]:
        """获取分类的显示信息

        Args:
            category: 分类标识

        Returns:
            包含名称、颜色、描述、图标的字典
        """
        return self._categories.get(category, {
            'name': '未知分类',
            'icon': 'help-circle',
            'color': 'secondary',
            'description': '未知的分类类型'
        })

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
