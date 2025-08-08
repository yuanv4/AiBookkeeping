#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
商户分类服务模块

提供基于商户类型的智能分类功能：
- 商户类型分类规则
- 用户自定义规则管理
- 智能AI分类建议

"""

import json
import logging
import re
from pathlib import Path
from typing import Dict, List, Tuple
from flask import current_app

from app.configs.categories import CATEGORIES

# ==================== 配置数据区域 ====================

CLASSIFICATION_RULES = {
    'employer': {
        'keywords': ['代发工资', '工资', '薪水', '薪酬'],
        'confidence': 0.95
    },
    'ecommerce': {
        'keywords': ['京东', '拼多多', '天猫', '淘宝', '商城', '旗舰店', '电子商务'],
        'confidence': 0.9
    },
    'financial': {
        'keywords': ['朝朝宝', '理财', '基金', '投资', '太平洋人寿', '保险', '银行', '代销理财', '待清算电子汇差'],
        'confidence': 0.9
    },
    'personal': {
        'keywords': ['微信转账', '个人转账'],
        'confidence': 0.95
    },
    'utilities': {
        'keywords': ['物业服务', '燃气集团', '供水', '广东移动', '深***勤物业', '深***气集团', '深***吉供水'],
        'confidence': 0.9
    },
    'healthcare': {
        'keywords': ['医院', '药店', '诊所', '体检'],
        'confidence': 0.9
    },
    'lifestyle': {
        'keywords': [
            # 餐饮关键词
            '美团', '饿了么', '餐厅', '咖啡', '北京三快在线科技',
            # 交通关键词  
            '高德打车', '深圳通', '地铁', '公交', '滴滴', '出行',
            # 其他服务关键词
            '快递', '理发', '美容', '维修', '成都所见所得科技'
        ],
        'confidence': 0.8
    }
}

# ==================== 用户规则管理 ====================

def _get_user_rules_file_path() -> Path:
    """获取用户规则文件路径"""
    instance_path = current_app.instance_path
    return Path(instance_path) / 'user_category_rules.json'

def _load_user_rules() -> Dict[str, str]:
    """加载用户自定义规则"""
    try:
        file_path = _get_user_rules_file_path()
        if not file_path.exists():
            return {}

        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        logging.warning(f"读取用户规则失败: {e}")
        return {}

def _save_user_rules(rules: Dict[str, str]) -> bool:
    """保存用户自定义规则"""
    try:
        file_path = _get_user_rules_file_path()
        file_path.parent.mkdir(exist_ok=True)

        # 原子写入
        temp_path = file_path.with_suffix('.tmp')
        with open(temp_path, 'w', encoding='utf-8') as f:
            json.dump(rules, f, ensure_ascii=False, indent=2)

        temp_path.replace(file_path)
        return True
    except (IOError, OSError) as e:
        logging.error(f"保存用户规则失败: {e}")
        return False

# ==================== 分类逻辑 ====================

def _normalize_merchant_name(name: str) -> str:
    """标准化商户名称"""
    if not name:
        return ''
    # 去除多余空格，转换为小写，移除特殊字符
    normalized = re.sub(r'\s+', '', name.strip().lower())
    normalized = re.sub(r'[^\w\u4e00-\u9fff]', '', normalized)
    return normalized

def _classify_by_rules(merchant_name: str, description: str = '') -> Tuple[str, float]:
    """基于预定义规则分类商户"""
    if not merchant_name:
        return 'uncategorized', 0.0

    normalized_name = _normalize_merchant_name(merchant_name)
    normalized_desc = _normalize_merchant_name(description) if description else ''

    # 在分类规则中查找匹配
    for category, rule in CLASSIFICATION_RULES.items():
        # 在商户名称和描述中查找关键词
        for keyword in rule['keywords']:
            if keyword in normalized_name or keyword in normalized_desc:
                return category, rule['confidence']

    return 'uncategorized', 0.0

class CategoryService:
    """商户分类服务

    提供基于商户类型的智能分类功能。
    """

    def __init__(self):
        """初始化分类服务"""
        self.logger = logging.getLogger(self.__class__.__name__)
        self._categories = CATEGORIES.copy()

        # 缓存用户规则到内存
        self._user_rules_cache = _load_user_rules()

        self.logger.info(f"分类服务初始化完成: {len(self._categories)}个分类")

    def classify_merchant(self, merchant_name: str, description: str = '') -> str:
        """智能分类商户

        Args:
            merchant_name: 商户名称
            description: 交易描述

        Returns:
            分类代码
        """
        if not merchant_name:
            return 'uncategorized'

        # 1. 优先查询用户自定义规则（使用缓存）
        user_category = self._user_rules_cache.get(merchant_name)
        if user_category and user_category in self._categories:
            return user_category

        # 2. 使用预定义规则
        category, confidence = _classify_by_rules(merchant_name, description)
        return category

    def get_all_categories(self) -> Dict:
        """获取所有分类

        Returns:
            分类字典
        """
        return self._categories

    def update_merchant_category(self, merchant_name: str, category: str) -> bool:
        """更新商户分类规则（简化版）"""
        if category not in self._categories:
            self.logger.warning(f"无效的分类代码: {category}")
            return False

        # 更新缓存和文件
        self._user_rules_cache[merchant_name] = category
        return _save_user_rules(self._user_rules_cache)

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

    def get_ai_suggestion(self, merchant_name: str, description: str = '') -> Dict:
        """为商户生成AI分类建议

        Args:
            merchant_name: 商户名称
            description: 交易描述

        Returns:
            包含分类建议的字典
        """
        if not merchant_name:
            return {
                'category': 'uncategorized',
                'category_name': CATEGORIES['uncategorized']['name'],
                'confidence': 0,
                'reason': '商户名称为空'
            }

        category, confidence_float = _classify_by_rules(merchant_name, description)
        confidence = int(confidence_float * 100)
        category_info = CATEGORIES.get(category, CATEGORIES['uncategorized'])

        # 生成推荐理由
        if category != 'uncategorized':
            reason = f"基于关键词匹配识别为{category_info['name']}"
        else:
            reason = "未找到匹配的分类规则"

        return {
            'category': category,
            'category_name': category_info['name'],
            'confidence': confidence,
            'reason': reason
        }

    def get_ai_suggestions_batch(self, merchant_names: List[str]) -> Dict[str, Dict]:
        """批量为商户生成AI分类建议

        Args:
            merchant_names: 商户名称列表

        Returns:
            商户名称到分类建议的映射
        """
        suggestions = {}
        for merchant_name in merchant_names:
            suggestions[merchant_name] = self.get_ai_suggestion(merchant_name)
        return suggestions
