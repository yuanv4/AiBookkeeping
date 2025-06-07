# -*- coding: utf-8 -*-
"""
提取器工厂模块
==============

负责管理和创建银行提取器实例。
"""

import logging
from typing import Dict, List, Type, Optional

from .extractors.base_extractor import BankStatementExtractorInterface
from .extractors import CMBTransactionExtractor, CCBTransactionExtractor

class ExtractorFactory:
    """银行提取器工厂"""
    
    def __init__(self):
        self.extractors: Dict[str, Type[BankStatementExtractorInterface]] = {}
        self.logger = logging.getLogger('extractor_factory')
        self._register_default_extractors()
    
    def _register_default_extractors(self):
        """注册默认提取器"""
        self.register('CMB', CMBTransactionExtractor)
        self.register('CCB', CCBTransactionExtractor)
    
    def register(self, bank_code: str, extractor_class: Type[BankStatementExtractorInterface]):
        """注册银行提取器"""
        self.extractors[bank_code] = extractor_class
        self.logger.info(f"注册提取器: {bank_code} -> {extractor_class.__name__}")
    
    def create(self, bank_code: str) -> Optional[BankStatementExtractorInterface]:
        """创建指定银行的提取器实例"""
        if bank_code in self.extractors:
            return self.extractors[bank_code]()
        return None
    
    def get_available_banks(self) -> List[str]:
        """获取可用的银行代码列表"""
        return list(self.extractors.keys())
    
    def find_suitable_extractor(self, file_path: str) -> Optional[BankStatementExtractorInterface]:
        """根据文件找到合适的提取器"""
        for bank_code in self.extractors:
            extractor = self.create(bank_code)
            if extractor and extractor.can_process_file(file_path):
                return extractor
        return None