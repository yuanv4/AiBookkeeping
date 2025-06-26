# -*- coding: utf-8 -*-
"""
银行配置文件
============

集中管理所有银行提取器的配置信息，实现配置与逻辑的分离。
"""

from .extractors.base_extractor import ExtractionConfig, AccountExtractionPattern, BankInfo

# 银行配置字典
BANK_CONFIGS = {
    'CCB': {
        'date_format': '%Y%m%d',
        'date_validation': 'digit',  # 建设银行日期是纯数字格式
        'config': ExtractionConfig(
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
    },
    'CMB': {
        'date_format': '%Y-%m-%d %H:%M:%S',
        'date_validation': 'datetime',  # 招商银行日期是标准日期时间格式
        'config': ExtractionConfig(
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
    }
}

def get_bank_config(bank_code: str) -> dict:
    """获取指定银行的配置信息
    
    Args:
        bank_code: 银行代码，如 'CCB', 'CMB'
        
    Returns:
        dict: 银行配置字典
        
    Raises:
        KeyError: 当银行代码不存在时抛出
    """
    if bank_code not in BANK_CONFIGS:
        raise KeyError(f"不支持的银行代码: {bank_code}")
    return BANK_CONFIGS[bank_code] 