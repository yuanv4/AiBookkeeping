from flask import render_template, current_app
from . import main_bp
from app.models import Transaction, Account, db
from datetime import datetime, timedelta
from sqlalchemy import func, desc
from decimal import Decimal

@main_bp.route('/')
@main_bp.route('/dashboard')
def dashboard():
    """仪表盘页面 - 显示财务概览和统计信息"""
    try:
        # 使用 Account 模型的类方法获取总余额
        balance = Account.get_all_accounts_balance()
        
        # 使用 Account 模型的类方法获取月度趋势
        monthly_trends = Account.get_monthly_balance_trends()
        
        # 准备统计数据（转换为 float 用于显示）
        stats = {
            'balance': float(balance),
            'monthly_trends': [{
                'month': trend['month'],
                'balance': float(trend['balance'])
            } for trend in monthly_trends]
        }
        
        return render_template('dashboard.html',
                             page_title='仪表盘',
                             stats=stats)
                             
    except Exception as e:
        current_app.logger.error(f"加载仪表盘页面失败: {str(e)}")
        return render_template('dashboard.html',
                             page_title='仪表盘',
                             stats={
                                 'balance': 0.0,
                                 'monthly_trends': []
                             })