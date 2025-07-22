"""服务层数据模型

简化的数据传输对象定义，专注于核心功能。
遵循简单实用的原则，避免过度抽象。
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from decimal import Decimal

# ==================== 核心数据模型 ====================

@dataclass
class ExtractedData:
    """从银行对账单中提取的标准化数据"""
    bank_name: str
    bank_code: str
    name: str
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

@dataclass
class DashboardData:
    """仪表盘数据"""
    period: Dict[str, Any]
    current_total_assets: float
    total_income: float
    total_expense: float
    net_income: float
    emergency_reserve_months: float
    monthly_trend: List[Dict[str, Any]]
    expense_composition: List[Dict[str, Any]]
    income_composition: List[Dict[str, Any]]
    transaction_count: int

# ==================== 常用常量 ====================

class ImportConstants:
    """导入相关常量"""
    ALLOWED_EXTENSIONS = {'xlsx', 'xls'}
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    DEFAULT_UPLOAD_FOLDER = 'uploads'

# ==================== 工具类 ====================

class DataConverters:
    """简化的数据转换工具类"""

    @staticmethod
    def decimal_to_float(value: Any) -> float:
        """将Decimal类型转换为float"""
        if value is None:
            return 0.0
        if isinstance(value, Decimal):
            return float(value)
        return float(value)
