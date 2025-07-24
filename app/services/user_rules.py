"""用户自定义分类规则管理器

将用户自定义分类规则保存到instance目录的JSON文件中，
参照数据库文件的命名和存储方式。
"""

import json
import logging
from pathlib import Path
from typing import Optional, Dict
from flask import current_app

logger = logging.getLogger(__name__)


class SimpleUserRules:
    """极简用户规则管理器
    
    将用户自定义分类规则保存到instance目录的JSON文件中
    """
    
    def __init__(self):
        self._file_path = None
    
    @property
    def file_path(self) -> Path:
        """获取用户规则文件路径"""
        if self._file_path is None:
            # 使用Flask的instance_path，参照数据库文件的方式
            instance_path = current_app.instance_path
            self._file_path = Path(instance_path) / 'user_category_rules.json'
        return self._file_path
    
    def get_rule(self, merchant_name: str) -> Optional[str]:
        """获取商户规则
        
        Args:
            merchant_name: 商户名称
            
        Returns:
            分类代码，如果不存在则返回None
        """
        try:
            if not self.file_path.exists():
                return None
            
            with open(self.file_path, 'r', encoding='utf-8') as f:
                rules = json.load(f)
            
            return rules.get(merchant_name)
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"读取用户规则失败: {e}")
            return None
    
    def set_rule(self, merchant_name: str, category: str) -> bool:
        """设置商户规则
        
        Args:
            merchant_name: 商户名称
            category: 分类代码
            
        Returns:
            是否保存成功
        """
        try:
            # 确保instance目录存在
            self.file_path.parent.mkdir(exist_ok=True)
            
            # 读取现有规则
            rules = {}
            if self.file_path.exists():
                try:
                    with open(self.file_path, 'r', encoding='utf-8') as f:
                        rules = json.load(f)
                except json.JSONDecodeError:
                    # 文件损坏时重新开始
                    logger.warning("用户规则文件损坏，重新创建")
                    rules = {}
            
            # 更新规则
            rules[merchant_name] = category
            
            # 原子写入：先写临时文件，再重命名
            temp_path = self.file_path.with_suffix('.tmp')
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(rules, f, ensure_ascii=False, indent=2)
            
            temp_path.replace(self.file_path)
            logger.info(f"用户规则已保存: {merchant_name} -> {category}")
            return True
            
        except IOError as e:
            logger.error(f"保存用户规则失败: {e}")
            return False
    
    def get_all_rules(self) -> Dict[str, str]:
        """获取所有规则
        
        Returns:
            商户名称到分类的映射字典
        """
        try:
            if not self.file_path.exists():
                return {}
            
            with open(self.file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"读取用户规则失败: {e}")
            return {}
    
    def remove_rule(self, merchant_name: str) -> bool:
        """删除商户规则
        
        Args:
            merchant_name: 商户名称
            
        Returns:
            是否删除成功
        """
        try:
            if not self.file_path.exists():
                return True
            
            with open(self.file_path, 'r', encoding='utf-8') as f:
                rules = json.load(f)
            
            if merchant_name in rules:
                del rules[merchant_name]
                
                # 原子写入
                temp_path = self.file_path.with_suffix('.tmp')
                with open(temp_path, 'w', encoding='utf-8') as f:
                    json.dump(rules, f, ensure_ascii=False, indent=2)
                
                temp_path.replace(self.file_path)
                logger.info(f"用户规则已删除: {merchant_name}")
            
            return True
            
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"删除用户规则失败: {e}")
            return False
    
    def get_rules_count(self) -> int:
        """获取用户自定义规则数量"""
        return len(self.get_all_rules())
