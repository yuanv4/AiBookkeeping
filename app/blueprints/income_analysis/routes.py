from flask import render_template, current_app

# 使用新的服务层
from app.services.core.database_service import DatabaseService
from app.services.analysis.analysis_service import ComprehensiveService as AnalysisService

from . import income_analysis_bp

@income_analysis_bp.route('/')
def income_analysis():
    """收入分析页面"""
    try:
        # 使用新的服务层
        database_service = DatabaseService()
        analysis_service = AnalysisService()
        
        # 获取综合收入分析数据（包含模板所需的data结构）
        data = analysis_service.get_comprehensive_income_analysis()
        
        return render_template('income_analysis.html', data=data)
    except Exception as e:
        current_app.logger.error(f"收入分析页面错误: {str(e)}")
        return render_template('income_analysis.html', data=None, error=str(e))