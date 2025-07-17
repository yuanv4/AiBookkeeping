"""服务层数据模型

统一的数据传输对象定义，简化了原来分散在各个服务中的DTO类。
专注于个人用户的核心需求，移除了过度复杂的数据结构。
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Tuple
from decimal import Decimal
from datetime import date, datetime
from dateutil.relativedelta import relativedelta

# ==================== 基础数据结构 ====================

# ==================== 简化的数据结构 ====================
# 以下数据结构已简化为字典，使用便捷构造函数创建：
# - Period: 使用 create_period() 创建字典 {'start_date': str, 'end_date': str, 'days': int}
# - CompositionItem: 使用 create_composition_item() 创建字典 {'name': str, 'amount': float, 'percentage': float, 'count': int}
# - TrendPoint: 使用 create_trend_point() 创建字典 {'date': str, 'income': float, 'expense': float, 'net': float}
# - PeriodSummary: 使用 create_period_summary() 创建字典
# - AccountSummary: 使用 create_account_summary() 创建字典
# - ExpenseItem: 使用 create_expense_item() 创建字典

# ==================== 提取服务数据模型 ====================

@dataclass
class ExtractedData:
    """从银行对账单中提取的标准化数据"""
    bank_name: str
    bank_code: str
    account_name: str
    account_number: str
    transactions: List[Dict[str, Any]]

@dataclass
class ImportResult:
    """文件导入结果"""
    success: bool
    bank: Optional[str]
    record_count: int
    file_path: str
    error: Optional[str] = None

# ==================== 报告服务数据模型 ====================

# PeriodSummary, AccountSummary 已简化为字典，使用对应的便捷构造函数创建

@dataclass
class DashboardData:
    """仪表盘完整数据"""
    period: Dict[str, Any]  # 使用字典替代Period DTO
    current_total_assets: float
    total_income: float
    total_expense: float
    net_income: float
    emergency_reserve_months: float
    monthly_trend: List[Dict[str, Any]]  # 使用字典替代TrendPoint DTO
    expense_composition: List[Dict[str, Any]]  # 使用字典替代CompositionItem DTO
    income_composition: List[Dict[str, Any]]  # 使用字典替代CompositionItem DTO
    transaction_count: int

# ExpenseItem 已简化为字典，使用 create_expense_item() 便捷构造函数创建

# ==================== 便捷构造函数 ====================

def create_period(start_date: str, end_date: str) -> Dict[str, Any]:
    """创建时间周期字典对象"""
    from datetime import datetime
    start = datetime.strptime(start_date, '%Y-%m-%d').date()
    end = datetime.strptime(end_date, '%Y-%m-%d').date()
    days = (end - start).days + 1
    return {
        'start_date': start_date,
        'end_date': end_date,
        'days': days
    }

def create_composition_item(name: str, amount: float, total: float, count: int) -> Dict[str, Any]:
    """创建构成项目字典对象"""
    percentage = (amount / total * 100) if total > 0 else 0
    return {
        'name': name,
        'amount': amount,
        'percentage': round(percentage, 2),
        'count': count
    }

def create_trend_point(date: str, income: float = 0.0, expense: float = 0.0) -> Dict[str, Any]:
    """创建趋势数据点字典对象"""
    net = income - expense
    return {
        'date': date,
        'income': income,
        'expense': expense,
        'net': net
    }

def create_period_summary(period: Dict[str, Any], total_income: float, total_expense: float,
                         net_income: float, transaction_count: int) -> Dict[str, Any]:
    """创建期间汇总字典对象"""
    return {
        'period': period,
        'total_income': total_income,
        'total_expense': total_expense,
        'net_income': net_income,
        'transaction_count': transaction_count
    }

def create_account_summary(account_id: int, account_name: str, account_number: str,
                          bank_name: str, balance: float, currency: str) -> Dict[str, Any]:
    """创建账户汇总字典对象"""
    return {
        'account_id': account_id,
        'account_name': account_name,
        'account_number': account_number,
        'bank_name': bank_name,
        'balance': balance,
        'currency': currency
    }

def create_expense_item(date: str, amount: float, counterparty: str, description: str) -> Dict[str, Any]:
    """创建支出项目字典对象"""
    return {
        'date': date,
        'amount': amount,
        'counterparty': counterparty,
        'description': description
    }

# ==================== 数据验证函数 ====================

def validate_period(period: Dict[str, Any]) -> bool:
    """验证时间周期字典数据"""
    try:
        from datetime import datetime
        start = datetime.strptime(period['start_date'], '%Y-%m-%d')
        end = datetime.strptime(period['end_date'], '%Y-%m-%d')
        return start <= end and period['days'] > 0
    except (ValueError, TypeError, KeyError):
        return False

def validate_composition_items(items: List[Dict[str, Any]]) -> bool:
    """验证构成项目字典数据"""
    if not items:
        return True

    try:
        total_percentage = sum(item['percentage'] for item in items)
        # 允许一定的浮点数误差
        return abs(total_percentage - 100.0) < 1.0 or total_percentage <= 100.0
    except (KeyError, TypeError):
        return False

def validate_dashboard_data(data: DashboardData) -> bool:
    """验证仪表盘数据"""
    return (
        validate_period(data.period) and
        data.current_total_assets >= 0 and
        data.total_income >= 0 and
        data.total_expense >= 0 and
        data.emergency_reserve_months >= 0 and
        validate_composition_items(data.expense_composition) and
        validate_composition_items(data.income_composition)
    )

# ==================== 数据转换函数 ====================
# 注意：decimal_to_float 函数已移至 DataConverters.decimal_to_float
# 为了向后兼容，保留一个简单的包装函数

def decimal_to_float(value: Decimal) -> float:
    """安全地将Decimal转换为float

    注意：此函数已弃用，请使用 DataConverters.decimal_to_float
    """
    from .models import DataConverters
    return DataConverters.decimal_to_float(value)

def safe_percentage(part: float, total: float) -> float:
    """安全地计算百分比"""
    if total == 0:
        return 0.0
    return round((part / total) * 100, 2)

def format_currency(amount: float, currency: str = 'CNY') -> str:
    """格式化货币显示"""
    if currency == 'CNY':
        return f"¥{amount:,.2f}"
    elif currency == 'USD':
        return f"${amount:,.2f}"
    else:
        return f"{amount:,.2f} {currency}"

# ==================== 常用常量 ====================

class ReportConstants:
    """报告相关常量"""
    DEFAULT_CURRENCY = 'CNY'
    DEFAULT_MONTHS = 12
    DEFAULT_LIMIT = 10
    MIN_EMERGENCY_RESERVE = 3.0  # 最低应急储备月数
    MAX_TREND_POINTS = 24  # 最大趋势点数量

class ImportConstants:
    """导入相关常量"""
    ALLOWED_EXTENSIONS = {'xlsx', 'xls'}
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    DEFAULT_UPLOAD_FOLDER = 'uploads'

# ==================== 错误类定义 ====================

class ServiceError(Exception):
    """服务层基础异常"""
    pass

class DataValidationError(ServiceError):
    """数据验证异常"""
    pass

class ImportError(ServiceError):
    """导入异常"""
    pass

class ReportError(ServiceError):
    """报告生成异常"""
    pass

# ==================== 工具类定义 ====================

class DateUtils:
    """日期处理工具类

    统一的日期计算和处理方法，避免在各个服务中重复实现相同的日期逻辑。
    """

    @staticmethod
    def get_date_range(months: int, end_date: Optional[date] = None) -> Tuple[date, date]:
        """获取指定月数的日期范围

        Args:
            months: 月数（向前推算）
            end_date: 结束日期，默认为今天

        Returns:
            Tuple[date, date]: (开始日期, 结束日期)
        """
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
        """
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
        """
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
        """
        try:
            year, month = map(int, month_str.split('-'))
            return f"{year}年{month}月"
        except (ValueError, TypeError):
            return month_str  # 如果格式不正确，返回原字符串

    @staticmethod
    def is_valid_month_format(month_str: str) -> bool:
        """验证月份格式是否正确

        Args:
            month_str: 月份字符串

        Returns:
            bool: 格式是否正确
        """
        try:
            year, month = map(int, month_str.split('-'))
            return 1 <= month <= 12 and year > 1900
        except (ValueError, TypeError, AttributeError):
            return False

