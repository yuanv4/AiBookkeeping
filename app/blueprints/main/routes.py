# app/main/routes.py
from flask import redirect, url_for, render_template, flash, current_app, request, g
from datetime import datetime # dashboard 中使用
from app.services.core.statistics_service import StatisticsService
from app.services.core.transaction_service import TransactionService
from app.services.analysis.analysis_service import ComprehensiveService as AnalysisService
# from scripts.analyzers.transaction_analyzer import TransactionAnalyzer # 将在需要时实例化

from . import main # 从同级 __init__.py 导入 main 蓝图实例

@main.before_request
def before_request():
    pass

@main.after_request
def after_request(response):
    # 新的 DatabaseService 使用 Flask-SQLAlchemy 自动管理连接，无需手动关闭
    return response

@main.route('/')
def index():
    """首页，重定向到仪表盘"""
    return redirect(url_for('main.dashboard')) # 注意蓝图内部 url_for 要带蓝图名

@main.route('/dashboard')
def dashboard():
    """仪表盘页面"""
    try:
        # 使用专门的服务类获取数据
        # 获取账户余额
        summary_data = StatisticsService.get_balance_summary()
        
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

        # 获取最近交易记录（最多10条）
        recent_transactions_data = TransactionService.get_transactions(limit=10)
        
        recent_transactions = []
        for trans in recent_transactions_data:
            recent_transactions.append({
                'date': trans.date.strftime('%Y-%m-%d'),
                'amount': float(trans.amount),
                'counterparty': trans.counterparty or 'N/A',
                'description': trans.description or 'N/A',
                'account': trans.account.account_number if trans.account else 'N/A'
            })
        
        # 获取月度统计数据
        from datetime import date
        current_date = date.today()
        start_of_month = current_date.replace(day=1)
        
        analysis_service = AnalysisService()
        monthly_report = analysis_service.generate_financial_report(
            start_date=start_of_month,
            end_date=current_date
        )
        
        monthly_income = float(monthly_report['summary'].get('total_income', 0))
        monthly_expense = float(monthly_report['summary'].get('total_expense', 0))
        monthly_net = monthly_income - monthly_expense
        
        # 获取总体统计数据
        all_time_report = analysis_service.generate_financial_report()
        
        income = all_time_report['summary'].get('total_income', 0)
        expense = all_time_report['summary'].get('total_expense', 0)
        net_income = all_time_report['summary'].get('net_amount', 0)
        
        # 获取余额范围和历史数据
        balance_range = StatisticsService.get_balance_range()
        monthly_balance_history = StatisticsService.get_monthly_balance_history(months=12)
        
        months_count = 1
        if all_time_report['summary'].get('start_date') and all_time_report['summary'].get('end_date'):
            try:
                start_date_dt = all_time_report['summary']['start_date']
                end_date_dt = all_time_report['summary']['end_date']
                if isinstance(start_date_dt, str):
                    start_date_dt = datetime.strptime(start_date_dt, '%Y-%m-%d')
                if isinstance(end_date_dt, str):
                    end_date_dt = datetime.strptime(end_date_dt, '%Y-%m-%d')
                months_count = (end_date_dt.year - start_date_dt.year) * 12 + end_date_dt.month - start_date_dt.month + 1
                if months_count < 1:
                    months_count = 1
            except Exception as e:
                current_app.logger.warning(f"计算月份数时出错: {e}")
        
        avg_transaction = 0
        total_transactions = all_time_report['summary'].get('total_transactions', 0)
        if total_transactions > 0:
            total_amount_for_avg = abs(income) + abs(expense)
            avg_transaction = total_amount_for_avg / total_transactions
        
        data = {
            'summary': {
                'account_balance': total_balance,
                'account_balance_list': account_balances,
                'total_income': income,
                'total_expense': expense,
                'net_amount': net_income,
                'income_count': all_time_report['summary'].get('income_count', 0),
                'expense_count': all_time_report['summary'].get('expense_count', 0),
                'total_transactions': all_time_report['summary'].get('total_transactions', 0),
                'start_date': all_time_report['summary'].get('start_date'),
                'end_date': all_time_report['summary'].get('end_date')
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