"""配置加载器模块，负责加载和提供银行配置信息"""
import os
import json
import logging
from typing import Dict, Any, Optional, List

class ConfigLoader:
    """银行配置加载器"""
    
    def __init__(self, config_file=None):
        """初始化配置加载器
        
        Args:
            config_file: 配置文件路径，如果为None则使用默认路径
        """
        self.logger = logging.getLogger('config_loader')
        
        # 如果未指定配置文件，使用默认路径
        if config_file is None:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            config_file = os.path.join(current_dir, 'bank_configs.json')
        
        self.config_file = config_file
        self.configs = self._load_configs()
    
    def _load_configs(self) -> Dict[str, Any]:
        """加载配置文件
        
        Returns:
            dict: 银行配置字典
        """
        try:
            if not os.path.exists(self.config_file):
                self.logger.error(f"配置文件不存在: {self.config_file}")
                return {}
            
            with open(self.config_file, 'r', encoding='utf-8') as f:
                configs = json.load(f)
            
            self.logger.info(f"成功加载配置文件: {self.config_file}")
            self.logger.info(f"已加载 {len(configs)} 个银行配置")
            return configs
            
        except Exception as e:
            self.logger.error(f"加载配置文件时出错: {str(e)}")
            return {}
    
    def get_bank_config(self, bank_code: str) -> Optional[Dict[str, Any]]:
        """获取指定银行的配置
        
        Args:
            bank_code: 银行代码，如CMB、CCB
            
        Returns:
            dict: 银行配置字典，如果不存在返回None
        """
        return self.configs.get(bank_code)
    
    def get_all_banks(self) -> List[str]:
        """获取所有支持的银行代码
        
        Returns:
            list: 银行代码列表
        """
        return list(self.configs.keys())
    
    def get_bank_keyword(self, bank_code: str) -> List[str]:
        """获取银行关键词列表，用于文件匹配
        
        Args:
            bank_code: 银行代码
            
        Returns:
            list: 关键词列表，如果银行不存在返回空列表
        """
        config = self.get_bank_config(bank_code)
        if config:
            return config.get('keywords', [])
        return []
    
    def reload(self):
        """重新加载配置文件"""
        self.configs = self._load_configs()
        self.logger.info("已重新加载配置文件")

# 单例模式
_config_loader = None

def get_config_loader() -> ConfigLoader:
    """获取配置加载器单例
    
    Returns:
        ConfigLoader: 配置加载器实例
    """
    global _config_loader
    if _config_loader is None:
        _config_loader = ConfigLoader()
    return _config_loader 