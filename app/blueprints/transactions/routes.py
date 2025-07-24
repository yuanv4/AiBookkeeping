# 使用重构后的服务层和路由助手
from flask import request, render_template, current_app, jsonify
from app.utils.decorators import handle_errors
from app.utils import DataUtils, get_transaction_service, get_account_service, get_categories_config, get_category_service
from app.utils.route_helpers import get_common_filters, log_route_access, build_filter_summary
from app.models import Transaction, db
from app.services.category_service import CATEGORIES
import logging

from . import transactions_bp

logger = logging.getLogger(__name__)

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
    all_transactions = transaction_service.get_transactions_filtered(filters=filters, include_relations=True)

    # 使用DataUtils统一转换交易数据
    transactions_data = DataUtils.transactions_to_dict(all_transactions)
    total_transactions = len(all_transactions)

    # 获取账户和货币信息
    accounts = account_service.get_all()
    currencies_for_filter = transaction_service.get_all_currencies() if hasattr(transaction_service, 'get_all_currencies') else ['CNY']

    # 获取分类配置信息
    categories_config = get_categories_config()

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
        total_count=total_transactions,
        categories_config=categories_config
    )


@transactions_bp.route('/api/transactions/<int:transaction_id>/category', methods=['PUT'])
@handle_errors
def update_transaction_category(transaction_id):
    """更新交易分类并学习用户规则

    Args:
        transaction_id: 交易ID

    Request Body:
        {
            "category": "dining"  // 新的分类代码
        }

    Returns:
        {
            "success": true,
            "data": {
                "updated_transactions": 5,  // 更新的交易数量
                "merchant_name": "麦当劳",
                "old_category": "other",
                "new_category": "dining"
            }
        }
    """
    data = request.get_json()
    new_category = data.get('category') if data else None

    # 验证请求数据
    if not new_category:
        return DataUtils.format_api_response(False, error='缺少分类参数')

    # 验证分类有效性
    if new_category not in CATEGORIES:
        return DataUtils.format_api_response(False, error='无效的分类代码')

    # 获取交易记录
    transaction = Transaction.query.get_or_404(transaction_id)
    old_category = transaction.category
    merchant_name = transaction.counterparty

    if not merchant_name:
        return DataUtils.format_api_response(False, error='交易缺少商户信息')

    # 获取分类服务
    category_service = get_category_service()

    # 保存用户规则
    if not category_service.update_merchant_category(merchant_name, new_category):
        return DataUtils.format_api_response(False, error='保存用户规则失败')

    # 批量更新同商户的所有交易
    updated_count = Transaction.query.filter_by(counterparty=merchant_name).update({
        'category': new_category
    })

    db.session.commit()

    logger.info(f"用户更新分类: {merchant_name} {old_category} -> {new_category}, 影响 {updated_count} 笔交易")

    return DataUtils.format_api_response(True, data={
        'updated_transactions': updated_count,
        'merchant_name': merchant_name,
        'old_category': old_category,
        'new_category': new_category
    })