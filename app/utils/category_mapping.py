"""分类映射工具函数

处理数据源分类到目标分类的映射和查询
"""

from app.models import CoreTransaction, CategoryMapping, db, Account, Entry
from sqlalchemy import func
from .category_utils import CategoryUtils
from app.configs.basic_categories import get_category_options
from collections import defaultdict


def get_all_source_categories() -> list:
    """
    获取所有数据源分类及其统计信息

    Returns:
        list: [{source_category, transaction_count, is_mapped, target_category, is_active}]
    """
    # 查询所有数据源分类
    source_categories_query = db.session.query(
        CoreTransaction.source_category,
        func.count(CoreTransaction.id).label('transaction_count')
    ).filter(
        CoreTransaction.source_category.isnot(None)
    ).group_by(
        CoreTransaction.source_category
    ).all()

    result = []
    for (category, count) in source_categories_query:
        # 查找映射状态
        mapping = CategoryMapping.query.filter_by(source_category=category).first()

        result.append({
            'source_category': category,
            'transaction_count': count,
            'has_mapping': mapping is not None,
            'target_category': mapping.target_category if mapping else None,
            'is_active': mapping.is_active if mapping else False,
            'created_at': mapping.created_at.isoformat() if mapping else None
        })

    return result


def get_unmapped_merchants(limit: int = 50) -> list:
    """
    获取未映射分类的商户列表

    Args:
        limit: 返回数量限制

    Returns:
        list: [{merchant_name, source_category, transaction_count, latest_date}]
    """
    # 获取已映射的数据源分类
    mapped_categories = db.session.query(CategoryMapping.source_category)\
                                 .filter_by(is_active=True)\
                                 .subquery()

    # 查询未映射的商户
    unmapped_merchants_query = db.session.query(
        CoreTransaction.merchant_name,
        CoreTransaction.source_category,
        func.count(CoreTransaction.id).label('transaction_count'),
        func.max(CoreTransaction.date).label('latest_date')
    ).filter(
        CoreTransaction.merchant_name.isnot(None),
        CoreTransaction.source_category.isnot(None)
    ).filter(
        ~CoreTransaction.source_category.in_(mapped_categories)
    ).group_by(
        CoreTransaction.merchant_name,
        CoreTransaction.source_category
    ).order_by(
        func.count(CoreTransaction.id).desc()
    ).limit(limit)

    result = []
    for merchant in unmapped_merchants_query:
        result.append({
            'merchant_name': merchant.merchant_name,
            'source_category': merchant.source_category,
            'transaction_count': merchant.transaction_count,
            'latest_date': merchant.latest_date.strftime('%Y-%m-%d'),
            'mapped_category': None
        })

    return result


def get_merchant_details_by_name(merchant_name: str) -> dict:
    """
    获取商户详细信息，优化查询以避免 N+1 问题。

    Args:
        merchant_name: 商户名称

    Returns:
        dict: 包含商户详情的字典，如果找不到则返回 None
    """
    # 1. 一次性查询该商户的所有交易和相关的 Entry/Account
    transactions = db.session.query(
        CoreTransaction,
        Entry,
        Account
    ).join(Entry, CoreTransaction.id == Entry.transaction_id)\
    .join(Account, Entry.account_id == Account.id)\
    .filter(CoreTransaction.merchant_name == merchant_name)\
    .order_by(CoreTransaction.date.desc()).all()

    if not transactions:
        return None

    # 2. 数据预处理和分组
    source_category_groups = defaultdict(lambda: {
        'transaction_count': 0,
        'total_amount': 0.0,
        'latest_date': None,
        'recent_transactions': []
    })
    total_transactions = 0
    total_amount = 0.0
    income_count = 0
    expense_count = 0

    processed_tx_ids = set()

    for tx, entry, account in transactions:
        if account.type != 'ASSET':
            continue

        if tx.id not in processed_tx_ids:
            total_transactions += 1
            processed_tx_ids.add(tx.id)

        group = source_category_groups[tx.source_category]
        amount = float(entry.amount)

        group['transaction_count'] += 1
        group['total_amount'] += abs(amount)
        total_amount += abs(amount)
        
        if group['latest_date'] is None or tx.date > group['latest_date']:
            group['latest_date'] = tx.date
        
        if amount > 0:
            income_count += 1
        else:
            expense_count += 1

        if len(group['recent_transactions']) < 8:
            group['recent_transactions'].append({
                'date': tx.date.strftime('%Y-%m-%d'),
                'amount': abs(amount),
                'description': tx.description
            })

    source_categories = list(source_category_groups.keys())

    # 3. 一次性查询所有相关的分类映射
    mappings = CategoryMapping.query.filter(
        CategoryMapping.source_category.in_(source_categories)
    ).all()
    mappings_dict = {m.source_category: m for m in mappings}

    # 4. 构建最终的分组数据
    groups = []
    for source_cat, data in source_category_groups.items():
        mapping = mappings_dict.get(source_cat)
        groups.append({
            'source_category': source_cat,
            'transaction_count': data['transaction_count'],
            'total_amount': data['total_amount'],
            'latest_date': data['latest_date'].strftime('%Y-%m-%d'),
            'mapped_category': mapping.target_category if mapping and mapping.is_active else None,
            'is_mapped': mapping is not None and mapping.is_active,
            'recent_transactions': data['recent_transactions']
        })

    # 5. 获取AI推荐
    ai_suggestion = CategoryUtils.get_ai_suggestion(merchant_name)

    return {
        'merchant': {
            'name': merchant_name,
            'transaction_count': total_transactions,
            'total_amount': total_amount,
            'income_count': income_count,
            'expense_count': expense_count
        },
        'category_groups': groups,
        'categories': get_category_options(),
        'ai_suggestion': ai_suggestion
    }


