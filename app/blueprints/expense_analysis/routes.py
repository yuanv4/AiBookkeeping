"""支出分析路由

提供支出分析页面和API端点
"""

from flask import render_template, jsonify, current_app
from . import expense_analysis_bp
from app.utils.decorators import handle_errors
from app.utils import get_report_service, DataUtils
import logging

logger = logging.getLogger(__name__)


@expense_analysis_bp.route('/')
@handle_errors
def index():
    """支出分析主页面"""
    return render_template('expense_analysis.html')



@expense_analysis_bp.route('/api/merchant-analysis')
@handle_errors
def api_merchant_analysis():
    """获取商户分类支出分析数据API"""
    try:
        from flask import request
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
        valid_categories = ['dining', 'transport', 'shopping', 'services', 'healthcare', 'finance', 'other']
        if category_filter and category_filter not in valid_categories:
            return DataUtils.format_api_response(
                success=False,
                error=f'无效的分类筛选参数，支持的分类: {", ".join(valid_categories)}'
            ), 400

        # 获取报告服务
        report_service = get_report_service()

        # 获取商户分类服务
        category_service = report_service.category_service

        # 根据参数类型选择不同的分析方法
        if month_str:
            # 使用月份分析方法，包含完整历史数据
            analysis_data = category_service.get_month_expense_analysis(
                target_month=month_str,
                category_filter=category_filter,
                search_term=search_term
            )
        else:
            # 使用日期范围分析方法
            analysis_data = category_service.get_expense_analysis_by_category(
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




@expense_analysis_bp.route('/api/available-months')
@handle_errors
def api_available_months():
    """获取可用月份列表API"""
    try:
        # 获取报告服务
        report_service = get_report_service()

        # 获取商户分类服务
        category_service = report_service.category_service

        # 获取有数据的月份列表
        months_data = category_service.get_available_months()

        return DataUtils.format_api_response(success=True, data=months_data)

    except Exception as e:
        logger.error(f"Error getting available months: {e}")
        return DataUtils.format_api_response(
            success=False,
            error=str(e)
        ), 500


@expense_analysis_bp.route('/api/merchant-details/<merchant_name>')
@handle_errors
def api_merchant_details(merchant_name):
    """获取商户详情API"""
    try:
        # 获取报告服务
        report_service = get_report_service()

        # 获取商户分类服务
        category_service = report_service.category_service

        # 获取商户交易详情
        merchant_data = category_service.get_merchant_transactions(merchant_name)

        return DataUtils.format_api_response(success=True, data=merchant_data)

    except Exception as e:
        logger.error(f"Error getting merchant details for {merchant_name}: {e}")
        return DataUtils.format_api_response(
            success=False,
            error=str(e)
        ), 500
