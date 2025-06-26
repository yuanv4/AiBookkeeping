# -*- coding: utf-8 -*-
"""
提取器工厂模块
==============

负责管理和创建银行提取器实例。
"""

import logging
import pandas as pd
from typing import Dict, List, Type, Optional

from .extractors.base_extractor import BaseTransactionExtractor

class ExtractorFactory:
    """银行提取器工厂"""
    
    def __init__(self, extractor_classes: List[Type[BaseTransactionExtractor]] = None):
        self._extractors: Dict[str, Type[BaseTransactionExtractor]] = {}
        self.logger = logging.getLogger('extraction_factory')
        
        # 如果没有提供提取器类列表，使用默认的
        if extractor_classes is None:
            extractor_classes = self._get_default_extractors()
        
        # 注册提取器
        for extractor_class in extractor_classes:
            self._register_extractor(extractor_class)
    
    def _get_default_extractors(self) -> List[Type[BaseTransactionExtractor]]:
        """获取默认的提取器类列表"""
        try:
            from .extractors import CMBTransactionExtractor, CCBTransactionExtractor
            return [CMBTransactionExtractor, CCBTransactionExtractor]
        except ImportError as e:
            self.logger.error(f"无法导入默认提取器: {e}")
            return []
    
    def _register_extractor(self, extractor_class: Type[BaseTransactionExtractor]):
        """注册单个提取器"""
        try:
            # 直接从类属性获取银行代码，无需实例化
            if hasattr(extractor_class, 'BANK_CODE') and extractor_class.BANK_CODE is not NotImplemented:
                bank_code = extractor_class.BANK_CODE
                
                # 注册提取器
                self._extractors[bank_code] = extractor_class
                self.logger.info(f"注册提取器: {bank_code} -> {extractor_class.__name__}")
            else:
                self.logger.warning(f"提取器 {extractor_class.__name__} 未定义 BANK_CODE 类属性，跳过注册")
        except Exception as e:
            self.logger.error(f"注册提取器失败 {extractor_class}: {e}")
    
    def register(self, bank_code: str, extractor_class: Type[BaseTransactionExtractor]):
        """手动注册银行提取器"""
        self._extractors[bank_code] = extractor_class
        self.logger.info(f"手动注册提取器: {bank_code} -> {extractor_class.__name__}")
    
    def create(self, bank_code: str) -> Optional[BaseTransactionExtractor]:
        """创建指定银行的提取器实例"""
        if bank_code in self._extractors:
            return self._extractors[bank_code]()
        return None
    
    def get_available_banks(self) -> List[str]:
        """获取可用的银行代码列表"""
        return list(self._extractors.keys())
    
    def find_suitable_extractor(self, df: pd.DataFrame) -> Optional[BaseTransactionExtractor]:
        """根据数据找到合适的提取器
        
        Args:
            df: 从Excel文件读取的原始DataFrame
            
        Returns:
            Optional[BaseTransactionExtractor]: 
                如果找到合适的提取器，返回提取器实例
                否则返回 None
        """
        for bank_code, extractor_class in self._extractors.items():
            try:
                extractor = extractor_class()
                if extractor.is_applicable(df):
                    self.logger.info(f"找到合适的提取器: {bank_code}")
                    return extractor
            except Exception as e:
                # 如果提取器检查失败，继续尝试下一个
                self.logger.debug(f"提取器 {bank_code} 检查数据时出错: {e}")
                continue
        
        self.logger.warning(f"未找到适用的提取器")
        return None