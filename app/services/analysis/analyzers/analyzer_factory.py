"""分析器工厂

提供统一的分析器创建接口，支持依赖注入和配置管理。
"""

from typing import Type, TypeVar, Dict, Any, Optional
from .analyzer_context import AnalyzerContext
from .base_analyzer import BaseAnalyzer

# 单一职责分析器
from .single_income_expense_analyzer import IncomeExpenseAnalyzer
from .single_income_stability_analyzer import IncomeStabilityAnalyzer
from .single_cash_flow_analyzer import CashFlowAnalyzer
from .single_expense_pattern_analyzer import ExpensePatternAnalyzer

# 综合分析器
from .composite_income_analyzer import ComprehensiveIncomeAnalyzer
from .composite_financial_health_analyzer import FinancialHealthAnalyzer

# 类型变量
T = TypeVar('T', bound=BaseAnalyzer)


class AnalyzerFactory:
    """分析器工厂类
    
    提供统一的分析器创建接口，支持依赖注入和配置管理。
    使用工厂模式确保分析器的正确初始化和配置。
    """
    
    # 分析器类型注册表
    _analyzer_registry: Dict[str, Type[BaseAnalyzer]] = {
        # 单一职责分析器
        'income_expense': IncomeExpenseAnalyzer,
        'income_stability': IncomeStabilityAnalyzer,
        'cash_flow': CashFlowAnalyzer,
        'expense_pattern': ExpensePatternAnalyzer,
        
        # 综合分析器
        'comprehensive_income': ComprehensiveIncomeAnalyzer,
        'financial_health': FinancialHealthAnalyzer,
    }
    
    def __init__(self, context: AnalyzerContext):
        """初始化工厂
        
        Args:
            context: 分析器上下文，包含所有依赖项
        """
        self._context = context
    
    def create_analyzer(self, analyzer_type: str, **kwargs) -> BaseAnalyzer:
        """创建指定类型的分析器
        
        Args:
            analyzer_type: 分析器类型名称
            **kwargs: 额外的初始化参数
            
        Returns:
            分析器实例
            
        Raises:
            ValueError: 当分析器类型不存在时
        """
        if analyzer_type not in self._analyzer_registry:
            available_types = ', '.join(self._analyzer_registry.keys())
            raise ValueError(
                f"Unknown analyzer type: {analyzer_type}. "
                f"Available types: {available_types}"
            )
        
        analyzer_class = self._analyzer_registry[analyzer_type]
        
        # 合并上下文配置和额外参数
        init_kwargs = {'context': self._context}
        init_kwargs.update(kwargs)
        
        return analyzer_class(**init_kwargs)
    
    def create_typed_analyzer(self, analyzer_class: Type[T], **kwargs) -> T:
        """创建指定类型的分析器（类型安全版本）
        
        Args:
            analyzer_class: 分析器类
            **kwargs: 额外的初始化参数
            
        Returns:
            分析器实例
        """
        init_kwargs = {'context': self._context}
        init_kwargs.update(kwargs)
        
        return analyzer_class(**init_kwargs)
    
    # 便捷方法：单一职责分析器
    def create_income_expense_analyzer(self, **kwargs) -> IncomeExpenseAnalyzer:
        """创建收支分析器"""
        return self.create_typed_analyzer(IncomeExpenseAnalyzer, **kwargs)
    
    def create_income_stability_analyzer(self, **kwargs) -> IncomeStabilityAnalyzer:
        """创建收入稳定性分析器"""
        return self.create_typed_analyzer(IncomeStabilityAnalyzer, **kwargs)
    
    def create_cash_flow_analyzer(self, **kwargs) -> CashFlowAnalyzer:
        """创建现金流分析器"""
        return self.create_typed_analyzer(CashFlowAnalyzer, **kwargs)
    
    def create_spending_pattern_analyzer(self, **kwargs) -> SpendingPatternAnalyzer:
        """创建支出模式分析器"""
        return self.create_typed_analyzer(SpendingPatternAnalyzer, **kwargs)
    
    def create_budget_variance_analyzer(self, **kwargs) -> BudgetVarianceAnalyzer:
        """创建预算差异分析器"""
        return self.create_typed_analyzer(BudgetVarianceAnalyzer, **kwargs)
    
    # 便捷方法：综合分析器
    def create_comprehensive_income_analyzer(self, **kwargs) -> ComprehensiveIncomeAnalyzer:
        """创建综合收入分析器"""
        return self.create_typed_analyzer(ComprehensiveIncomeAnalyzer, **kwargs)
    
    def create_financial_health_analyzer(self, **kwargs) -> FinancialHealthAnalyzer:
        """创建财务健康分析器"""
        return self.create_typed_analyzer(FinancialHealthAnalyzer, **kwargs)
    
    # 批量创建方法
    def create_all_single_responsibility_analyzers(self) -> Dict[str, BaseAnalyzer]:
        """创建所有单一职责分析器
        
        Returns:
            分析器字典，键为分析器类型名称
        """
        single_responsibility_types = [
            'income_expense',
            'income_stability', 
            'cash_flow',
            'spending_pattern',
            'budget_variance'
        ]
        
        return {
            analyzer_type: self.create_analyzer(analyzer_type)
            for analyzer_type in single_responsibility_types
        }
    
    def create_all_comprehensive_analyzers(self) -> Dict[str, BaseAnalyzer]:
        """创建所有综合分析器
        
        Returns:
            分析器字典，键为分析器类型名称
        """
        comprehensive_types = [
            'comprehensive_income',
            'financial_health'
        ]
        
        return {
            analyzer_type: self.create_analyzer(analyzer_type)
            for analyzer_type in comprehensive_types
        }
    
    def create_all_analyzers(self) -> Dict[str, BaseAnalyzer]:
        """创建所有分析器
        
        Returns:
            分析器字典，键为分析器类型名称
        """
        return {
            analyzer_type: self.create_analyzer(analyzer_type)
            for analyzer_type in self._analyzer_registry.keys()
        }
    
    @classmethod
    def register_analyzer(cls, name: str, analyzer_class: Type[BaseAnalyzer]) -> None:
        """注册新的分析器类型
        
        Args:
            name: 分析器类型名称
            analyzer_class: 分析器类
        """
        cls._analyzer_registry[name] = analyzer_class
    
    @classmethod
    def unregister_analyzer(cls, name: str) -> None:
        """注销分析器类型
        
        Args:
            name: 分析器类型名称
        """
        cls._analyzer_registry.pop(name, None)
    
    @classmethod
    def get_available_analyzer_types(cls) -> list[str]:
        """获取所有可用的分析器类型
        
        Returns:
            分析器类型名称列表
        """
        return list(cls._analyzer_registry.keys())
    
    @property
    def context(self) -> AnalyzerContext:
        """获取分析器上下文"""
        return self._context
    
    def with_context(self, context: AnalyzerContext) -> 'AnalyzerFactory':
        """创建使用新上下文的工厂实例
        
        Args:
            context: 新的分析器上下文
            
        Returns:
            新的工厂实例
        """
        return AnalyzerFactory(context)