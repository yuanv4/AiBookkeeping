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
    def get_monthly_income_summary(year: int = None, month: int = None, 
                                 account_id: int = None) -> Dict[str, Any]:
        """Get monthly income summary."""
        # ComprehensiveService方法不接受参数，使用默认实现
        return ComprehensiveService.get_monthly_income_summary()
    
    @staticmethod
    def get_yearly_income_summary(year: int = None, account_id: int = None) -> Dict[str, Any]:
        """Get yearly income summary."""
        # ComprehensiveService方法不接受参数，使用默认实现
        return ComprehensiveService.get_yearly_income_summary()
    
    @staticmethod
    def get_income_by_account(start_date: date = None, end_date: date = None) -> Dict[str, Any]:
        """Get income breakdown by account."""
        # ComprehensiveService方法不接受参数，使用默认实现
        return ComprehensiveService.get_income_by_account()
    
    @staticmethod
    def get_income_trends(start_date: date = None, end_date: date = None, 
                         account_id: int = None) -> Dict[str, Any]:
        """Get income trends analysis."""
        # ComprehensiveService方法不接受参数，使用默认实现
        return ComprehensiveService.get_income_trends()
    
    @staticmethod
    def compare_periods(period1_start: date, period1_end: date,
                       period2_start: date, period2_end: date,
                       account_id: int = None) -> Dict[str, Any]:
        """Compare financial data between two periods."""
        # 调整参数顺序以匹配ComprehensiveService方法
        return ComprehensiveService.compare_periods(
            account_id=account_id, 
            current_start=period1_start, 
            current_end=period1_end,
            previous_start=period2_start, 
            previous_end=period2_end
        )
    
    @staticmethod
    def get_budget_analysis(start_date: date = None, end_date: date = None) -> Dict[str, Any]:
        """Get budget analysis."""
        # ComprehensiveService方法需要budget_limits参数，传入None使用默认值
        return ComprehensiveService.get_budget_analysis(
            account_id=None, 
            budget_limits=None, 
            start_date=start_date, 
            end_date=end_date
        )
    
    @staticmethod
    def export_financial_data(start_date: date = None, end_date: date = None,
                            account_id: int = None, format: str = 'json') -> Dict[str, Any]:
        """Export financial data."""
        # 调整参数顺序以匹配ComprehensiveService方法
        return ComprehensiveService.export_financial_data(
            account_id=account_id, 
            start_date=start_date, 
            end_date=end_date, 
            format=format
        )
    
    @staticmethod
    def get_comprehensive_income_analysis(start_date: date = None, 
                                        end_date: date = None):
        """Get comprehensive income analysis using all specialized analyzers."""
        # ComprehensiveService方法只接受account_id参数，暂时传入None
        return ComprehensiveService.get_comprehensive_income_analysis(account_id=None)