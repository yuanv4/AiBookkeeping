# -*- coding: utf-8 -*-
"""
通用银行提取器
==============

配置驱动的通用银行对账单数据提取器实现。
"""

import pandas as pd
from datetime import datetime
from typing import Optional, Tuple

from . import ExtractedData
from app.configs.extractors import EXTRACTORS


class ExtractorService:
    """通用银行交易提取器"""
    
    def __init__(self, bank_config_key: str):
        """初始化通用提取器
        
        Args:
            bank_config_key: 银行配置键名，如'CCB'或'CMB'
        """
        if bank_config_key not in EXTRACTORS:
            raise ValueError(f"不支持的银行配置: {bank_config_key}")
        
        self.config = EXTRACTORS[bank_config_key]
        self.BANK_NAME = self.config['bank_name']
        self.BANK_CODE = self.config['bank_code']
    
    def is_applicable(self, df: pd.DataFrame) -> bool:
        """检查此提取器是否适用于给定的数据
        
        Args:
            df: 从Excel文件读取的原始DataFrame
            
        Returns:
            bool: 如果此提取器适用于该数据则返回True，否则返回False
        """
        try:
            # 检查前10行是否包含银行特有的关键字
            for i in range(min(10, len(df))):
                for j in range(len(df.columns)):
                    cell_value = str(df.iloc[i, j])
                    if (self.config['account_name_key'] in cell_value or 
                        self.config['account_number_key'] in cell_value):
                        return True
            return False
        except:
            return False

    def extract(self, df_raw: pd.DataFrame) -> ExtractedData:
        """从原始数据中提取标准化的银行对账单数据
        
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
                raise ValueError(f'无法提取{self.BANK_NAME}账户信息')
            
            # 提取交易数据
            transactions_df = self._extract_transactions(df_raw)
            if transactions_df is None or transactions_df.empty:
                raise ValueError(f'无法提取{self.BANK_NAME}交易数据')
            
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
                    'category': 'uncategorized',
                }
                transactions_list.append(transaction_dict)
            
            # 返回标准化的提取数据
            return ExtractedData(
                bank_name=self.BANK_NAME,
                bank_code=self.BANK_CODE,
                account_name=name,
                account_number=account_number,
                transactions=transactions_list
            )
            
        except ValueError:
            raise
        except Exception as e:
            raise ValueError(f'{self.BANK_NAME}数据提取失败: {str(e)}')

    def _extract_account_info(self, df: pd.DataFrame) -> Tuple[Optional[str], Optional[str]]:
        """提取银行账户信息
        
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
                if name is None and self.config['account_name_key'] in cell_value:
                    try:
                        name = cell_value.split(self.config['account_name_key'])[1].strip()
                    except (IndexError, AttributeError):
                        continue
                
                # 提取账户号码
                if account_number is None and self.config['account_number_key'] in cell_value:
                    try:
                        account_number = cell_value.split(self.config['account_number_key'])[1].strip()
                    except (IndexError, AttributeError):
                        continue
                
                # 如果都找到了就可以提前退出
                if name and account_number:
                    return name, account_number
        
        return name, account_number

    def _extract_transactions(self, df_raw: pd.DataFrame) -> Optional[pd.DataFrame]:
        """提取银行交易数据

        Args:
            df_raw: 从Excel文件读取的原始DataFrame

        Returns:
            DataFrame: 标准格式的交易数据或None（提取失败）
        """
        # 查找包含交易日期的表头行
        header_row = None
        for i, row in df_raw.iterrows():
            if any(self.config['transaction_header'] in str(val) for val in row.values):
                header_row = i
                break

        if header_row is None:
            raise ValueError(f"未找到包含关键字 '{self.config['transaction_header']}' 的表头行")

        # 使用找到的行作为表头创建新的DataFrame
        df = df_raw.iloc[header_row+1:].copy()
        df.columns = df_raw.iloc[header_row].values

        # 清理列名
        df.columns = df.columns.astype(str).str.strip()

        # 过滤有效数据行（排除空的日期列）
        if self.config['transaction_header'] in df.columns:
            df = df.dropna(subset=[self.config['transaction_header']])
            df = df[df[self.config['transaction_header']].astype(str).str.strip() != '']
        else:
            raise ValueError(f"未找到日期列: {self.config['transaction_header']}")

        # 使用列名映射
        df = df.rename(columns=self.config['column_mapping'])

        # 只保留映射后的目标列
        target_columns = list(self.config['column_mapping'].values())
        available_columns = [col for col in target_columns if col in df.columns]
        df = df[available_columns]

        # 处理日期列：将银行日期字符串转换为标准datetime对象
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
        """将银行日期字符串转换为标准datetime对象

        Args:
            date_str: 银行日期字符串

        Returns:
            datetime: 转换后的标准日期时间对象，转换失败返回None
        """
        # 根据配置进行日期验证
        if not self.config['date_validator'](date_str):
            return None

        try:
            return pd.to_datetime(str(date_str).strip(), format=self.config['date_format'])
        except:
            return None

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
