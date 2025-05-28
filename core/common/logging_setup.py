import logging
import os
from logging.handlers import RotatingFileHandler
from typing import Optional

# from flask import current_app # Removed

# 缓存已配置的日志记录器名称，避免重复配置
_configured_loggers = set()

def setup_logging(
    app,  # Added app parameter
    log_level_override: Optional[str] = None,
    log_file_override: Optional[str] = None,
    module_name: Optional[str] = None, # 如果为 None，则配置根记录器
    console_output_override: Optional[bool] = None,
    file_output_override: Optional[bool] = None,
    log_format_override: Optional[str] = None,
    date_format_override: Optional[str] = None
) -> logging.Logger:
    """设置日志系统

    Args:
        log_level_override: 覆盖配置中的日志级别
        log_file_override: 覆盖配置中的日志文件路径
        module_name: 要配置的模块名称，如果为 None，则配置根记录器。
        console_output_override: 是否覆盖配置中的控制台输出设置
        file_output_override: 是否覆盖配置中的文件输出设置
        log_format_override: 覆盖配置中的日志格式
        date_format_override: 覆盖配置中的日期格式

    Returns:
        logging.Logger: 配置好的日志记录器
    """
    # 确定要配置的记录器
    # 如果 module_name 为 None，则获取根记录器
    # 否则获取指定名称的记录器
    logger_to_configure = logging.getLogger(module_name)

    # 检查是否已经配置过，避免重复添加 handlers
    # 对于根记录器，我们可能希望在应用启动时强制重新配置
    # 对于特定模块的记录器，如果它已经有 handlers (可能继承自根记录器或已被配置)，
    # 并且我们不是要强制覆盖，则可以考虑跳过。
    # 为简单起见，如果 logger_to_configure 已经有 handlers，并且不是根记录器，
    # 且没有指定 module_name (意味着我们想配置根)，则先清除。
    # 或者，更简单的方式是，总是清除现有的 handlers 来确保配置生效。
    if logger_to_configure.handlers and module_name is not None:
        # 如果是特定模块且已有handler，通常意味着它已通过根记录器或其他方式配置
        # 但如果我们要显式配置它，还是清掉旧的
        pass # 决定是否需要清除，或者依赖下面的 logger.handlers = []

    # 获取配置，优先使用覆盖参数
    if app is None:
        # Fallback or raise error if app is critical for config
        # For now, let's assume if app is None, we might be in a non-Flask context
        # and try to proceed with defaults or raise a more specific error.
        # This part needs careful consideration based on how setup_logging is used outside Flask.
        # However, the primary goal here is to fix the RuntimeError within Flask context.
        raise ValueError("Flask app instance is required for logging setup.")

    config = app.config

    log_level = log_level_override if log_level_override is not None else config.get('LOG_LEVEL', 'INFO')
    console_output = console_output_override if console_output_override is not None else config.get('LOG_CONSOLE_OUTPUT', True)
    file_output = file_output_override if file_output_override is not None else config.get('LOG_FILE_OUTPUT', True)
    log_format = log_format_override if log_format_override is not None else config.get(
        'LOG_FORMAT',
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    date_format = date_format_override if date_format_override is not None else config.get(
        'LOG_DATE_FORMAT',
        '%Y-%m-%d %H:%M:%S'
    )

    level_map = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR,
        'CRITICAL': logging.CRITICAL
    }
    numeric_level = level_map.get(log_level.upper(), logging.INFO)

    logger_to_configure.setLevel(numeric_level)
    
    # 清除旧的 handlers，确保配置是最新的
    # 这一步很重要，特别是当 setup_logging 可能被多次调用时（尽管我们希望它只在初始化时被恰当调用）
    logger_to_configure.handlers = []
    # 如果是配置特定模块的记录器，我们可能不希望它将日志消息向上传播到根记录器，
    # 如果根记录器也有自己的处理器，这可能导致日志重复。
    # 但通常我们希望它传播，除非有特殊需求。
    # logger_to_configure.propagate = False # 通常保持为 True

    formatter = logging.Formatter(log_format, date_format)

    if console_output:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger_to_configure.addHandler(console_handler)

    if file_output:
        log_file = log_file_override # 优先使用参数
        if log_file is None:
            log_dir_config = config.get('LOG_DIR', 'logs')
            # 确保日志目录存在，相对于项目根目录 (run.py 所在目录)
            # app.root_path 指向 app 包的路径
            project_root = os.path.abspath(os.path.join(app.root_path, os.pardir))
            log_dir = os.path.join(project_root, log_dir_config) if not os.path.isabs(log_dir_config) else log_dir_config
            
            os.makedirs(log_dir, exist_ok=True)
            
            # 日志文件名基于 logger_to_configure.name 或 'app.log' (如果是根记录器)
            base_log_name = logger_to_configure.name if logger_to_configure.name != 'root' else 'app'
            log_file = os.path.join(log_dir, f"{base_log_name}.log")

        max_bytes = config.get('LOG_MAX_BYTES', 10 * 1024 * 1024)  # 10MB
        backup_count = config.get('LOG_BACKUP_COUNT', 5)
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        logger_to_configure.addHandler(file_handler)
    
    _configured_loggers.add(logger_to_configure.name)
    return logger_to_configure

def get_logger(module_name: str) -> logging.Logger:
    """获取指定模块的日志记录器。
    这个函数现在只返回一个 logger 实例，而不尝试配置它。
    配置应该由 app 初始化时对 setup_logging 的调用来完成。

    Args:
        module_name: 模块名称

    Returns:
        logging.Logger: 日志记录器实例
    """
    return logging.getLogger(module_name)