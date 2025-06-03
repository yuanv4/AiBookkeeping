"""
配置管理模块
==========

为AI记账系统提供统一的配置管理功能，支持多种配置源和验证。
"""

import os
import json
import logging
import jsonschema
from pathlib import Path
from typing import Dict, Any, Optional, List, Union
import copy

# 导入异常
from scripts.common.exceptions import ConfigError, ConfigLoadError, ConfigValidationError

# 配置日志
logger = logging.getLogger('config_manager')

class ConfigManager:
    """配置管理器，负责加载、验证和提供配置信息"""
    
    def __init__(self, config_dir: Optional[str] = None):
        """初始化配置管理器
        
        Args:
            config_dir: 配置目录路径，默认为项目根目录下的config目录
        """
        # 如果未指定配置目录，使用默认路径
        if config_dir is None:
            # 定位项目根目录
            current_dir = os.path.dirname(os.path.abspath(__file__))
            scripts_dir = os.path.dirname(current_dir)
            root_dir = os.path.dirname(scripts_dir)
            config_dir = os.path.join(root_dir, 'config')
        
        self.config_dir = config_dir
        os.makedirs(config_dir, exist_ok=True)
        
        # 默认配置文件路径
        self.default_config_file = os.path.join(config_dir, 'default.json')
        self.user_config_file = os.path.join(config_dir, 'config.json')
        self.schema_file = os.path.join(config_dir, 'config_schema.json')
        
        # 保存加载的配置
        self.config = {}
        
        # 加载配置
        self._load_config()
    
    def _load_config(self) -> None:
        """加载配置文件"""
        config = {}
        
        # 1. 尝试加载默认配置
        try:
            if os.path.exists(self.default_config_file):
                with open(self.default_config_file, 'r', encoding='utf-8') as f:
                    default_config = json.load(f)
                    config.update(default_config)
                    logger.info(f"已加载默认配置: {self.default_config_file}")
        except Exception as e:
            logger.error(f"加载默认配置失败: {e}")
            # 默认配置加载失败时不抛出异常，而是使用空配置继续
        
        # 2. 尝试加载用户配置，如果存在则覆盖默认配置
        try:
            if os.path.exists(self.user_config_file):
                with open(self.user_config_file, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                    # 深度合并配置
                    self._deep_update(config, user_config)
                    logger.info(f"已加载用户配置: {self.user_config_file}")
        except Exception as e:
            logger.error(f"加载用户配置失败: {e}")
            # 如果默认配置已加载，用户配置加载失败时不抛出异常
            if not config:
                raise ConfigLoadError(f"无法加载任何配置: {e}")
        
        # 3. 加载和验证配置模式
        try:
            if os.path.exists(self.schema_file):
                with open(self.schema_file, 'r', encoding='utf-8') as f:
                    schema = json.load(f)
                
                # 验证配置是否符合模式
                try:
                    jsonschema.validate(instance=config, schema=schema)
                    logger.info("配置验证通过")
                except jsonschema.exceptions.ValidationError as e:
                    logger.error(f"配置验证失败: {e}")
                    raise ConfigValidationError(f"配置验证失败: {e}")
        except ConfigValidationError:
            raise
        except Exception as e:
            logger.warning(f"无法加载或验证配置模式: {e}")
            # 配置模式加载失败时不抛出异常，跳过验证
        
        self.config = config
    
    def _deep_update(self, d: Dict[str, Any], u: Dict[str, Any]) -> Dict[str, Any]:
        """深度更新字典，递归合并嵌套字典
        
        Args:
            d: 目标字典
            u: 更新字典
        
        Returns:
            dict: 更新后的字典
        """
        for k, v in u.items():
            if isinstance(v, dict) and k in d and isinstance(d[k], dict):
                d[k] = self._deep_update(d[k], v)
            else:
                d[k] = v
        return d
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值
        
        Args:
            key: 配置键，支持使用点号访问嵌套配置，如 'db.host'
            default: 如果配置不存在，返回的默认值
        
        Returns:
            配置值
        """
        # 处理嵌套键名
        keys = key.split('.')
        value = self.config
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def get_all(self) -> Dict[str, Any]:
        """获取所有配置
        
        Returns:
            dict: 完整配置字典的副本
        """
        return copy.deepcopy(self.config)
    
    def set(self, key: str, value: Any, save: bool = False) -> None:
        """设置配置值
        
        Args:
            key: 配置键，支持使用点号访问嵌套配置，如 'db.host'
            value: 要设置的值
            save: 是否立即保存到用户配置文件
        """
        # 处理嵌套键名
        keys = key.split('.')
        
        # 从根配置开始
        config = self.config
        
        # 遍历到最后一个键的前一个位置
        for k in keys[:-1]:
            # 如果键不存在或不是字典，创建一个新字典
            if k not in config or not isinstance(config[k], dict):
                config[k] = {}
            config = config[k]
        
        # 设置最后一个键的值
        config[keys[-1]] = value
        
        # 如果需要，保存配置
        if save:
            self.save()
    
    def save(self) -> None:
        """保存配置到用户配置文件"""
        try:
            with open(self.user_config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            logger.info(f"配置已保存到: {self.user_config_file}")
        except Exception as e:
            logger.error(f"保存配置失败: {e}")
            raise ConfigError(f"保存配置失败: {e}")
    
    def reload(self) -> None:
        """重新加载配置"""
        self._load_config()
        logger.info("配置已重新加载")
    
    def create_default_config(self) -> None:
        """创建默认配置文件"""
        default_config = {
            "version": "1.0.0",
            "application": {
                "name": "AI记账系统",
                "debug": False,
                "log_level": "INFO"
            },
            "database": {
                "type": "sqlite",
                "path": "data/transactions.db",
                "backup_enabled": True,
                "backup_interval_days": 7
            },
            "extractors": {
                "supported_banks": ["CMB", "CCB"],
                "default_currency": "CNY",
                "date_format": "%Y-%m-%d"
            },
            "analysis": {
                "default_date_range_days": 90,
                "summary_enabled": True,
                "category_analysis_enabled": True,
                "merchant_analysis_enabled": True,
                "time_analysis_enabled": True,
                "anomaly_detection_enabled": True
            },
            "visualization": {
                "default_chart_type": "bar",
                "theme": "default",
                "charts_dir": "static/charts",
                "max_categories_in_pie": 8
            }
        }
        
        try:
            with open(self.default_config_file, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=2, ensure_ascii=False)
            logger.info(f"已创建默认配置文件: {self.default_config_file}")
        except Exception as e:
            logger.error(f"创建默认配置文件失败: {e}")
            raise ConfigError(f"创建默认配置文件失败: {e}")
    
    def create_schema_file(self) -> None:
        """创建配置模式文件"""
        schema = {
            "type": "object",
            "properties": {
                "version": {"type": "string"},
                "application": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "debug": {"type": "boolean"},
                        "log_level": {"type": "string", "enum": ["DEBUG", "INFO", "WARNING", "ERROR"]}
                    },
                    "required": ["name", "debug", "log_level"]
                },
                "database": {
                    "type": "object",
                    "properties": {
                        "type": {"type": "string", "enum": ["sqlite"]},
                        "path": {"type": "string"},
                        "backup_enabled": {"type": "boolean"},
                        "backup_interval_days": {"type": "integer", "minimum": 1}
                    },
                    "required": ["type", "path"]
                },
                "extractors": {
                    "type": "object",
                    "properties": {
                        "supported_banks": {"type": "array", "items": {"type": "string"}},
                        "default_currency": {"type": "string"},
                        "date_format": {"type": "string"}
                    },
                    "required": ["supported_banks", "default_currency"]
                },
                "analysis": {
                    "type": "object",
                    "properties": {
                        "default_date_range_days": {"type": "integer", "minimum": 1},
                        "summary_enabled": {"type": "boolean"},
                        "category_analysis_enabled": {"type": "boolean"},
                        "merchant_analysis_enabled": {"type": "boolean"},
                        "time_analysis_enabled": {"type": "boolean"},
                        "anomaly_detection_enabled": {"type": "boolean"}
                    }
                },
                "visualization": {
                    "type": "object",
                    "properties": {
                        "default_chart_type": {"type": "string", "enum": ["bar", "line", "pie", "scatter"]},
                        "theme": {"type": "string"},
                        "charts_dir": {"type": "string"},
                        "max_categories_in_pie": {"type": "integer", "minimum": 2, "maximum": 20}
                    }
                }
            },
            "required": ["version", "application", "database"]
        }
        
        try:
            with open(self.schema_file, 'w', encoding='utf-8') as f:
                json.dump(schema, f, indent=2, ensure_ascii=False)
            logger.info(f"已创建配置模式文件: {self.schema_file}")
        except Exception as e:
            logger.error(f"创建配置模式文件失败: {e}")
            raise ConfigError(f"创建配置模式文件失败: {e}")

# 单例模式
_config_manager = None

def get_config_manager() -> ConfigManager:
    """获取配置管理器单例
    
    Returns:
        ConfigManager: 配置管理器实例
    """
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager 