# extractors包初始化文件
"""
数据提取模块
===========

负责从不同银行的Excel文件中提取交易数据。

主要模块：
- base.bank_transaction_extractor - 银行交易提取器基类
- interfaces.extractor_interface - 银行交易提取器接口
- factory.extractor_factory - 银行交易提取器工厂
- config.config_loader - 银行配置加载器
- banks.cmb_transaction_extractor - 招商银行交易提取器
- banks.ccb_transaction_extractor - 建设银行交易提取器
"""

# 导入基础接口和工厂
from scripts.extractors.interfaces.extractor_interface import ExtractorInterface
from scripts.extractors.factory.extractor_factory import get_extractor_factory
from scripts.extractors.config.config_loader import get_config_loader

# 导入基类实现
from scripts.extractors.base.bank_transaction_extractor import BankTransactionExtractor

# 导入银行实现
from scripts.extractors.banks.cmb_transaction_extractor import CMBTransactionExtractor
from scripts.extractors.banks.ccb_transaction_extractor import CCBTransactionExtractor

__all__ = [
    'ExtractorInterface',
    'get_extractor_factory',
    'get_config_loader',
    'BankTransactionExtractor',
    'CMBTransactionExtractor',
    'CCBTransactionExtractor'
]

# 初始化工厂
factory = get_extractor_factory()

# 提供简便函数用于处理文件
def process_files(upload_dir):
    """处理上传目录中的所有文件
    
    Args:
        upload_dir: 上传文件目录
        
    Returns:
        list: 处理结果信息
    """
    return factory.process_files(upload_dir)

# 添加到导出列表
__all__.append('process_files') 