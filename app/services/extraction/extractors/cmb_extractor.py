# -*- coding: utf-8 -*-
"""
招商银行提取器
==============

招商银行对账单数据提取器实现。
"""

import os
import re
import pandas as pd
from typing import Optional, Tuple

from .base_extractor import BaseTransactionExtractor

class CMBTransactionExtractor(BaseTransactionExtractor):
    """招商银行交易提取器"""
    
    def __init__(self):
        super().__init__('CMB')
    
    def get_bank_code(self) -> str:
        return 'CMB'
    
    def get_bank_name(self) -> str:
        return '招商银行'
    
    def get_bank_keyword(self) -> str:
        return '招商银行'
    

    
    def extract_account_info(self, file_path: str) -> Tuple[str, str]:
        """提取账户信息"""
        account_name = None
        account_number = None
        
        try:
            # 读取Excel文件的前几行来查找账户信息
            df = pd.read_excel(file_path)
            
            # 尝试从DataFrame的前几行提取账户信息
            for i in range(min(10, len(df))):
                for col in df.columns:
                    cell_value = str(df.iloc[i][col])
                    
                    # 查找账号模式
                    if '账号' in cell_value or '卡号' in cell_value:
                        # 提取数字
                        numbers = re.findall(r'\d{10,}', cell_value)
                        if numbers:
                            account_number = numbers[0]
                    
                    # 查找户名
                    if '户名' in cell_value or '姓名' in cell_value:
                        parts = cell_value.split()
                        if len(parts) > 1:
                            account_name = parts[1]
            
            # 只有当真正提取到账户信息时才返回，否则返回None
            if account_name and account_number:
                return account_name, account_number
            else:
                return None, None
        
        except Exception as e:
            self.logger.warning(f"提取账户信息失败: {e}")
            return None, None
    
    def extract_transactions(self, file_path: str) -> Optional[pd.DataFrame]:
        """提取交易数据"""
        try:
            # 读取Excel文件
            df = pd.read_excel(file_path)
            
            # 查找数据开始行
            data_start_row = 0
            for i, row in df.iterrows():
                if '交易日期' in str(row.values):
                    data_start_row = i
                    break
            
            # 重新读取，跳过前面的行
            if data_start_row > 0:
                df = pd.read_excel(file_path, skiprows=data_start_row)
            
            # 清理列名
            df.columns = df.columns.str.strip()
            
            # 过滤有效数据行
            df = df.dropna(subset=['交易日期'], how='all')
            
            # 重命名列以匹配标准格式
            column_mapping = {
                '交易日期': 'transaction_date',
                '交易金额': 'amount',
                '余额': 'balance',
                '对方户名': 'counterparty',
                '摘要': 'description',
                '备注': 'description'
            }
            
            df = df.rename(columns=column_mapping)
            
            return df
            
        except Exception as e:
            self.logger.error(f"提取招商银行交易数据失败: {e}")
            return None