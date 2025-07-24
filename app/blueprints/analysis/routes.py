"""财务分析路由

合并仪表盘和支出分析功能的统一路由
提供现金流健康监控与支出分类分析的页面和API端点
"""

import logging
from flask import render_template, jsonify, request, redirect, url_for
from datetime import datetime

from . import analysis_bp
from app.utils.decorators import handle_errors, validate_date_range
from app.utils import get_report_service, DataUtils, get_categories_config, get_valid_category_codes
from app.utils.route_helpers import log_route_access

logger = logging.getLogger(__name__)


@analysis_bp.route('/')
@handle_errors
def index():
    """财务分析主页面 - 合并仪表盘和支出分析功能"""
    try:
        # 获取报告服务
        report_service = get_report_service()
        
        # 获取仪表盘数据
        dashboard_data = report_service.get_dashboard_data()
        
        # 获取分类配置
        try:
            categories_config = get_categories_config()
        except Exception as e:
            logger.error(f"获取分类配置失败: {e}")
            categories_config = {}
        
        return render_template('analysis.html',
                             page_title='财务分析中心',
                             dashboard_data=dashboard_data,
                             categories_config=categories_config)
                             
    except Exception as e:
        logger.error(f"加载财务分析页面失败: {str(e)}")
        # 返回空数据结构
        empty_dashboard_data = {
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
        return render_template('analysis.html',
                             page_title='财务分析中心',
                             dashboard_data=empty_dashboard_data,
                             categories_config={})


@analysis_bp.route('/api/dashboard-data')
@handle_errors
@validate_date_range(['start_date', 'end_date'])
def get_dashboard_data():
    """获取仪表盘数据的API接口"""
    log_route_access('dashboard-data', request.args.to_dict())

    # 获取验证后的日期参数
    start_date = request.validated_args['start_date']
    end_date = request.validated_args['end_date']

    # 获取报告服务实例
    report_service = get_report_service()

    # 获取期间汇总和月度趋势
    period_summary = report_service.get_period_summary(start_date, end_date)
    monthly_trend = report_service.get_monthly_trend(months=12)

    # 转换为前端期望的现金流数据格式
    data = {
        'period_summary': period_summary,
        'monthly_trend': monthly_trend,
        'cash_flow': monthly_trend  # 月度趋势可以作为现金流数据
    }

    return DataUtils.format_api_response(success=True, data=data)


@analysis_bp.route('/api/expense-analysis')
@handle_errors
def get_expense_analysis():
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


def _handle_enhanced_expense_analysis(target_month_str):
    """处理增强的支出分析请求"""
    try:
        # 解析目标月份
        target_month = datetime.strptime(target_month_str, '%Y-%m').date()
    except ValueError:
        return DataUtils.format_api_response(success=False, error='月份格式错误，请使用 YYYY-MM 格式')
    
    # 获取报告服务
    report_service = get_report_service()
    
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
    """处理支出分析请求"""
    # 获取报告服务
    report_service = get_report_service()
    
    # 使用DataUtils验证日期范围
    start_date, end_date, error = DataUtils.validate_date_range(start_date_str, end_date_str)
    if error:
        return DataUtils.format_api_response(success=False, error=error)
    
    # 获取支出构成数据
    data = report_service.get_expense_composition(start_date, end_date)
    return DataUtils.format_api_response(success=True, data={'expense_composition': data})


@analysis_bp.route('/api/merchant-analysis')
@handle_errors
def api_merchant_analysis():
    """获取商户分类支出分析数据API"""
    try:
        from datetime import date, datetime

        # 获取查询参数
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        month_str = request.args.get('month')  # 新增月份参数 (YYYY-MM格式)
        category_filter = request.args.get('category_filter')
        search_term = request.args.get('search_term')

        # 解析日期参数
        start_date = None
        end_date = None

        # 优先处理月份参数
        if month_str:
            try:
                from calendar import monthrange
                month_date = datetime.strptime(month_str, '%Y-%m').date()
                start_date = month_date.replace(day=1)
                last_day = monthrange(month_date.year, month_date.month)[1]
                end_date = month_date.replace(day=last_day)
            except ValueError:
                return jsonify({
                    'success': False,
                    'error': '月份格式错误，请使用 YYYY-MM 格式'
                }), 400
        else:
            # 处理日期范围参数
            if start_date_str:
                try:
                    start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
                except ValueError:
                    return jsonify({
                        'success': False,
                        'error': '开始日期格式错误，请使用 YYYY-MM-DD 格式'
                    }), 400

            if end_date_str:
                try:
                    end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
                except ValueError:
                    return jsonify({
                        'success': False,
                        'error': '结束日期格式错误，请使用 YYYY-MM-DD 格式'
                    }), 400

        # 验证分类筛选参数
        try:
            valid_categories = get_valid_category_codes()
        except Exception as e:
            return DataUtils.format_api_response(
                success=False,
                error=f'无法获取分类配置: {str(e)}'
            ), 500

        if category_filter and category_filter not in valid_categories:
            return DataUtils.format_api_response(
                success=False,
                error=f'无效的分类筛选参数，支持的分类: {", ".join(valid_categories)}'
            ), 400

        # 获取报告服务
        report_service = get_report_service()

        # 根据参数类型选择不同的分析方法
        if month_str:
            # 使用月份分析方法，包含完整历史数据
            analysis_data = report_service.get_month_expense_analysis(
                target_month=month_str,
                category_filter=category_filter,
                search_term=search_term
            )
        else:
            # 使用日期范围分析方法
            analysis_data = report_service.get_expense_analysis_by_category(
                start_date=start_date,
                end_date=end_date,
                category_filter=category_filter,
                search_term=search_term
            )

        # 构建响应数据，包含分析结果和过滤器信息
        response_data = {
            **analysis_data,  # 展开分析数据
            'filters': {
                'month': month_str,
                'start_date': start_date_str,
                'end_date': end_date_str,
                'category_filter': category_filter,
                'search_term': search_term
            }
        }

        return DataUtils.format_api_response(success=True, data=response_data)

    except Exception as e:
        logger.error(f"Error getting merchant analysis data: {e}")
        return DataUtils.format_api_response(
            success=False,
            error=str(e)
        ), 500


@analysis_bp.route('/api/available-months')
@handle_errors
def api_available_months():
    """获取可用月份列表API"""
    try:
        # 获取报告服务
        report_service = get_report_service()

        # 获取有数据的月份列表
        months_data = report_service.get_available_months()

        return DataUtils.format_api_response(success=True, data=months_data)

    except Exception as e:
        logger.error(f"Error getting available months: {e}")
        return DataUtils.format_api_response(
            success=False,
            error=str(e)
        ), 500


@analysis_bp.route('/api/merchant-details/<merchant_name>')
@handle_errors
def api_merchant_details(merchant_name):
    """获取商户详情API"""
    try:
        # 获取报告服务
        report_service = get_report_service()

        # 获取月份参数
        month = request.args.get('month')

        # 获取商户交易详情
        merchant_data = report_service.get_merchant_transactions(merchant_name, month)

        return DataUtils.format_api_response(success=True, data=merchant_data)

    except Exception as e:
        logger.error(f"Error getting merchant details for {merchant_name}: {e}")
        return DataUtils.format_api_response(
            success=False,
            error=str(e)
        ), 500
