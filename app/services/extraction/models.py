"""提取服务数据模型

此模块定义了提取服务使用的数据模型类。
"""

from dataclasses import dataclass
from typing import Dict, Any, List

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




