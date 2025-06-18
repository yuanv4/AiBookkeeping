"""Services package for the Flask application.

This package contains business logic and service layer functionality.
"""

# 核心服务
from .core import TransactionService, FileProcessorService, FinancialService

# 新的推荐导入路径
from .business.extraction.service import BankStatementExtractor
from .business.extraction.factory import ExtractorFactory
from .business.extraction.models import ExtractionResult, StatementData

__all__ = [
    'FinancialService',
    'BankStatementExtractor', 
    'ExtractorFactory',
    'ExtractionResult',
    'StatementData'
]