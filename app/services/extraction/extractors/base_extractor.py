# -*- coding: utf-8 -*-
"""
基础提取器模块
==============

定义银行对账单提取器的接口和基础实现。
"""

import pandas as pd
import re
from datetime import datetime
from typing import Dict, List, Type, Optional, Any, Union, Tuple
from abc import ABC, abstractmethod

from ..models import ExtractionConfig


class BaseTransactionExtractor(ABC):
    """银行交易明细提取器基类"""
    
    # 子类必须重写这些类属性
    BANK_CODE: str = NotImplemented
    BANK_NAME: str = NotImplemented
    
    def __init__(self):
        """初始化提取器，缓存配置以提高性能"""
        self._config = None
    
    @property
    def config(self) -> ExtractionConfig:
        """获取缓存的提取配置"""
        if self._config is None:
            self._config = self.get_extraction_config()
        return self._config
    
    def get_bank_code(self) -> str:
        """获取银行代码，如CMB、CCB等"""
        if self.BANK_CODE is NotImplemented:
            raise NotImplementedError(f"{self.__class__.__name__} 必须定义 BANK_CODE 类属性")
        return self.BANK_CODE

    def get_bank_name(self) -> str:
        """获取银行名称，如招商银行、建设银行等"""
        if self.BANK_NAME is NotImplemented:
            raise NotImplementedError(f"{self.__class__.__name__} 必须定义 BANK_NAME 类属性")
        return self.BANK_NAME

    @abstractmethod
    def _convert_date(self, date_str: str) -> Optional[datetime]:
        """将银行特定的日期字符串转换为标准datetime对象
        
        Args:
            date_str: 银行特定的日期字符串
            
        Returns:
            datetime: 转换后的标准日期时间对象，转换失败返回None
        """
        pass

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
    def get_extraction_config(self) -> ExtractionConfig:
        """获取银行特定的数据提取配置
        
        Returns:
            ExtractionConfig: 银行特定的提取配置
        """
        pass

    def extract_account_info(self, df: pd.DataFrame) -> Tuple[Optional[str], Optional[str]]:
        """模板方法：提取账户信息
        
        Args:
            df: 包含账户信息的DataFrame
            
        Returns:
            tuple: (account_name, account_number)
        """
        account_name = None
        account_number = None
        
        try:
            # 遍历前10行查找账户信息
            for i in range(min(10, len(df))):
                for j in range(len(df.columns)):
                    cell_value = str(df.iloc[i, j])
                    
                    # 使用子类定义的匹配规则
                    if account_name is None:
                        account_name = self._extract_account_name(cell_value)
                    
                    if account_number is None:
                        account_number = self._extract_account_number(cell_value)
                    
                    # 如果都找到了就可以提前退出
                    if account_name and account_number:
                        break
                
                if account_name and account_number:
                    break
            
            return account_name, account_number
        
        except Exception as e:
            return None, None
    
    def _extract_account_name(self, cell_value: str) -> Optional[str]:
        """通用账户名称提取实现
        
        Args:
            cell_value: 单元格字符串值
            
        Returns:
            str: 提取到的账户名称，未找到返回None
        """
        pattern = self.config.account_name_pattern
        
        if pattern.keyword in cell_value:
            name_match = re.search(pattern.regex_pattern, cell_value)
            if name_match:
                account_name = name_match.group(1).strip()
                return account_name
        return None
    
    def _extract_account_number(self, cell_value: str) -> Optional[str]:
        """通用账户号码提取实现
        
        Args:
            cell_value: 单元格字符串值
            
        Returns:
            str: 提取到的账户号码，未找到返回None
        """
        pattern = self.config.account_number_pattern
        
        if pattern.keyword in cell_value:
            number_match = re.search(pattern.regex_pattern, cell_value)
            if number_match:
                account_number = number_match.group(1).strip()
                return account_number
        return None

    def extract_transactions(self, df: pd.DataFrame) -> Optional[pd.DataFrame]:
        """提取交易数据 - 模板方法
        
        Args:
            df: 从Excel文件读取的原始DataFrame
            
        Returns:
            DataFrame: 标准格式的交易数据或None（提取失败）
        """
        return self._extract_transactions_with_config(df, self.config)
        
    def _extract_transactions_with_config(self, df_raw: pd.DataFrame, config: ExtractionConfig) -> Optional[pd.DataFrame]:
        """使用配置提取交易数据的通用实现
        
        Args:
            df_raw: 从Excel文件读取的原始DataFrame
            config: 银行特定的提取配置
            
        Returns:
            DataFrame: 标准格式的交易数据或None（提取失败）
        """
        try:
            # 使用配置中的关键字查找表头行
            header_row = None
            for i, row in df_raw.iterrows():
                row_values = row.values
                if any(config.header_keyword in str(val) for val in row_values):
                    header_row = i
                    break
            
            if header_row is None:
                raise ValueError(f"未找到包含关键字 '{config.header_keyword}' 的表头行")
            
            # 使用找到的行作为表头创建新的DataFrame
            df = df_raw.iloc[header_row+1:].copy()
            df.columns = df_raw.iloc[header_row].values
            
            # 清理列名
            df.columns = df.columns.astype(str).str.strip()

            # 获取日期列名（从列映射中获取）
            date_col_name = None
            for source_col, target_col in config.column_mapping.items():
                if target_col == 'date':
                    date_col_name = source_col
                    break
            
            if not date_col_name:
                raise ValueError("配置中未找到日期列映射")
            
            # 过滤有效数据行（排除空的日期列）
            if date_col_name in df.columns:
                df = df.dropna(subset=[date_col_name])
                df = df[df[date_col_name].astype(str).str.strip() != '']
            else:
                raise ValueError(f"未找到日期列: {date_col_name}")
            
            # 使用配置中的列名映射
            df = df.rename(columns=config.column_mapping)
            
            # 只保留映射后的目标列
            target_columns = list(config.column_mapping.values())
            df = df[target_columns]
            
            # 处理日期列：使用子类的日期转换方法
            if 'date' in df.columns:
                df['date'] = df['date'].astype(str).apply(self._convert_date)
                df = df.dropna(subset=['date'])
            else:
                raise ValueError("未找到'date'列，无法进行日期转换")
            
            # 标准化货币代码
            if 'currency' in df.columns:
                df['currency'] = df['currency'].apply(self._normalize_currency_code)
            
            return df
            
        except Exception as e:
            bank_name = config.bank_info.name if config.bank_info else "未知银行"
            raise Exception(f"提取{bank_name}交易数据失败: {e}")
    
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
        
        # 获取配置中的货币映射表
        currency_mapping = self.config.currency_mapping
        
        # 查找映射
        if currency_str in currency_mapping:
            mapped_code = currency_mapping[currency_str]
            return mapped_code
        
        # 如果没有找到映射，返回默认值
        return 'CNY'
    
