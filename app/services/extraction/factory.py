# -*- coding: utf-8 -*-
"""
提取器工厂模块
==============

负责管理和创建银行提取器实例。
"""

import logging
from typing import Dict, List, Optional, Tuple
import pandas as pd

from .extractors.base_extractor import BankStatementExtractorInterface
from .extractors.configurable_extractor import ConfigurableTransactionExtractor
from .bank_configs import get_bank_config, BANK_CONFIGS

class ExtractorFactory:
    """银行提取器工厂"""
    
    def __init__(self):
        self.logger = logging.getLogger('extraction_factory')
    
    def create(self, bank_code: str) -> Optional[BankStatementExtractorInterface]:
        """创建指定银行的提取器实例"""
        try:
            bank_config = get_bank_config(bank_code)
            extractor = ConfigurableTransactionExtractor(bank_code, bank_config)
            self.logger.info(f"创建提取器: {bank_code} -> ConfigurableTransactionExtractor")
            return extractor
        except KeyError:
            self.logger.error(f"不支持的银行代码: {bank_code}")
            return None
    
    def get_available_banks(self) -> List[str]:
        """获取可用的银行代码列表"""
        return list(BANK_CONFIGS.keys())
    
    def find_suitable_extractor(self, file_path: str) -> Optional[Tuple[BankStatementExtractorInterface, str, str]]:
        """根据文件找到合适的提取器
        
        Args:
            file_path: 文件路径
            
        Returns:
            Optional[Tuple[BankStatementExtractorInterface, str, str]]: 
                如果找到合适的提取器，返回 (extractor, account_name, account_number) 元组
                否则返回 None
        """
        for bank_code in BANK_CONFIGS.keys():
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