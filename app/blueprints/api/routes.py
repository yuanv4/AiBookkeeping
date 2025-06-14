from flask import request, jsonify, current_app
from datetime import datetime, timedelta

# 使用统一的财务服务
from app.services import FinancialService

from . import api_bp

@api_bp.route('/data') # API 路径 /api/data
def api_data_route(): #重命名函数
    """API接口获取分析数据"""
    try:
        # 使用新的分析服务

        start_date = request.args.get('start_date', None)
        end_date = request.args.get('end_date', None)
        account_number = request.args.get('account_number', None)
        currency = request.args.get('currency', None)
        account_name = request.args.get('account_name', None)
        
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')
        if not start_date:
            start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
        
        # 转换日期格式
        if start_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        if end_date:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()

        # 获取账户ID（如果指定了账户号码）
        account_id = None
        if account_number:
            from app.models import Account
            account = Account.query.filter_by(account_number=account_number).first()
            if account:
                account_id = account.id

        # 获取分析数据
        financial_service = FinancialService()
        data = financial_service.generate_financial_report(
            account_id=account_id,
            start_date=start_date,
            end_date=end_date
        )
        
        if data and isinstance(data, dict) and 'summary' in data:
            return jsonify({
                'success': True,
                'data': data
            })
        else:
            current_app.logger.warning("API /data: 直接从数据库分析数据失败或未返回有效数据结构")
            return jsonify({
                'success': False,
                'error': '无法分析交易数据'
            }), 400 # Bad request or no data for parameters
    except Exception as e:
        current_app.logger.error(f"API /data 时出错: {e}", exc_info=True)
        # 依赖全局错误处理器返回 500 JSON 响应
        raise