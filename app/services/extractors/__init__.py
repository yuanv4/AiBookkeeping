# -*- coding: utf-8 -*-
"""
银行提取器实现模块
==================

包含各个银行的具体提取器实现和相关数据结构。
"""

from dataclasses import dataclass
from typing import List, Dict, Any

@dataclass
class ExtractedData:
    """从银行对账单中提取的标准化数据

    字段直接对应Transaction模型的字段：
    - bank_name -> Transaction.bank_name
    - bank_code -> Transaction.bank_code
    - account_name -> Transaction.account_name
    - account_number -> Transaction.account_number
    - transactions -> 用于创建Transaction记录的数据列表
    """
    bank_name: str
    bank_code: str
    account_name: str  # 账户名称
    account_number: str
    transactions: List[Dict[str, Any]]

from .base_extractor import BaseTransactionExtractor
from .cmb_extractor import CMBTransactionExtractor
from .ccb_extractor import CCBTransactionExtractor

# 中央提取器注册列表 - 添加新提取器只需在此处注册
ALL_EXTRACTORS = [
    CMBTransactionExtractor,
    CCBTransactionExtractor
]

__all__ = [
    'ExtractedData',
    'BaseTransactionExtractor',
    'ALL_EXTRACTORS'
]