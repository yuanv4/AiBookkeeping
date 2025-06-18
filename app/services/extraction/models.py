"""提取服务数据模型

此模块定义了提取服务使用的数据模型类。
"""

from dataclasses import dataclass
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
    def error_result(cls, error: str, bank: str = '未知', file_path: str = '') -> 'ExtractionResult':
        """创建错误结果
        
        Args:
            error: 错误信息
            bank: 银行名称
            file_path: 文件路径
            
        Returns:
            ExtractionResult: 错误结果实例
        """
        return cls(
            success=False,
            error=error,
            bank=bank,
            record_count=0,
            file_path=file_path
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
class StatementData:
    """银行对账单数据类
    
    用于表示从银行对账单中提取的交易数据。
    
    Attributes:
        date: 交易日期
        description: 交易描述
        amount: 交易金额
        balance: 余额
        transaction_type: 交易类型（收入/支出）
        reference: 参考号码
        category: 交易分类
    """
    date: datetime
    description: str
    amount: float
    balance: Optional[float] = None
    transaction_type: Optional[str] = None
    reference: Optional[str] = None
    category: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式
        
        Returns:
            Dict[str, Any]: 字典格式的数据
        """
        return {
            'date': self.date.isoformat() if self.date else None,
            'description': self.description,
            'amount': self.amount,
            'balance': self.balance,
            'transaction_type': self.transaction_type,
            'reference': self.reference,
            'category': self.category
        }