"""商户分类管理路由

提供商户分类管理页面和API端点
"""

from flask import render_template, request
from app.utils.decorators import handle_errors
from app.utils import DataUtils, get_category_service, get_categories_config
from app.models import Transaction, db
from sqlalchemy import func
import logging

from . import merchant_categories_bp

logger = logging.getLogger(__name__)


@merchant_categories_bp.route('/')
def index():
    """商户分类管理主页面"""
    return render_template('merchant_categories.html',
                         page_title='商户分类管理',
                         categories_config=get_categories_config())


@merchant_categories_bp.route('/api/uncategorized-merchants')
@handle_errors
def get_uncategorized_merchants():
    """获取未分类商户列表API"""
    # 查询所有未分类交易的商户统计
    merchants_data = Transaction.query.filter_by(category='uncategorized').with_entities(
        Transaction.counterparty.label('merchant_name'),
        func.count(Transaction.id).label('transaction_count'),
        func.sum(Transaction.amount).label('total_amount'),
        func.max(Transaction.date).label('latest_date')
    ).group_by(Transaction.counterparty).order_by(
        func.count(Transaction.id).desc()
    ).all()

    # 转换为字典格式
    merchants_list = []
    for merchant in merchants_data:
        merchants_list.append({
            'merchant_name': merchant.merchant_name,
            'transaction_count': merchant.transaction_count,
            'total_amount': float(merchant.total_amount),
            'latest_date': merchant.latest_date.strftime('%Y-%m-%d'),
            'category': 'uncategorized'
        })

    return DataUtils.format_api_response(True, data=merchants_list)


@merchant_categories_bp.route('/api/merchant/<merchant_name>/category', methods=['PUT'])
@handle_errors
def update_merchant_category(merchant_name):
    """更新单个商户分类API"""
    data = request.get_json()
    new_category = data.get('category') if data else None
    
    # 验证请求数据
    if not new_category:
        return DataUtils.format_api_response(False, error='缺少分类参数')
    
    # 验证分类有效性
    from app.services.category_service import CATEGORIES
    if new_category not in CATEGORIES:
        return DataUtils.format_api_response(False, error='无效的分类代码')
    
    # 获取分类服务并保存用户规则
    category_service = get_category_service()
    if not category_service.update_merchant_category(merchant_name, new_category):
        return DataUtils.format_api_response(False, error='保存用户规则失败')
    
    # 批量更新同商户的所有交易
    updated_count = Transaction.query.filter_by(counterparty=merchant_name).update({
        'category': new_category
    })
    
    db.session.commit()
    
    logger.info(f"商户分类更新: {merchant_name} -> {new_category}, 影响 {updated_count} 笔交易")
    
    return DataUtils.format_api_response(True, data={
        'updated_transactions': updated_count,
        'merchant_name': merchant_name,
        'new_category': new_category
    })
