"""支出分析路由

提供支出分析页面的路由和API接口
"""

from flask import request, render_template, jsonify, current_app
from datetime import date, datetime
from app.utils.decorators import handle_errors
from . import expense_analysis_bp

@expense_analysis_bp.route('/')
@handle_errors(template='expense_analysis.html', 
               default_data={'overview': {}, 'trends': [], 'patterns': {}, 'categories': []}, 
               log_prefix="支出分析页面")
def expense_analysis_page():
    """支出分析页面"""
    
    # 获取查询参数
    start_date_str = request.args.get('start_date', None)
    end_date_str = request.args.get('end_date', None)
    account_id = request.args.get('account_id', None, type=int)
    
    # 解析日期
    start_date = None
    end_date = None
    if start_date_str:
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        except ValueError:
            pass
    if end_date_str:
        try:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        except ValueError:
            pass
    
    # 获取支出概览数据
    overview_data = current_app.financial_service.get_expense_overview(
        start_date=start_date,
        end_date=end_date,
        account_id=account_id
    )
    
    # 获取支出趋势数据
    trends_data = current_app.financial_service.get_expense_trends(
        months=12,
        account_id=account_id
    )
    
    # 获取支出模式数据
    patterns_data = current_app.financial_service.get_expense_patterns(
        start_date=start_date,
        end_date=end_date,
        account_id=account_id
    )
    
    # 获取支出分类数据
    categories_data = current_app.financial_service.get_expense_categories(
        start_date=start_date,
        end_date=end_date,
        account_id=account_id,
        limit=10
    )
    
    # 获取账户列表
    accounts = current_app.account_service.get_all_accounts()
    
    # 准备模板数据
    template_data = {
        'overview': overview_data,
        'trends': trends_data,
        'patterns': patterns_data,
        'categories': categories_data,
        'accounts': accounts,
        'filters': {
            'start_date': start_date_str,
            'end_date': end_date_str,
            'account_id': account_id
        }
    }
    
    return render_template('expense_analysis.html', **template_data)

# ==================== API路由 ====================

@expense_analysis_bp.route('/api/overview')
def api_expense_overview():
    """获取支出概览数据的API"""
    try:
        # 获取查询参数
        start_date_str = request.args.get('start_date', None)
        end_date_str = request.args.get('end_date', None)
        account_id = request.args.get('account_id', None, type=int)
        
        # 解析日期
        start_date = None
        end_date = None
        if start_date_str:
            try:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            except ValueError:
                return jsonify({'error': '无效的开始日期格式'}), 400
        if end_date_str:
            try:
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            except ValueError:
                return jsonify({'error': '无效的结束日期格式'}), 400
        
        # 获取支出概览数据
        overview_data = current_app.financial_service.get_expense_overview(
            start_date=start_date,
            end_date=end_date,
            account_id=account_id
        )
        
        return jsonify(overview_data)
        
    except Exception as e:
        current_app.logger.error(f"API获取支出概览失败: {e}")
        return jsonify({'error': '获取支出概览数据失败'}), 500

@expense_analysis_bp.route('/api/trends')
def api_expense_trends():
    """获取支出趋势数据的API"""
    try:
        # 获取查询参数
        months = request.args.get('months', 12, type=int)
        account_id = request.args.get('account_id', None, type=int)
        
        # 获取支出趋势数据
        trends_data = current_app.financial_service.get_expense_trends(
            months=months,
            account_id=account_id
        )
        
        return jsonify(trends_data)
        
    except Exception as e:
        current_app.logger.error(f"API获取支出趋势失败: {e}")
        return jsonify({'error': '获取支出趋势数据失败'}), 500

@expense_analysis_bp.route('/api/patterns')
def api_expense_patterns():
    """获取支出模式数据的API"""
    try:
        # 获取查询参数
        start_date_str = request.args.get('start_date', None)
        end_date_str = request.args.get('end_date', None)
        account_id = request.args.get('account_id', None, type=int)
        
        # 解析日期
        start_date = None
        end_date = None
        if start_date_str:
            try:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            except ValueError:
                return jsonify({'error': '无效的开始日期格式'}), 400
        if end_date_str:
            try:
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            except ValueError:
                return jsonify({'error': '无效的结束日期格式'}), 400
        
        # 获取支出模式数据
        patterns_data = current_app.financial_service.get_expense_patterns(
            start_date=start_date,
            end_date=end_date,
            account_id=account_id
        )
        
        return jsonify(patterns_data)
        
    except Exception as e:
        current_app.logger.error(f"API获取支出模式失败: {e}")
        return jsonify({'error': '获取支出模式数据失败'}), 500

@expense_analysis_bp.route('/api/categories')
def api_expense_categories():
    """获取支出分类数据的API"""
    try:
        # 获取查询参数
        start_date_str = request.args.get('start_date', None)
        end_date_str = request.args.get('end_date', None)
        account_id = request.args.get('account_id', None, type=int)
        limit = request.args.get('limit', 10, type=int)
        
        # 解析日期
        start_date = None
        end_date = None
        if start_date_str:
            try:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            except ValueError:
                return jsonify({'error': '无效的开始日期格式'}), 400
        if end_date_str:
            try:
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            except ValueError:
                return jsonify({'error': '无效的结束日期格式'}), 400
        
        # 获取支出分类数据
        categories_data = current_app.financial_service.get_expense_categories(
            start_date=start_date,
            end_date=end_date,
            account_id=account_id,
            limit=limit
        )
        
        return jsonify(categories_data)
        
    except Exception as e:
        current_app.logger.error(f"API获取支出分类失败: {e}")
        return jsonify({'error': '获取支出分类数据失败'}), 500 