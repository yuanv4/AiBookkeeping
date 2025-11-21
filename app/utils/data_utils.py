"""极简数据工具类

只保留高频使用的核心功能，符合项目简化原则。
"""

from typing import Optional, List, Dict, Any, Tuple
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from flask import jsonify
import logging
import re

logger = logging.getLogger(__name__)


class DataUtils:
    """极简数据工具类 - 只保留高频核心功能"""
    
    @staticmethod
    def format_api_response(success: bool = True, data: Any = None,
                          message: str = "", error: str = "") -> Any:
        """统一API响应格式"""
        response = {'success': success}
        
        if success:
            if data is not None:
                response['data'] = data
            if message:
                response['message'] = message
        else:
            response['error'] = error or "操作失败"
            
        return jsonify(response)
