"""基础分析器类 - 所有财务分析器的基类

该模块定义了所有财务分析器的基础接口和通用功能。
重构后的基类使用依赖注入模式，将具体实现移到服务层。

Created: 2024-12-19
Author: AI Assistant
Refactored: 2024-12-19
"""

import time
from abc import ABC, abstractmethod
from datetime import date, datetime
from typing import Dict, List, Optional, Any, Union
from decimal import Decimal

from ..analyzer_context import AnalyzerContext



class BaseAnalyzer(ABC):
    """财务分析器基类
    
    重构后的基类使用依赖注入模式，提供抽象接口和基础功能。
    具体的数据访问和计算逻辑已移到服务层。
    """
    
    def __init__(
        self, 
        start_date: date, 
        end_date: date, 
        context: AnalyzerContext,
        account_id: Optional[int] = None
    ):
        """初始化分析器
        
        Args:
            start_date: 分析开始日期
            end_date: 分析结束日期
            context: 分析器上下文，包含所有服务依赖
            account_id: 可选的账户ID，用于过滤特定账户的数据
        """
        self.start_date = start_date
        self.end_date = end_date
        self.account_id = account_id
        self.context = context
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # 验证日期范围
        if start_date > end_date:
            raise ValueError("开始日期不能晚于结束日期")
        
        # 获取服务引用
        self.data_service = context.data_service
        self.calculation_service = context.calculation_service
        self.cache_service = context.cache_service
    
    def analyze(self) -> Dict[str, Any]:
        """执行分析的通用模板方法
        
        Returns:
            分析结果字典
        """
        method_name = 'analyze'
        self.log_analysis_start(method_name)
        start_time = time.time()
        
        try:
            # 检查缓存
            cached_result = self.get_cached_result(method_name)
            if cached_result:
                return cached_result
            
            # 执行具体分析
            result = self._perform_analysis()
            
            # 缓存结果
            self.set_cached_result(method_name, result, ttl_minutes=30)
            
            duration_ms = (time.time() - start_time) * 1000
            self.log_analysis_complete(method_name, duration_ms)
            return result
            
        except Exception as e:
            self.handle_analysis_error(method_name, e)
            return self._get_error_result()
    
    @abstractmethod
    def _perform_analysis(self) -> Dict[str, Any]:
        """执行具体的分析逻辑
        
        子类必须实现此方法来提供具体的分析逻辑
        
        Returns:
            分析结果字典
        """
        pass
    
    def _get_error_result(self) -> Dict[str, Any]:
        """获取错误时的默认结果
        
        Returns:
            错误时的默认结果字典
        """
        return {
            'error': True,
            'message': '分析过程中发生错误',
            'analyzer_type': self.analyzer_type
        }
    
    @property
    def analyzer_type(self) -> str:
        """获取分析器类型
        
        Returns:
            分析器类型字符串
        """
        return self.__class__.__name__
    
    def get_cached_result(self, method_name: str, **kwargs) -> Optional[Any]:
        """获取缓存的分析结果
        
        Args:
            method_name: 方法名
            **kwargs: 其他参数
            
        Returns:
            缓存的结果，如果不存在则返回None
        """
        return self.context.get_cached_result(
            analyzer_type=self.analyzer_type,
            method_name=method_name,
            start_date=self.start_date,
            end_date=self.end_date,
            account_id=self.account_id,
            **kwargs
        )
    
    def set_cached_result(
        self, 
        method_name: str, 
        result: Any, 
        ttl_minutes: Optional[int] = None,
        **kwargs
    ) -> None:
        """设置缓存的分析结果
        
        Args:
            method_name: 方法名
            result: 分析结果
            ttl_minutes: TTL（分钟）
            **kwargs: 其他参数
        """
        self.context.set_cached_result(
            analyzer_type=self.analyzer_type,
            method_name=method_name,
            start_date=self.start_date,
            end_date=self.end_date,
            result=result,
            account_id=self.account_id,
            ttl_minutes=ttl_minutes,
            **kwargs
        )
    
    def log_analysis_start(self, method_name: str) -> None:
        """记录分析开始
        
        Args:
            method_name: 方法名
        """
        self.logger.info(
            f"开始执行 {self.analyzer_type}.{method_name} "
            f"(日期范围: {self.start_date} - {self.end_date}, "
            f"账户ID: {self.account_id or 'all'})"
        )
    
    def log_analysis_complete(self, method_name: str, duration_ms: float) -> None:
        """记录分析完成
        
        Args:
            method_name: 方法名
            duration_ms: 执行时间（毫秒）
        """
        self.logger.info(
            f"完成执行 {self.analyzer_type}.{method_name} "
            f"(耗时: {duration_ms:.2f}ms)"
        )
    
    def handle_analysis_error(self, method_name: str, error: Exception) -> None:
        """处理分析错误
        
        Args:
            method_name: 方法名
            error: 异常对象
        """
        self.logger.error(
            f"执行 {self.analyzer_type}.{method_name} 时发生错误: {error}",
            exc_info=True
        )
    
    def validate_date_range(self) -> bool:
        """验证日期范围
        
        Returns:
            日期范围是否有效
        """
        return self.start_date <= self.end_date
    
    def get_analysis_period_days(self) -> int:
        """获取分析期间的天数
        
        Returns:
            分析期间的天数
        """
        return (self.end_date - self.start_date).days + 1