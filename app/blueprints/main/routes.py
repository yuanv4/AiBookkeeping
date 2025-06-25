from flask import render_template, current_app, request, jsonify
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from . import main_bp

@main_bp.route('/')
@main_bp.route('/dashboard')
def dashboard():
    """财务健康仪表盘页面"""
    try:
        # 设置默认时间范围为过去30天
        end_date = date.today()
        start_date = end_date - relativedelta(days=30)
        
        # 获取初始数据
        dashboard_data = current_app.financial_service.get_financial_dashboard_data(start_date, end_date)
        
        return render_template('dashboard.html',
                             page_title='财务健康仪表盘',
                             dashboard_data=dashboard_data)
                             
    except Exception as e:
        current_app.logger.error(f"加载财务仪表盘页面失败: {str(e)}")
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
                'net_change_percentage': 0.0
            },
            'cash_flow': [],
            'income_composition': [],
            'expense_composition': []
        }
        return render_template('dashboard.html',
                             page_title='财务健康仪表盘',
                             dashboard_data=empty_data)

@main_bp.route('/dashboard-data')
def get_dashboard_data():
    """获取仪表盘数据的API接口"""
    try:
        # 获取查询参数
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        
        if not start_date_str or not end_date_str:
            return jsonify({'error': '缺少必要的日期参数'}), 400
        
        # 解析日期
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'error': '日期格式错误，请使用 YYYY-MM-DD 格式'}), 400
        
        # 获取数据
        dashboard_data = current_app.financial_service.get_financial_dashboard_data(start_date, end_date)
        
        return jsonify(dashboard_data)
        
    except Exception as e:
        current_app.logger.error(f"获取仪表盘数据失败: {str(e)}")
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
        transactions = current_app.financial_service.get_category_transactions(category, start_date, end_date)
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