"""路由助手函数

提取蓝图路由中的公共逻辑，减少重复代码。
"""

from typing import Dict, Any, Optional
from flask import request
import logging

logger = logging.getLogger(__name__)


def get_common_filters() -> Dict[str, Any]:
    """获取通用的过滤器参数
    
    从请求参数中提取常用的过滤条件，用于交易查询等场景。
    
    Returns:
        包含过滤条件的字典
    """
    filters = {}
    
    # 账户相关过滤
    if request.args.get('account_number'):
        filters['account_number'] = request.args.get('account_number').strip()
    
    if request.args.get('account_name_filter'):
        filters['account_name'] = request.args.get('account_name_filter').strip()
    
    # 日期范围过滤
    if request.args.get('start_date'):
        filters['start_date'] = request.args.get('start_date').strip()
    
    if request.args.get('end_date'):
        filters['end_date'] = request.args.get('end_date').strip()
    
    # 金额范围过滤
    if request.args.get('min_amount'):
        try:
            filters['min_amount'] = float(request.args.get('min_amount'))
        except (ValueError, TypeError):
            pass
    
    if request.args.get('max_amount'):
        try:
            filters['max_amount'] = float(request.args.get('max_amount'))
        except (ValueError, TypeError):
            pass
    
    # 交易类型过滤
    if request.args.get('type'):
        filters['transaction_type'] = request.args.get('type').strip()
    
    # 对方信息过滤
    if request.args.get('counterparty'):
        filters['counterparty'] = request.args.get('counterparty').strip()
    
    # 货币类型过滤
    if request.args.get('currency'):
        filters['currency'] = request.args.get('currency').strip()
    
    # 去重选项
    if request.args.get('distinct'):
        filters['distinct'] = request.args.get('distinct').lower() == 'true'
    
    return filters


def get_pagination_params() -> Dict[str, int]:
    """获取分页参数
    
    Returns:
        包含分页信息的字典
    """
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        
        # 限制分页参数范围
        page = max(1, page)
        per_page = max(1, min(100, per_page))  # 限制每页最多100条
        
        return {
            'page': page,
            'per_page': per_page
        }
    except (ValueError, TypeError):
        return {
            'page': 1,
            'per_page': 20
        }


def get_service_instances():
    """获取常用的服务实例
    
    Returns:
        包含服务实例的字典
    """
    from app.utils import (
        get_data_service, get_import_service, 
        get_report_service, get_category_service
    )
    
    return {
        'data_service': get_data_service(),
        'import_service': get_import_service(),
        'report_service': get_report_service(),
        'category_service': get_category_service()
    }


def log_route_access(route_name: str, params: Dict[str, Any] = None):
    """记录路由访问日志
    
    Args:
        route_name: 路由名称
        params: 请求参数（可选）
    """
    if params:
        logger.info(f"访问路由 {route_name}，参数: {params}")
    else:
        logger.info(f"访问路由 {route_name}")


def build_filter_summary(filters: Dict[str, Any]) -> str:
    """构建过滤条件摘要
    
    Args:
        filters: 过滤条件字典
        
    Returns:
        过滤条件的文字描述
    """
    summary_parts = []
    
    if filters.get('account_number'):
        summary_parts.append(f"账户: {filters['account_number']}")
    
    if filters.get('start_date') and filters.get('end_date'):
        summary_parts.append(f"日期: {filters['start_date']} 至 {filters['end_date']}")
    
    if filters.get('min_amount') is not None or filters.get('max_amount') is not None:
        min_amt = filters.get('min_amount', '不限')
        max_amt = filters.get('max_amount', '不限')
        summary_parts.append(f"金额: {min_amt} 至 {max_amt}")
    
    if filters.get('transaction_type'):
        summary_parts.append(f"类型: {filters['transaction_type']}")
    
    if filters.get('counterparty'):
        summary_parts.append(f"对方: {filters['counterparty']}")
    
    return "; ".join(summary_parts) if summary_parts else "无过滤条件"


def validate_month_param(month_str: str) -> Optional[str]:
    """验证月份参数格式
    
    Args:
        month_str: 月份字符串 (YYYY-MM格式)
        
    Returns:
        验证后的月份字符串，如果无效则返回None
    """
    if not month_str:
        return None
    
    try:
        from app.utils import DataUtils
        parsed_date = DataUtils.parse_date_safe(month_str, ['%Y-%m'])
        if parsed_date:
            return parsed_date.strftime('%Y-%m')
    except Exception as e:
        logger.warning(f"月份参数验证失败: {month_str}, 错误: {e}")
    
    return None


def format_route_response(success: bool, data: Any = None, message: str = "", error: str = ""):
    """统一的路由响应格式化
    
    Args:
        success: 操作是否成功
        data: 返回数据
        message: 成功消息
        error: 错误消息
        
    Returns:
        格式化的响应
    """
    from app.utils import DataUtils
    return DataUtils.format_api_response(success, data, message, error)
