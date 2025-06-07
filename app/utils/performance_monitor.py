"""Performance monitoring utilities."""

import time
import logging
from functools import wraps
from typing import Callable, Any

logger = logging.getLogger(__name__)


def monitor_performance(operation_name: str = None):
    """Decorator to monitor performance of functions.
    
    Args:
        operation_name: Name of the operation for logging
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            start_time = time.time()
            op_name = operation_name or f"{func.__module__}.{func.__name__}"
            
            try:
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time
                logger.info(f"Performance: {op_name} completed in {execution_time:.3f}s")
                return result
            except Exception as e:
                execution_time = time.time() - start_time
                logger.error(f"Performance: {op_name} failed after {execution_time:.3f}s - {str(e)}")
                raise
        
        return wrapper
    return decorator


def performance_monitor(operation_name: str = None):
    """Alias for monitor_performance for backward compatibility."""
    return monitor_performance(operation_name)