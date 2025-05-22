"""
日志配置模块
==========

为AI记账系统提供统一的日志配置功能，支持控制台和文件输出。
"""

import os
import logging
import logging.handlers
from typing import Optional, List, Dict, Any, Union
from pathlib import Path

# 导入配置管理器
from scripts.common.config import get_config_manager

def setup_logging(
    log_level: Optional[str] = None,
    log_file: Optional[str] = None,
    module_name: Optional[str] = None,
    console_output: bool = True,
    file_output: bool = True,
    log_format: Optional[str] = None,
    date_format: Optional[str] = None
) -> logging.Logger:
    """设置日志系统
    
    Args:
        log_level: 日志级别，默认从配置获取
        log_file: 日志文件路径，默认从配置获取
        module_name: 模块名称，用于日志记录器名称
        console_output: 是否输出到控制台
        file_output: 是否输出到文件
        log_format: 日志格式，默认从配置获取
        date_format: 日期格式，默认从配置获取
        
    Returns:
        logging.Logger: 配置好的日志记录器
    """
    # 获取配置管理器
    config_manager = get_config_manager()
    
    # 如果未指定日志级别，从配置中获取
    if log_level is None:
        log_level = config_manager.get('application.log_level', 'INFO')
    
    # 日志级别映射
    level_map = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR,
        'CRITICAL': logging.CRITICAL
    }
    
    # 获取数字日志级别
    numeric_level = level_map.get(log_level.upper(), logging.INFO)
    
    # 如果未指定日志格式，使用默认格式
    if log_format is None:
        log_format = config_manager.get(
            'logging.format', 
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    # 如果未指定日期格式，使用默认格式
    if date_format is None:
        date_format = config_manager.get(
            'logging.date_format', 
            '%Y-%m-%d %H:%M:%S'
        )
    
    # 创建格式化器
    formatter = logging.Formatter(log_format, date_format)
    
    # 获取日志记录器
    logger_name = module_name if module_name else 'aibookkeeping'
    logger = logging.getLogger(logger_name)
    logger.setLevel(numeric_level)
    
    # 防止重复添加处理器
    if logger.handlers:
        logger.handlers = []
    
    # 添加控制台处理器
    if console_output:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    # 添加文件处理器
    if file_output:
        # 如果未指定日志文件，从配置中获取
        if log_file is None:
            log_dir = config_manager.get('logging.directory', 'logs')
            
            # 确保日志目录存在
            # 如果是相对路径，相对于项目根目录
            if not os.path.isabs(log_dir):
                # 获取项目根目录
                current_dir = os.path.dirname(os.path.abspath(__file__))
                scripts_dir = os.path.dirname(current_dir)
                root_dir = os.path.dirname(scripts_dir)
                log_dir = os.path.join(root_dir, log_dir)
            
            os.makedirs(log_dir, exist_ok=True)
            
            # 构建日志文件名
            file_name = f"{logger_name}.log" if module_name else "app.log"
            log_file = os.path.join(log_dir, file_name)
        
        # 使用 RotatingFileHandler 自动轮转日志文件
        max_bytes = config_manager.get('logging.max_bytes', 10*1024*1024)  # 默认10MB
        backup_count = config_manager.get('logging.backup_count', 5)
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger

def get_logger(module_name: str) -> logging.Logger:
    """获取指定模块的日志记录器
    
    如果日志记录器已存在，则返回现有的，否则创建新的
    
    Args:
        module_name: 模块名称
    
    Returns:
        logging.Logger: 日志记录器
    """
    # 检查日志记录器是否已存在
    logger = logging.getLogger(module_name)
    
    # 如果已配置，直接返回
    if logger.handlers:
        return logger
    
    # 否则创建新的
    return setup_logging(module_name=module_name)

def set_level(logger_name: Optional[str] = None, level: str = 'INFO') -> None:
    """设置日志级别
    
    Args:
        logger_name: 日志记录器名称，如果为None则设置根日志记录器
        level: 日志级别
    """
    # 日志级别映射
    level_map = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR,
        'CRITICAL': logging.CRITICAL
    }
    
    # 获取数字日志级别
    numeric_level = level_map.get(level.upper(), logging.INFO)
    
    # 设置日志级别
    logger = logging.getLogger(logger_name) if logger_name else logging.getLogger()
    logger.setLevel(numeric_level) 