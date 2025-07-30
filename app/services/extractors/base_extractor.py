# -*- coding: utf-8 -*-
"""
基础提取器模块
==============

定义银行对账单提取器的接口和基础实现。
"""

import pandas as pd
from abc import ABC, abstractmethod
from . import ExtractedData


class BaseTransactionExtractor(ABC):
    """银行交易明细提取器基类"""
    
    # 子类必须重写这些类属性
    BANK_CODE: str = NotImplemented
    BANK_NAME: str = NotImplemented
    


    @abstractmethod
    def is_applicable(self, df: pd.DataFrame) -> bool:
        """检查此提取器是否适用于给定的数据
        
        Args:
            df: 从Excel文件读取的原始DataFrame
            
        Returns:
            bool: 如果此提取器适用于该数据则返回True，否则返回False
        """
        pass

    @abstractmethod
    def extract(self, df_raw: pd.DataFrame) -> ExtractedData:
        """从原始数据中提取标准化的银行对账单数据
        
        Args:
            df_raw: 从Excel文件读取的原始DataFrame
            
        Returns:
            ExtractedData: 标准化的提取数据，包含账户信息和交易记录
            
        Raises:
            ValueError: 数据提取失败时抛出
        """
        pass

    def _normalize_currency_code(self, currency_value: str) -> str:
        """标准化货币代码
        
        将银行原始的货币描述转换为标准的3字符货币代码
        
        Args:
            currency_value: 原始货币值，如"人民币元"、"美元"等
            
        Returns:
            str: 标准化的3字符货币代码，如"CNY"、"USD"等
        """
        if not currency_value or pd.isna(currency_value):
            return 'CNY'  # 默认为人民币
        
        # 转换为字符串并去除空白字符
        currency_str = str(currency_value).strip()
        
        # 如果已经是3字符代码，直接返回（转为大写）
        if len(currency_str) == 3 and currency_str.isalpha():
            return currency_str.upper()
        
        # 货币映射表
        currency_mapping = {
            '人民币元': 'CNY',
            '人民币': 'CNY',
            '美元': 'USD',
            '港币': 'HKD',
            '欧元': 'EUR',
        }
        
        # 查找映射
        return currency_mapping.get(currency_str, 'CNY')
