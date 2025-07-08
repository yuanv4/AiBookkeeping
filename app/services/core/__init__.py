# -*- coding: utf-8 -*-
"""Core Services Package

核心服务包，提供基础的CRUD操作和数据管理功能。
"""

from .account_service import AccountService
from .bank_service import BankService
from .transaction_service import TransactionService
from .file_processor_service import FileProcessorService

# 导入新的分析服务以便于使用
try:
    from ..analysis import FinancialAnalysisService
    _ANALYSIS_SERVICES_AVAILABLE = True
except ImportError:
    _ANALYSIS_SERVICES_AVAILABLE = False

__all__ = [
    'AccountService',
    'BankService', 
    'TransactionService',
    'FileProcessorService'
]

# 如果分析服务可用，也导出它们
if _ANALYSIS_SERVICES_AVAILABLE:
    __all__.extend(['FinancialAnalysisService'])