"""Extraction Services Package.

This package contains services for extracting transaction data from bank statements.
Includes base extractors, specific bank extractors, factory patterns, and comprehensive facade service.
"""

from .extractors.base_extractor import BankStatementExtractorInterface, BaseTransactionExtractor
from .extractor_factory import ExtractorFactory
from .bank_statement_service import BankStatementExtractor, get_extractor_service
from .comprehensive_extraction_service import ComprehensiveExtractionService, get_comprehensive_extraction_service
from .extractors import *

__all__ = [
    'BankStatementExtractorInterface',
    'BaseTransactionExtractor', 
    'ExtractorFactory',
    'BankStatementExtractor',
    'get_extractor_service',
    'ComprehensiveExtractionService',
    'get_comprehensive_extraction_service'
]