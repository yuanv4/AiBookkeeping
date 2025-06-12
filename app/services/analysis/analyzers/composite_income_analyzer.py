# -*- coding: utf-8 -*-
"""
综合收入分析器。
合并了收入支出分析、收入稳定性分析和收入多样性分析功能。
优化版本：使用新的基类和缓存策略。
"""

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from app.services.analysis.analyzers.base_analyzer import BaseAnalyzer
from app.services.analysis.analyzers.single_income_expense_analyzer import IncomeExpenseAnalyzer
from app.services.analysis.analyzers.single_income_stability_analyzer import IncomeStabilityAnalyzer
from app.services.analysis.analysis_models import (
    IncomeExpenseAnalysis, IncomeStability, IncomeDiversity,
    StabilityMetrics, DiversityMetrics,
    MonthlyData, OverallStats
)



class ComprehensiveIncomeAnalyzer(BaseAnalyzer):
    """综合收入分析器。
    
    使用组合模式，通过调用单一职责分析器来提供全面的收入分析功能：
    - 收入支出分析（通过 IncomeExpenseAnalyzer）
    - 收入稳定性分析（通过 IncomeStabilityAnalyzer）
    - 收入多样性分析（待实现）
    """
    
    def __init__(self, context):
        """初始化综合收入分析器。
        
        Args:
            context: 分析器上下文，包含依赖注入的服务
        """
        super().__init__(context)
        
        # 初始化单一职责分析器
        self.income_expense_analyzer = IncomeExpenseAnalyzer(context)
        self.income_stability_analyzer = IncomeStabilityAnalyzer(context)
    
    @property
    def analyzer_type(self) -> str:
        """分析器类型。"""
        return "comprehensive_income"
    
    def analyze_income_expense(self) -> IncomeExpenseAnalysis:
        """分析收入支出状况。
        
        委托给 IncomeExpenseAnalyzer 处理。
        """
        try:
            return self.income_expense_analyzer.analyze()
        except Exception as e:
            self.logger.error(f"收入支出分析失败: {e}")
            return IncomeExpenseAnalysis()
    
    def analyze_income_stability(self) -> IncomeStability:
        """分析收入稳定性。
        
        委托给 IncomeStabilityAnalyzer 处理。
        """
        try:
            return self.income_stability_analyzer.analyze()
        except Exception as e:
            self.logger.error(f"收入稳定性分析失败: {e}")
            return IncomeStability()
    
    def analyze_income_diversity(self) -> IncomeDiversity:
        """分析收入多样性。
        
        注意：此功能暂时保留原有实现，待创建对应的单一职责分析器后重构。
        """
        try:
            # 暂时返回空结果，等待实现
            self.logger.warning("收入多样性分析功能待实现")
            return IncomeDiversity()
            
        except Exception as e:
            self.logger.error(f"收入多样性分析失败: {e}")
            return IncomeDiversity()
    
    def get_comprehensive_summary(self) -> Dict[str, Any]:
        """获取综合收入分析摘要。
        
        整合各个单一职责分析器的结果。
        """
        try:
            # 获取各项分析结果
            income_expense = self.analyze_income_expense()
            stability = self.analyze_income_stability()
            diversity = self.analyze_income_diversity()
            
            return {
                'income_expense': {
                    'total_income': income_expense.total_income if hasattr(income_expense, 'total_income') else 0,
                    'total_expense': income_expense.total_expense if hasattr(income_expense, 'total_expense') else 0,
                    'net_income': income_expense.net_income if hasattr(income_expense, 'net_income') else 0,
                    'income_expense_ratio': income_expense.metrics.income_expense_ratio if hasattr(income_expense, 'metrics') and income_expense.metrics else 0
                },
                'stability': {
                    'stability_score': stability.stability_score if hasattr(stability, 'stability_score') else 0,
                    'trend_direction': stability.trend_direction if hasattr(stability, 'trend_direction') else 'stable',
                    'coefficient_of_variation': stability.metrics.coefficient_of_variation if hasattr(stability, 'metrics') and stability.metrics else 0
                },
                'diversity': {
                    'diversity_score': diversity.diversity_score if hasattr(diversity, 'diversity_score') else 0,
                    'total_sources': diversity.metrics.total_sources if hasattr(diversity, 'metrics') and diversity.metrics else 0,
                    'primary_source_ratio': diversity.primary_source_ratio if hasattr(diversity, 'primary_source_ratio') else 0
                },
                'overall_health_score': self._calculate_overall_health_score(income_expense, stability, diversity)
            }
        except Exception as e:
            self.logger.error(f"获取综合收入分析摘要失败: {e}")
            return {}
    
    def _calculate_overall_health_score(self, income_expense: IncomeExpenseAnalysis, 
                                      stability: IncomeStability, 
                                      diversity: IncomeDiversity) -> float:
        """计算综合健康分数。
        
        Args:
            income_expense: 收入支出分析结果
            stability: 收入稳定性分析结果
            diversity: 收入多样性分析结果
            
        Returns:
            综合健康分数（0-100）
        """
        try:
            scores = []
            
            # 收支健康分数（30%权重）
            if hasattr(income_expense, 'net_income') and income_expense.net_income > 0:
                # 基于净收入和收支比例计算分数
                ie_score = min(100, abs(income_expense.net_income) / 1000 * 10)  # 简化计算
                scores.append(ie_score * 0.3)
            
            # 稳定性分数（40%权重）
            if hasattr(stability, 'stability_score') and stability.stability_score > 0:
                scores.append(stability.stability_score * 0.4)
            
            # 多样性分数（30%权重）
            if hasattr(diversity, 'diversity_score') and diversity.diversity_score > 0:
                scores.append(diversity.diversity_score * 0.3)
            
            return sum(scores) if scores else 0.0
        except Exception as e:
            self.logger.error(f"计算综合健康分数失败: {e}")
            return 0.0
    
    def _perform_analysis(self) -> Dict[str, Any]:
        """执行综合收入分析。
        
        实现BaseAnalyzer要求的抽象方法。
        
        Returns:
            综合分析结果字典
        """
        try:
            return self.get_comprehensive_summary()
        except Exception as e:
            self.logger.error(f"执行综合收入分析失败: {e}")
            return {}