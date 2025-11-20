"""Data Transfer Objects for the new double-entry system"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from datetime import date
from decimal import Decimal

@dataclass
class AccountIdentifier:
    """账户标识符 - 用于查找或创建账户"""
    bank_name: str
    account_number: str
    account_name: str = "未知账户"
    account_type: str = "ASSET"  # ASSET, LIABILITY, etc.
    currency: str = "CNY"

@dataclass
class EntryData:
    """分录数据 - 描述一笔资金变动"""
    account_identifier: AccountIdentifier
    amount: Decimal  # 正数=增加, 负数=减少
    memo: Optional[str] = None

@dataclass
class TransactionDTO:
    """交易数据传输对象 - Extractor 输出格式"""
    date: date
    description: str
    transaction_type: str  # EXPENSE, INCOME, TRANSFER
    entries: List[EntryData]  # 至少需要一个 Entry
    raw_data: Optional[Dict[str, Any]] = None
    link_id: Optional[str] = None

    def __post_init__(self):
        if not self.entries:
            raise ValueError("Transaction must have at least one entry")

