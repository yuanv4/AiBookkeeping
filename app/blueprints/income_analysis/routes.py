from flask import render_template, current_app
from app.services.analysis import FinancialAnalyzer
from . import income_analysis_bp

@income_analysis_bp.route('/')
def income_analysis():
    """收入分析页面"""
    try:
        analyzer = FinancialAnalyzer()
        data = analyzer.get_comprehensive_analysis(12)
        return render_template('income_analysis.html', data=data)
    except Exception as e:
        current_app.logger.error(f"收入分析页面错误: {str(e)}")
        return render_template('income_analysis.html', data=None, error=str(e))