class DataConverters:
    """数据转换工具类

    统一的数据类型转换方法，避免在各个服务中重复实现相同的转换逻辑。
    """

    @staticmethod
    def decimal_to_float(value: Any) -> float:
        """将Decimal类型转换为float

        Args:
            value: 待转换的值，可以是Decimal、int、float或字符串

        Returns:
            float: 转换后的浮点数

        Raises:
            ValueError: 当值无法转换为数字时
        """
        if value is None:
            return 0.0

        if isinstance(value, Decimal):
            return float(value)
        elif isinstance(value, (int, float)):
            return float(value)
        elif isinstance(value, str):
            try:
                return float(value)
            except ValueError:
                # 尝试先转换为Decimal再转换为float
                try:
                    return float(Decimal(value))
                except (ValueError, TypeError) as e:
                    raise ValueError(f"无法将字符串 '{value}' 转换为数字") from e
        else:
            try:
                return float(value)
            except (ValueError, TypeError) as e:
                raise ValueError(f"无法将类型 {type(value)} 的值转换为float") from e

    @staticmethod
    def safe_decimal_to_float(value: Any, default: float = 0.0) -> float:
        """安全地将Decimal转换为float，失败时返回默认值

        Args:
            value: 待转换的值
            default: 转换失败时的默认值

        Returns:
            float: 转换后的浮点数或默认值
        """
        try:
            return DataConverters.decimal_to_float(value)
        except (ValueError, TypeError):
            return default

    @staticmethod
    def format_currency(value: Any, currency_symbol: str = '¥') -> str:
        """格式化货币显示

        Args:
            value: 金额值
            currency_symbol: 货币符号

        Returns:
            str: 格式化后的货币字符串
        """
        try:
            amount = DataConverters.decimal_to_float(value)
            return f"{currency_symbol}{amount:,.2f}"
        except (ValueError, TypeError):
            return f"{currency_symbol}0.00"
