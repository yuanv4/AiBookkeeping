from flask import render_template, current_app, request, jsonify
from app.services import FinancialService
from app.utils.decorators import handle_errors
from . import analysis_bp
from datetime import date, timedelta

@analysis_bp.route('/')
@handle_errors(template='analysis/overview.html', default_data={'data': None}, log_prefix="财务分析总览页面")
def analysis_overview():
    """财务分析总览页面"""
    financial_service = FinancialService()
    data = financial_service.get_comprehensive_analysis(12)
    return render_template('analysis/overview.html', data=data)

@analysis_bp.route('/income')
@handle_errors(template='analysis/income.html', 
               default_data={'income_data': None, 'comprehensive_data': None}, 
               log_prefix="收入分析页面")
def income_analysis():
    """收入分析页面"""
    financial_service = FinancialService()
    
    # 获取查询参数
    months = request.args.get('months', 12, type=int)
    account_id = request.args.get('account_id', type=int)
    
    # 计算日期范围
    end_date = date.today()
    start_date = end_date - timedelta(days=months * 30)
    
    # 获取收入分析数据
    income_data = financial_service.analyze_income(start_date, end_date, account_id)
    comprehensive_data = financial_service.get_comprehensive_analysis(months)
    
    return render_template('analysis/income.html', 
                         income_data=income_data,
                         comprehensive_data=comprehensive_data,
                         months=months)

@analysis_bp.route('/expense')
def expense_analysis():
    """支出分析页面"""
    try:
        financial_service = FinancialService()
        
        # 获取查询参数
        months = request.args.get('months', 12, type=int)
        account_id = request.args.get('account_id', type=int)
        
        # 计算日期范围
        end_date = date.today()
        start_date = end_date - timedelta(days=months * 30)
        
        # 获取支出分析数据
        expense_data = financial_service.analyze_expenses(start_date, end_date, account_id)
        comprehensive_data = financial_service.get_comprehensive_analysis(months)
        
        return render_template('analysis/expense.html', 
                             expense_data=expense_data,
                             comprehensive_data=comprehensive_data,
                             months=months)
    except Exception as e:
        current_app.logger.error(f"支出分析页面错误: {str(e)}")
        return render_template('analysis/expense.html', 
                             expense_data=None, 
                             comprehensive_data=None,
                             error="数据加载失败，请稍后重试")

@analysis_bp.route('/cash-flow')
@handle_errors(template='analysis/cash_flow.html', 
               default_data={'cash_flow_data': None, 'comprehensive_data': None}, 
               log_prefix="现金流分析页面")
def cash_flow_analysis():
    """现金流分析页面"""
    financial_service = FinancialService()
    
    # 获取查询参数
    months = request.args.get('months', 12, type=int)
    account_id = request.args.get('account_id', type=int)
    
    # 计算日期范围
    end_date = date.today()
    start_date = end_date - timedelta(days=months * 30)
    
    # 获取现金流分析数据
    cash_flow_data = financial_service.analyze_cash_flow(start_date, end_date, account_id)
    comprehensive_data = financial_service.get_comprehensive_analysis(months)
    
    return render_template('analysis/cash_flow.html', 
                         cash_flow_data=cash_flow_data,
                         comprehensive_data=comprehensive_data,
                         months=months)

@analysis_bp.route('/health')
@handle_errors(template='analysis/health.html', 
               default_data={'health_data': None, 'comprehensive_data': None}, 
               log_prefix="财务健康页面")
def financial_health():
    """财务健康状况页面"""
    financial_service = FinancialService()
    
    # 获取查询参数
    months = request.args.get('months', 12, type=int)
    
    # 获取财务健康数据
    health_data = financial_service.analyze_financial_health(months)
    comprehensive_data = financial_service.get_comprehensive_analysis(months)
    
    return render_template('analysis/health.html', 
                         health_data=health_data,
                         comprehensive_data=comprehensive_data,
                         months=months)

# API 端点
@analysis_bp.route('/api/summary')
@handle_errors(default_data={}, log_prefix="财务摘要API")
def api_summary():
    """获取财务摘要API"""
    financial_service = FinancialService()
    months = request.args.get('months', 6, type=int)
    summary = financial_service.generate_summary(months)
    return jsonify({'success': True, 'data': summary})

@analysis_bp.route('/api/comprehensive')
@handle_errors(default_data={}, log_prefix="综合分析API")
def api_comprehensive():
    """获取综合分析API"""
    financial_service = FinancialService()
    months = request.args.get('months', 12, type=int)
    data = financial_service.get_comprehensive_analysis(months)
    return jsonify({'success': True, 'data': data})