"""Services package for the Flask application.

This package contains business logic and service layer functionality.
"""

# Core services
from .core.transaction_service import TransactionService
from .core.file_processor_service import FileProcessorService

# Analysis services
from .analysis.analysis_service import ComprehensiveService as AnalysisService
from .analysis import ComprehensiveService

# Reporting services
from .report import FinancialReportService

# Extraction services
from .extraction import BankStatementExtractor

__all__ = [
    # Core services
    'TransactionService',
    'FileProcessorService',
    
    # Analysis services
    'AnalysisService',
    'ComprehensiveService',
    
    # Reporting services
    'FinancialReportService',
    
    # Extraction services
    'BankStatementExtractor',
]