def create_mapping(source_category: str, target_category: str, is_active: bool = True) -> CategoryMapping:
    """
    创建或更新分类映射

    Args:
        source_category: 数据源分类
        target_category: 目标分类
        is_active: 是否启用

    Returns:
        CategoryMapping: 映射对象
    """
    mapping = CategoryMapping.query.filter_by(source_category=source_category).first()

    if mapping:
        mapping.target_category = target_category
        mapping.is_active = is_active
    else:
        mapping = CategoryMapping(
            source_category=source_category,
            target_category=target_category,
            is_active=is_active
        )
        db.session.add(mapping)

    db.session.commit()
    return mapping


def delete_mapping(source_category: str) -> bool:
    """
    删除分类映射

    Args:
        source_category: 数据源分类

    Returns:
        bool: 是否删除成功
    """
    mapping = CategoryMapping.query.filter_by(source_category=source_category).first()
    if mapping:
        db.session.delete(mapping)
        db.session.commit()
        return True
    return False


def get_category_statistics() -> dict:
    """
    获取分类统计信息

    Returns:
        dict: {
            total_transactions: 总交易数,
            mapped_transactions: 已映射交易数,
            unmapped_transactions: 未映射交易数,
            unique_sources: 数据源分类数量,
            mapped_sources: 已映射数据源分类数
        }
    """
    # 总交易数
    total_transactions = db.session.query(func.count(CoreTransaction.id))\
                                  .scalar() or 0

    # 有数据源分类的交易数
    with_category = db.session.query(func.count(CoreTransaction.id))\
                              .filter(CoreTransaction.source_category.isnot(None))\
                              .scalar() or 0

    # 已映射的源分类
    mapped_sources = db.session.query(func.count(CategoryMapping.source_category))\
                              .filter_by(is_active=True)\
                              .scalar() or 0

    # 所有数据源分类数
    all_sources = db.session.query(
        CoreTransaction.source_category
    ).filter(
        CoreTransaction.source_category.isnot(None)
    ).distinct().count()

    # 已映射的交易数（估算）
    # 获取已映射的源分类列表
    mapped_categories = db.session.query(CategoryMapping.source_category)\
                                 .filter_by(is_active=True)\
                                 .all()

    mapped_categories = [mc[0] for mc in mapped_categories]

    mapped_transactions = 0
    if mapped_categories:
        mapped_transactions = db.session.query(func.count(CoreTransaction.id))\
                                       .filter(CoreTransaction.source_category.in_(mapped_categories))\
                                       .scalar() or 0

    return {
        'total_transactions': total_transactions,
        'mapped_transactions': mapped_transactions,
        'unmapped_transactions': with_category - mapped_transactions,
        'unique_sources': all_sources,
        'mapped_sources': mapped_sources,
        'mapping_rate': round(mapped_transactions / with_category * 100, 1) if with_category > 0 else 0
    }