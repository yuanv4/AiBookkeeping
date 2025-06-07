# -*- coding: utf-8 -*-
"""
Reporting Services Package

This package contains services responsible for generating various types of financial reports,
including comprehensive financial statements, charts, and export functionality.
"""

from .financial_report_service import FinancialReportService

__all__ = [
    'FinancialReportService'
]