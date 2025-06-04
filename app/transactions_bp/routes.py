from flask import request, render_template, current_app

from . import transactions_bp

@transactions_bp.route('/') # 蓝图根路径对应 /transactions/
def transactions_list_route(): # 重命名函数
    """交易记录页面"""
    try:
        db_facade = current_app.db_facade
        page = request.args.get('page', 1, type=int)
        # limit 从 app.config 获取
        limit = request.args.get('limit', current_app.config.get('ITEMS_PER_PAGE', 20), type=int)
        
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

        offset = (page - 1) * limit

        query_params_for_db = {
            'account_number_filter': account_number_req,
            'start_date': start_date_req,
            'end_date': end_date_req,
            'min_amount': min_amount_req,
            'max_amount': max_amount_req,
            'transaction_type_filter': transaction_type_req,
            'counterparty_filter': counterparty_req,
            'currency_filter': currency_req,
            'account_name_filter': account_name_req,
            'limit': limit,
            'offset': offset,
            'distinct': distinct_req
        }
        
        transactions_list = db_facade.get_transactions(**query_params_for_db)
        
        count_query_params = {
            'account_number_filter': account_number_req,
            'start_date': start_date_req,
            'end_date': end_date_req,
            'min_amount': min_amount_req,
            'max_amount': max_amount_req,
            'transaction_type_filter': transaction_type_req, 
            'counterparty_filter': counterparty_req, 
            'currency_filter': currency_req,
            'account_name_filter': account_name_req,
            'distinct': distinct_req
        }
        total_transactions = db_facade.get_transactions_count(**count_query_params) 

        accounts = db_facade.get_accounts()
        
        distinct_types_from_db = db_facade.get_distinct_values('transaction_types', 'type_name')
        transaction_types_for_filter = [{'type_name': t} for t in distinct_types_from_db]

        distinct_currencies_from_db = db_facade.get_distinct_values('transactions', 'currency')
        currencies_for_filter = [{'currency_code': c} for c in distinct_currencies_from_db]

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

        if limit <= 0: limit = current_app.config.get('ITEMS_PER_PAGE', 20)
        total_pages = (total_transactions + limit - 1) // limit if total_transactions > 0 else 1

        data_for_template = {
            'transactions': transactions_list,
            'pagination': {
                'page': page,
                'limit': limit,
                'total_items': total_transactions,
                'totalPages': total_pages
            },
            'accounts': accounts,
            'transaction_types': transaction_types_for_filter,
            'currencies': currencies_for_filter,
            'current_filters': current_filters
        }

        return render_template(
            'transactions.html', 
            data=data_for_template,
            total_count=total_transactions
        )
    except Exception as e:
        current_app.logger.error(f"Error in /transactions route: {e}", exc_info=True)
        # 依赖全局错误处理器
        raise # 或者 return render_template('errors/500.html', error_message="无法加载交易记录。 " + str(e)), 500