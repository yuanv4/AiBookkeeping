from flask import render_template, current_app
from app.services import FinancialService
from . import expense_analysis_bp

@expense_analysis_bp.route('/')
def expense_analysis():
    """支出分析页面"""
    try:
        financial_service = FinancialService()
        data = financial_service.get_comprehensive_analysis(12)
        return render_template('expense_analysis.html', data=data)
    except Exception as e:
        current_app.logger.error(f"支出分析页面错误: {str(e)}")
        return render_template('expense_analysis.html', data=None, error=str(e))