"""Services package for the Flask application.

This package contains business logic and service layer functionality.
"""

# Core services
from .core.database_service import DatabaseService
from .core.transaction_service import TransactionService
from .core.file_processor_service import FileProcessorService

# Analysis services
from .analysis_service import AnalysisService
from .analysis import ComprehensiveService

# Reporting services
from .reporting import FinancialReportService

# Extraction services
from .extraction import BankStatementExtractor

# Backward compatibility imports
from .core.database_service import DatabaseService as DatabaseService_Legacy
from .core.transaction_service import TransactionService as TransactionService_Legacy

__all__ = [
    # Core services
    'DatabaseService',
    'TransactionService',
    'FileProcessorService',
    
    # Analysis services
    'AnalysisService',
    'ComprehensiveService',
    
    # Reporting services
    'FinancialReportService',
    
    # Extraction services
    'BankStatementExtractor',
    
    # Legacy compatibility
    'DatabaseService_Legacy',
    'TransactionService_Legacy'
]