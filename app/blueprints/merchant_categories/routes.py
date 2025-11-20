"""商户分类管理路由 - 基于数据源映射的新版本

提供商户分类管理页面和API端点
"""

from flask import render_template, request
from app.utils.decorators import handle_errors
from app.utils import DataUtils
from app.models import CoreTransaction, Entry, Account, CategoryMapping, db
from app.utils.category_mapping import (
    get_unmapped_merchants, create_mapping,
    get_merchant_category, get_transaction_category
)
from app.configs.basic_categories import get_category_options
from sqlalchemy import func
import logging

from . import merchant_categories_bp

logger = logging.getLogger(__name__)


@merchant_categories_bp.route('/')
def index():
    """商户分类管理主页面"""
    from app.utils import has_financial_data
    has_data = has_financial_data()

    return render_template('merchant_categories.html',
                         categories=get_category_options(),
                         has_data=has_data)


@merchant_categories_bp.route('/api/uncategorized-merchants')
@handle_errors
def get_uncategorized_merchants():
    """获取未映射分类的商户列表API"""
    limit = request.args.get('limit', 50, type=int)

    # 获取未映射的商户
    merchants = get_unmapped_merchants(limit)

    merchants_list = []
    for merchant in merchants:
        transactions = CoreTransaction.query.filter_by(
            merchant_name=merchant['merchant_name'],
            source_category=merchant['source_category']
        ).all()

        # 计算总金额（通过Entry表）
        total_amount = 0
        for tx in transactions:
            asset_entry = Entry.query.join(Account).filter(
                Entry.transaction_id == tx.id,
                Account.type == 'ASSET'
            ).first()
            if asset_entry:
                total_amount += float(abs(asset_entry.amount))

        merchants_list.append({
            'id': abs(hash(f"{merchant['merchant_name']}_{merchant['source_category']}")) % 999999,
            'merchant_name': merchant['merchant_name'],
            'source_category': merchant['source_category'],
            'transaction_count': merchant['transaction_count'],
            'total_amount': total_amount,
            'latest_date': merchant['latest_date'],
            'mapped_category': None
        })

    return DataUtils.format_api_response(True, data=merchants_list)


@merchant_categories_bp.route('/api/merchant/<merchant_name>/category', methods=['PUT'])
@handle_errors
def update_merchant_category(merchant_name):
    """更新商户分类API（重新实现）"""
    data = request.get_json()
    source_category = data.get('source_category')
    target_category = data.get('category') if data else None

    if not source_category or not target_category:
        return DataUtils.format_api_response(False, error='缺少源分类或目标分类参数')

    # 验证目标分类有效性
    valid_categories = get_category_options()
    valid_codes = [cat['code'] for cat in valid_categories]

    if target_category not in valid_codes:
        return DataUtils.format_api_response(False, error='无效的目标分类')

    try:
        # 创建映射
        mapping = create_mapping(source_category, target_category, True)

        # 获取影响的交易数量
        affected_count = CoreTransaction.query.filter(
            CoreTransaction.merchant_name == merchant_name,
            CoreTransaction.source_category == source_category
        ).count()

        logger.info(f"商户分类更新: {merchant_name} ({source_category}) -> {target_category}, "
                   f"影响 {affected_count} 笔交易")

        return DataUtils.format_api_response(True, data={
            'updated_transactions': affected_count,
            'merchant_name': merchant_name,
            'source_category': source_category,
            'target_category': target_category
        })

    except Exception as e:
        db.session.rollback()
        logger.error(f"更新商户分类失败: {merchant_name} - {source_category} -> {target_category}, 错误: {e}")
        return DataUtils.format_api_response(False, error='操作失败')


