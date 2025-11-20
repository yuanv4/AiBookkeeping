"""Services package for the Flask application.

简化的服务层架构 - Phase 2 重构后保留 ImportService。

架构变更:
- TransactionService: 已移除，逻辑移至 Transaction Model
- CategoryService: 已移除，逻辑移至 category_utils
- ExtractorService: 已移除，逻辑移至 extractors 包
- ImportService: 保留，作为文件导入流程协调者

使用示例:
    from app.utils import get_import_service
    
    # 文件导入
    import_service = get_import_service()
    result = import_service.process_uploaded_files(files)
"""

# 核心服务类（仅保留 ImportService）
from .import_service import ImportService

__all__ = [
    'ImportService',
]
