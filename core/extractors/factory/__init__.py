"""
提取器工厂模块
===========

负责创建和管理银行提取器实例。
"""

from .extractor_factory import get_extractor_factory, ExtractorFactory

__all__ = ['get_extractor_factory', 'ExtractorFactory'] 