@merchant_categories_bp.route('/api/merchant-detail')
@handle_errors
def get_merchant_detail():
    """获取商户详细信息（按原始分类分组）"""
    merchant_name = request.args.get('name')
    if not merchant_name:
        return DataUtils.format_api_response(False, error='缺少商户名称参数')

    # 按原始分类分组查询
    category_groups = db.session.query(
        CoreTransaction.source_category,
        func.count(CoreTransaction.id).label('transaction_count'),
        func.sum(func.abs(Entry.amount)).label('total_amount'),
        func.max(CoreTransaction.date).label('latest_date')
    ).join(Entry).join(Account).filter(
        CoreTransaction.merchant_name == merchant_name,
        Account.type == 'ASSET'
    ).group_by(CoreTransaction.source_category)\
    .all()

    if not category_groups:
        return DataUtils.format_api_response(False, error='未找到该商户的交易记录')

    # 构建分类分组数据
    groups = []
    total_transactions = 0
    total_amount = 0
    income_count = 0
    expense_count = 0

    for group in category_groups:
        # 查找映射状态
        mapping = CategoryMapping.query.filter_by(source_category=group.source_category).first()

        # 获取该分组的交易明细
        group_txs = CoreTransaction.query.filter_by(
            merchant_name=merchant_name,
            source_category=group.source_category
        ).order_by(CoreTransaction.date.desc()).limit(8).all()

        # 准备交易数据
        recent_tx = []
        for tx in group_txs:
            asset_entry = Entry.query.join(Account).filter(
                Entry.transaction_id == tx.id,
                Account.type == 'ASSET'
            ).first()

            if asset_entry:
                amount = float(asset_entry.amount)
                if amount > 0:
                    income_count += 1
                else:
                    expense_count += 1

                recent_tx.append({
                    'date': tx.date.strftime('%Y-%m-%d'),
                    'amount': float(abs(amount)),
                    'description': tx.description
                })

        groups.append({
            'source_category': group.source_category,
            'transaction_count': group.transaction_count,
            'total_amount': float(group.total_amount or 0),
            'latest_date': group.latest_date.strftime('%Y-%m-%d'),
            'mapped_category': mapping.target_category if mapping and mapping.is_active else None,
            'is_mapped': mapping is not None and mapping.is_active,
            'recent_transactions': recent_tx
        })

        total_transactions += group.transaction_count
        total_amount += float(group.total_amount or 0)

    return DataUtils.format_api_response(True, data={
        'merchant': {
            'name': merchant_name,
            'transaction_count': total_transactions,
            'total_amount': total_amount,
            'income_count': income_count,
            'expense_count': expense_count
        },
        'category_groups': groups,
        'categories': get_category_options()
    })


@merchant_categories_bp.route('/api/quick-mapping', methods=['POST'])
@handle_errors
def quick_mapping():
    """快速创建分类映射（来自商户分类页面）"""
    data = request.get_json()
    merchant_name = data.get('merchant_name')
    source_category = data.get('source_category')
    target_category = data.get('category')

    if not source_category or not target_category:
        return DataUtils.format_api_response(False, error='缺少源分类或目标分类参数')

    # 验证目标分类有效性
    valid_categories = get_category_options()
    valid_codes = [cat['code'] for cat in valid_categories]

    if target_category not in valid_codes:
        return DataUtils.format_api_response(False, error='无效的目标分类')

    try:
        mapping = create_mapping(source_category, target_category, True)

        # 获取影响的交易数量
        affected_count = CoreTransaction.query.filter_by(
            source_category=source_category
        ).count()

        logger.info(f"快速映射: {merchant_name} ({source_category}) -> {target_category}, "
                   f"影响 {affected_count} 笔交易")

        return DataUtils.format_api_response(True, data={
            'message': f'已将 "{source_category}" 映射为 "{target_category}"',
            'affected_count': affected_count,
            'merchant_name': merchant_name
        })
    except Exception as e:
        logger.error(f"快速映射失败: {source_category} -> {target_category}, 错误: {e}")
        db.session.rollback()
        return DataUtils.format_api_response(False, error='操作失败')
