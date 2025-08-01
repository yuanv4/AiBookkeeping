# -*- coding: utf-8 -*-
"""
银行配置常量
============

包含所有银行的配置数据，用于配置驱动的通用提取器。
"""

import pandas as pd

EXTRACTORS = {
    'CCB': {
        'bank_name': '建设银行',
        'bank_code': 'CCB',
        'account_name_key': '客户名称:',
        'account_number_key': '卡号/账号:',
        'transaction_header': '交易日期',
        'column_mapping': {
            '交易日期': 'date',
            '交易金额': 'amount',
            '账户余额': 'balance_after',
            '对方账号与户名': 'counterparty',
            '摘要': 'description',
            '币别': 'currency'
        },
        'date_format': '%Y%m%d',
        'date_validator': lambda x: not pd.isna(x) and str(x).strip().isdigit()
    },
    'CMB': {
        'bank_name': '招商银行',
        'bank_code': 'CMB',
        'account_name_key': '户    名：',
        'account_number_key': '账号：',
        'transaction_header': '记账日期',
        'column_mapping': {
            '记账日期': 'date',
            '交易金额': 'amount',
            '联机余额': 'balance_after',
            '对手信息': 'counterparty',
            '交易摘要': 'description',
            '货币': 'currency'
        },
        'date_format': '%Y-%m-%d %H:%M:%S',
        'date_validator': lambda x: not pd.isna(x)
    }
}
