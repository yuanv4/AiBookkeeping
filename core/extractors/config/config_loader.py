"""配置加载器模块，负责加载和提供银行配置信息"""
import os
import json
import logging
from typing import Dict, Any, Optional, List

# 导入错误处理机制
from core.common.exceptions import ConfigError, ConfigLoadError
from core.common.error_handler import error_handler, safe_operation

# from core.common.config import get_config_manager # Removed

class ConfigLoader:
    """银行配置加载器"""
    
    def __init__(self, app):
        """初始化配置加载器
        
        Args:
            app: Flask application instance.
        """
        self.logger = logging.getLogger('config_loader')
        self.app = app
        # 存储银行配置
        self.configs = self._load_configs()
    
    @error_handler(fallback_value={})
    def _load_configs(self) -> Dict[str, Any]:
        """加载配置文件
        
        Returns:
            dict: 银行配置字典
        """
        try:
            # 从 Flask app 配置中获取银行配置
            banks_config = self.app.config.get('EXTRACTORS_BANKS', {})
            
            if banks_config:
                self.logger.info(f"成功从 app.config 加载银行配置，共 {len(banks_config)} 个银行")
                return banks_config
            else:
                self.logger.warning("在 app.config 中未找到 'EXTRACTORS_BANKS' 配置")
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
        # 配置现在通过 Flask app.config 管理，通常在应用重启或特定机制下重新加载
        # 此处仅重新从 app.config 加载银行特定配置
        self.configs = self._load_configs()
        self.logger.info("已从 app.config 重新加载银行配置")
    
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
            
            # 更新统一配置系统 - 注意：此操作现在可能不会持久化到配置文件
            # 需要通过 Flask 的配置管理机制来处理持久化，或者此功能需要调整
            # self.config_manager.set(f'extractors.banks.{bank_code}', config, save=save)
            self.app.config.get('EXTRACTORS_BANKS', {})[bank_code] = config
            self.logger.warning(f"银行配置 '{bank_code}' 已在内存中更新，但持久化依赖于 Flask 配置管理。")
            
            self.logger.info(f"已更新银行配置: {bank_code}")
            return True
        except Exception as e:
            self.logger.error(f"更新银行配置时出错: {str(e)}")
            return False

# 单例模式
# _config_loader singleton is removed as ConfigLoader now requires 'app' instance.
# It should be instantiated in ExtractorFactory with the app context.

def get_config_loader(app) -> ConfigLoader:
    """获取配置加载器实例

    Args:
        app: Flask application instance.

    Returns:
        ConfigLoader: 配置加载器实例
    """
    # Consider if a singleton per app is needed or just direct instantiation.
    # For now, direct instantiation is simpler.
    return ConfigLoader(app)