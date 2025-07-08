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
        
        # 为了向后兼容，在app对象上提供服务访问属性
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
        
        # 为了向后兼容，同时在app对象上设置属性
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
        
        这个方法包含了应用启动时需要初始化的所有核心服务。
        """
        try:
            # 导入服务类
            from ..services.core.bank_service import BankService
            from ..services.core.account_service import AccountService
            from ..services.core.transaction_service import TransactionService
            from ..services.analysis import FinancialAnalysisService
            from ..services.extraction import get_extraction_service
            from ..services.core.file_processor_service import FileProcessorService
            
            # 初始化核心服务
            bank_service = BankService()
            account_service = AccountService()
            transaction_service = TransactionService()
            reporting_service = FinancialAnalysisService()
            extractor_service = get_extraction_service()
            
            # 注册服务
            self.register_service('bank_service', bank_service)
            self.register_service('account_service', account_service)
            self.register_service('transaction_service', transaction_service)
            self.register_service('reporting_service', reporting_service)
            self.register_service('extractor_service', extractor_service)
            
            # 初始化文件处理服务（需要其他服务作为依赖）
            file_processor_service = FileProcessorService(
                extractor_service=extractor_service,
                bank_service=bank_service,
                account_service=account_service,
                transaction_service=transaction_service,
                upload_folder=self.app.config.get('UPLOAD_FOLDER', 'uploads'),
                allowed_extensions=self.app.config.get('ALLOWED_EXTENSIONS', {'xlsx', 'xls'})
            )
            self.register_service('file_processor_service', file_processor_service)
            
            self.logger.info("核心服务注册完成")
            
        except Exception as e:
            self.logger.error(f"注册核心服务时发生错误: {str(e)}")
            raise
    
    def __repr__(self):
        return f'<ServiceManager(services={list(self._services.keys())})>'
