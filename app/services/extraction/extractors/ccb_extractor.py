# -*- coding: utf-8 -*-
"""
建设银行提取器
==============

建设银行对账单数据提取器实现。
"""

import os
import re
import pandas as pd
from datetime import datetime
from typing import Optional, Tuple

from .base_extractor import BaseTransactionExtractor, ExtractionConfig, AccountExtractionPattern, BankInfo

class CCBTransactionExtractor(BaseTransactionExtractor):
    """建设银行交易提取器"""
    
    def __init__(self):
        super().__init__('CCB')
    
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
            use_skiprows=False,
            account_name_pattern=AccountExtractionPattern(
                keyword='客户名称:',
                regex_pattern=r'客户名称:(.+)'
            ),
            account_number_pattern=AccountExtractionPattern(
                keyword='卡号/账号:',
                regex_pattern=r'卡号/账号:(.+)'
            ),
            bank_info=BankInfo(
                code='CCB',
                name='建设银行'
            ),
            source_columns=['交易日期', '交易金额', '账户余额', '对方账号与户名', '摘要', '币别']
        )