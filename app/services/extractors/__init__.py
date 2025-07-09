# -*- coding: utf-8 -*-
"""
银行提取器实现模块
==================

包含各个银行的具体提取器实现。
"""

from .base_extractor import BaseTransactionExtractor
from .cmb_extractor import CMBTransactionExtractor
from .ccb_extractor import CCBTransactionExtractor

# 中央提取器注册列表 - 添加新提取器只需在此处注册
ALL_EXTRACTORS = [
    CMBTransactionExtractor,
    CCBTransactionExtractor
]

__all__ = [
    'BaseTransactionExtractor',
    'ALL_EXTRACTORS'
]