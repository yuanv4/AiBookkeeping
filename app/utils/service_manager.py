"""服务管理器模块

提供统一的服务实例化和管理功能，避免在app对象上直接挂载服务属性。
"""

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class ServiceManager:
    """服务管理器类
    
    统一管理应用中的所有服务实例，提供依赖注入和服务定位功能。
    """
    
    def __init__(self, app=None):
        """初始化服务管理器
        
        Args:
            app: Flask应用实例
        """
        self.app = app
        self._services: Dict[str, Any] = {}
        self.logger = logging.getLogger(__name__)
        
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """初始化Flask应用
        
        Args:
            app: Flask应用实例
        """
        self.app = app
        # 将服务管理器注册到app扩展中
        if not hasattr(app, 'extensions'):
            app.extensions = {}
        app.extensions['service_manager'] = self

        # 在app对象上提供服务管理器访问
        app.service_manager = self
    
    def register_service(self, name: str, service_instance: Any) -> None:
        """注册服务实例
        
        Args:
            name: 服务名称
            service_instance: 服务实例
        """
        if name in self._services:
            self.logger.warning(f"服务 '{name}' 已存在，将被覆盖")
        
        self._services[name] = service_instance
        self.logger.info(f"已注册服务: {name}")

        # 在app对象上设置服务属性以便访问
        if self.app:
            setattr(self.app, name, service_instance)
    
    def get_service(self, name: str) -> Optional[Any]:
        """获取服务实例
        
        Args:
            name: 服务名称
            
        Returns:
            服务实例，如果不存在则返回None
        """
        return self._services.get(name)
    
    def has_service(self, name: str) -> bool:
        """检查服务是否存在
        
        Args:
            name: 服务名称
            
        Returns:
            如果服务存在返回True，否则返回False
        """
        return name in self._services
    
    def remove_service(self, name: str) -> bool:
        """移除服务
        
        Args:
            name: 服务名称
            
        Returns:
            如果成功移除返回True，否则返回False
        """
        if name in self._services:
            del self._services[name]
            # 同时从app对象上移除属性
            if self.app and hasattr(self.app, name):
                delattr(self.app, name)
            self.logger.info(f"已移除服务: {name}")
            return True
        return False
    
    def get_all_services(self) -> Dict[str, Any]:
        """获取所有已注册的服务
        
        Returns:
            服务名称到服务实例的字典
        """
        return self._services.copy()
    
    def register_core_services(self):
        """注册核心服务

        使用新的统一服务架构。
        """
        try:
            # 导入新的统一服务
            from ..services import DataService, ImportService, ReportService

            # 初始化新的统一服务
            data_service = DataService()
            import_service = ImportService(data_service)
            report_service = ReportService(data_service)

            # 注册新服务
            self.register_service('data_service', data_service)
            self.register_service('import_service', import_service)
            self.register_service('report_service', report_service)

            self.logger.info("核心服务注册完成（新统一架构）")

        except Exception as e:
            self.logger.error(f"注册核心服务时发生错误: {str(e)}")
            raise
    
    def __repr__(self):
        return f'<ServiceManager(services={list(self._services.keys())})>'
