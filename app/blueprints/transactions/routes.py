# 使用重构后的服务层和路由助手
from flask import request, render_template, current_app
from app.utils.decorators import handle_errors
from app.utils import DataUtils, get_transaction_service, get_account_service
from app.utils.route_helpers import get_common_filters, log_route_access, build_filter_summary

from . import transactions_bp

@transactions_bp.route('/') # 蓝图根路径对应 /transactions/
@handle_errors
def transactions_list_route(): # 重命名函数
    """交易记录页面（重构后使用统一的路由助手）"""

    log_route_access('transactions-list', request.args.to_dict())

    # 使用统一的过滤器获取函数
    filters = get_common_filters()

    # 记录过滤条件摘要
    filter_summary = build_filter_summary(filters)
    current_app.logger.info(f"交易查询过滤条件: {filter_summary}")

    # 获取服务实例
    transaction_service = get_transaction_service()
    account_service = get_account_service()

    # 使用优化的查询方法，预加载关联数据避免N+1问题
    all_transactions = transaction_service.get_transactions_with_relations(filters=filters)

    # 使用DataUtils统一转换交易数据
    transactions_data = DataUtils.transactions_to_dict(all_transactions)
    total_transactions = len(all_transactions)

    # 获取账户和货币信息
    accounts = account_service.get_all()
    currencies_for_filter = transaction_service.get_all_currencies() if hasattr(transaction_service, 'get_all_currencies') else ['CNY']

    # 构建当前过滤条件（用于模板显示）
    current_filters = {
        'account_number': filters.get('account_number'),
        'start_date': filters.get('start_date'),
        'end_date': filters.get('end_date'),
        'min_amount': filters.get('min_amount'),
        'max_amount': filters.get('max_amount'),
        'type': filters.get('transaction_type'),
        'counterparty': filters.get('counterparty'),
        'currency': filters.get('currency'),
        'account_name_filter': filters.get('name'),
        'distinct': filters.get('distinct', False)
    }

    return render_template(
        'transactions.html',
        transactions=transactions_data,
        accounts=accounts,
        currencies=currencies_for_filter,
        current_filters=current_filters,
        total_count=total_transactions
    )