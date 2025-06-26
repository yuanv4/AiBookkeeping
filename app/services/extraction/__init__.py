"""Extraction Services Package.

This package contains services for extracting transaction data from bank statements.
Includes base extractors, specific bank extractors, factory patterns, and comprehensive facade service.
"""

from .service import BankStatementExtractor, get_extractor_service
from .models import ExtractionResult

__all__ = [
    'BankStatementExtractor', 
    'get_extractor_service',
    'ExtractionResult'
]