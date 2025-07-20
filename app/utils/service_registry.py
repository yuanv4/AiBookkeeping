"""轻量级服务注册器

提供简单的服务管理机制，替代直接在Flask app对象上挂载服务的方式。
支持服务注册、获取、替换（用于测试）等功能。
"""

from typing import Dict, Any, Optional, TypeVar, Type
import logging

T = TypeVar('T')

logger = logging.getLogger(__name__)


class ServiceRegistry:
    """轻量级服务注册器 - 简单的服务管理
    
    这是一个全局的服务注册表，提供基本的服务管理功能。
    相比复杂的依赖注入框架，这个实现更简单直观，易于理解和维护。
    
    主要特性:
    - 服务注册和获取
    - 测试时的服务替换
    - 类型提示支持
    - 服务列表查看
    
    使用示例:
        # 注册服务
        ServiceRegistry.register('data', DataService())
        
        # 获取服务
        data_service = ServiceRegistry.get('data')
        
        # 测试时替换服务
        mock_service = Mock()
        old_service = ServiceRegistry.replace('data', mock_service)
    """
    
    _services: Dict[str, Any] = {}
    _initialized: bool = False
    
    @classmethod
    def register(cls, name: str, service_instance: Any) -> None:
        """注册服务实例
        
        Args:
            name: 服务名称，建议使用简短的标识符
            service_instance: 服务实例对象
            
        Raises:
            ValueError: 如果服务名称为空或服务实例为None
            
        Examples:
            >>> ServiceRegistry.register('data', DataService())
            >>> ServiceRegistry.register('import', ImportService(data_service))
        """
        if not name or not isinstance(name, str):
            raise ValueError("服务名称不能为空且必须是字符串")
        
        if service_instance is None:
            raise ValueError("服务实例不能为None")
        
        # 检查是否重复注册
        if name in cls._services:
            logger.warning(f"服务 '{name}' 已存在，将被覆盖")
        
        cls._services[name] = service_instance
        logger.info(f"注册服务: {name} -> {type(service_instance).__name__}")
    
    @classmethod
    def get(cls, name: str, service_type: Type[T] = None) -> Optional[T]:
        """获取服务实例
        
        Args:
            name: 服务名称
            service_type: 服务类型（用于类型提示，可选）
            
        Returns:
            服务实例，不存在返回None
            
        Examples:
            >>> data_service = ServiceRegistry.get('data', DataService)
            >>> import_service = ServiceRegistry.get('import')
        """
        if not name or not isinstance(name, str):
            logger.warning(f"无效的服务名称: {name}")
            return None
        
        service = cls._services.get(name)
        if service is None:
            logger.warning(f"服务未找到: {name}")
            return None
        
        # 可选的类型检查（仅在开发时有用）
        if service_type and not isinstance(service, service_type):
            logger.warning(f"服务类型不匹配: {name} 期望 {service_type.__name__}, 实际 {type(service).__name__}")
        
        return service
    
    @classmethod
    def replace(cls, name: str, service_instance: Any) -> Any:
        """替换服务实例（主要用于测试）
        
        Args:
            name: 服务名称
            service_instance: 新的服务实例
            
        Returns:
            原来的服务实例，如果不存在返回None
            
        Examples:
            >>> mock_service = Mock()
            >>> old_service = ServiceRegistry.replace('data', mock_service)
            >>> # 执行测试...
            >>> ServiceRegistry.replace('data', old_service)  # 恢复原服务
        """
        if not name or not isinstance(name, str):
            raise ValueError("服务名称不能为空且必须是字符串")
        
        if service_instance is None:
            raise ValueError("服务实例不能为None")
        
        old_service = cls._services.get(name)
        cls._services[name] = service_instance
        
        logger.info(f"替换服务: {name} -> {type(service_instance).__name__}")
        
        return old_service
    
    @classmethod
    def unregister(cls, name: str) -> Any:
        """注销服务
        
        Args:
            name: 服务名称
            
        Returns:
            被注销的服务实例，如果不存在返回None
        """
        if not name or not isinstance(name, str):
            return None
        
        service = cls._services.pop(name, None)
        if service:
            logger.info(f"注销服务: {name}")
        else:
            logger.warning(f"尝试注销不存在的服务: {name}")
        
        return service
    
    @classmethod
    def clear(cls) -> None:
        """清空所有服务（主要用于测试）
        
        Examples:
            >>> ServiceRegistry.clear()  # 清空所有服务
        """
        service_count = len(cls._services)
        cls._services.clear()
        cls._initialized = False
        logger.info(f"清空所有服务，共清理 {service_count} 个服务")
    
    @classmethod
    def list_services(cls) -> Dict[str, str]:
        """列出所有注册的服务
        
        Returns:
            服务名称到类型名称的映射字典
            
        Examples:
            >>> services = ServiceRegistry.list_services()
            >>> print(services)
            {'data': 'DataService', 'import': 'ImportService', ...}
        """
        return {name: type(service).__name__ for name, service in cls._services.items()}
    
    @classmethod
    def is_registered(cls, name: str) -> bool:
        """检查服务是否已注册
        
        Args:
            name: 服务名称
            
        Returns:
            如果服务已注册返回True，否则返回False
        """
        return name in cls._services
    
    @classmethod
    def get_service_count(cls) -> int:
        """获取已注册的服务数量
        
        Returns:
            服务数量
        """
        return len(cls._services)
    
    @classmethod
    def mark_initialized(cls) -> None:
        """标记服务注册器已初始化
        
        用于跟踪服务初始化状态，避免重复初始化
        """
        cls._initialized = True
        logger.info("服务注册器已标记为初始化完成")
    
    @classmethod
    def is_initialized(cls) -> bool:
        """检查服务注册器是否已初始化
        
        Returns:
            如果已初始化返回True，否则返回False
        """
        return cls._initialized
    
    @classmethod
    def get_debug_info(cls) -> Dict[str, Any]:
        """获取调试信息
        
        Returns:
            包含服务注册器状态的调试信息
        """
        return {
            'service_count': cls.get_service_count(),
            'initialized': cls.is_initialized(),
            'services': cls.list_services()
        }
