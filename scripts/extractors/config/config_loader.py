"""配置加载器模块，负责加载和提供银行配置信息"""
import os
import json
import logging
from typing import Dict, Any, Optional, List

# 导入错误处理机制
from scripts.common.exceptions import ConfigError, ConfigLoadError
from scripts.common.error_handler import error_handler, safe_operation

# 导入新的配置管理器
from scripts.common.config import get_config_manager

class ConfigLoader:
    """银行配置加载器"""
    
    def __init__(self, config_file=None):
        """初始化配置加载器
        
        Args:
            config_file: 配置文件路径，如果为None则使用默认路径
        """
        self.logger = logging.getLogger('config_loader')
        
        # 获取配置管理器
        self.config_manager = get_config_manager()
        
        # 存储银行配置
        self.configs = self._load_configs()
    
    @error_handler(fallback_value={})
    def _load_configs(self) -> Dict[str, Any]:
        """加载配置文件
        
        Returns:
            dict: 银行配置字典
        """
        try:
            # 从统一配置系统获取银行配置
            banks_config = self.config_manager.get('extractors.banks')
            
            if banks_config:
                self.logger.info(f"成功加载银行配置，共 {len(banks_config)} 个银行")
                return banks_config
            
            # 如果统一配置中没有银行配置，尝试从原始文件加载（向后兼容）
            current_dir = os.path.dirname(os.path.abspath(__file__))
            legacy_config_file = os.path.join(current_dir, 'bank_configs.json')
            
            if os.path.exists(legacy_config_file):
                with open(legacy_config_file, 'r', encoding='utf-8') as f:
                    configs = json.load(f)
                
                self.logger.info(f"从原始配置文件加载了 {len(configs)} 个银行配置")
                
                # 将配置迁移到新的配置系统
                self.config_manager.set('extractors.banks', configs, save=True)
                
                return configs
            
            self.logger.warning("未找到任何银行配置")
            return {}
            
        except Exception as e:
            self.logger.error(f"加载配置文件时出错: {str(e)}")
            raise ConfigLoadError(f"加载银行配置失败: {str(e)}")
    
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
    
    @safe_operation("重新加载配置")
    def reload(self):
        """重新加载配置文件"""
        # 首先重新加载统一配置
        self.config_manager.reload()
        # 然后更新银行配置
        self.configs = self._load_configs()
        self.logger.info("已重新加载配置文件")
    
    def update_bank_config(self, bank_code: str, config: Dict[str, Any], save: bool = True) -> bool:
        """更新银行配置
        
        Args:
            bank_code: 银行代码
            config: 银行配置
            save: 是否保存到配置文件
            
        Returns:
            bool: 是否更新成功
        """
        try:
            # 验证必要字段
            if not all(k in config for k in ['bank_name', 'keywords', 'column_mappings']):
                self.logger.warning(f"更新银行配置失败: 缺少必要字段")
                return False
            
            # 更新内存中的配置
            self.configs[bank_code] = config
            
            # 更新统一配置系统
            self.config_manager.set(f'extractors.banks.{bank_code}', config, save=save)
            
            self.logger.info(f"已更新银行配置: {bank_code}")
            return True
        except Exception as e:
            self.logger.error(f"更新银行配置时出错: {str(e)}")
            return False

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