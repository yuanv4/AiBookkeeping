from flask import render_template, current_app, request, jsonify
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from . import main_bp


def _parse_target_month(target_month_str):
    """解析目标月份字符串

    Args:
        target_month_str: 目标月份字符串 (格式: YYYY-MM)

    Returns:
        解析后的日期对象

    Raises:
        ValueError: 如果日期格式错误
    """
    return datetime.strptime(target_month_str, '%Y-%m').date()


def _convert_enhanced_data_to_dict(enhanced_data):
    """将增强的支出分析数据转换为JSON可序列化的字典

    Args:
        enhanced_data: 增强的支出分析数据对象

    Returns:
        JSON可序列化的字典
    """
    return {
        'target_month': enhanced_data.target_month,
        'total_expense': enhanced_data.total_expense,
        'expense_trend': [
            {'date': trend.date, 'value': trend.value, 'category': trend.category}
            for trend in enhanced_data.expense_trend
        ],
        'recurring_expenses': [
            {
                'category': recurring.category,
                'total_amount': recurring.total_amount,
                'amount': recurring.amount,
                'frequency': recurring.frequency,
                'confidence_score': recurring.confidence_score,
                'last_occurrence': recurring.last_occurrence,
                'count': recurring.count,
                'combination_key': recurring.combination_key
            }
            for recurring in enhanced_data.recurring_expenses
        ],
        'flexible_composition': [
            {
                'name': comp.name,
                'amount': comp.amount,
                'percentage': comp.percentage,
                'count': comp.count
            }
            for comp in enhanced_data.flexible_composition
        ],
        'top_expense_categories': [],
        'recurring_transactions': enhanced_data.recurring_transactions or [],
        'flexible_transactions': enhanced_data.flexible_transactions or []
    }


def _handle_enhanced_expense_analysis(target_month_str):
    """处理增强模式的支出分析请求

    Args:
        target_month_str: 目标月份字符串

    Returns:
        JSON响应
    """
    try:
        target_month = _parse_target_month(target_month_str)
        enhanced_data = current_app.reporting_service.get_expense_analysis_data(target_month)
        return jsonify(_convert_enhanced_data_to_dict(enhanced_data))
    except ValueError:
        return jsonify({'error': '目标月份格式错误，请使用 YYYY-MM 格式'}), 400


def _handle_legacy_expense_analysis(start_date_str, end_date_str):
    """处理兼容模式的支出分析请求

    Args:
        start_date_str: 开始日期字符串
        end_date_str: 结束日期字符串

    Returns:
        JSON响应
    """
    if not start_date_str or not end_date_str:
        return jsonify({'error': '缺少必要的日期参数，请提供 target_month 或 start_date+end_date'}), 400

    start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
    end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()

    data = current_app.reporting_service.get_expense_analysis_data(start_date, end_date)
    return jsonify(data)

@main_bp.route('/')
@main_bp.route('/dashboard')
def dashboard():
    """现金流健康仪表盘页面"""
    try:
        # 获取初始数据
        dashboard_data = current_app.reporting_service.get_initial_dashboard_data()
        
        return render_template('dashboard.html',
                             page_title='现金流健康仪表盘',
                             dashboard_data=dashboard_data)
                             
    except Exception as e:
        current_app.logger.error(f"加载现金流仪表盘页面失败: {str(e)}")
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
def get_cash_flow_data():
    """获取资金流分析数据的API接口"""
    try:
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        
        if not start_date_str or not end_date_str:
            return jsonify({'error': '缺少必要的日期参数'}), 400
        
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        
        data = current_app.reporting_service.get_cash_flow_data(start_date, end_date)
        
        return jsonify(data)
        
    except ValueError:
        return jsonify({'error': '日期格式错误，请使用 YYYY-MM-DD 格式'}), 400
    except Exception as e:
        current_app.logger.error(f"获取资金流数据失败: {str(e)}")
        return jsonify({'error': '服务器内部错误'}), 500

@main_bp.route('/api/dashboard/expense-analysis')
def get_expense_analysis_data():
    """获取支出分析数据的API接口

    支持两种调用模式：
    1. 增强模式：传入target_month参数，返回完整的支出结构透视数据
    2. 兼容模式：传入start_date和end_date参数，返回原有的支出分析数据
    """
    try:
        target_month_str = request.args.get('target_month')

        # 新的增强模式：基于目标月份的完整支出分析
        if target_month_str:
            return _handle_enhanced_expense_analysis(target_month_str)

        # 原有的兼容模式：基于日期范围的支出分析
        else:
            start_date_str = request.args.get('start_date')
            end_date_str = request.args.get('end_date')
            return _handle_legacy_expense_analysis(start_date_str, end_date_str)

    except ValueError:
        return jsonify({'error': '日期格式错误，请使用正确的日期格式'}), 400
    except Exception as e:
        current_app.logger.error(f"获取支出分析数据失败: {str(e)}")
        return jsonify({'error': '服务器内部错误'}), 500

@main_bp.route('/category-transactions')
def get_category_transactions():
    """获取指定分类的交易明细（下钻功能）"""
    try:
        # 获取查询参数
        category = request.args.get('category')
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        
        current_app.logger.info(f"获取分类交易明细请求: category={category}, start_date={start_date_str}, end_date={end_date_str}")
        
        if not all([category, start_date_str, end_date_str]):
            return jsonify({'error': '缺少必要参数'}), 400
        
        # 解析日期
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'error': '日期格式错误'}), 400
        
        # 获取交易明细
        transactions = current_app.reporting_service.get_category_transactions(category, start_date, end_date)
        current_app.logger.info(f"找到 {len(transactions)} 条交易记录")
        
        result = {
            'category': category,
            'transactions': transactions,
            'total_count': len(transactions)
        }
        
        return jsonify(result)
        
    except Exception as e:
        current_app.logger.error(f"获取分类交易明细失败: {str(e)}")
        return jsonify({'error': '服务器内部错误'}), 500