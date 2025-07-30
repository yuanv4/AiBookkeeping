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
    def parse_date_safe(date_str: str, formats: List[str] = None) -> Optional[date]:
        """安全的日期解析"""
        if not date_str or not isinstance(date_str, str):
            return None

        date_str = date_str.strip()
        if not date_str:
            return None

        formats = formats or ['%Y-%m-%d', '%Y/%m/%d', '%Y-%m', '%Y%m%d']
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt).date()
            except ValueError:
                continue

        return None

    @staticmethod
    def validate_date_range(start_str: str, end_str: str) -> Tuple[Optional[date], Optional[date], Optional[str]]:
        """验证日期范围"""
        if not start_str or not end_str:
            return None, None, "开始日期和结束日期不能为空"

        start_date = DataUtils.parse_date_safe(start_str)
        if not start_date:
            return None, None, f"无效的开始日期格式: {start_str}"

        end_date = DataUtils.parse_date_safe(end_str)
        if not end_date:
            return None, None, f"无效的结束日期格式: {end_str}"

        if start_date > end_date:
            return None, None, "开始日期不能晚于结束日期"

        return start_date, end_date, None

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

    @staticmethod
    def normalize_decimal(value: Any) -> Decimal:
        """金额标准化"""
        if value is None:
            return Decimal('0.00')

        try:
            if isinstance(value, str):
                value = re.sub(r'[^\d.-]', '', value.strip())

            if isinstance(value, (int, float)):
                return Decimal(str(value)).quantize(Decimal('0.01'))
            
            if isinstance(value, Decimal):
                return value.quantize(Decimal('0.01'))
            
            decimal_value = Decimal(str(value))
            return decimal_value.quantize(Decimal('0.01'))
            
        except (InvalidOperation, ValueError, TypeError) as e:
            logger.warning(f"金额标准化失败: {value}, 错误: {e}")
            return Decimal('0.00')
