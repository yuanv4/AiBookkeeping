from flask import render_template, current_app, request

# 使用新的服务层
from app.services.database_service import DatabaseService
from app.services.analysis_service import AnalysisService

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
        
        # 获取其他收入分析数据（保持向后兼容）
        monthly_income = analysis_service.get_monthly_income_summary()
        yearly_income = analysis_service.get_yearly_income_summary()
        income_by_account = analysis_service.get_income_by_account()
        income_trends = analysis_service.get_income_trends()
        
        return render_template('income_analysis.html',
                             data=data,
                             monthly_income=monthly_income,
                             yearly_income=yearly_income,
                             income_by_account=income_by_account,
                             income_trends=income_trends)
        
    except Exception as e:
        current_app.logger.error(f"收入分析页面加载出错: {e}", exc_info=True)
        raise