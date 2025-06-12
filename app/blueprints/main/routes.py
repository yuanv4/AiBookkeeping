# app/main/routes.py
from flask import Blueprint
from flask import redirect, url_for, render_template, flash, current_app, request, g
from datetime import datetime, date # dashboard 中使用
from app.services.analysis import AnalyzerFactory
from app.services.analysis.analyzers.analyzer_context import AnalyzerContext
from app.services.analysis.analyzers.single_balance_analyzer import BalanceAnalyzer
from app.services.core.transaction_service import TransactionService
from app.services.analysis.analysis_service import ComprehensiveService as AnalysisService
# from scripts.analyzers.transaction_analyzer import TransactionAnalyzer # 将在需要时实例化
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta

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
def dashboard():
    """仪表盘页面"""
    try:
        # 使用专门的服务类获取数据
        # 获取账户余额
        today = date.today()
        # 创建分析器上下文和余额分析器
        from app.models import db
        context = AnalyzerContext(
            db_session=db.session,
            user_id=1,  # 默认用户ID
            start_date=datetime.combine(today, datetime.min.time()),
            end_date=datetime.combine(today, datetime.max.time())
        )
        factory = AnalyzerFactory(context)
        # 计算分析日期范围（最近12个月）
        end_date = date.today()
        start_date = end_date - relativedelta(months=12)
        balance_analyzer = factory.create_typed_analyzer(BalanceAnalyzer, start_date=start_date, end_date=end_date)
        summary_data = balance_analyzer.get_balance_summary()
        
        # 检查 summary_data 是否为 None 或空，以避免后续错误
        if not summary_data:
            current_app.logger.warning("获取余额汇总数据失败。")
            # 提供默认值或重定向到错误页面
            summary_data = {
                'net_balance': 0.0, 
                'account_balances': {},
                'net_amount': 0.0,
                'account_balance': 0.0,
                'account_balance_list': []
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
        
        # 获取余额范围和历史数据
        balance_range = balance_analyzer.get_balance_range()
        monthly_balance_history = balance_analyzer.get_monthly_history(months=12)
        
        months_count = 1
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
        
        # 准备图表数据
        chart_data = {
            'balance_history': monthly_balance_history,  # 添加balance_history字段供模板使用
            'monthly_balance_history': monthly_balance_history,
            'income_expense': {
                'income': float(income),
                'expense': float(abs(expense)),
                'net': float(net_income)
            },
            'monthly_averages': {
                'income': float(monthly_avg_income),
                'expense': float(monthly_avg_expense),
                'net': float(monthly_avg_net)
            }
        }
        
        return render_template('dashboard.html', 
                             summary_data=summary_data,
                             chart_data=chart_data,
                             all_time_report=all_time_report)
    
    except Exception as e:
        current_app.logger.error(f"仪表盘页面加载失败: {e}")
        flash(f"加载仪表盘时发生错误: {str(e)}", 'error')
        # 提供默认的数据结构以避免模板错误
        default_chart_data = {
            'balance_history': [],
            'monthly_balance_history': [],
            'income_expense': {'income': 0.0, 'expense': 0.0, 'net': 0.0},
            'monthly_averages': {'income': 0.0, 'expense': 0.0, 'net': 0.0}
        }
        default_summary_data = {
            'net_balance': 0.0, 
            'account_balances': {},
            'account_balance_list': [],
            'net_amount': 0.0
        }
        return render_template('dashboard.html', 
                             summary_data=default_summary_data,
                             chart_data=default_chart_data,
                             all_time_report={'summary': {}})

        # 为了确保至少有一个响应，这里可以简单地重新抛出，让全局处理器捕获
        # 或者，如果全局处理器不能很好地处理这种情况（例如，它只渲染500页面而不带flash消息）
        # 可以在这里渲染一个带有错误消息的dashboard，或者重定向
        # 保持简单，依赖全局处理器：
        raise # 或者 return render_template('errors/500.html', error=str(e)), 500