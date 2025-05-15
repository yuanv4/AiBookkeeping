"""
银行提取器配置模块
==============

负责加载和管理银行提取器的配置信息。
"""

from .config_loader import get_config_loader, ConfigLoader

__all__ = ['get_config_loader', 'ConfigLoader'] 