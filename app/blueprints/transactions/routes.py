# 使用新的服务层
from flask import request, render_template, redirect, url_for, flash, current_app
from datetime import datetime
from app.services.core.account_service import AccountService
from app.services.core.transaction_service import TransactionService
from app.services.core.bank_service import BankService
from app.utils.decorators import handle_errors
from datetime import datetime, timedelta
import logging
from flask import jsonify

from . import transactions_bp

@transactions_bp.route('/') # 蓝图根路径对应 /transactions/
@handle_errors(template='transactions.html', 
               default_data={'data': {'transactions': [], 'accounts': [], 'transaction_types': [], 'currencies': [], 'current_filters': {}}, 'pagination': None, 'total_count': 0}, 
               log_prefix="交易记录页面")
def transactions_list_route(): # 重命名函数
    """交易记录页面"""
    # 使用新的服务层
    transaction_service = TransactionService()
    
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 20, type=int)
    
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

    # 使用Flask-SQLAlchemy分页获取交易记录
    pagination = transaction_service.get_transactions_paginated(
        filters=filters,
        page=page,
        per_page=limit
    )
    
    transactions_data = pagination.items
    total_transactions = pagination.total

    accounts = AccountService.get_all_accounts()
    
    transaction_types_for_filter = TransactionService.get_all_transaction_types()

    currencies_for_filter = TransactionService.get_all_currencies()

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
        'transaction_types': transaction_types_for_filter,
        'currencies': currencies_for_filter,
        'current_filters': current_filters
    }

    return render_template(
        'transactions.html', 
        transactions=transactions_data,
        accounts=accounts,
        transaction_types=transaction_types_for_filter,
        currencies=currencies_for_filter,
        current_filters=current_filters,
        pagination=pagination,
        total_count=total_transactions
    )