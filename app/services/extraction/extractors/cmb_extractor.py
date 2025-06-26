# -*- coding: utf-8 -*-
"""
招商银行提取器
==============

招商银行对账单数据提取器实现。
"""

import os
import re
import logging
import pandas as pd
from datetime import datetime
from typing import Optional, Tuple

from .base_extractor import BaseTransactionExtractor
from ..models import ExtractionConfig, AccountExtractionPattern, BankInfo

class CMBTransactionExtractor(BaseTransactionExtractor):
    """招商银行交易提取器"""
    
    BANK_CODE = 'CMB'
    BANK_NAME = '招商银行'
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger('cmb_extractor')

    def is_applicable(self, df: pd.DataFrame) -> bool:
        """检查此提取器是否适用于给定的数据
        
        Args:
            df: 从Excel文件读取的原始DataFrame
            
        Returns:
            bool: 如果此提取器适用于该数据则返回True，否则返回False
        """
        try:
            # 检查前几行是否包含招商银行特有的关键字
            for i in range(min(10, len(df))):
                for j in range(len(df.columns)):
                    cell_value = str(df.iloc[i, j])
                    if '户    名：' in cell_value or '账号：' in cell_value:
                        return True
            return False
        except:
            return False

    def _convert_date(self, date_str: str) -> Optional[datetime]:
        """将招商银行日期字符串转换为标准datetime对象
        
        Args:
            date_str: 招商银行日期字符串，格式为"M/D/YYYY"，如"2023-01-01"
            
        Returns:
            datetime: 转换后的标准日期时间对象，转换失败返回None
        """
        if pd.isna(date_str):
            return None
        try:
            return pd.to_datetime(str(date_str).strip(), format='%Y-%m-%d %H:%M:%S')
        except:
            self.logger.warning(f"无法解析招商银行日期格式: {date_str}")
            return None

    def get_extraction_config(self) -> ExtractionConfig:
        """获取招商银行特定的数据提取配置"""
        return ExtractionConfig(
            account_name_pattern=AccountExtractionPattern(
                keyword='户    名：',
                regex_pattern=r'户    名：(.+)'
            ),
            account_number_pattern=AccountExtractionPattern(
                keyword='账号：',
                regex_pattern=r'账号：(.+)'
            ),
            header_keyword='记账日期',
            column_mapping={
                '记账日期': 'date',
                '交易金额': 'amount',
                '联机余额': 'balance_after',
                '对手信息': 'counterparty',
                '交易摘要': 'description',
                '货币': 'currency'
            }
        )