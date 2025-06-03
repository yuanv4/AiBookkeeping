"""
统一错误处理模块
=============

提供统一的错误处理机制，包括错误日志记录、错误处理装饰器等。
"""

import sys
import traceback
import logging
import functools
import os
from typing import Type, Callable, Any, Dict, Optional, Union
import time

# 导入自定义异常
from scripts.common.exceptions import AIBookkeepingError

# 创建日志记录器
logger = logging.getLogger('error_handler')

def log_error(error: Exception, context: Optional[Dict[str, Any]] = None) -> None:
    """记录错误信息到日志
    
    Args:
        error: 异常对象
        context: 错误上下文信息
    """
    # 获取错误调用栈
    exc_type, exc_value, exc_traceback = sys.exc_info()
    stack_trace = traceback.format_exception(exc_type, exc_value, exc_traceback)
    
    # 获取异常详情
    if isinstance(error, AIBookkeepingError):
        error_type = error.__class__.__name__
        error_code = error.error_code
        error_message = error.message
        error_details = error.details
    else:
        error_type = error.__class__.__name__
        error_code = "ERR_UNKNOWN"
        error_message = str(error)
        error_details = None
    
    # 构建错误日志消息
    log_message = f"错误类型: {error_type} | 错误代码: {error_code} | 消息: {error_message}"
    
    # 添加上下文信息
    if context:
        context_str = " | ".join([f"{k}={v}" for k, v in context.items()])
        log_message += f" | 上下文: {context_str}"
    
    # 添加详情
    if error_details:
        log_message += f" | 详情: {error_details}"
    
    # 记录错误日志
    logger.error(log_message)
    logger.debug("错误调用栈: %s", "".join(stack_trace))


# 在装饰器函数中，移除重复的导入
def error_handler(reraise=True, fallback_value=None, log_level=logging.ERROR, expected_exceptions=None):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # 检查是否为预期异常
                if expected_exceptions and not isinstance(e, expected_exceptions):
                    raise
                
                # 记录错误
                if log_level >= logging.ERROR:
                    # 修复：创建context字典包含函数调用信息
                    context = {"function": func.__name__, "args": str(args), "kwargs": str(kwargs)}
                    log_error(e, context)
                elif log_level >= logging.WARNING:
                    logger.warning(f"警告: {func.__name__} 中发生异常: {str(e)}")
                elif log_level >= logging.INFO:
                    logger.info(f"信息: {func.__name__} 中发生异常: {str(e)}")
                
                # 处理异常
                if reraise:
                    # 如果是自定义异常，直接重新抛出
                    if isinstance(e, AIBookkeepingError):
                        raise
                    
                    # 否则包装为AIBookkeepingError
                    error_message = f"在 {func.__name__} 中发生异常: {str(e)}"
                    raise AIBookkeepingError(error_message, details=str(e))
                
                # 返回后备值
                return fallback_value
        return wrapper
    return decorator


def retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff_factor: float = 2.0,
    exceptions: Union[Type[Exception], tuple] = Exception
) -> Callable:
    """重试装饰器
    
    当函数调用失败时自动重试
    
    Args:
        max_attempts: 最大尝试次数
        delay: 初始延迟时间（秒）
        backoff_factor: 延迟时间的增长因子
        exceptions: 捕获的异常类型
        
    Returns:
        装饰后的函数
    
    Examples:
        ```python
        @retry(max_attempts=3, delay=1, backoff_factor=2)
        def unstable_network_call():
            # 可能因网络问题失败的代码
            pass
        ```
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            attempt = 1
            current_delay = delay
            
            while attempt <= max_attempts:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    # 最后一次尝试失败，记录错误并重新抛出
                    if attempt == max_attempts:
                        log_error(e, {'function': func.__name__, 'attempt': attempt})
                        raise
                    
                    # 记录重试信息
                    logger.warning(
                        f"函数 {func.__name__} 第 {attempt} 次调用失败: {str(e)}，"
                        f"{current_delay:.2f}秒后重试..."
                    )
                    
                    # 等待后重试
                    time.sleep(current_delay)
                    current_delay *= backoff_factor
                    attempt += 1
        return wrapper
    return decorator


def safe_operation(operation_name: str = "操作") -> Callable:
    """安全操作装饰器
    
    包装数据库操作等需要额外安全处理的函数
    
    Args:
        operation_name: 操作名称，用于日志记录
        
    Returns:
        装饰后的函数
        
    Examples:
        ```python
        @safe_operation("数据库查询")
        def query_database(sql):
            # 数据库操作代码
            pass
        ```
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            logger.info(f"开始{operation_name}: {func.__name__}")
            
            try:
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time
                logger.info(f"{operation_name}成功: {func.__name__}, 耗时: {execution_time:.2f}秒")
                return result
            except Exception as e:
                execution_time = time.time() - start_time
                log_error(e, {
                    'operation': operation_name,
                    'function': func.__name__,
                    'execution_time': f"{execution_time:.2f}秒"
                })
                raise
        return wrapper
    return decorator