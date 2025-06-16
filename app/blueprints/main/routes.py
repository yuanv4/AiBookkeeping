from flask import render_template, current_app
from . import main_bp
from app.models import Transaction
from datetime import datetime, timedelta
from sqlalchemy import func, desc


@main_bp.route('/')
@main_bp.route('/dashboard')
def dashboard():
    """仪表盘页面 - 显示财务概览和统计信息"""
    try:
        # 获取账户余额（简单计算）
        balance = 0
        
        # 准备统计数据
        stats = {
            'balance': balance,
        }
        
        current_app.logger.info(f"仪表盘数据加载成功，共 {total_transactions} 条交易记录")
        
        return render_template('dashboard.html', stats=stats)
        
    except Exception as e:
        current_app.logger.error(f"加载仪表盘数据时出错: {e}", exc_info=True)
        # 返回错误页面或基本的仪表盘
        return render_template('dashboard.html', stats={
            'balance': 0,
        })