"""Analyzer Factory Module.

包含分析器工厂类，用于统一创建和管理各种财务分析器。
实现工厂模式，提供类型安全的分析器创建和注册机制。
"""

from typing import Dict, Type, Optional, Any, List
from datetime import date
import logging
from abc import ABC

from .analyzers.base_analyzer import BaseAnalyzer
from .analyzers.comprehensive_income_analyzer import ComprehensiveIncomeAnalyzer
from .analyzers.growth_analyzer import GrowthAnalyzer
from .analyzers.financial_health_analyzer import FinancialHealthAnalyzer
from .analyzers.balance_analyzer import BalanceAnalyzer
from .analyzers.database_stats_analyzer import DatabaseStatsAnalyzer

logger = logging.getLogger(__name__)


class AnalyzerType:
    """分析器类型常量定义。"""
    # 新的合并分析器类型
    COMPREHENSIVE_INCOME = 'comprehensive_income'
    FINANCIAL_HEALTH = 'financial_health'
    
    # 向后兼容的类型（映射到新的合并分析器）
    INCOME_EXPENSE = 'income_expense'
    INCOME_STABILITY = 'stability'
    CASH_FLOW = 'cash_flow'
    INCOME_DIVERSITY = 'diversity'
    
    # 独立的分析器类型
    INCOME_GROWTH = 'growth'
    FINANCIAL_RESILIENCE = 'resilience'
    BALANCE = 'balance'
    DATABASE_STATS = 'database_stats'


class AnalyzerFactory:
    """分析器工厂类。
    
    提供统一的分析器创建接口，支持动态注册和类型安全的分析器管理。
    """
    
    # 分析器类型注册表
    _analyzers: Dict[str, Type[BaseAnalyzer]] = {}
    
    @classmethod
    def register_analyzer(cls, analyzer_type: str, analyzer_class: Type[BaseAnalyzer]) -> None:
        """注册分析器类型。
        
        Args:
            analyzer_type: 分析器类型标识
            analyzer_class: 分析器类
            
        Raises:
            ValueError: 当分析器类型已存在或分析器类不是BaseAnalyzer的子类时
        """
        if not issubclass(analyzer_class, BaseAnalyzer):
            raise ValueError(f"分析器类 {analyzer_class.__name__} 必须继承自 BaseAnalyzer")
            
        if analyzer_type in cls._analyzers:
            logger.warning(f"分析器类型 '{analyzer_type}' 已存在，将被覆盖")
            
        cls._analyzers[analyzer_type] = analyzer_class
        logger.info(f"已注册分析器: {analyzer_type} -> {analyzer_class.__name__}")
    
    @classmethod
    def create_analyzer(cls, analyzer_type: str, start_date: date, end_date: date, 
                       account_id: Optional[int] = None) -> BaseAnalyzer:
        """创建指定类型的分析器实例。
        
        Args:
            analyzer_type: 分析器类型
            start_date: 分析开始日期
            end_date: 分析结束日期
            account_id: 可选的账户ID
            
        Returns:
            BaseAnalyzer: 分析器实例
            
        Raises:
            ValueError: 当分析器类型不存在时
            Exception: 当分析器创建失败时
        """
        if analyzer_type not in cls._analyzers:
            available_types = list(cls._analyzers.keys())
            raise ValueError(f"未知的分析器类型: {analyzer_type}. 可用类型: {available_types}")
        
        analyzer_class = cls._analyzers[analyzer_type]
        
        try:
            return analyzer_class(start_date, end_date, account_id)
        except Exception as e:
            logger.error(f"创建分析器 {analyzer_type} 失败: {e}")
            raise Exception(f"无法创建分析器 {analyzer_type}: {str(e)}")
    
    @classmethod
    def create_all_analyzers(cls, start_date: date, end_date: date, 
                            account_id: Optional[int] = None) -> Dict[str, BaseAnalyzer]:
        """创建所有已注册的分析器实例。
        
        Args:
            start_date: 分析开始日期
            end_date: 分析结束日期
            account_id: 可选的账户ID
            
        Returns:
            Dict[str, BaseAnalyzer]: 分析器类型到实例的映射
        """
        analyzers = {}
        
        for analyzer_type in cls._analyzers:
            try:
                analyzers[analyzer_type] = cls.create_analyzer(
                    analyzer_type, start_date, end_date, account_id
                )
            except Exception as e:
                logger.error(f"创建分析器 {analyzer_type} 时出错: {e}")
                # 继续创建其他分析器，不因单个失败而中断
                continue
        
        return analyzers
    
    @classmethod
    def create_specific_analyzers(cls, analyzer_types: List[str], start_date: date, 
                                 end_date: date, account_id: Optional[int] = None) -> Dict[str, BaseAnalyzer]:
        """创建指定类型的分析器实例集合。
        
        Args:
            analyzer_types: 要创建的分析器类型列表
            start_date: 分析开始日期
            end_date: 分析结束日期
            account_id: 可选的账户ID
            
        Returns:
            Dict[str, BaseAnalyzer]: 分析器类型到实例的映射
        """
        analyzers = {}
        
        for analyzer_type in analyzer_types:
            try:
                analyzers[analyzer_type] = cls.create_analyzer(
                    analyzer_type, start_date, end_date, account_id
                )
            except Exception as e:
                logger.error(f"创建分析器 {analyzer_type} 时出错: {e}")
                continue
        
        return analyzers
    
    @classmethod
    def get_available_analyzers(cls) -> List[str]:
        """获取所有可用的分析器类型。
        
        Returns:
            List[str]: 可用的分析器类型列表
        """
        return list(cls._analyzers.keys())
    
    @classmethod
    def is_analyzer_registered(cls, analyzer_type: str) -> bool:
        """检查分析器类型是否已注册。
        
        Args:
            analyzer_type: 分析器类型
            
        Returns:
            bool: 是否已注册
        """
        return analyzer_type in cls._analyzers
    
    @classmethod
    def unregister_analyzer(cls, analyzer_type: str) -> bool:
        """注销分析器类型。
        
        Args:
            analyzer_type: 要注销的分析器类型
            
        Returns:
            bool: 是否成功注销
        """
        if analyzer_type in cls._analyzers:
            del cls._analyzers[analyzer_type]
            logger.info(f"已注销分析器: {analyzer_type}")
            return True
        return False


