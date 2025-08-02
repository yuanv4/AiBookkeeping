#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
商户分类服务模块

提供基于规则的商户分类功能：
- 预定义分类规则（合并自merchant_config.py）
- 用户自定义规则（合并自user_rules.py）
- 智能匹配算法

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
    'healthcare': {
        'keywords': ['医院', '药店', '药房', '诊所', '体检'],
        'confidence': 0.9
    },
    'finance': {
        'keywords': ['银行', '保险', '证券', '基金', '理财', '投资', '代销', '汇差', '转账'],
        'confidence': 0.9
    },
    'shopping': {
        'keywords': ['超市', '商场', '百货', '购物', '便利店', '商行', '商城', '电商',
                    '电子商务', '旗舰店', '铺子'],
        'confidence': 0.8
    },
    'dining': {
        'keywords': ['餐厅', '咖啡', '茶饮', '火锅', '烧烤', '美团', '饿了么', '煲仔饭',
                    '牛肉面', '米线', '蜜雪冰城', '奶茶', '茶姬', '肠粉', '小炒', '家常菜',
                    '餐饮', '拉面', '螺蛳粉', '烧鹅', '汤粉', '厨房', '快餐'],
        'confidence': 0.8
    },
    'transport': {
        'keywords': ['地铁', '公交', '出租', '加油', '停车', '深圳通', '公交卡', '地铁卡',
                    '滴滴', '出行'],
        'confidence': 0.8
    },
    'services': {
        'keywords': ['快递', '物流', '通信', '宽带', '理发', '美容', '顺丰', '速运', '圆通',
                    '中通', '韵达', '申通', '平台商户', '网络科技', '在线科技', '移动',
                    '通讯', '信息技术', '供应链', '菜鸟'],
        'confidence': 0.7
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

def _classify_by_rules(merchant_name: str) -> Tuple[str, float]:
    """基于预定义规则分类商户"""
    if not merchant_name:
        return 'uncategorized', 0.0

    normalized_name = _normalize_merchant_name(merchant_name)

    # 关键词匹配
    for category, rule in CLASSIFICATION_RULES.items():
        if any(keyword in normalized_name for keyword in rule['keywords']):
            return category, rule['confidence']

    return 'uncategorized', 0.0

class CategoryService:
    """简化的商户分类服务

    合并了用户规则管理和智能匹配功能，提供统一的分类接口。
    """

    def __init__(self):
        """初始化分类服务"""
        self.logger = logging.getLogger(self.__class__.__name__)
        self._categories = CATEGORIES.copy()

        # 缓存用户规则到内存
        self._user_rules_cache = _load_user_rules()

        self.logger.info(f"分类服务初始化完成: {len(self._categories)}个分类")

    def classify_merchant(self, merchant_name: str) -> str:
        """智能分类商户（简化版）

        优先级：用户自定义规则 > 预定义规则
        """
        if not merchant_name:
            return 'uncategorized'

        # 1. 优先查询用户自定义规则（使用缓存）
        user_category = self._user_rules_cache.get(merchant_name)
        if user_category and user_category in self._categories:
            return user_category

        # 2. 使用预定义规则
        category, confidence = _classify_by_rules(merchant_name)
        return category

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

    def get_ai_suggestion(self, merchant_name: str) -> Dict:
        """为商户生成AI分类建议"""
        if not merchant_name:
            return {
                'category': 'uncategorized',
                'category_name': CATEGORIES['uncategorized']['name'],
                'confidence': 0,
                'reason': '商户名称为空'
            }

        category, confidence_float = _classify_by_rules(merchant_name)
        confidence = int(confidence_float * 100)
        category_info = CATEGORIES.get(category, CATEGORIES['uncategorized'])

        # 简化的推荐理由
        reason = f"基于关键词匹配识别为{category_info['name']}" if category != 'uncategorized' else "未找到匹配规则"

        return {
            'category': category,
            'category_name': category_info['name'],
            'confidence': confidence,
            'reason': reason
        }

    def get_ai_suggestions_batch(self, merchant_names: List[str]) -> Dict[str, Dict]:
        """批量为商户生成AI分类建议"""
        return {name: self.get_ai_suggestion(name) for name in merchant_names}
