"""Financial Analysis Service

This module provides comprehensive financial analysis, reporting, and insights.
"""

from typing import List, Dict, Any, Optional, Tuple
from decimal import Decimal
from datetime import date, datetime, timedelta
import logging

from app.services.analysis import ComprehensiveService
from app.services.reporting import FinancialReportService

logger = logging.getLogger(__name__)

class AnalysisService:
    """Service for financial analysis and reporting.
    
    This class serves as a facade that delegates to specialized analysis services.
    """
    
    @staticmethod
    def generate_financial_report(account_id: int = None, start_date: date = None, 
                                end_date: date = None) -> Dict[str, Any]:
        """Generate comprehensive financial report."""
        return FinancialReportService.generate_financial_report(account_id, start_date, end_date)
    

    
    @staticmethod
    def get_comprehensive_income_analysis(start_date: date = None, 
                                        end_date: date = None):
        """Get comprehensive income analysis using all specialized analyzers."""
        # ComprehensiveService方法只接受account_id参数，暂时传入None
        return ComprehensiveService.get_comprehensive_income_analysis(account_id=None)