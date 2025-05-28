"""
自定义异常模块
============

为AI记账系统定义统一的异常类，用于标准化错误处理。
所有模块应使用这些异常类而不是通用异常。
"""

class AIBookkeepingError(Exception):
    """AI记账系统基础异常类，所有自定义异常继承自此类"""
    
    def __init__(self, message="系统内部错误", error_code=None, details=None):
        """初始化异常
        
        Args:
            message: 错误消息
            error_code: 错误代码
            details: 错误详情
        """
        self.message = message
        self.error_code = error_code or "ERR_UNKNOWN"
        self.details = details
        super().__init__(self.message)
    
    def to_dict(self):
        """转换为字典格式，便于JSON序列化"""
        return {
            'error_code': self.error_code,
            'message': self.message,
            'details': self.details
        }


# 数据提取相关异常
class ExtractorError(AIBookkeepingError):
    """数据提取模块通用异常"""
    def __init__(self, message="数据提取错误", error_code="ERR_EXTRACTOR", details=None):
        super().__init__(message, error_code, details)


class FileProcessingError(ExtractorError):
    """文件处理异常"""
    def __init__(self, message="文件处理错误", error_code="ERR_FILE_PROCESSING", details=None):
        super().__init__(message, error_code, details)


class UnsupportedFileError(ExtractorError):
    """不支持的文件类型异常"""
    def __init__(self, message="不支持的文件类型", error_code="ERR_UNSUPPORTED_FILE", details=None):
        super().__init__(message, error_code, details)


class DataExtractionError(ExtractorError):
    """数据提取异常"""
    def __init__(self, message="数据提取失败", error_code="ERR_DATA_EXTRACTION", details=None):
        super().__init__(message, error_code, details)


# 数据库相关异常
class DatabaseError(AIBookkeepingError):
    """数据库模块通用异常"""
    def __init__(self, message="数据库操作错误", error_code="ERR_DATABASE", details=None):
        super().__init__(message, error_code, details)


class ConnectionError(DatabaseError):
    """数据库连接异常"""
    def __init__(self, message="数据库连接失败", error_code="ERR_DB_CONNECTION", details=None):
        super().__init__(message, error_code, details)


class QueryError(DatabaseError):
    """数据库查询异常"""
    def __init__(self, message="数据库查询失败", error_code="ERR_DB_QUERY", details=None):
        super().__init__(message, error_code, details)


class ImportError(DatabaseError):
    """数据导入异常"""
    def __init__(self, message="数据导入失败", error_code="ERR_DB_IMPORT", details=None):
        super().__init__(message, error_code, details)


# 分析模块相关异常
class AnalyzerError(AIBookkeepingError):
    """分析模块通用异常"""
    def __init__(self, message="数据分析错误", error_code="ERR_ANALYZER", details=None):
        super().__init__(message, error_code, details)


class InvalidParameterError(AnalyzerError):
    """参数无效异常"""
    def __init__(self, message="参数无效", error_code="ERR_INVALID_PARAMETER", details=None):
        super().__init__(message, error_code, details)


class NoDataError(AnalyzerError):
    """无数据异常"""
    def __init__(self, message="无可分析数据", error_code="ERR_NO_DATA", details=None):
        super().__init__(message, error_code, details)


# 可视化模块相关异常
class VisualizationError(AIBookkeepingError):
    """可视化模块通用异常"""
    def __init__(self, message="数据可视化错误", error_code="ERR_VISUALIZATION", details=None):
        super().__init__(message, error_code, details)


class ChartGenerationError(VisualizationError):
    """图表生成异常"""
    def __init__(self, message="图表生成失败", error_code="ERR_CHART_GENERATION", details=None):
        super().__init__(message, error_code, details)


# 配置相关异常
class ConfigError(AIBookkeepingError):
    """配置模块通用异常"""
    def __init__(self, message="配置错误", error_code="ERR_CONFIG", details=None):
        super().__init__(message, error_code, details)


class ConfigLoadError(ConfigError):
    """配置加载异常"""
    def __init__(self, message="配置加载失败", error_code="ERR_CONFIG_LOAD", details=None):
        super().__init__(message, error_code, details)


class ConfigValidationError(ConfigError):
    """配置验证异常"""
    def __init__(self, message="配置验证失败", error_code="ERR_CONFIG_VALIDATION", details=None):
        super().__init__(message, error_code, details) 