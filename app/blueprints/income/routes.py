from flask import render_template, current_app
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta
from app.services import FinancialService
from app.utils.decorators import handle_errors

from . import income_bp  # 从同级 __init__.py 导入 income_bp 蓝图实例

@income_bp.before_request
def before_request():
    pass

@income_bp.after_request
def after_request(response):
    # Flask-SQLAlchemy 自动管理连接，无需手动关闭
    return response

@income_bp.route('/')
@handle_errors
def income_analysis():
    """收入分析页面"""
    # 使用财务服务获取收入分析数据
    financial_service = FinancialService()
    
    try:
        # 获取收入分析数据（默认12个月）
        income_analysis_result = financial_service.analyze_income(
            months=12,
            account_filter=None  # 不筛选特定账户
        )
        
        # 检查数据是否获取成功
        if not income_analysis_result:
            current_app.logger.warning("获取收入分析数据失败")
            income_analysis_result = {
                'total_income': 0.0,
                'avg_monthly_income': 0.0,
                'income_growth_rate': 0.0,
                'income_sources': [],
                'monthly_trends': [],
                'transaction_count': 0
            }
        
        # 准备模板数据
        template_data = {
            'page_title': '收入分析',
            'income_data': income_analysis_result,
            'current_date': datetime.now().strftime('%Y-%m-%d'),
            'analysis_period': '12个月'
        }
        
        current_app.logger.info(f"收入分析页面数据准备完成，总收入: {income_analysis_result.get('total_income', 0)}")
        
        return render_template('income_analysis.html', **template_data)
        
    except Exception as e:
        current_app.logger.error(f"收入分析页面处理异常: {str(e)}")
        # 返回错误页面或默认数据
        template_data = {
            'page_title': '收入分析',
            'income_data': {
                'total_income': 0.0,
                'avg_monthly_income': 0.0,
                'income_growth_rate': 0.0,
                'income_sources': [],
                'monthly_trends': [],
                'transaction_count': 0
            },
            'current_date': datetime.now().strftime('%Y-%m-%d'),
            'analysis_period': '12个月',
            'error_message': '数据加载失败，请稍后重试'
        }
        
        return render_template('income_analysis.html', **template_data)