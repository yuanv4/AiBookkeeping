"""服务层基础接口规范

提供统一的服务层接口定义和通用功能，确保所有服务遵循一致的设计模式。
遵循简单性、实用性、易维护性原则。
"""

from abc import ABC, abstractmethod
from typing import Any, Optional, List, Dict
import logging

from app.models import db


class BaseService(ABC):
    """服务层基础接口规范
    
    所有业务服务类都应该继承此基类，确保接口一致性和代码复用。
    提供统一的错误处理、日志记录和数据库会话管理。
    """
    
    def __init__(self, db_session=None):
        """初始化服务基类
        
        Args:
            db_session: 数据库会话，如果为None则使用默认会话
        """
        self.db = db_session or db.session
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @abstractmethod
    def get_by_id(self, id: int) -> Optional[Any]:
        """根据ID获取实体
        
        Args:
            id: 实体ID
            
        Returns:
            实体对象或None
        """
        pass
    
    @abstractmethod
    def get_all(self) -> List[Any]:
        """获取所有实体
        
        Returns:
            实体列表
        """
        pass
    
    def _handle_service_error(self, operation: str, error: Exception):
        """统一的服务错误处理
        
        Args:
            operation: 操作描述
            error: 异常对象
            
        Raises:
            重新抛出原始异常
        """
        self.logger.error(f"{operation} 失败: {error}")
        raise
    
    def _log_operation(self, operation: str, details: str = ""):
        """记录操作日志
        
        Args:
            operation: 操作名称
            details: 操作详情
        """
        if details:
            self.logger.info(f"{operation}: {details}")
        else:
            self.logger.info(f"{operation}")
    
    def _validate_id(self, id: int) -> bool:
        """验证ID参数
        
        Args:
            id: 要验证的ID
            
        Returns:
            验证结果
        """
        return isinstance(id, int) and id > 0
