import json
import logging
import re
from pathlib import Path
from typing import Dict, Tuple, Optional, List
from flask import current_app
from app.configs.categories import CATEGORIES

logger = logging.getLogger(__name__)

# 预定义规则 (迁移自原 Service)
CLASSIFICATION_RULES = {
    'employer': {'keywords': ['代发工资', '工资', '薪水', '薪酬'], 'confidence': 0.95},
    'ecommerce': {'keywords': ['京东', '拼多多', '天猫', '淘宝', '商城', '旗舰店', '电子商务'], 'confidence': 0.9},
    'financial': {'keywords': ['朝朝宝', '理财', '基金', '投资', '太平洋人寿', '保险', '银行', '代销理财'], 'confidence': 0.9},
    'personal': {'keywords': ['微信转账', '个人转账'], 'confidence': 0.95},
    'utilities': {'keywords': ['物业服务', '燃气集团', '供水', '广东移动', '电费', '水费'], 'confidence': 0.9},
    'healthcare': {'keywords': ['医院', '药店', '诊所', '体检'], 'confidence': 0.9},
    'lifestyle': {'keywords': ['美团', '饿了么', '餐厅', '咖啡', '滴滴', '打车', '地铁', '公交', '理发'], 'confidence': 0.8}
}

class CategoryUtils:
    """商户分类工具类"""

    _user_rules_cache = None

    @staticmethod
    def _get_user_rules_path() -> Path:
        return Path(current_app.instance_path) / 'user_category_rules.json'

    @classmethod
    def _load_user_rules(cls) -> Dict[str, str]:
        if cls._user_rules_cache is not None:
            return cls._user_rules_cache
        
        try:
            path = cls._get_user_rules_path()
            if path.exists():
                with open(path, 'r', encoding='utf-8') as f:
                    cls._user_rules_cache = json.load(f)
            else:
                cls._user_rules_cache = {}
        except Exception as e:
            logger.warning(f"加载用户规则失败: {e}")
            cls._user_rules_cache = {}
        
        return cls._user_rules_cache

    @classmethod
    def save_user_rule(cls, merchant_name: str, category: str) -> bool:
        """保存用户自定义规则"""
        rules = cls._load_user_rules()
        rules[merchant_name] = category
        cls._user_rules_cache = rules # 更新缓存
        
        try:
            path = cls._get_user_rules_path()
            path.parent.mkdir(exist_ok=True)
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(rules, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            logger.error(f"保存规则失败: {e}")
            return False

    @staticmethod
    def normalize_name(name: str) -> str:
        if not name: return ''
        return re.sub(r'\s+', '', name.strip().lower())

    @classmethod
    def predict_category(cls, merchant_name: str, description: str = '') -> str:
        """预测分类"""
        if not merchant_name:
            return 'uncategorized'

        # 1. 用户规则优先
        rules = cls._load_user_rules()
        if merchant_name in rules:
            return rules[merchant_name]

        # 2. 关键词匹配
        norm_name = cls.normalize_name(merchant_name)
        norm_desc = cls.normalize_name(description)

        for cat, rule in CLASSIFICATION_RULES.items():
            for kw in rule['keywords']:
                if kw in norm_name or kw in norm_desc:
                    return cat
        
        return 'uncategorized'

    @classmethod
    def get_ai_suggestion(cls, merchant_name: str) -> Dict:
        """获取建议 (用于前端展示)"""
        cat = cls.predict_category(merchant_name)
        return {
            'category': cat,
            'category_name': CATEGORIES.get(cat, {}).get('name', '未知'),
            'confidence': 90 if cat != 'uncategorized' else 0
        }

    @classmethod
    def get_ai_suggestions_batch(cls, merchant_names: List[str]) -> Dict[str, Dict]:
        """批量获取建议"""
        suggestions = {}
        for name in merchant_names:
            suggestions[name] = cls.get_ai_suggestion(name)
        return suggestions
