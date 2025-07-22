# -*- coding: utf-8 -*-
"""
建设银行提取器
==============

建设银行对账单数据提取器实现。
"""

import pandas as pd
from datetime import datetime
from typing import Optional, Tuple

from .base_extractor import BaseTransactionExtractor
from ..models import ExtractedData

class CCBTransactionExtractor(BaseTransactionExtractor):
    """建设银行交易提取器"""
    
    BANK_CODE = 'CCB'
    BANK_NAME = '建设银行'
    
    # 配置常量
    _ACCOUNT_NAME_KEY = '客户名称:'
    _ACCOUNT_NUMBER_KEY = '卡号/账号:'
    _TRANSACTION_HEADER_KEY = '交易日期'
    _COLUMN_MAPPING = {
        '交易日期': 'date',
        '交易金额': 'amount',
        '账户余额': 'balance_after',
        '对方账号与户名': 'counterparty',
        '摘要': 'description',
        '币别': 'currency'
    }
    
    def is_applicable(self, df: pd.DataFrame) -> bool:
        """检查此提取器是否适用于给定的数据
        
        Args:
            df: 从Excel文件读取的原始DataFrame
            
        Returns:
            bool: 如果此提取器适用于该数据则返回True，否则返回False
        """
        try:
            # 检查前10行是否包含建设银行特有的关键字
            for i in range(min(10, len(df))):
                for j in range(len(df.columns)):
                    cell_value = str(df.iloc[i, j])
                    if self._ACCOUNT_NAME_KEY in cell_value or self._ACCOUNT_NUMBER_KEY in cell_value:
                        return True
            return False
        except:
            return False

    def extract(self, df_raw: pd.DataFrame) -> ExtractedData:
        """从原始数据中提取标准化的建设银行对账单数据
        
        Args:
            df_raw: 从Excel文件读取的原始DataFrame
            
        Returns:
            ExtractedData: 标准化的提取数据，包含账户信息和交易记录
            
        Raises:
            ValueError: 数据提取失败时抛出
        """
        try:
            # 提取账户信息
            name, account_number = self._extract_account_info(df_raw)
            if not name or not account_number:
                raise ValueError('无法提取建设银行账户信息')
            
            # 提取交易数据
            transactions_df = self._extract_transactions(df_raw)
            if transactions_df is None or transactions_df.empty:
                raise ValueError('无法提取建设银行交易数据')
            
            # 转换交易数据为字典列表
            transactions_list = []
            for _, row in transactions_df.iterrows():
                transaction_dict = {
                    'date': row['date'].date() if hasattr(row['date'], 'date') else row['date'],
                    'amount': row['amount'],
                    'balance_after': row['balance_after'],
                    'currency': row['currency'],
                    'description': row['description'],
                    'counterparty': row['counterparty'],
                }
                transactions_list.append(transaction_dict)
            
            # 返回标准化的提取数据
            return ExtractedData(
                bank_name=self.get_bank_name(),
                bank_code=self.get_bank_code(),
                name=name,
                account_number=account_number,
                transactions=transactions_list
            )
            
        except ValueError:
            raise
        except Exception as e:
            raise ValueError(f'建设银行数据提取失败: {str(e)}')

    def _extract_account_info(self, df: pd.DataFrame) -> Tuple[Optional[str], Optional[str]]:
        """提取建设银行账户信息
        
        Args:
            df: 包含账户信息的DataFrame
            
        Returns:
            tuple: (name, account_number)
        """
        name = None
        account_number = None
        
        # 遍历前10行查找账户信息
        for i in range(min(10, len(df))):
            for j in range(len(df.columns)):
                cell_value = str(df.iloc[i, j])
                
                # 提取账户名称
                if name is None and self._ACCOUNT_NAME_KEY in cell_value:
                    try:
                        name = cell_value.split(self._ACCOUNT_NAME_KEY)[1].strip()
                    except (IndexError, AttributeError):
                        continue
                
                # 提取账户号码
                if account_number is None and self._ACCOUNT_NUMBER_KEY in cell_value:
                    try:
                        account_number = cell_value.split(self._ACCOUNT_NUMBER_KEY)[1].strip()
                    except (IndexError, AttributeError):
                        continue
                
                # 如果都找到了就可以提前退出
                if name and account_number:
                    return name, account_number
        
        return name, account_number

    def _extract_transactions(self, df_raw: pd.DataFrame) -> Optional[pd.DataFrame]:
        """提取建设银行交易数据
        
        Args:
            df_raw: 从Excel文件读取的原始DataFrame
            
        Returns:
            DataFrame: 标准格式的交易数据或None（提取失败）
        """
        # 查找包含交易日期的表头行
        header_row = None
        for i, row in df_raw.iterrows():
            if any(self._TRANSACTION_HEADER_KEY in str(val) for val in row.values):
                header_row = i
                break
        
        if header_row is None:
            raise ValueError(f"未找到包含关键字 '{self._TRANSACTION_HEADER_KEY}' 的表头行")
        
        # 使用找到的行作为表头创建新的DataFrame
        df = df_raw.iloc[header_row+1:].copy()
        df.columns = df_raw.iloc[header_row].values
        
        # 清理列名
        df.columns = df.columns.astype(str).str.strip()

        # 过滤有效数据行（排除空的日期列）
        if self._TRANSACTION_HEADER_KEY in df.columns:
            df = df.dropna(subset=[self._TRANSACTION_HEADER_KEY])
            df = df[df[self._TRANSACTION_HEADER_KEY].astype(str).str.strip() != '']
        else:
            raise ValueError(f"未找到日期列: {self._TRANSACTION_HEADER_KEY}")
        
        # 使用列名映射
        df = df.rename(columns=self._COLUMN_MAPPING)
        
        # 只保留映射后的目标列
        target_columns = list(self._COLUMN_MAPPING.values())
        available_columns = [col for col in target_columns if col in df.columns]
        df = df[available_columns]
        
        # 处理日期列：将建设银行日期字符串转换为标准datetime对象
        if 'date' in df.columns:
            df['date'] = df['date'].astype(str).apply(self._convert_date)
            df = df.dropna(subset=['date'])
        else:
            raise ValueError("未找到'date'列，无法进行日期转换")
        
        # 标准化货币代码
        if 'currency' in df.columns:
            df['currency'] = df['currency'].apply(self._normalize_currency_code)
        
        return df

    def _convert_date(self, date_str: str) -> Optional[datetime]:
        """将建设银行日期字符串转换为标准datetime对象
        
        Args:
            date_str: 建设银行日期字符串，格式为"YYYYMMDD"，如"20230103"
            
        Returns:
            datetime: 转换后的标准日期时间对象，转换失败返回None
        """
        if pd.isna(date_str) or not str(date_str).strip().isdigit():
            return None
        try:
            return pd.to_datetime(str(date_str).strip(), format='%Y%m%d')
        except:
            return None

