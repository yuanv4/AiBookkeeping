import logging
from flask import render_template, request, jsonify
from datetime import date, datetime
from dateutil.relativedelta import relativedelta

from . import main_bp
from app.utils import DataUtils, get_report_service
from app.utils.decorators import handle_errors, validate_date_range
from app.utils.route_helpers import get_service_instances, format_route_response, log_route_access

logger = logging.getLogger(__name__)
def _handle_enhanced_expense_analysis(target_month_str):
    """处理增强模式的支出分析请求

    Args:
        target_month_str: 目标月份字符串

    Returns:
        JSON响应
    """
    # 获取报告服务
    from app.utils import get_report_service
    report_service = get_report_service()

    # 使用DataUtils解析日期
    target_month = DataUtils.parse_date_safe(target_month_str, ['%Y-%m'])
    if not target_month:
        return DataUtils.format_api_response(
            success=False,
            error='目标月份格式错误，请使用 YYYY-MM 格式'
        )

    # 计算目标月份的开始和结束日期
    from calendar import monthrange
    start_date = target_month.replace(day=1)
    last_day = monthrange(target_month.year, target_month.month)[1]
    end_date = target_month.replace(day=last_day)

    # 获取支出构成数据
    expense_composition = report_service.get_expense_composition(start_date, end_date)

    # 转换为前端期望的格式
    enhanced_data = {
        'expense_composition': expense_composition,
        'period': {
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': end_date.strftime('%Y-%m-%d'),
            'month': target_month.strftime('%Y-%m')
        }
    }

    return DataUtils.format_api_response(success=True, data=enhanced_data)


def _handle_expense_analysis(start_date_str, end_date_str):
    """处理支出分析请求

    Args:
        start_date_str: 开始日期字符串
        end_date_str: 结束日期字符串

    Returns:
        JSON响应
    """
    # 获取报告服务
    report_service = get_report_service()

    # 使用DataUtils验证日期范围
    start_date, end_date, error = DataUtils.validate_date_range(start_date_str, end_date_str)
    if error:
        return DataUtils.format_api_response(success=False, error=error)

    # 获取支出构成数据
    data = report_service.get_expense_composition(start_date, end_date)
    return DataUtils.format_api_response(success=True, data={'expense_composition': data})

@main_bp.route('/')
@main_bp.route('/dashboard')
def dashboard():
    """现金流健康仪表盘页面"""
    try:
        # 获取报告服务
        from app.utils import get_report_service
        report_service = get_report_service()

        # 获取仪表盘数据
        dashboard_data = report_service.get_dashboard_data()

        return render_template('dashboard.html',
                             page_title='现金流健康仪表盘',
                             dashboard_data=dashboard_data)

    except Exception as e:
        logger.error(f"加载现金流仪表盘页面失败: {str(e)}")
        # 返回空数据结构
        empty_data = {
            'period': {'start_date': '', 'end_date': '', 'days': 0},
            'net_worth_trend': [],
            'core_metrics': {
                'current_total_assets': 0.0,
                'total_income': 0.0,
                'total_expense': 0.0,
                'net_income': 0.0,
                'income_change_percentage': 0.0,
                'expense_change_percentage': 0.0,
                'net_change_percentage': 0.0,
                'emergency_reserve_months': 0.0
            },
            'cash_flow': [],
            'income_composition': [],
            'expense_composition': []
        }
        return render_template('dashboard.html',
                             page_title='现金流健康仪表盘',
                             dashboard_data=empty_data)

@main_bp.route('/api/dashboard/cash-flow')
@handle_errors
@validate_date_range(['start_date', 'end_date'])
def get_cash_flow_data():
    """获取资金流分析数据的API接口（重构后使用统一装饰器）"""
    log_route_access('cash-flow', request.args.to_dict())

    # 获取验证后的日期参数
    start_date = request.validated_args['start_date']
    end_date = request.validated_args['end_date']

    # 获取服务实例
    services = get_service_instances()
    report_service = services['report_service']

    # 获取期间汇总和月度趋势
    period_summary = report_service.get_period_summary(start_date, end_date)
    monthly_trend = report_service.get_monthly_trend(months=12)

    # 转换为前端期望的现金流数据格式
    data = {
        'period_summary': period_summary,
        'monthly_trend': monthly_trend,
        'cash_flow': monthly_trend  # 月度趋势可以作为现金流数据
    }

    return format_route_response(success=True, data=data)

@main_bp.route('/api/dashboard/expense-analysis')
def get_expense_analysis_data():
    """获取支出分析数据的API接口

    支持两种调用模式：
    1. 传入target_month参数，返回完整的支出结构透视数据
    2. 传入start_date和end_date参数，返回原有的支出分析数据
    """
    try:
        target_month_str = request.args.get('target_month')

        # 新的增强模式：基于目标月份的完整支出分析
        if target_month_str:
            return _handle_enhanced_expense_analysis(target_month_str)

        # 基于日期范围的支出分析
        else:
            start_date_str = request.args.get('start_date')
            end_date_str = request.args.get('end_date')
            return _handle_expense_analysis(start_date_str, end_date_str)

    except Exception as e:
        logger.error(f"获取支出分析数据失败: {str(e)}")
        return DataUtils.format_api_response(success=False, error='服务器内部错误')

@main_bp.route('/category-transactions')
def get_category_transactions():
    """获取指定分类的交易明细（下钻功能）"""
    try:
        # 获取数据服务
        from app.services import DataService
        data_service = DataService()

        # 获取查询参数
        category = request.args.get('category')
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')

        logger.info(f"获取分类交易明细请求: category={category}, start_date={start_date_str}, end_date={end_date_str}")

        if not category:
            return DataUtils.format_api_response(success=False, error='缺少分类参数')

        # 使用DataUtils验证日期范围
        start_date, end_date, error = DataUtils.validate_date_range(start_date_str, end_date_str)
        if error:
            return DataUtils.format_api_response(success=False, error=error)

        # 获取交易明细（服务已通过装饰器注入）
        all_transactions = data_service.get_transactions(
            start_date=start_date,
            end_date=end_date
        )

        # 按分类（交易对手）过滤交易
        transactions = []
        for transaction in all_transactions:
            if transaction.counterparty and category in transaction.counterparty:
                transactions.append({
                    'id': transaction.id,
                    'date': transaction.date.strftime('%Y-%m-%d'),
                    'amount': float(transaction.amount),
                    'description': transaction.description or '',
                    'counterparty': transaction.counterparty or '',
                    'account_name': transaction.account.account_name if transaction.account else ''
                })

        logger.info(f"找到 {len(transactions)} 条交易记录")

        result = {
            'category': category,
            'transactions': transactions,
            'total_count': len(transactions)
        }

        return DataUtils.format_api_response(success=True, data=result)

    except Exception as e:
        current_app.logger.error(f"获取分类交易明细失败: {str(e)}")
        return DataUtils.format_api_response(success=False, error='服务器内部错误')