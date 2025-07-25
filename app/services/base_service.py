"""服务层基础类

提供统一的通用功能，包括错误处理、日志记录和数据库会话管理。
遵循简单性、实用性、易维护性原则。

注意：移除了抽象方法约束，因为不同服务的实现差异很大，
强制抽象并没有带来实际的代码复用价值。
"""

from typing import Any, Optional, List, Dict
import logging

from app.models import db


class BaseService:
    """服务层基础类

    提供统一的错误处理、日志记录和数据库会话管理功能。
    服务类可以选择继承此基类来获得通用功能，但不强制要求。
    """

    def __init__(self, db_session=None):
        """初始化服务基类

        Args:
            db_session: 数据库会话，如果为None则使用默认会话
        """
        self.db = db_session or db.session
        self.logger = logging.getLogger(self.__class__.__name__)
    
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
    

    def _validate_id(self, id: int) -> bool:
        """验证ID参数
        
        Args:
            id: 要验证的ID
            
        Returns:
            验证结果
        """
        return isinstance(id, int) and id > 0
