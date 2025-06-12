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

from .base_extractor import BaseTransactionExtractor, ExtractionConfig, AccountExtractionPattern, BankInfo

class CCBTransactionExtractor(BaseTransactionExtractor):
    """建设银行交易提取器"""
    
    def __init__(self):
        super().__init__('CCB')
    
    def get_extraction_config(self) -> ExtractionConfig:
        """获取建设银行特定的数据提取配置"""
        return ExtractionConfig(
            date_column_keyword='交易日期',
            column_mapping={
                '交易日期': 'transaction_date',
                '交易金额': 'amount',
                '账户余额': 'balance_after',
                '对方账号与户名': 'counterparty',
                '摘要': 'description',
                '币别': 'currency',
            },
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
                name='建设银行',
                keyword='建设银行'
            )
        )