# -*- coding: utf-8 -*-
"""
建设银行提取器
==============

建设银行对账单数据提取器实现。
"""

import os
import re
import pandas as pd
from typing import Optional, Tuple

from .base_extractor import BaseTransactionExtractor

class CCBTransactionExtractor(BaseTransactionExtractor):
    """建设银行交易提取器"""
    
    def __init__(self):
        super().__init__('CCB')
    
    def get_bank_code(self) -> str:
        return 'CCB'
    
    def get_bank_name(self) -> str:
        return '建设银行'
    
    def get_bank_keyword(self) -> str:
        return '建设银行'
    

    
    def _extract_account_name(self, cell_value: str) -> Optional[str]:
        """从单元格值中提取账户名称 - 建设银行格式"""
        # 查找户名 - 建设银行格式：客户名称:***
        if '客户名称:' in cell_value:
            name_match = re.search(r'客户名称:(.+)', cell_value)
            if name_match:
                account_name = name_match.group(1).strip()
                self.logger.info(f"找到户名: {account_name}")
                return account_name
        return None
    
    def _extract_account_number(self, cell_value: str) -> Optional[str]:
        """从单元格值中提取账户号码 - 建设银行格式"""
        # 查找账号模式 - 建设银行格式：卡号/账号:6217**********2832
        if '卡号/账号:' in cell_value:
            numbers = re.findall(r'\d{10,}', cell_value)
            if numbers:
                self.logger.info(f"找到账号: {numbers[0]}")
                return numbers[0]
        return None
    
    def _extract_transactions_impl(self, file_path: str) -> Optional[pd.DataFrame]:
        """提取交易数据"""
        try:
            # 读取Excel文件，不设置header，先分析结构
            df_raw = pd.read_excel(file_path, header=None)
            
            # 查找包含'交易日期'的行作为表头
            header_row = None
            for i, row in df_raw.iterrows():
                row_values = row.values
                if any('交易日期' in str(val) for val in row_values):
                    header_row = i
                    self.logger.info(f"找到表头行在第{i}行: {row_values}")
                    break
            
            if header_row is None:
                self.logger.error("未找到包含'交易日期'的表头行")
                return None
            
            # 使用找到的行作为表头重新读取
            df = pd.read_excel(file_path, header=header_row)
            
            # 清理列名
            df.columns = df.columns.str.strip()
            
            self.logger.info(f"读取到的列名: {df.columns.tolist()}")
            self.logger.info(f"数据形状: {df.shape}")
            
            # 过滤有效数据行（排除空的交易日期）
            if '交易日期' in df.columns:
                df = df.dropna(subset=['交易日期'], how='all')
                # 进一步过滤：确保交易日期不是字符串'交易日期'本身
                df = df[df['交易日期'] != '交易日期']
                self.logger.info(f"过滤后数据行数: {len(df)}")
            else:
                self.logger.error(f"未找到'交易日期'列，可用列: {df.columns.tolist()}")
                return None
            
            # 重命名列以匹配标准格式
            column_mapping = {
                '交易日期': 'transaction_date',
                '交易金额': 'amount',
                '账户余额': 'balance',
                '对方账号与户名': 'counterparty',
                '摘要': 'description',
                '备注': 'description',
                '交易地点/附言': 'memo'
            }
            
            df = df.rename(columns=column_mapping)
            
            # 确保必要的列存在
            required_columns = ['transaction_date', 'amount']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                self.logger.error(f"缺少必要的列: {missing_columns}")
                return None
            
            return df
            
        except Exception as e:
            self.logger.error(f"提取建设银行交易数据失败: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            return None