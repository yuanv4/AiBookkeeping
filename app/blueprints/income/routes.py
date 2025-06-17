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
        analyze_income_result = financial_service.analyze_income(
            months=12,
            account_filter=None  # 不筛选特定账户
        )
        # 准备模板数据
        template_data = {
            'total_income': float(analyze_income_result['total_income']),
            'avg_monthly_income': float(analyze_income_result['avg_monthly_income']),
            'income_growth_rate': float(analyze_income_result['income_growth_rate']),
            'income_sources': analyze_income_result['income_sources'],
            'monthly_trends': [{
                'month': trend['month'],
                'balance': float(trend['balance'])
            } for trend in analyze_income_result['monthly_trends']],
            'transaction_count': analyze_income_result['transaction_count']
        }
        
        return render_template('income_analysis.html',
                             page_title='收入分析',
                             template_data=template_data)
        
    except Exception as e:
        current_app.logger.error(f"收入分析页面处理异常: {str(e)}")
        template_data = {
            'total_income': 0.0,
            'avg_monthly_income': 0.0,
            'income_growth_rate': 0.0,
            'income_sources': [],
            'monthly_trends': [],
            'transaction_count': 0
        }
        return render_template('income_analysis.html',
                             page_title='收入分析',
                             template_data=template_data)