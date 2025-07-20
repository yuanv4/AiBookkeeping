"""统一数据处理工具类

合并了原DataUtils和UnifiedUtils的功能，提供完整的数据处理、转换、验证功能。
专注于解决80%的常见数据处理需求，减少代码重复。

重构说明:
- 合并了DataUtils和UnifiedUtils的最佳实现
- 统一了日期解析、API响应格式、数据转换、金额处理等操作
- 遵循简单实用的设计原则，避免过度工程化
- 保持向后兼容性，支持渐进式迁移

使用示例:
    # 日期解析
    date_obj = DataUtils.parse_date_safe('2024-01-15')

    # 日期范围验证
    start, end, error = DataUtils.validate_date_range('2024-01-01', '2024-01-31')

    # 金额处理
    amount = DataUtils.normalize_decimal('100.50')

    # API响应
    return DataUtils.format_api_response(success=True, data=result)

    # 数据转换
    dict_list = DataUtils.transactions_to_dict(transactions)
"""

from typing import Optional, List, Dict, Any, Union, Tuple
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from flask import jsonify
import logging
import re

logger = logging.getLogger(__name__)


class DataUtils:
    """统一数据处理工具类 - 合并原DataUtils和UnifiedUtils功能"""
    
    @staticmethod
    def parse_date_safe(date_str: str, formats: List[str] = None) -> Optional[date]:
        """安全的日期解析，支持多种格式（合并原DataUtils和UnifiedUtils实现）

        Args:
            date_str: 日期字符串
            formats: 支持的日期格式列表，默认支持常见格式

        Returns:
            解析后的日期对象，失败返回None

        Examples:
            >>> DataUtils.parse_date_safe('2024-01-15')
            date(2024, 1, 15)
            >>> DataUtils.parse_date_safe('2024-01')  # 返回月初
            date(2024, 1, 1)
            >>> DataUtils.parse_date_safe('invalid')
            None
        """
        if not date_str or not isinstance(date_str, str):
            return None

        date_str = date_str.strip()
        if not date_str:
            return None

        # 扩展的日期格式支持（合并两个类的格式）
        formats = formats or [
            '%Y-%m-%d',      # 2024-01-15
            '%Y-%m',         # 2024-01 (返回月初)
            '%Y/%m/%d',      # 2024/01/15
            '%d/%m/%Y',      # 15/01/2024
            '%d-%m-%Y',      # 15-01-2024
            '%Y%m%d',        # 20240115
            '%m/%d/%Y',      # 01/15/2024
        ]
        
        for fmt in formats:
            try:
                parsed_date = datetime.strptime(date_str, fmt).date()
                
                # 对于月份格式，返回月初
                if fmt == '%Y-%m':
                    parsed_date = parsed_date.replace(day=1)
                
                logger.debug(f"成功解析日期: {date_str} -> {parsed_date} (格式: {fmt})")
                return parsed_date
                
            except ValueError:
                continue
        
        logger.warning(f"无法解析日期: {date_str}")
        return None

    @staticmethod
    def validate_date_range(start_date_str: str, end_date_str: str) -> Tuple[Optional[date], Optional[date], Optional[str]]:
        """验证日期范围（从UnifiedUtils合并）

        Args:
            start_date_str: 开始日期字符串
            end_date_str: 结束日期字符串

        Returns:
            (start_date, end_date, error_message) 元组
            如果验证失败，日期为None，error_message包含错误信息

        Examples:
            >>> start, end, error = DataUtils.validate_date_range('2024-01-01', '2024-01-31')
            >>> if error:
            ...     print(f"验证失败: {error}")
            >>> else:
            ...     print(f"日期范围: {start} 到 {end}")
        """
        start_date = DataUtils.parse_date_safe(start_date_str)
        end_date = DataUtils.parse_date_safe(end_date_str)

        if not start_date:
            return None, None, f"开始日期格式错误: {start_date_str}"

        if not end_date:
            return None, None, f"结束日期格式错误: {end_date_str}"

        if start_date > end_date:
            return None, None, "开始日期不能晚于结束日期"

        # 检查日期范围是否合理（不超过5年）
        if (end_date - start_date).days > 1825:  # 5年
            return None, None, "日期范围不能超过5年"

        return start_date, end_date, None

    @staticmethod
    def format_api_response(success: bool = True, data: Any = None,
                          message: str = "", error: str = "") -> Any:
        """统一API响应格式
        
        Args:
            success: 操作是否成功
            data: 返回数据
            message: 成功消息
            error: 错误消息
            
        Returns:
            Flask jsonify响应对象
            
        Examples:
            >>> DataUtils.format_api_response(True, {'count': 10})
            {'success': True, 'data': {'count': 10}}
            >>> DataUtils.format_api_response(False, error='参数错误')
            {'success': False, 'error': '参数错误'}
        """
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
    def transactions_to_dict(transactions: List) -> List[Dict]:
        """统一的交易数据转换
        
        Args:
            transactions: Transaction对象列表
            
        Returns:
            字典列表，如果输入为空则返回空列表
            
        Examples:
            >>> transactions = [transaction1, transaction2]
            >>> DataUtils.transactions_to_dict(transactions)
            [{'id': 1, 'amount': 100.0, ...}, {'id': 2, 'amount': -50.0, ...}]
        """
        if not transactions:
            return []
        
        try:
            result = [t.to_dict() for t in transactions]
            logger.debug(f"转换了 {len(result)} 条交易记录")
            return result
        except Exception as e:
            logger.error(f"交易数据转换失败: {e}")
            return []

    @staticmethod
    def normalize_decimal(value: Any) -> Decimal:
        """标准化金额为Decimal类型（从UnifiedUtils合并）

        Args:
            value: 待标准化的金额值

        Returns:
            标准化后的Decimal对象，保留2位小数

        Raises:
            ValueError: 当金额格式无效时抛出异常

        Examples:
            >>> DataUtils.normalize_decimal('100.50')
            Decimal('100.50')
            >>> DataUtils.normalize_decimal(100)
            Decimal('100.00')
            >>> DataUtils.normalize_decimal('¥100.5')
            Decimal('100.50')
        """
        if value is None:
            return Decimal('0.00')

        try:
            # 如果是字符串类型，进行标准化处理
            if isinstance(value, str):
                # 移除所有非数字字符（保留小数点和负号）
                value = re.sub(r'[^\d.-]', '', value.strip())

            # 转换为Decimal
            if isinstance(value, (int, float)):
                decimal_value = Decimal(str(value))
            elif not isinstance(value, Decimal):
                decimal_value = Decimal(str(value))
            else:
                decimal_value = value

            # 验证精度
            if decimal_value.as_tuple().exponent < -2:
                raise ValueError('金额最多支持2位小数')

            # 标准化为2位小数
            return decimal_value.quantize(Decimal('0.01'))

        except (ValueError, TypeError, InvalidOperation) as e:
            raise ValueError(f'无效的金额格式: {value} - {str(e)}')

    @staticmethod
    def safe_decimal(value: Any, default: Decimal = Decimal('0')) -> Decimal:
        """安全的Decimal转换
        
        Args:
            value: 待转换的值
            default: 转换失败时的默认值
            
        Returns:
            Decimal对象
            
        Examples:
            >>> DataUtils.safe_decimal('123.45')
            Decimal('123.45')
            >>> DataUtils.safe_decimal('invalid', Decimal('0'))
            Decimal('0')
        """
        if value is None:
            return default
            
        try:
            if isinstance(value, Decimal):
                return value
            return Decimal(str(value))
        except (ValueError, TypeError, ArithmeticError) as e:
            logger.warning(f"Decimal转换失败: {value} -> {e}")
            return default
    
    @staticmethod
    def validate_date_range(start_date_str: str, end_date_str: str) -> Tuple[Optional[date], Optional[date], Optional[str]]:
        """验证和解析日期范围
        
        Args:
            start_date_str: 开始日期字符串
            end_date_str: 结束日期字符串
            
        Returns:
            (start_date, end_date, error_message) 元组
            如果验证成功，error_message为None
            如果验证失败，日期为None，error_message包含错误信息
            
        Examples:
            >>> DataUtils.validate_date_range('2024-01-01', '2024-01-31')
            (date(2024, 1, 1), date(2024, 1, 31), None)
            >>> DataUtils.validate_date_range('2024-01-31', '2024-01-01')
            (None, None, '开始日期不能晚于结束日期')
        """
        # 检查输入参数
        if not start_date_str or not end_date_str:
            return None, None, "开始日期和结束日期都不能为空"
        
        # 解析日期
        start_date = DataUtils.parse_date_safe(start_date_str)
        end_date = DataUtils.parse_date_safe(end_date_str)
        
        if not start_date:
            return None, None, f"开始日期格式错误: {start_date_str}"
        
        if not end_date:
            return None, None, f"结束日期格式错误: {end_date_str}"
        
        # 验证日期范围
        if start_date > end_date:
            return None, None, "开始日期不能晚于结束日期"
        
        # 检查日期范围是否合理（可选的业务规则）
        date_diff = (end_date - start_date).days
        if date_diff > 365 * 2:  # 超过2年
            logger.warning(f"日期范围较大: {date_diff} 天")
            
        return start_date, end_date, None
    
    @staticmethod
    def safe_float(value: Any, default: float = 0.0) -> float:
        """安全的float转换
        
        Args:
            value: 待转换的值
            default: 转换失败时的默认值
            
        Returns:
            float值
        """
        if value is None:
            return default
            
        try:
            return float(value)
        except (ValueError, TypeError) as e:
            logger.warning(f"float转换失败: {value} -> {e}")
            return default
    
    @staticmethod
    def safe_int(value: Any, default: int = 0) -> int:
        """安全的int转换
        
        Args:
            value: 待转换的值
            default: 转换失败时的默认值
            
        Returns:
            int值
        """
        if value is None:
            return default
            
        try:
            return int(value)
        except (ValueError, TypeError) as e:
            logger.warning(f"int转换失败: {value} -> {e}")
            return default
    
    @staticmethod
    def clean_string(value: Any, max_length: int = None) -> str:
        """清理和标准化字符串

        Args:
            value: 待清理的值
            max_length: 最大长度限制

        Returns:
            清理后的字符串
        """
        if value is None:
            return ""

        # 转换为字符串并去除首尾空白
        cleaned = str(value).strip()

        # 长度限制
        if max_length and len(cleaned) > max_length:
            cleaned = cleaned[:max_length]
            logger.debug(f"字符串被截断到 {max_length} 字符")

        return cleaned

    # ==================== 日期处理方法（从DateUtils迁移） ====================

    @staticmethod
    def get_date_range(months: int, end_date: Optional[date] = None) -> Tuple[date, date]:
        """获取指定月数的日期范围

        Args:
            months: 月数（向前推算）
            end_date: 结束日期，默认为今天

        Returns:
            Tuple[date, date]: (开始日期, 结束日期)

        Examples:
            >>> DataUtils.get_date_range(3)  # 最近3个月
            (date(2024, 10, 20), date(2025, 1, 20))
        """
        from dateutil.relativedelta import relativedelta

        if end_date is None:
            end_date = date.today()

        start_date = end_date - relativedelta(months=months)
        return start_date, end_date

    @staticmethod
    def get_month_boundaries(target_month: str) -> Tuple[date, date]:
        """获取指定月份的边界日期

        Args:
            target_month: 目标月份，格式为 'YYYY-MM'

        Returns:
            Tuple[date, date]: (月初日期, 月末日期)

        Raises:
            ValueError: 当月份格式不正确时

        Examples:
            >>> DataUtils.get_month_boundaries('2024-01')
            (date(2024, 1, 1), date(2024, 1, 31))
        """
        from dateutil.relativedelta import relativedelta

        try:
            year, month = map(int, target_month.split('-'))
            start_date = date(year, month, 1)

            # 计算月末日期
            if month == 12:
                end_date = date(year + 1, 1, 1) - relativedelta(days=1)
            else:
                end_date = date(year, month + 1, 1) - relativedelta(days=1)

            return start_date, end_date
        except (ValueError, TypeError) as e:
            raise ValueError(f"无效的月份格式: {target_month}，应为 'YYYY-MM'") from e

    @staticmethod
    def get_recent_months(count: int, end_date: Optional[date] = None) -> List[str]:
        """获取最近N个月的月份列表

        Args:
            count: 月份数量
            end_date: 结束日期，默认为今天

        Returns:
            List[str]: 月份列表，格式为 ['YYYY-MM', ...]，按时间倒序

        Examples:
            >>> DataUtils.get_recent_months(3)
            ['2025-01', '2024-12', '2024-11']
        """
        from dateutil.relativedelta import relativedelta

        if end_date is None:
            end_date = date.today()

        months = []
        current_date = end_date.replace(day=1)  # 月初

        for _ in range(count):
            months.append(current_date.strftime('%Y-%m'))
            current_date = current_date - relativedelta(months=1)

        return months

    @staticmethod
    def format_month_display(month_str: str) -> str:
        """格式化月份显示

        Args:
            month_str: 月份字符串，格式为 'YYYY-MM'

        Returns:
            str: 格式化后的显示字符串，如 '2024年1月'

        Examples:
            >>> DataUtils.format_month_display('2024-01')
            '2024年1月'
        """
        try:
            year, month = map(int, month_str.split('-'))
            # 验证月份有效性
            if not (1 <= month <= 12):
                return month_str  # 无效月份，返回原字符串
            return f"{year}年{month}月"
        except (ValueError, TypeError):
            return month_str  # 如果格式不正确，返回原字符串
