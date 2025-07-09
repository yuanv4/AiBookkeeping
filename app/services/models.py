"""服务层数据模型

统一的数据传输对象定义，简化了原来分散在各个服务中的DTO类。
专注于个人用户的核心需求，移除了过度复杂的数据结构。
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from decimal import Decimal

# ==================== 基础数据结构 ====================

@dataclass
class Period:
    """时间周期"""
    start_date: str
    end_date: str
    days: int

@dataclass
class CompositionItem:
    """构成项目（收入或支出分类）"""
    name: str
    amount: float
    percentage: float
    count: int

@dataclass
class TrendPoint:
    """趋势数据点"""
    date: str
    income: float = 0.0
    expense: float = 0.0
    net: float = 0.0

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

@dataclass
class PeriodSummary:
    """期间汇总数据"""
    period: Period
    total_income: float
    total_expense: float
    net_income: float
    transaction_count: int

@dataclass
class AccountSummary:
    """账户汇总信息"""
    account_id: int
    account_name: str
    account_number: str
    bank_name: str
    balance: float
    currency: str

@dataclass
class DashboardData:
    """仪表盘完整数据"""
    period: Period
    current_total_assets: float
    total_income: float
    total_expense: float
    net_income: float
    emergency_reserve_months: float
    monthly_trend: List[TrendPoint]
    expense_composition: List[CompositionItem]
    income_composition: List[CompositionItem]
    transaction_count: int

@dataclass
class ExpenseItem:
    """支出项目"""
    date: str
    amount: float
    counterparty: str
    description: str

# ==================== 便捷构造函数 ====================

def create_period(start_date: str, end_date: str) -> Period:
    """创建时间周期对象"""
    from datetime import datetime
    start = datetime.strptime(start_date, '%Y-%m-%d').date()
    end = datetime.strptime(end_date, '%Y-%m-%d').date()
    days = (end - start).days + 1
    return Period(start_date=start_date, end_date=end_date, days=days)

def create_composition_item(name: str, amount: float, total: float, count: int) -> CompositionItem:
    """创建构成项目对象"""
    percentage = (amount / total * 100) if total > 0 else 0
    return CompositionItem(
        name=name,
        amount=amount,
        percentage=round(percentage, 2),
        count=count
    )

def create_trend_point(date: str, income: float = 0.0, expense: float = 0.0) -> TrendPoint:
    """创建趋势数据点对象"""
    net = income - expense
    return TrendPoint(
        date=date,
        income=income,
        expense=expense,
        net=net
    )

# ==================== 数据验证函数 ====================

def validate_period(period: Period) -> bool:
    """验证时间周期数据"""
    try:
        from datetime import datetime
        start = datetime.strptime(period.start_date, '%Y-%m-%d')
        end = datetime.strptime(period.end_date, '%Y-%m-%d')
        return start <= end and period.days > 0
    except (ValueError, TypeError):
        return False

def validate_composition_items(items: List[CompositionItem]) -> bool:
    """验证构成项目数据"""
    if not items:
        return True
    
    total_percentage = sum(item.percentage for item in items)
    # 允许一定的浮点数误差
    return abs(total_percentage - 100.0) < 1.0 or total_percentage <= 100.0

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

def decimal_to_float(value: Decimal) -> float:
    """安全地将Decimal转换为float"""
    try:
        return float(value) if value is not None else 0.0
    except (ValueError, TypeError):
        return 0.0

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
