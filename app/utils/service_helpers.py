"""简化的服务助手模块

提供简单的服务实例获取功能。
"""

import logging

logger = logging.getLogger(__name__)

def get_import_service():
    """获取导入服务实例"""
    from ..services import ImportService
    return ImportService()
