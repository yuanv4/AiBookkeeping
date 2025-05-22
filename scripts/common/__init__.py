"""
通用工具模块
==========

包含系统通用工具、错误处理和配置功能。
"""

# 导入并导出所有异常类
from scripts.common.exceptions import (
    AIBookkeepingError,
    # 数据提取相关异常
    ExtractorError,
    FileProcessingError,
    UnsupportedFileError,
    DataExtractionError,
    # 数据库相关异常
    DatabaseError,
    ConnectionError,
    QueryError,
    ImportError,
    # 分析模块相关异常
    AnalyzerError,
    InvalidParameterError,
    NoDataError,
    # 可视化模块相关异常
    VisualizationError,
    ChartGenerationError,
    # 配置相关异常
    ConfigError,
    ConfigLoadError,
    ConfigValidationError
)

# 导入并导出错误处理功能
from scripts.common.error_handler import (
    log_error,
    error_handler,
    retry,
    safe_operation
)

__all__ = [
    # 异常类
    'AIBookkeepingError',
    'ExtractorError',
    'FileProcessingError',
    'UnsupportedFileError',
    'DataExtractionError',
    'DatabaseError',
    'ConnectionError',
    'QueryError',
    'ImportError',
    'AnalyzerError',
    'InvalidParameterError',
    'NoDataError',
    'VisualizationError',
    'ChartGenerationError',
    'ConfigError',
    'ConfigLoadError',
    'ConfigValidationError',
    
    # 错误处理函数
    'log_error',
    'error_handler',
    'retry',
    'safe_operation'
]

# 版本信息
__version__ = '1.0.0' 