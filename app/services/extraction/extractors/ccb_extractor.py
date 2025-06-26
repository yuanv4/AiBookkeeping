# -*- coding: utf-8 -*-
"""
建设银行提取器
==============

建设银行对账单数据提取器实现。
"""

import os
import re
import logging
import pandas as pd
from datetime import datetime
from typing import Optional, Tuple

from .base_extractor import BaseTransactionExtractor
from ..models import ExtractionConfig, AccountExtractionPattern, BankInfo

class CCBTransactionExtractor(BaseTransactionExtractor):
    """建设银行交易提取器"""
    
    BANK_CODE = 'CCB'
    BANK_NAME = '建设银行'
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger('ccb_extractor')
    
    def is_applicable(self, df: pd.DataFrame) -> bool:
        """检查此提取器是否适用于给定的数据
        
        Args:
            df: 从Excel文件读取的原始DataFrame
            
        Returns:
            bool: 如果此提取器适用于该数据则返回True，否则返回False
        """
        try:
            # 检查前几行是否包含建设银行特有的关键字
            for i in range(min(10, len(df))):
                for j in range(len(df.columns)):
                    cell_value = str(df.iloc[i, j])
                    if '客户名称:' in cell_value or '卡号/账号:' in cell_value:
                        return True
            return False
        except:
            return False
    
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
            self.logger.warning(f"无法解析建设银行日期格式: {date_str}")
            return None
    
    def get_extraction_config(self) -> ExtractionConfig:
        """获取建设银行特定的数据提取配置"""
        return ExtractionConfig(
            account_name_pattern=AccountExtractionPattern(
                keyword='客户名称:',
                regex_pattern=r'客户名称:(.+)'
            ),
            account_number_pattern=AccountExtractionPattern(
                keyword='卡号/账号:',
                regex_pattern=r'卡号/账号:(.+)'
            ),
            header_keyword='交易日期',
            column_mapping={
                '交易日期': 'date',
                '交易金额': 'amount',
                '账户余额': 'balance_after',
                '对方账号与户名': 'counterparty',
                '摘要': 'description',
                '币别': 'currency'
            }
        )