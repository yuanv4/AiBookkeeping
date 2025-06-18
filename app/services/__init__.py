"""Services package for the Flask application."""

# 核心服务
from .core import TransactionService, FileProcessorService, FinancialService

# 新的推荐导入路径
from .extraction.service import BankStatementExtractor
from .extraction.factory import ExtractorFactory
from .extraction.models import ExtractionResult, StatementData

__all__ = [
    'TransactionService',
    'FileProcessorService',
    'FinancialService',
    'BankStatementExtractor', 
    'ExtractorFactory',
    'ExtractionResult',
    'StatementData'
]