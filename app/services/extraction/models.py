"""提取服务数据模型

此模块定义了提取服务使用的数据模型类。
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from datetime import datetime

@dataclass
class ExtractionResult:
    """提取结果数据类
    
    用于统一表示文件提取和验证的结果。
    
    Attributes:
        success: 是否成功
        bank: 银行名称
        record_count: 记录数量
        file_path: 文件路径
        error: 错误信息（如果有）
        data: 额外数据（如果有）
    """
    success: bool
    bank: str
    record_count: int
    file_path: str
    error: Optional[str] = None
    data: Optional[Dict[str, Any]] = None

    @classmethod
    def error_result(cls, error: str, bank: str = '未知', file_path: str = '', data: Optional[Dict[str, Any]] = None) -> 'ExtractionResult':
        """创建错误结果
        
        Args:
            error: 错误信息
            bank: 银行名称
            file_path: 文件路径
            data: 额外数据（如果有）
            
        Returns:
            ExtractionResult: 错误结果实例
        """
        return cls(
            success=False,
            error=error,
            bank=bank,
            record_count=0,
            file_path=file_path,
            data=data
        )

    @classmethod
    def success_result(cls, bank: str, record_count: int, file_path: str, data: Dict[str, Any]) -> 'ExtractionResult':
        """创建成功结果
        
        Args:
            bank: 银行名称
            record_count: 记录数量
            file_path: 文件路径
            data: 额外数据
            
        Returns:
            ExtractionResult: 成功结果实例
        """
        return cls(
            success=True,
            bank=bank,
            record_count=record_count,
            file_path=file_path,
            data=data
        )


@dataclass
class ExtractedData:
    """提取的数据
    
    用于表示从银行对账单中提取的标准化数据。
    
    Attributes:
        bank_name: 银行名称
        bank_code: 银行代码
        account_name: 账户名称
        account_number: 账户号码
        transactions: 交易记录列表
    """
    bank_name: str
    bank_code: str
    account_name: str
    account_number: str
    transactions: List[Dict[str, Any]]


@dataclass
class AccountExtractionPattern:
    """账户信息提取模式配置"""
    keyword: str        # 关键词，如 "户    名：" 或 "客户名称:"
    regex_pattern: str  # 正则表达式模式，如 r'户    名：(.+)'

@dataclass
class BankInfo:
    """银行基本信息配置"""
    code: str          # 银行代码，如 'CMB', 'CCB'
    name: str          # 银行名称，如 '招商银行'

@dataclass
class ExtractionConfig:
    """银行数据提取配置"""
    # 账户信息提取配置（必需字段，无默认值）
    account_name_pattern: 'AccountExtractionPattern'  # 账户名称提取模式
    account_number_pattern: 'AccountExtractionPattern'  # 账户号码提取模式
    # 表头定位配置
    header_keyword: str  # 用于定位数据表头的关键字
    # 列名映射配置：从银行原始列名到标准列名的映射
    column_mapping: Dict[str, str]  # 键为银行原始列名，值为标准列名
    # 可选字段（有默认值）
    bank_info: Optional[BankInfo] = None
    # 货币代码映射配置
    currency_mapping: Dict[str, str] = field(default_factory=lambda: {
        '人民币元': 'CNY',
    })  # 货币代码映射表，将银行原始货币描述映射为标准3字符代码

