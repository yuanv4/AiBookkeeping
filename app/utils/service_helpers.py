"""服务获取辅助函数

提供类型安全的服务获取函数，简化服务调用并提供更好的IDE支持。
这些函数是ServiceRegistry的便捷包装，提供了类型提示和更清晰的API。
"""

from typing import Optional
from .service_registry import ServiceRegistry

# 类型导入 - 提供更好的IDE支持和类型检查
try:
    from app.services.data_service import DataService
    from app.services.import_service import ImportService
    from app.services.report_service import ReportService
    from app.services.category_service import CategoryService
except ImportError:
    # 在某些情况下（如测试）可能无法导入，使用Any类型
    from typing import Any
    DataService = Any
    ImportService = Any
    ReportService = Any
    CategoryService = Any

import logging

logger = logging.getLogger(__name__)


def get_data_service() -> Optional[DataService]:
    """获取数据服务
    
    Returns:
        DataService实例，如果未注册返回None
        
    Examples:
        >>> data_service = get_data_service()
        >>> if data_service:
        ...     banks = data_service.get_all_banks()
    """
    service = ServiceRegistry.get('data', DataService)
    if service is None:
        logger.error("DataService未注册，请检查服务初始化")
    return service


def get_import_service() -> Optional[ImportService]:
    """获取导入服务
    
    Returns:
        ImportService实例，如果未注册返回None
        
    Examples:
        >>> import_service = get_import_service()
        >>> if import_service:
        ...     result = import_service.process_uploaded_files(files)
    """
    service = ServiceRegistry.get('import', ImportService)
    if service is None:
        logger.error("ImportService未注册，请检查服务初始化")
    return service


def get_report_service() -> Optional[ReportService]:
    """获取报告服务
    
    Returns:
        ReportService实例，如果未注册返回None
        
    Examples:
        >>> report_service = get_report_service()
        >>> if report_service:
        ...     dashboard_data = report_service.get_dashboard_data()
    """
    service = ServiceRegistry.get('report', ReportService)
    if service is None:
        logger.error("ReportService未注册，请检查服务初始化")
    return service


def get_category_service() -> Optional[CategoryService]:
    """获取分类服务
    
    Returns:
        CategoryService实例，如果未注册返回None
        
    Examples:
        >>> category_service = get_category_service()
        >>> if category_service:
        ...     category = category_service.classify_merchant('麦当劳')
    """
    service = ServiceRegistry.get('category', CategoryService)
    if service is None:
        logger.error("CategoryService未注册，请检查服务初始化")
    return service


def ensure_service_available(service_name: str) -> bool:
    """确保指定服务可用
    
    Args:
        service_name: 服务名称
        
    Returns:
        如果服务可用返回True，否则返回False
        
    Examples:
        >>> if ensure_service_available('data'):
        ...     # 安全使用数据服务
        ...     pass
    """
    return ServiceRegistry.is_registered(service_name)


def get_all_services() -> dict:
    """获取所有已注册的服务
    
    Returns:
        包含所有服务实例的字典
        
    Examples:
        >>> services = get_all_services()
        >>> print(f"已注册 {len(services)} 个服务")
    """
    service_names = ['data', 'import', 'report', 'category']
    services = {}
    
    for name in service_names:
        service = ServiceRegistry.get(name)
        if service:
            services[name] = service
    
    return services


def check_services_health() -> dict:
    """检查所有服务的健康状态
    
    Returns:
        包含服务健康状态的字典
        
    Examples:
        >>> health = check_services_health()
        >>> if not health['all_healthy']:
        ...     logger.warning("部分服务不可用")
    """
    required_services = ['data', 'import', 'report', 'category']
    health_status = {
        'all_healthy': True,
        'services': {},
        'missing_services': []
    }
    
    for service_name in required_services:
        is_available = ServiceRegistry.is_registered(service_name)
        health_status['services'][service_name] = is_available
        
        if not is_available:
            health_status['all_healthy'] = False
            health_status['missing_services'].append(service_name)
    
    return health_status


def log_service_status() -> None:
    """记录服务状态到日志
    
    用于调试和监控服务注册情况
    """
    health = check_services_health()
    
    if health['all_healthy']:
        logger.info("所有核心服务都已正常注册")
    else:
        logger.warning(f"缺少服务: {', '.join(health['missing_services'])}")
    
    # 记录详细状态
    for service_name, is_available in health['services'].items():
        status = "✓" if is_available else "✗"
        logger.debug(f"服务状态 {status} {service_name}")


# 便捷的服务获取函数别名
# 为了保持向后兼容性和提供更简洁的API
def data_service() -> Optional[DataService]:
    """get_data_service的简化别名"""
    return get_data_service()


def import_service() -> Optional[ImportService]:
    """get_import_service的简化别名"""
    return get_import_service()


def report_service() -> Optional[ReportService]:
    """get_report_service的简化别名"""
    return get_report_service()


def category_service() -> Optional[CategoryService]:
    """get_category_service的简化别名"""
    return get_category_service()


# 服务初始化辅助函数
def initialize_core_services(data_service_instance, import_service_instance, 
                           report_service_instance, category_service_instance) -> None:
    """初始化核心服务的便捷函数
    
    Args:
        data_service_instance: DataService实例
        import_service_instance: ImportService实例
        report_service_instance: ReportService实例
        category_service_instance: CategoryService实例
    """
    ServiceRegistry.register('data', data_service_instance)
    ServiceRegistry.register('import', import_service_instance)
    ServiceRegistry.register('report', report_service_instance)
    ServiceRegistry.register('category', category_service_instance)
    ServiceRegistry.mark_initialized()
    
    logger.info("核心服务初始化完成")
    log_service_status()
