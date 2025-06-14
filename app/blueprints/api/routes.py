from flask import jsonify, request, current_app
from . import api_bp
from app.models import Account
from app.services.financial_service import FinancialService
from app.utils.decorators import handle_errors
from datetime import date, datetime

from . import api_bp

@api_bp.route('/data')
@handle_errors
def get_data():
    """获取财务数据API"""
    # 获取查询参数
    account_number = request.args.get('account')
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    
    # 解析日期
    start_date = None
    end_date = None
    
    if start_date_str:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
    if end_date_str:
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
    
    # 获取账户ID
    account_id = None
    if account_number:
        account = Account.query.filter_by(account_number=account_number).first()
        if account:
            account_id = account.id
        else:
            return jsonify({'error': '账户不存在'}), 404
    
    # 获取财务数据
    financial_service = FinancialService()
    data = financial_service.get_comprehensive_analysis(
        account_id=account_id,
        start_date=start_date,
        end_date=end_date
    )
    
    return jsonify(data)