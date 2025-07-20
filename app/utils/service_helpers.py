"""简化的服务辅助函数

提供便捷的服务获取接口，移除ServiceRegistry依赖，使用简单的工厂模式。
"""

from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

# 全局服务实例缓存
_service_cache: Dict[str, Any] = {}

def get_data_service():
    """获取数据服务实例

    Returns:
        DataService: 数据服务实例
    """
    if 'data' not in _service_cache:
        from ..services import DataService
        _service_cache['data'] = DataService()
        logger.info("创建DataService实例")
    return _service_cache['data']

def get_import_service():
    """获取导入服务实例

    Returns:
        ImportService: 导入服务实例
    """
    if 'import' not in _service_cache:
        from ..services import ImportService
        data_service = get_data_service()
        _service_cache['import'] = ImportService(data_service)
        logger.info("创建ImportService实例")
    return _service_cache['import']

def get_report_service():
    """获取报告服务实例

    Returns:
        ReportService: 报告服务实例
    """
    if 'report' not in _service_cache:
        from ..services import ReportService
        data_service = get_data_service()
        category_service = get_category_service()
        _service_cache['report'] = ReportService(data_service, category_service=category_service)
        logger.info("创建ReportService实例")
    return _service_cache['report']

def get_category_service():
    """获取分类服务实例

    Returns:
        CategoryService: 分类服务实例
    """
    if 'category' not in _service_cache:
        from ..services.category_service import CategoryService
        _service_cache['category'] = CategoryService()
        logger.info("创建CategoryService实例")
    return _service_cache['category']

def check_services_health() -> dict:
    """检查所有服务的健康状态"""
    services_status = {}

    try:
        services_status['data'] = get_data_service() is not None
        services_status['import'] = get_import_service() is not None
        services_status['report'] = get_report_service() is not None
        services_status['category'] = get_category_service() is not None
        services_status['cached_services'] = len(_service_cache)

        logger.info(f"服务健康检查完成: {services_status}")

    except Exception as e:
        logger.error(f"服务健康检查失败: {e}")
        services_status['error'] = str(e)

    return services_status
