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
    from app.utils import has_financial_data
    has_data = has_financial_data()

    return render_template('merchant_categories.html',
                         categories_config=get_categories_config(),
                         has_data=has_data)


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

    # 获取分类服务
    category_service = get_category_service()

    # 批量获取所有商户的AI建议，避免N+1查询问题
    merchant_names = [merchant.merchant_name for merchant in merchants_data]
    ai_suggestions = category_service.get_ai_suggestions_batch(merchant_names)

    # 转换为字典格式并添加AI建议
    merchants_list = []
    for merchant in merchants_data:
        # 从批量结果中获取AI建议
        ai_suggestion = ai_suggestions.get(merchant.merchant_name, {
            'category': 'other',
            'category_name': '其他',
            'confidence': 0,
            'reason': '无法分类'
        })

        merchants_list.append({
            'id': hash(merchant.merchant_name) % 1000000,  # 生成简单ID
            'merchant_name': merchant.merchant_name,
            'transaction_count': merchant.transaction_count,
            'total_amount': float(merchant.total_amount),
            'latest_date': merchant.latest_date.strftime('%Y-%m-%d'),
            'category': 'uncategorized',
            'ai_suggestion': ai_suggestion
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
    from app.constants.categories import CATEGORIES
    if new_category not in CATEGORIES:
        return DataUtils.format_api_response(False, error='无效的分类代码')

    # 获取分类服务并保存用户规则
    category_service = get_category_service()
    if not category_service.update_merchant_category(merchant_name, new_category):
        return DataUtils.format_api_response(False, error='保存用户规则失败')

    try:
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
    except Exception as e:
        db.session.rollback()
        logger.error(f"更新商户分类失败: {merchant_name} -> {new_category}, 错误: {e}")
        return DataUtils.format_api_response(False, error='数据库更新失败')


@merchant_categories_bp.route('/api/merchant-detail/<merchant_name>')
@handle_errors
def get_merchant_detail(merchant_name):
    """获取商户详细信息用于弹窗显示"""
    # 获取商户的交易记录
    transactions = Transaction.query.filter_by(
        counterparty=merchant_name,
        category='uncategorized'
    ).order_by(Transaction.date.desc()).limit(10).all()

    if not transactions:
        return DataUtils.format_api_response(False, error='未找到该商户的交易记录')

    # 获取分类服务
    category_service = get_category_service()

    # 准备交易数据
    transaction_data = [{
        'date': t.date.strftime('%Y-%m-%d'),
        'amount': float(t.amount),
        'description': t.description or '无描述'
    } for t in transactions]

    # 获取AI建议
    ai_suggestion = category_service.get_ai_suggestion(merchant_name)

    # 获取所有可用分类
    categories = []
    for code, info in category_service.get_all_categories().items():
        if code != 'uncategorized':  # 排除未分类选项
            categories.append({
                'code': code,
                'name': info['name'],
                'icon': info['icon']
            })

    # 计算基本统计信息
    total_amount = sum(float(t.amount) for t in transactions)
    transaction_count = len(transactions)

    return DataUtils.format_api_response(True, data={
        'merchant': {
            'name': merchant_name,
            'transaction_count': transaction_count,
            'total_amount': total_amount
        },
        'ai_suggestion': ai_suggestion,
        'recent_transactions': transaction_data,
        'categories': categories
    })


@merchant_categories_bp.route('/api/confirm-ai-suggestion', methods=['POST'])
@handle_errors
def confirm_ai_suggestion():
    """确认AI建议并更新分类"""
    data = request.get_json()
    merchant_name = data.get('merchant_name') if data else None
    category = data.get('category') if data else None

    # 验证请求数据
    if not merchant_name or not category:
        return DataUtils.format_api_response(False, error='缺少必要参数')

    # 验证分类有效性
    from app.constants.categories import CATEGORIES
    if category not in CATEGORIES:
        return DataUtils.format_api_response(False, error='无效的分类代码')

    # 获取分类服务并保存用户规则
    category_service = get_category_service()
    if not category_service.update_merchant_category(merchant_name, category):
        return DataUtils.format_api_response(False, error='保存用户规则失败')

    try:
        # 批量更新同商户的所有交易
        updated_count = Transaction.query.filter_by(counterparty=merchant_name).update({
            'category': category
        })

        db.session.commit()

        logger.info(f"AI建议确认: {merchant_name} -> {category}, 影响 {updated_count} 笔交易")

        return DataUtils.format_api_response(True, data={
            'updated_transactions': updated_count,
            'merchant_name': merchant_name,
            'category': category
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f"确认AI建议失败: {merchant_name} -> {category}, 错误: {e}")
        return DataUtils.format_api_response(False, error='数据库更新失败')
