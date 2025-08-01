"""Services package for the Flask application.

简化的服务层架构，专注于简单、实用、易维护的原则。

架构特点:
- TransactionService: 交易数据管理服务
- ImportService: 文件导入服务，集成了提取、解析、商家识别功能
- CategoryService: 商户分类服务，提供分类算法和业务分析功能
- ExtractorService: 银行交易数据提取服务

使用示例:
    from app.services import TransactionService, ImportService, CategoryService

    # 服务层操作
    transaction_service = TransactionService()
    category_service = CategoryService()

    # 文件导入（依赖注入）
    import_service = ImportService(transaction_service)
    result = import_service.process_uploaded_files(files)

    # 商户分类
    category = category_service.classify_merchant('麦当劳')
"""

from dataclasses import dataclass
from typing import List, Dict, Any

@dataclass
class ExtractedData:
    """从银行对账单中提取的标准化数据

    字段直接对应Transaction模型的字段：
    - bank_name -> Transaction.bank_name
    - bank_code -> Transaction.bank_code
    - account_name -> Transaction.account_name
    - account_number -> Transaction.account_number
    - transactions -> 用于创建Transaction记录的数据列表
    """
    bank_name: str
    bank_code: str
    account_name: str  # 账户名称
    account_number: str
    transactions: List[Dict[str, Any]]

# 核心服务类
from .transaction_service import TransactionService
from .import_service import ImportService
from .category_service import CategoryService
from .extractor_service import ExtractorService

# 提取器注册列表
ALL_EXTRACTORS = [
    lambda: ExtractorService('CMB'),
    lambda: ExtractorService('CCB')
]

__all__ = [
    # 核心服务类
    'TransactionService',
    'ImportService',
    'CategoryService',
    'ExtractorService',
    # 核心DTO类
    'ExtractedData',
    # 提取器
    'ALL_EXTRACTORS',
]