# 自动注册所有内置分析器
def _register_builtin_analyzers():
    """注册所有内置分析器。"""
    # 注册新的合并分析器
    AnalyzerFactory.register_analyzer(AnalyzerType.COMPREHENSIVE_INCOME, ComprehensiveIncomeAnalyzer)
    AnalyzerFactory.register_analyzer(AnalyzerType.FINANCIAL_HEALTH, FinancialHealthAnalyzer)
    
    # 向后兼容注册（映射到新的合并分析器）
    AnalyzerFactory.register_analyzer(AnalyzerType.INCOME_EXPENSE, ComprehensiveIncomeAnalyzer)
    AnalyzerFactory.register_analyzer(AnalyzerType.INCOME_STABILITY, ComprehensiveIncomeAnalyzer)
    AnalyzerFactory.register_analyzer(AnalyzerType.INCOME_DIVERSITY, ComprehensiveIncomeAnalyzer)
    AnalyzerFactory.register_analyzer(AnalyzerType.CASH_FLOW, FinancialHealthAnalyzer)
    AnalyzerFactory.register_analyzer(AnalyzerType.FINANCIAL_RESILIENCE, FinancialHealthAnalyzer)
    
    # 独立分析器注册
    AnalyzerFactory.register_analyzer(AnalyzerType.INCOME_GROWTH, GrowthAnalyzer)
    AnalyzerFactory.register_analyzer(AnalyzerType.BALANCE, BalanceAnalyzer)
    AnalyzerFactory.register_analyzer(AnalyzerType.DATABASE_STATS, DatabaseStatsAnalyzer)


# 模块加载时自动注册内置分析器
_register_builtin_analyzers()