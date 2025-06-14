"""Services package for the Flask application.

This package contains business logic and service layer functionality.
"""

# 核心服务
from .core import TransactionService, FileProcessorService

# 统一财务服务（替代原有的分析和报告服务）
from .financial_service import FinancialService

# 分析服务（保持向后兼容，但建议使用FinancialService）
from .analysis import (
    FinancialAnalyzer,
    AnalysisResult, MonthlyData, FinancialSummary, 
    FinancialHealthMetrics, ComprehensiveReport,
    cache_result, handle_analysis_errors, AnalysisError
)

# 报告服务功能已合并到FinancialService中

# 提取服务
from .extraction import BankStatementExtractor

__all__ = [
    # Core services
    'TransactionService',
    'FileProcessorService',
    
    # Analysis services
    'AnalysisService',
    
    # Unified financial service
    'FinancialService',
    
    # Extraction services
    'BankStatementExtractor',
]