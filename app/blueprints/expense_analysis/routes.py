from flask import render_template, current_app

# 使用新的服务层
from app.services.analysis.analysis_service import ComprehensiveService as AnalysisService

from . import expense_analysis_bp

@expense_analysis_bp.route('/')
def expense_analysis():
    """支出分析页面"""
    try:
        # 使用新的服务层
        analysis_service = AnalysisService()
        
        # 获取综合支出分析数据（包含模板所需的data结构）
        data = analysis_service.get_comprehensive_expense_analysis()
        
        return render_template('expense_analysis.html', data=data)
    except Exception as e:
        current_app.logger.error(f"支出分析页面错误: {str(e)}")
        return render_template('expense_analysis.html', data=None, error=str(e))