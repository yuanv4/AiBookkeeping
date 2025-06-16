from flask import jsonify, render_template, flash
from flask_login import login_required, current_user
from sqlalchemy import func
from datetime import datetime

@bp.route('/api/dashboard/stats')
@login_required
def get_dashboard_stats():
    """获取仪表盘统计数据"""
    try:
        # 获取账户余额
        balance = db.session.query(func.sum(Transaction.amount)).filter(
            Transaction.user_id == current_user.id
        ).scalar() or 0
        
        # 获取最近12个月的余额趋势
        monthly_trends = db.session.query(
            func.strftime('%Y-%m', Transaction.date).label('month'),
            func.sum(Transaction.amount).label('total')
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
        for month, total in monthly_trends:
            trends_data.append({
                'month': month,
                'total': float(total)
            })
        
        return jsonify({
            'success': True,
            'data': {
                'balance': float(balance),
                'monthly_trends': trends_data,
                'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"获取仪表盘数据失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': '获取仪表盘数据失败'
        }), 500

@bp.route('/dashboard')
@login_required
def dashboard():
    """仪表盘页面"""
    try:
        # 获取账户余额
        balance = db.session.query(func.sum(Transaction.amount)).filter(
            Transaction.user_id == current_user.id
        ).scalar() or 0
        
        # 获取最近12个月的余额趋势
        monthly_trends = db.session.query(
            func.strftime('%Y-%m', Transaction.date).label('month'),
            func.sum(Transaction.amount).label('total')
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
        for month, total in monthly_trends:
            trends_data.append({
                'month': month,
                'total': float(total)
            })
        
        return render_template('dashboard.html',
                             page_title='仪表盘',
                             stats={
                                 'balance': float(balance),
                                 'monthly_trends': trends_data if trends_data is not None else [],
                                 'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                             })
                             
    except Exception as e:
        current_app.logger.error(f"加载仪表盘页面失败: {str(e)}")
        flash('加载仪表盘数据失败，请稍后重试', 'error')
        return render_template('dashboard.html',
                             page_title='仪表盘',
                             stats={
                                 'balance': 0,
                                 'monthly_trends': [],
                                 'last_updated': None
                             }) 