from flask import render_template, current_app
from . import main_bp
from app.models import Transaction, Account, db
from datetime import datetime, timedelta
from sqlalchemy import func, desc
from decimal import Decimal
from app.services.business.financial.financial_service import FinancialService

@main_bp.route('/')
@main_bp.route('/dashboard')
def dashboard():
    """仪表盘页面 - 显示财务概览和统计信息"""
    # 使用财务服务获取总览数据
    financial_service = FinancialService()    
    try:
        # 获取总览数据（默认12个月）
        balance_data = financial_service.get_balance_data()

        # 准备统计数据（转换为 float 用于显示）
        template_data = {
            'balance': balance_data[len(balance_data)-1]['balance'],
            'monthly_trends': [{
                'month': trend['month'],
                'balance': float(trend['balance'])
            } for trend in balance_data]
        }
        
        return render_template('dashboard.html',
                             page_title='仪表盘',
                             template_data=template_data)
                             
    except Exception as e:
        current_app.logger.error(f"加载仪表盘页面失败: {str(e)}")
        template_data={
            'balance': 0.0,
            'monthly_trends': []
        }
        return render_template('dashboard.html',
                             page_title='仪表盘',
                             template_data=template_data)