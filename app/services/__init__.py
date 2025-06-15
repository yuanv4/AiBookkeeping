"""Services package for the Flask application.

This package contains business logic and service layer functionality.
"""

# 核心服务
from .core import TransactionService, FileProcessorService

# 新的推荐导入路径
from .business.financial.financial_service import FinancialService
from .business.extraction.service import BankStatementExtractor
from .business.extraction.factory import ExtractorFactory
from .business.extraction.models import ExtractionResult, StatementData

# 向后兼容的导入路径
from .business.financial.financial_service import FinancialService as financial_service_FinancialService
from .business.extraction.service import BankStatementExtractor as extraction_service_BankStatementExtractor
from .business.extraction.factory import ExtractorFactory as extraction_factory_ExtractorFactory
from .business.extraction.models import ExtractionResult as extraction_models_ExtractionResult
from .business.extraction.models import StatementData as extraction_models_StatementData

__all__ = [
    'FinancialService',
    'BankStatementExtractor', 
    'ExtractorFactory',
    'ExtractionResult',
    'StatementData'
]