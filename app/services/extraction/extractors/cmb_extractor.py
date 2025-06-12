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

from .base_extractor import BaseTransactionExtractor, ExtractionConfig, AccountExtractionPattern, BankInfo

class CMBTransactionExtractor(BaseTransactionExtractor):
    """招商银行交易提取器"""
    
    def __init__(self):
        super().__init__('CMB')

    def get_extraction_config(self) -> ExtractionConfig:
        """获取招商银行特定的数据提取配置"""
        return ExtractionConfig(
            date_column_keyword='记账日期',
            column_mapping={
                '记账日期': 'transaction_date',
                '交易金额': 'amount',
                '联机余额': 'balance_after',
                '对手信息': 'counterparty',
                '交易摘要': 'description',
                '货币': 'currency',
            },
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
                name='招商银行',
                keyword='招商银行'
            )
        )