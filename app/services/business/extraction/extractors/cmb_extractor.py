# -*- coding: utf-8 -*-
"""
招商银行提取器
==============

招商银行对账单数据提取器实现。
"""

import os
import re
import pandas as pd
from datetime import datetime
from typing import Optional, Tuple

from .base_extractor import BaseTransactionExtractor, ExtractionConfig, AccountExtractionPattern, BankInfo

class CMBTransactionExtractor(BaseTransactionExtractor):
    """招商银行交易提取器"""
    
    def __init__(self):
        super().__init__('CMB')

    def _convert_date(self, date_str: str) -> Optional[datetime]:
        """将招商银行日期字符串转换为标准datetime对象
        
        Args:
            date_str: 招商银行日期字符串，格式为"M/D/YYYY"，如"1/1/2023"
            
        Returns:
            datetime: 转换后的标准日期时间对象，转换失败返回None
        """
        if pd.isna(date_str):
            return None
        try:
            return pd.to_datetime(str(date_str).strip(), format='%m/%d/%Y')
        except:
            self.logger.warning(f"无法解析招商银行日期格式: {date_str}")
            return None

    def get_extraction_config(self) -> ExtractionConfig:
        """获取招商银行特定的数据提取配置"""
        return ExtractionConfig(
            use_skiprows=True,
            account_name_pattern=AccountExtractionPattern(
                keyword='户    名：',
                regex_pattern=r'户    名：(.+)'
            ),
            account_number_pattern=AccountExtractionPattern(
                keyword='账号：',
                regex_pattern=r'账号：(.+)'
            ),
            bank_info=BankInfo(
                code='CMB',
                name='招商银行'
            ),
            source_columns=['记账日期', '交易金额', '联机余额', '对手信息', '交易摘要', '货币']
        )