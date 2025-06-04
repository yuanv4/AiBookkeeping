# app/main/routes.py
from flask import redirect, url_for, render_template, flash, current_app, request, g
from datetime import datetime # dashboard 中使用
# from scripts.analyzers.transaction_analyzer import TransactionAnalyzer # 将在需要时实例化

from . import main # 从同级 __init__.py 导入 main 蓝图实例

@main.before_request
def before_request():
    g.db_facade = current_app.db_facade

@main.after_request
def after_request(response):
    if hasattr(g, 'db_facade'):
        g.db_facade.db_connection.close_connection()
    return response

@main.route('/')
def index():
    """首页，重定向到仪表盘"""
    return redirect(url_for('main.dashboard')) # 注意蓝图内部 url_for 要带蓝图名

@main.route('/dashboard')
def dashboard():
    """仪表盘页面"""
    try:
        # 从 g 对象获取 db_facade，确保每个请求使用独立的连接
        db_facade = g.db_facade
        # 获取账户余额
        summary_data = db_facade.get_balance_summary()
        
        # 检查 summary_data 是否为 None 或空，以避免后续错误
        if not summary_data:
            current_app.logger.warning("获取余额汇总数据失败。")
            # 提供默认值或重定向到错误页面
            summary_data = {'net_balance': 0.0, 'account_balances': {}}

        total_balance = summary_data.get('net_balance', 0.0)
        
        # 将 account_balances 从字典的值转换为列表
        account_balances_raw = summary_data.get('account_balances', {}).values()
        
        account_balances = []
        for acc_data in account_balances_raw:
            account_balances.append({
                'account': acc_data.get('account_number', 'N/A'),
                'bank': acc_data.get('bank_name', 'N/A'), # Assuming bank_name might be added to acc_data in future or fetched separately
                'balance': float(acc_data.get('balance', 0) or 0),
                'update_date': acc_data.get('balance_date', 'N/A') # Assuming balance_date might be added to acc_data in future or fetched separately
            })

        recent_transactions = db_facade.get_transactions(limit=10, distinct=True)
        
        db_stats = db_facade.get_general_statistics()
        balance_range = db_facade.get_balance_range()
        monthly_balance_history = db_facade.get_monthly_balance_history(months=12)
        
        income = db_stats.get('total_income', 0)
        expense = db_stats.get('total_expense', 0)
        net_income = db_stats.get('net_amount', 0)
        
        months_count = 1
        if db_stats.get('min_date') and db_stats.get('max_date'):
            try:
                start_date_dt = datetime.strptime(db_stats['min_date'], '%Y-%m-%d')
                end_date_dt = datetime.strptime(db_stats['max_date'], '%Y-%m-%d')
                months_count = (end_date_dt.year - start_date_dt.year) * 12 + end_date_dt.month - start_date_dt.month + 1
                if months_count < 1:
                    months_count = 1
            except Exception as e:
                current_app.logger.warning(f"计算月份数时出错: {e}")
        
        avg_transaction = 0
        if db_stats.get('total_transactions', 0) > 0:
            total_amount_for_avg = abs(income) + abs(expense) # 原代码中使用 abs(income)
            avg_transaction = total_amount_for_avg / db_stats['total_transactions']
        
        data = {
            'summary': {
                'account_balance': total_balance,
                'account_balance_list': account_balances,
                'total_income': income,
                'total_expense': expense,
                'net_amount': net_income,
                'income_count': db_stats.get('income_count', 0),
                'expense_count': db_stats.get('expense_count', 0),
                'total_transactions': db_stats.get('total_transactions', 0),
                'start_date': db_stats.get('min_date'),
                'end_date': db_stats.get('max_date')
            },
            'transactions': recent_transactions,
            'charts': {
                'balance_history': monthly_balance_history,
                'monthly_labels': [], 'monthly_income': [], 'monthly_expense': [], 'monthly_net': [],
                'income_source_labels': [], 'income_source_values': [],
                'expense_category_labels': [], 'expense_category_values': []
            },
            'max_balance': balance_range.get('max_balance', 0),
            'min_balance': balance_range.get('min_balance', 0),
            'months_count': months_count,
            'avg_transaction': avg_transaction
        }
        
        if recent_transactions:
            current_app.logger.info(f"仪表盘显示 {len(recent_transactions)} 条近期交易")
        else:
            current_app.logger.warning("没有近期交易数据可显示")
            
        current_app.logger.info(f"仪表盘总余额: {total_balance}")
        current_app.logger.info(f"余额范围: 最高 = {data['max_balance']}, 最低 = {data['min_balance']}")
        
        return render_template('dashboard.html', data=data)
        
    except Exception as e:
        current_app.logger.error(f"仪表盘加载出错: {e}", exc_info=True)
        flash(f'加载仪表盘数据时出错: {str(e)}')
        # 依赖全局错误处理器处理模板渲染和状态码
        # 为了确保至少有一个响应，这里可以简单地重新抛出，让全局处理器捕获
        # 或者，如果全局处理器不能很好地处理这种情况（例如，它只渲染500页面而不带flash消息）
        # 可以在这里渲染一个带有错误消息的dashboard，或者重定向
        # 保持简单，依赖全局处理器：
        raise # 或者 return render_template('errors/500.html', error=str(e)), 500