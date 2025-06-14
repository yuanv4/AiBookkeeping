# app/main/routes.py
from flask import redirect, url_for, render_template, flash, current_app
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta
from app.services import FinancialService, TransactionService
from app.utils.decorators import handle_errors

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
    return redirect(url_for('main.dashboard'))

@main.route('/dashboard')
@handle_errors
def dashboard():
    """仪表盘页面"""
    # 使用统一的财务服务获取数据
    financial_service = FinancialService()
    
    # 获取综合分析数据
    analysis_result = financial_service.get_comprehensive_analysis(12)
    
    # 从综合分析结果中提取数据
    if analysis_result:
        income_summary = analysis_result.get('income_summary', {})
        expense_summary = analysis_result.get('expense_summary', {})
        
        # 计算净储蓄
        total_income = income_summary.get('total_income', 0.0)
        total_expense = expense_summary.get('total_expense', 0.0)
        net_saving = total_income - total_expense
        
        summary_data = {
            'net_balance': net_saving,
            'account_balances': {},  # 暂时为空，后续可以从账户服务获取
            'net_amount': net_saving,
            'account_balance': net_saving,
            'account_balance_list': [],  # 暂时为空
            'monthly_income': income_summary.get('avg_monthly_income', 0.0),
            'monthly_expense': expense_summary.get('avg_monthly_expense', 0.0),
            'monthly_net': income_summary.get('avg_monthly_income', 0.0) - expense_summary.get('avg_monthly_expense', 0.0),
        }
    else:
        summary_data = None
    
    # 检查 summary_data 是否为 None 或空，以避免后续错误
    if not summary_data:
        current_app.logger.warning("获取余额汇总数据失败。")
        # 提供默认值或重定向到错误页面
        summary_data = {
            'net_balance': 0.0, 
            'account_balances': {},
            'net_amount': 0.0,
            'account_balance': 0.0,
            'account_balance_list': [],
            'monthly_income': 0.0,
            'monthly_expense': 0.0,
            'monthly_net': 0.0,
            'transaction_count': 0
        }

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
        
    # 更新summary_data以包含模板需要的字段
    summary_data['account_balance'] = total_balance
    summary_data['account_balance_list'] = account_balances
    summary_data['net_amount'] = total_balance

    # 获取最近交易记录（最多10条）
    recent_transactions_data = TransactionService.get_transactions(limit=10)
    
    # 获取交易总数
    transaction_count = len(recent_transactions_data) if recent_transactions_data else 0
    
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
    current_date = date.today()
    start_of_month = current_date.replace(day=1)
    
    monthly_report = financial_service.generate_financial_report(
        start_date=start_of_month,
        end_date=current_date
    )
    
    monthly_income = float(monthly_report['summary'].get('total_income', 0))
    monthly_expense = float(monthly_report['summary'].get('total_expense', 0))
    monthly_net = monthly_income - monthly_expense
    
    # 将月度统计数据添加到summary_data中
    summary_data['monthly_income'] = monthly_income
    summary_data['monthly_expense'] = monthly_expense
    summary_data['monthly_net'] = monthly_net
    summary_data['transaction_count'] = transaction_count
    
    # 获取总体统计数据
    all_time_report = financial_service.generate_financial_report()
    
    # 检查 all_time_report 是否为 None 或空
    if not all_time_report or 'summary' not in all_time_report:
        current_app.logger.warning("获取综合报告失败。")
        all_time_report = {
            'summary': {
                'total_income': 0.0,
                'total_expense': 0.0,
                'net_amount': 0.0,
                'start_date': None,
                'end_date': None
            }
        }
    
    # 从 all_time_report 中提取数据
    income = all_time_report['summary'].get('total_income', 0)
    expense = all_time_report['summary'].get('total_expense', 0)
    net_income = all_time_report['summary'].get('net_amount', 0)
    
    # 获取余额范围和历史数据（使用财务服务的月度趋势数据）
    monthly_trends = analysis_result.get('monthly_trends', [])
    monthly_balance_history = [{
        'month': f"{trend['year']}-{trend['month']:02d}",
        'balance': trend['net_amount']
    } for trend in monthly_trends]
    
    months_count = 1
    
    # 初始化默认的图表数据
    chart_data = {
        'balance_history': monthly_balance_history,
        'monthly_balance_history': monthly_balance_history,
        'income_expense': {
            'income': float(income),
            'expense': float(abs(expense)),
            'net': float(net_income)
        },
        'monthly_averages': {
            'income': 0.0,
            'expense': 0.0,
            'net': 0.0
        }
    }
    
    if all_time_report['summary'].get('start_date') and all_time_report['summary'].get('end_date'):
        try:
            start_date_dt = all_time_report['summary']['start_date']
            end_date_dt = all_time_report['summary']['end_date']
            if isinstance(start_date_dt, str):
                start_date_dt = datetime.strptime(start_date_dt, '%Y-%m-%d')
            if isinstance(end_date_dt, str):
                end_date_dt = datetime.strptime(end_date_dt, '%Y-%m-%d')
            
            # 计算月份差
            months_count = (end_date_dt.year - start_date_dt.year) * 12 + (end_date_dt.month - start_date_dt.month) + 1
            months_count = max(1, months_count)  # 至少1个月
        except Exception as e:
            current_app.logger.warning(f"计算月份数时出错: {e}")
            months_count = 1
        
        # 计算月平均值
        monthly_avg_income = income / months_count if months_count > 0 else 0
        monthly_avg_expense = abs(expense) / months_count if months_count > 0 else 0
        monthly_avg_net = net_income / months_count if months_count > 0 else 0
        
        # 更新图表数据的月平均值
        chart_data['monthly_averages'] = {
            'income': float(monthly_avg_income),
            'expense': float(monthly_avg_expense),
            'net': float(monthly_avg_net)
        }
        
    return render_template('dashboard.html', 
                         summary_data=summary_data,
                         chart_data=chart_data,
                         all_time_report=all_time_report)