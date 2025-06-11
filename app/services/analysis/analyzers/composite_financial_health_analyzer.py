"""财务健康分析器。"""

from typing import Dict, List, Any
from datetime import datetime, timedelta
from app.services.analysis.analyzers.base_analyzer import BaseAnalyzer
from app.services.analysis.analyzers.single_cash_flow_analyzer import CashFlowAnalyzer
from app.services.analysis.analysis_models import (
    CashFlowHealth, CashFlowMetrics,
    FinancialResilience, ResilienceMetrics
)



class FinancialHealthAnalyzer(BaseAnalyzer):
    """财务健康分析器。
    
    使用组合模式，通过调用单一职责分析器来提供财务健康分析功能：
    - 现金流健康状况分析（通过 CashFlowAnalyzer）
    - 财务韧性分析（待实现）
    """
    
    def __init__(self, context):
        """初始化财务健康分析器。
        
        Args:
            context: 分析器上下文，包含依赖注入的服务
        """
        super().__init__(context)
        
        # 初始化单一职责分析器
        self.cash_flow_analyzer = CashFlowAnalyzer(context)
    
    @property
    def analyzer_type(self) -> str:
        """分析器类型。"""
        return "financial_health"
    
    def analyze_cash_flow(self) -> CashFlowHealth:
        """分析现金流健康状况。
        
        委托给 CashFlowAnalyzer 处理。
        """
        try:
            return self.cash_flow_analyzer.analyze()
        except Exception as e:
            self.logger.error(f"现金流分析失败: {e}")
            return CashFlowHealth()
    
    def analyze_resilience(self) -> FinancialResilience:
        """分析财务韧性。
        
        注意：此功能暂时保留简化实现，待创建对应的单一职责分析器后重构。
        """
        try:
            # 暂时返回空结果，等待实现
            self.logger.warning("财务韧性分析功能待实现")
            return FinancialResilience()
        except Exception as e:
            self.logger.error(f"财务韧性分析失败: {e}")
            return FinancialResilience()
    
    def get_comprehensive_health_summary(self) -> Dict[str, Any]:
        """获取综合财务健康摘要。
        
        整合现金流和韧性分析结果。
        """
        try:
            # 获取各项分析结果
            cash_flow = self.analyze_cash_flow()
            resilience = self.analyze_resilience()
            
            return {
                'cash_flow': {
                    'health_score': cash_flow.health_score if hasattr(cash_flow, 'health_score') else 0,
                    'liquidity_ratio': cash_flow.liquidity_ratio if hasattr(cash_flow, 'liquidity_ratio') else 0,
                    'cash_flow_trend': cash_flow.trend_direction if hasattr(cash_flow, 'trend_direction') else 'stable'
                },
                'resilience': {
                    'resilience_score': resilience.resilience_score if hasattr(resilience, 'resilience_score') else 0,
                    'resilience_level': resilience.resilience_level if hasattr(resilience, 'resilience_level') else 'unknown',
                    'risk_level': 'low'  # 简化实现
                },
                'overall_health_score': self._calculate_overall_health_score(cash_flow, resilience)
            }
        except Exception as e:
            self.logger.error(f"获取综合财务健康摘要失败: {e}")
            return {}
    
    def _calculate_overall_health_score(self, cash_flow: CashFlowHealth, resilience: FinancialResilience) -> float:
        """计算综合财务健康分数。
        
        Args:
            cash_flow: 现金流健康分析结果
            resilience: 财务韧性分析结果
            
        Returns:
            综合财务健康分数（0-100）
        """
        try:
            scores = []
            
            # 现金流健康分数（60%权重）
            if hasattr(cash_flow, 'health_score') and cash_flow.health_score > 0:
                scores.append(cash_flow.health_score * 0.6)
            
            # 财务韧性分数（40%权重）
            if hasattr(resilience, 'resilience_score') and resilience.resilience_score > 0:
                scores.append(resilience.resilience_score * 0.4)
            
            return sum(scores) if scores else 0.0
        except Exception as e:
            self.logger.error(f"计算综合财务健康分数失败: {e}")
            return 0.0