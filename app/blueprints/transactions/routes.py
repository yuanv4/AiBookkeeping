# 使用新的服务层
from flask import request, render_template, current_app
from app.utils.decorators import handle_errors

from . import transactions_bp

# 使用新的统一服务架构

@transactions_bp.route('/') # 蓝图根路径对应 /transactions/
@handle_errors(template='transactions.html',
               default_data={'data': {'transactions': [], 'accounts': [], 'currencies': [], 'current_filters': {}}, 'total_count': 0},
               log_prefix="交易记录页面")
def transactions_list_route(): # 重命名函数
    """交易记录页面"""

    account_number_req = request.args.get('account_number', None)
    start_date_req = request.args.get('start_date', None)
    end_date_req = request.args.get('end_date', None)
    min_amount_req = request.args.get('min_amount', None, type=float)
    max_amount_req = request.args.get('max_amount', None, type=float)
    transaction_type_req = request.args.get('type', None)
    counterparty_req = request.args.get('counterparty', None)
    currency_req = request.args.get('currency', None)
    account_name_req = request.args.get('account_name_filter', None)
    distinct_req = request.args.get('distinct', False, type=lambda v: v.lower() == 'true')

    # 构建查询过滤器
    filters = {}
    if account_number_req:
        filters['account_number'] = account_number_req
    if start_date_req:
        filters['start_date'] = start_date_req
    if end_date_req:
        filters['end_date'] = end_date_req
    if min_amount_req is not None:
        filters['min_amount'] = min_amount_req
    if max_amount_req is not None:
        filters['max_amount'] = max_amount_req
    if transaction_type_req:
        filters['transaction_type'] = transaction_type_req
    if counterparty_req:
        filters['counterparty'] = counterparty_req
    if currency_req:
        filters['currency'] = currency_req
    if account_name_req:
        filters['account_name'] = account_name_req

    # 使用 DataService 获取所有交易记录（不分页）
    all_transactions = current_app.data_service.get_transactions_filtered(filters=filters)

    transactions_data = [t.to_dict() for t in all_transactions]
    total_transactions = len(all_transactions)

    # 使用 DataService 获取账户和货币信息
    accounts = current_app.data_service.get_all_accounts()
    currencies_for_filter = current_app.data_service.get_all_currencies()

    current_filters = {
        'account_number': account_number_req,
        'start_date': start_date_req,
        'end_date': end_date_req,
        'min_amount': min_amount_req,
        'max_amount': max_amount_req,
        'type': transaction_type_req,
        'counterparty': counterparty_req,
        'currency': currency_req,
        'account_name_filter': account_name_req,
        'distinct': distinct_req
    }

    data_for_template = {
        'transactions': transactions_data,
        'accounts': accounts,
        'currencies': currencies_for_filter,
        'current_filters': current_filters
    }

    return render_template(
        'transactions.html',
        transactions=transactions_data,
        accounts=accounts,
        currencies=currencies_for_filter,
        current_filters=current_filters,
        total_count=total_transactions
    )