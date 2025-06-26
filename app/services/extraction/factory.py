# -*- coding: utf-8 -*-
"""
提取器工厂模块
==============

负责管理和创建银行提取器实例。
"""

import logging
from typing import Dict, List, Type, Optional, Tuple
import pandas as pd

from .extractors.base_extractor import BankStatementExtractorInterface
from .extractors import CMBTransactionExtractor, CCBTransactionExtractor

class ExtractorFactory:
    """银行提取器工厂"""
    
    def __init__(self):
        self._extractors: Dict[str, Type[BankStatementExtractorInterface]] = {}
        self.logger = logging.getLogger('extraction_factory')
        self._register_default_extractors()
    
    def _register_default_extractors(self):
        """注册默认提取器"""
        self.register('CMB', CMBTransactionExtractor)
        self.register('CCB', CCBTransactionExtractor)
    
    def register(self, bank_code: str, extractor_class: Type[BankStatementExtractorInterface]):
        """注册银行提取器"""
        self._extractors[bank_code] = extractor_class
        self.logger.info(f"注册提取器: {bank_code} -> {extractor_class.__name__}")
    
    def create(self, bank_code: str) -> Optional[BankStatementExtractorInterface]:
        """创建指定银行的提取器实例"""
        if bank_code in self._extractors:
            return self._extractors[bank_code]()
        return None
    
    def get_available_banks(self) -> List[str]:
        """获取可用的银行代码列表"""
        return list(self._extractors.keys())
    
    def find_suitable_extractor(self, file_path: str) -> Optional[Tuple[BankStatementExtractorInterface, str, str]]:
        """根据文件找到合适的提取器
        
        Args:
            file_path: 文件路径
            
        Returns:
            Optional[Tuple[BankStatementExtractorInterface, str, str]]: 
                如果找到合适的提取器，返回 (extractor, account_name, account_number) 元组
                否则返回 None
        """
        for bank_code in self._extractors:
            extractor = self.create(bank_code)
            if extractor:
                try:
                    # 读取文件获取DataFrame用于账户信息提取
                    df = pd.read_excel(file_path, header=None)
                    if df is not None and not df.empty:
                        # 尝试提取账户信息
                        account_name, account_number = extractor.extract_account_info(df)
                        # 只有当成功提取到真实的账户信息时，才认为该提取器适用
                        if account_name and account_number:
                            return extractor, account_name, account_number
                except Exception as e:
                    # 如果提取失败，继续尝试下一个提取器
                    self.logger.debug(f"提取器 {bank_code} 无法处理文件 {file_path}: {e}")
                    continue
        return None