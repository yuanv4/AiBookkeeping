"""分类映射工具函数

处理数据源分类到目标分类的映射和查询
"""

from app.models import CoreTransaction, CategoryMapping, db
from sqlalchemy import func


def get_transaction_category(transaction: CoreTransaction) -> str:
    """
    通过映射表获取交易的最终分类

    Args:
        transaction: CoreTransaction 对象

    Returns:
        str: 映射后的分类，如未映射则返回 'uncategorized'
    """
    if not transaction.source_category:
        return 'uncategorized'

    mapping = CategoryMapping.query.filter_by(
        source_category=transaction.source_category,
        is_active=True
    ).first()

    return mapping.target_category if mapping else 'uncategorized'


def get_merchant_category(merchant_name: str) -> str:
    """
    获取商户的目标分类（基于最新交易的映射）

    Args:
        merchant_name: 商户名称

    Returns:
        str: 映射后的分类，如未映射则返回 'uncategorized'
    """
    # 查找该商户的最新交易
    latest_tx = CoreTransaction.query.filter_by(
        merchant_name=merchant_name
    ).order_by(CoreTransaction.date.desc()).first()

    if not latest_tx:
        return 'uncategorized'

    return get_transaction_category(latest_tx)


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