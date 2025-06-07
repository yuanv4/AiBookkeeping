# -*- coding: utf-8 -*-
"""
Data Extraction Services Package

This package contains services responsible for extracting and processing data from various sources,
including bank statements, receipts, and other financial documents.
"""

from .bank_statement_extractor import BankStatementExtractor

__all__ = [
    'BankStatementExtractor'
]