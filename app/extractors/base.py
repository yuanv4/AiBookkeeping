"""Base extractor for transaction data extraction - Double-Entry Version"""

from abc import ABC, abstractmethod
from typing import List

class BaseExtractor(ABC):
    """提取器基类 - 重构为支持复式记账"""

    @abstractmethod
    def can_handle(self, file_path: str, first_lines: List[str] = None) -> bool:
        """判断是否能处理该文件"""
        pass

    @abstractmethod
    def extract(self, file_path: str) -> List['TransactionDTO']:
        """执行提取，返回 TransactionDTO 列表"""
        pass
