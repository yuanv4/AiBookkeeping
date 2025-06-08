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
            # 读取Excel文件的前几行来查找账户信息，不设置表头
            df = pd.read_excel(file_path, header=None)
            
            # 遍历前10行查找账户信息
            for i in range(min(10, len(df))):
                for j in range(len(df.columns)):
                    cell_value = str(df.iloc[i, j])
                    
                    # 查找户名信息 - 招商银行格式: "户    名：袁成杰"
                    if '户' in cell_value and '名' in cell_value and '：' in cell_value:
                        # 提取冒号后的内容
                        parts = cell_value.split('：')
                        if len(parts) > 1:
                            account_name = parts[1].strip()
                            self.logger.info(f"找到户名: {account_name}")
                    
                    # 查找账号信息 - 可能在卡号或账号字段中
                    if ('卡号' in cell_value or '账号' in cell_value) and '：' in cell_value:
                        # 提取冒号后的内容
                        parts = cell_value.split('：')
                        if len(parts) > 1:
                            account_part = parts[1].strip()
                            # 处理带星号的账号格式，如: 6214********8516
                            if '*' in account_part:
                                # 提取前4位和后4位数字
                                account_match = re.match(r'(\d{4})\*+(\d{4})', account_part)
                                if account_match:
                                    # 保存带星号的完整格式
                                    account_number = account_part
                                    self.logger.info(f"找到账号(带星号): {account_number}")
                            else:
                                # 尝试提取完整数字
                                numbers = re.findall(r'\d{10,}', account_part)
                                if numbers:
                                    account_number = numbers[0]
                                    self.logger.info(f"找到账号: {account_number}")
                    
                    # 也尝试直接从单元格中提取长数字（可能是账号）
                    if not account_number:
                        # 查找带星号的银行卡号格式
                        card_pattern = re.search(r'\d{4}\*+\d{4}', cell_value)
                        if card_pattern:
                            account_number = card_pattern.group()
                            self.logger.info(f"找到带星号的账号: {account_number}")
                        else:
                            # 查找完整数字
                            numbers = re.findall(r'\d{16,}', cell_value)  # 银行卡号通常16位以上
                            if numbers:
                                account_number = numbers[0]
                                self.logger.info(f"找到可能的账号: {account_number}")
            
            # 记录提取结果
            self.logger.info(f"账户信息提取结果 - 户名: {account_name}, 账号: {account_number}")
            
            # 只有当真正提取到账户信息时才返回，否则返回None
            if account_name and account_number:
                return account_name, account_number
            else:
                return None, None
        
        except Exception as e:
            self.logger.warning(f"提取账户信息失败: {e}")
            import traceback
            self.logger.warning(traceback.format_exc())
            return None, None
    
    def extract_transactions(self, file_path: str) -> Optional[pd.DataFrame]:
        """提取交易数据"""
        try:
            # 先读取原始数据，不设置表头
            df_raw = pd.read_excel(file_path, header=None)
            self.logger.info(f"原始数据形状: {df_raw.shape}")
            
            # 查找包含表头关键词的行
            header_row = None
            keywords = ['记账日期', '交易日期', '交易金额', '联机余额']
            
            for i in range(min(15, len(df_raw))):
                row_str = ' '.join([str(cell) for cell in df_raw.iloc[i].values if not pd.isna(cell)])
                keyword_count = sum(1 for keyword in keywords if keyword in row_str)
                if keyword_count >= 2:  # 如果包含2个或以上关键词
                    header_row = i
                    self.logger.info(f"找到表头行: 第{i+1}行, 内容: {row_str}")
                    break
            
            if header_row is None:
                self.logger.error("未找到有效的表头行")
                return None
            
            # 使用找到的行作为表头重新读取
            df = pd.read_excel(file_path, skiprows=header_row)
            self.logger.info(f"使用第{header_row+1}行作为表头，数据形状: {df.shape}")
            
            # 清理列名
            df.columns = df.columns.str.strip()
            self.logger.info(f"列名: {list(df.columns)}")
            
            # 检查必要的列是否存在
            date_col = None
            amount_col = None
            balance_col = None
            
            for col in df.columns:
                if '日期' in str(col):
                    date_col = col
                elif '金额' in str(col):
                    amount_col = col
                elif '余额' in str(col):
                    balance_col = col
            
            if not date_col:
                self.logger.error("未找到日期列")
                return None
            
            # 过滤有效数据行
            df = df.dropna(subset=[date_col], how='all')
            self.logger.info(f"过滤后数据行数: {len(df)}")
            
            # 重命名列以匹配标准格式
            column_mapping = {
                date_col: 'transaction_date',
                amount_col: 'amount' if amount_col else None,
                balance_col: 'balance' if balance_col else None,
                '对手信息': 'counterparty',
                '交易摘要': 'description',
                '摘要': 'description',
                '备注': 'description'
            }
            
            # 移除None值
            column_mapping = {k: v for k, v in column_mapping.items() if k and v}
            
            df = df.rename(columns=column_mapping)
            
            # 确保必要的列存在
            if 'transaction_date' not in df.columns:
                self.logger.error("重命名后仍未找到transaction_date列")
                return None
            
            self.logger.info(f"成功提取{len(df)}条交易记录")
            return df
            
        except Exception as e:
            self.logger.error(f"提取招商银行交易数据失败: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            return None