"""Extraction Services Package.

This package contains services for extracting transaction data from bank statements.
Provides a clean public API with service facade and data models.
"""

from .service import get_extraction_service, ExtractionService
from .models import ExtractedData

__all__ = [
    'get_extraction_service',
    'ExtractionService',
    'ExtractedData'
]