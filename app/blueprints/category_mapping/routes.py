"""分类映射管理路由

提供分类映射管理页面和API端点
"""

from flask import render_template, request, jsonify
from app.utils.decorators import handle_errors
from app.utils import DataUtils
from app.models import CategoryMapping, CoreTransaction, db
from app.utils.category_mapping import (
    get_all_source_categories, create_mapping, delete_mapping,
    get_category_statistics, get_unmapped_merchants
)
from app.configs.basic_categories import get_category_options
from sqlalchemy import func
import logging

from . import category_mapping_bp

logger = logging.getLogger(__name__)


@category_mapping_bp.route('/')
def index():
    """分类管理主页面"""
    return render_template('category_mapping.html')


@category_mapping_bp.route('/api/source-categories')
@handle_errors
def get_source_categories():
    """获取所有数据源分类及映射状态"""
    categories = get_all_source_categories()
    return DataUtils.format_api_response(True, data=categories)


@category_mapping_bp.route('/api/categories')
@handle_errors
def get_basic_categories():
    """获取基础目标分类列表"""
    categories = get_category_options()
    return DataUtils.format_api_response(True, data=categories)


@category_mapping_bp.route('/api/statistics')
@handle_errors
def get_statistics():
    """获取分类统计信息"""
    stats = get_category_statistics()
    return DataUtils.format_api_response(True, data=stats)


@category_mapping_bp.route('/api/mapping', methods=['POST'])
@handle_errors
def create_mapping_endpoint():
    """创建或更新分类映射"""
    data = request.get_json()
    source_category = data.get('source_category')
    target_category = data.get('target_category')
    is_active = data.get('is_active', True)

    if not source_category or not target_category:
        return DataUtils.format_api_response(False, error='缺少必要参数')

    # 验证目标分类是否有效
    valid_categories = get_category_options()
    valid_codes = [cat['code'] for cat in valid_categories]

    if target_category not in valid_codes:
        return DataUtils.format_api_response(False, error='无效的目标分类')

    try:
        mapping = create_mapping(source_category, target_category, is_active)
        return DataUtils.format_api_response(True, data={
            'message': f'已将 "{source_category}" 映射为 "{target_category}"',
            'mapping': {
                'source_category': mapping.source_category,
                'target_category': mapping.target_category,
                'is_active': mapping.is_active
            }
        })
    except Exception as e:
        logger.error(f"创建映射失败: {source_category} -> {target_category}, 错误: {e}")
        db.session.rollback()
        return DataUtils.format_api_response(False, error='操作失败')


@category_mapping_bp.route('/api/mapping/<string:source_category>', methods=['PUT'])
@handle_errors
def update_mapping(source_category):
    """更新分类映射"""
    data = request.get_json()
    target_category = data.get('target_category')
    is_active = data.get('is_active')

    if not target_category:
        return DataUtils.format_api_response(False, error='缺少目标分类参数')

    mapping = CategoryMapping.query.filter_by(source_category=source_category).first()

    if not mapping:
        return DataUtils.format_api_response(False, error='映射不存在')

    try:
        mapping.target_category = target_category
        if is_active is not None:
            mapping.is_active = is_active

        db.session.commit()

        return DataUtils.format_api_response(True, data={
            'message': f'已更新映射 "{source_category}"',
            'mapping': {
                'source_category': mapping.source_category,
                'target_category': mapping.target_category,
                'is_active': mapping.is_active
            }
        })
    except Exception as e:
        logger.error(f"更新映射失败: {source_category}, 错误: {e}")
        db.session.rollback()
        return DataUtils.format_api_response(False, error='操作失败')


@category_mapping_bp.route('/api/mapping/<string:source_category>', methods=['DELETE'])
@handle_errors
def delete_mapping_endpoint(source_category):
    """删除分类映射"""
    try:
        success = delete_mapping(source_category)
        if success:
            return DataUtils.format_api_response(True, data={
                'message': f'已删除映射 "{source_category}"'
            })
        else:
            return DataUtils.format_api_response(False, error='映射不存在')
    except Exception as e:
        logger.error(f"删除映射失败: {source_category}, 错误: {e}")
        db.session.rollback()
        return DataUtils.format_api_response(False, error='操作失败')


@category_mapping_bp.route('/api/batch-mapping', methods=['POST'])
@handle_errors
def batch_mapping():
    """批量创建映射"""
    data = request.get_json()
    mappings = data.get('mappings', [])

    if not mappings:
        return DataUtils.format_api_response(False, error='缺少映射数据')

    results = []
    success_count = 0

    for item in mappings:
        source_category = item.get('source_category')
        target_category = item.get('target_category')

        if not source_category or not target_category:
            continue

        try:
            create_mapping(source_category, target_category, True)
            success_count += 1
            results.append({
                'source_category': source_category,
                'success': True
            })
        except Exception as e:
            logger.error(f"批量映射失败: {source_category} -> {target_category}, 错误: {e}")
            results.append({
                'source_category': source_category,
                'success': False,
                'error': str(e)
            })

    return DataUtils.format_api_response(True, data={
        'message': f'批量操作完成: 成功 {success_count}/{len(mappings)}',
        'results': results
    })


@category_mapping_bp.route('/api/unmapped-merchants')
@handle_errors
def get_unmapped_merchants_endpoint():
    """获取未映射分类的商户列表（用于商户分类页面）"""
    limit = request.args.get('limit', 50, type=int)
    merchants = get_unmapped_merchants(limit)

    return DataUtils.format_api_response(True, data=merchants)


@category_mapping_bp.route('/api/quick-mapping', methods=['POST'])
@handle_errors
def quick_mapping():
    """快速创建分类映射（来自商户分类页面）"""
    data = request.get_json()
    merchant_name = data.get('merchant_name')
    source_category = data.get('source_category')
    target_category = data.get('target_category')

    if not source_category or not target_category:
        return DataUtils.format_api_response(False, error='缺少必要参数')

    try:
        mapping = create_mapping(source_category, target_category, True)

        # 获取影响的交易数量
        affected_count = CoreTransaction.query.filter_by(
            source_category=source_category
        ).count()

        logger.info(f"快速映射: {merchant_name} (${source_category}) -> {target_category}, "
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


@category_mapping_bp.route('/api/discover-categories')
@handle_errors
def discover_categories():
    """发现新的数据源分类"""
    # 获取所有数据源分类
    all_categories = get_all_source_categories()

    # 提取未映射的分类
    unmapped = [
        cat for cat in all_categories
        if not cat['has_mapping'] or not cat['is_active']
    ]

    # 按交易数量降序排列
    unmapped.sort(key=lambda x: x['transaction_count'], reverse=True)

    return DataUtils.format_api_response(True, data={
        'total_categories': len(all_categories),
        'unmapped_count': len(unmapped),
        'unmapped_categories': unmapped[:100]  # 限制返回数量
    })