from flask import render_template, current_app
from flask_login import login_required, current_user
from . import main_bp
from app.models import Transaction, db
from datetime import datetime, timedelta
from sqlalchemy import func, desc

@main_bp.route('/')
@main_bp.route('/dashboard')
@login_required
def dashboard():
    """仪表盘页面 - 显示财务概览和统计信息"""
    try:
        # 获取账户余额
        balance = db.session.query(func.sum(Transaction.amount)).filter(
            Transaction.user_id == current_user.id
        ).scalar() or 0
        
        # 获取最近12个月的余额趋势
        monthly_trends = db.session.query(
            func.strftime('%Y-%m', Transaction.date).label('month'),
            func.sum(Transaction.amount).label('balance')
        ).filter(
            Transaction.user_id == current_user.id,
            Transaction.date >= func.date('now', '-12 months')
        ).group_by(
            func.strftime('%Y-%m', Transaction.date)
        ).order_by(
            func.strftime('%Y-%m', Transaction.date)
        ).all()
        
        # 格式化月度趋势数据
        trends_data = []
        for month, balance in monthly_trends:
            trends_data.append({
                'month': month,
                'balance': float(balance)
            })
        
        # 准备统计数据
        stats = {
            'balance': float(balance),
            'monthly_trends': trends_data
        }
        
        return render_template('dashboard.html',
                             page_title='仪表盘',
                             stats=stats)
                             
    except Exception as e:
        current_app.logger.error(f"加载仪表盘页面失败: {str(e)}")
        return render_template('dashboard.html',
                             page_title='仪表盘',
                             stats={
                                 'balance': 0,
                                 'monthly_trends': []
                             })