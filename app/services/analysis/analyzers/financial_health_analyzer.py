# -*- coding: utf-8 -*-
"""
财务健康分析器。
合并了现金流健康状况分析和财务韧性分析功能。
优化版本：使用新的基类和缓存策略。
"""

from typing import Dict, List, Any
import logging
from datetime import datetime, timedelta
from sqlalchemy import func

from app.models import Transaction, Account, db
from app.services.analysis.analysis_models import (
    CashFlowHealth, CashFlowMetrics,
    FinancialResilience, ResilienceMetrics
)
from app.utils.query_builder import OptimizedQueryBuilder, AnalysisException
from app.utils.cache_manager import optimized_cache
from .base_analyzer import BaseAnalyzer
from app.utils.performance_monitor import performance_monitor

logger = logging.getLogger(__name__)


class FinancialHealthAnalyzer(BaseAnalyzer):
    """财务健康分析器。
    
    整合现金流健康状况分析和财务韧性分析功能。
    """
    
    @performance_monitor("cash_flow_analysis")
    def analyze_cash_flow(self) -> CashFlowHealth:
        """分析现金流健康状况。"""
        try:
            # 使用优化的现金流分析
            cash_flow_data = self._analyze_cash_flow_patterns()
            metrics = self._build_cash_flow_metrics(cash_flow_data)
            
            return CashFlowHealth(
                metrics=metrics,
                monthly_flow=cash_flow_data.get('monthly_flow', []),
                gap_frequency=cash_flow_data.get('gap_frequency', 0.0),
                avg_gap=cash_flow_data.get('avg_gap', 0.0),
                total_balance=cash_flow_data.get('total_balance', 0.0),
                monthly_cash_flow=cash_flow_data.get('monthly_cash_flow', [])
            )
        except Exception as e:
            logger.error(f"现金流分析失败: {e}")
            return CashFlowHealth()
    
    @performance_monitor("financial_resilience_analysis")
    def analyze_resilience(self) -> FinancialResilience:
        """分析财务韧性。"""
        try:
            metrics = self._calculate_resilience_metrics()
            scenario_analysis = self._calculate_scenario_analysis()
            
            # 计算韧性分数
            resilience_score = self._calculate_resilience_score(metrics)
            resilience_level = self._determine_resilience_level(resilience_score)
            
            return FinancialResilience(
                resilience_score=resilience_score,
                resilience_level=resilience_level,
                metrics=metrics,
                recommendations=self._generate_recommendations(metrics),
                risk_factors=self._identify_risk_factors(metrics)
            )
        except Exception as e:
            logger.error(f"财务韧性分析失败: {e}")
            return FinancialResilience()
    
    @optimized_cache('cash_flow_analysis', expire_minutes=20, priority=2)
    def _analyze_cash_flow_patterns(self) -> Dict[str, Any]:
        """分析现金流模式。"""
        try:
            query_builder = OptimizedQueryBuilder()
            
            # 获取现金流分析查询
            cash_flow_query = query_builder.build_cash_flow_analysis_query(
                account_id=self.account_id,
                start_date=self.start_date,
                end_date=self.end_date
            )
            
            # 执行查询
            results = query_builder.execute_with_error_handling(
                cash_flow_query, "现金流分析查询"
            )
            
            # 处理结果
            daily_balances = []
            monthly_flows = {}
            
            for result in results:
                daily_balances.append({
                    'date': result.date,
                    'amount': float(result.amount),
                    'running_balance': float(result.running_balance),
                    'daily_net': float(result.daily_net),
                    'daily_income': float(result.daily_income),
                    'daily_expense': float(result.daily_expense)
                })
                
                # 按月汇总
                month_key = f"{result.date.year}-{result.date.month:02d}"
                if month_key not in monthly_flows:
                    monthly_flows[month_key] = {
                        'income': 0.0,
                        'expense': 0.0,
                        'net': 0.0
                    }
                
                monthly_flows[month_key]['income'] += float(result.daily_income)
                monthly_flows[month_key]['expense'] += float(result.daily_expense)
                monthly_flows[month_key]['net'] += float(result.daily_net)
            
            # 计算统计指标
            monthly_nets = [flow['net'] for flow in monthly_flows.values()]
            positive_months = sum(1 for net in monthly_nets if net > 0)
            negative_months = sum(1 for net in monthly_nets if net < 0)
            
            # 计算波动性
            volatility = self._calculate_coefficient_of_variation(monthly_nets)
            
            # 计算缺口频率和平均缺口
            gaps = [net for net in monthly_nets if net < 0]
            gap_frequency = len(gaps) / len(monthly_nets) if monthly_nets else 0.0
            avg_gap = abs(sum(gaps) / len(gaps)) if gaps else 0.0
            
            # 计算总余额
            total_balance = daily_balances[-1]['running_balance'] if daily_balances else 0.0
            
            return {
                'monthly_flow': list(monthly_flows.values()),
                'monthly_cash_flow': monthly_nets,
                'avg_monthly_income': sum(flow['income'] for flow in monthly_flows.values()) / len(monthly_flows) if monthly_flows else 0.0,
                'avg_monthly_expense': sum(flow['expense'] for flow in monthly_flows.values()) / len(monthly_flows) if monthly_flows else 0.0,
                'volatility': volatility,
                'positive_months': positive_months,
                'negative_months': negative_months,
                'gap_frequency': gap_frequency,
                'avg_gap': avg_gap,
                'total_balance': total_balance,
                'daily_balances': daily_balances
            }
            
        except Exception as e:
            logger.error(f"现金流模式分析失败: {e}")
            return {}
    
    def _build_cash_flow_metrics(self, cash_flow_data: Dict[str, Any]) -> CashFlowMetrics:
        """构建现金流指标。"""
        try:
            total_inflow = cash_flow_data.get('avg_monthly_income', 0.0) * 12
            total_outflow = cash_flow_data.get('avg_monthly_expense', 0.0) * 12
            
            return CashFlowMetrics(
                total_inflow=total_inflow,
                total_outflow=total_outflow,
                net_cash_flow=total_inflow - total_outflow,
                average_monthly_inflow=cash_flow_data.get('avg_monthly_income', 0.0),
                average_monthly_outflow=cash_flow_data.get('avg_monthly_expense', 0.0),
                cash_flow_volatility=cash_flow_data.get('volatility', 0.0),
                positive_months=cash_flow_data.get('positive_months', 0),
                negative_months=cash_flow_data.get('negative_months', 0)
            )
        except Exception as e:
            logger.error(f"构建现金流指标失败: {e}")
            return CashFlowMetrics()
    
    @optimized_cache('resilience_metrics', expire_minutes=35)
    def _calculate_resilience_metrics(self) -> ResilienceMetrics:
        """计算韧性指标。"""
        try:
            # 获取现金流数据
            cash_flow_data = self._analyze_cash_flow_patterns()
            
            # 计算应急基金月数
            avg_monthly_expense = cash_flow_data.get('avg_monthly_expense', 0.0)
            total_balance = cash_flow_data.get('total_balance', 0.0)
            emergency_fund_months = total_balance / avg_monthly_expense if avg_monthly_expense > 0 else 0
            
            # 计算储蓄率
            avg_monthly_income = cash_flow_data.get('avg_monthly_income', 0.0)
            avg_monthly_net = avg_monthly_income - avg_monthly_expense
            savings_rate = avg_monthly_net / avg_monthly_income if avg_monthly_income > 0 else 0
            
            # 计算债务收入比（简化计算，假设负现金流为债务指标）
            negative_months = cash_flow_data.get('negative_months', 0)
            total_months = cash_flow_data.get('positive_months', 0) + negative_months
            debt_to_income_ratio = negative_months / total_months if total_months > 0 else 0
            
            # 计算支出稳定性（波动性的倒数）
            volatility = cash_flow_data.get('volatility', 1.0)
            expense_stability = max(0, 1.0 - volatility)
            
            # 计算收入稳定性
            monthly_data = self._get_monthly_breakdown()
            monthly_incomes = [month['income'] for month in monthly_data]
            income_cv = self._calculate_coefficient_of_variation(monthly_incomes)
            income_stability = max(0, 1.0 - income_cv)
            
            return ResilienceMetrics(
                emergency_fund_months=emergency_fund_months,
                debt_to_income_ratio=debt_to_income_ratio,
                savings_rate=savings_rate,
                expense_stability=expense_stability,
                income_stability=income_stability
            )
        except Exception as e:
            logger.error(f"计算韧性指标失败: {e}")
            return ResilienceMetrics()
    
    @optimized_cache('scenario_analysis', expire_minutes=40)
    def _calculate_scenario_analysis(self) -> List[Dict[str, Any]]:
        """计算情景分析数据。"""
        try:
            cash_flow_data = self._analyze_cash_flow_patterns()
            avg_monthly_expense = cash_flow_data.get('avg_monthly_expense', 0.0)
            total_balance = cash_flow_data.get('total_balance', 0.0)
            
            scenarios = [
                {
                    'name': '收入减少30%',
                    'description': '模拟收入减少30%的情况',
                    'survival_months': self._calculate_survival_months(total_balance, avg_monthly_expense * 1.3),
                    'risk_level': 'medium'
                },
                {
                    'name': '收入减少50%',
                    'description': '模拟收入减少50%的情况',
                    'survival_months': self._calculate_survival_months(total_balance, avg_monthly_expense * 1.5),
                    'risk_level': 'high'
                },
                {
                    'name': '完全失业',
                    'description': '模拟完全失去收入的情况',
                    'survival_months': self._calculate_survival_months(total_balance, avg_monthly_expense),
                    'risk_level': 'critical'
                }
            ]
            
            return scenarios
        except Exception as e:
            logger.error(f"计算情景分析失败: {e}")
            return []
    
    def _calculate_survival_months(self, balance: float, monthly_expense: float) -> float:
        """计算在给定支出下的生存月数。"""
        if monthly_expense <= 0:
            return float('inf')
        return balance / monthly_expense
    
    def _calculate_resilience_score(self, metrics: ResilienceMetrics) -> float:
        """计算韧性分数。"""
        try:
            score = 0.0
            
            # 应急基金分数（30分）
            if metrics.emergency_fund_months >= 6:
                score += 30
            elif metrics.emergency_fund_months >= 3:
                score += 20
            elif metrics.emergency_fund_months >= 1:
                score += 10
            
            # 储蓄率分数（25分）
            if metrics.savings_rate >= 0.2:
                score += 25
            elif metrics.savings_rate >= 0.1:
                score += 15
            elif metrics.savings_rate > 0:
                score += 5
            
            # 债务收入比分数（20分）
            if metrics.debt_to_income_ratio <= 0.1:
                score += 20
            elif metrics.debt_to_income_ratio <= 0.3:
                score += 10
            elif metrics.debt_to_income_ratio <= 0.5:
                score += 5
            
            # 稳定性分数（25分）
            stability_score = (metrics.income_stability + metrics.expense_stability) / 2
            score += stability_score * 25
            
            return min(100.0, score)
        except Exception as e:
            logger.error(f"计算韧性分数失败: {e}")
            return 0.0
    
    def _determine_resilience_level(self, score: float) -> str:
        """确定韧性等级。"""
        if score >= 80:
            return "优秀"
        elif score >= 60:
            return "良好"
        elif score >= 40:
            return "一般"
        elif score >= 20:
            return "较差"
        else:
            return "很差"
    
    def _generate_recommendations(self, metrics: ResilienceMetrics) -> List[str]:
        """生成建议。"""
        recommendations = []
        
        if metrics.emergency_fund_months < 3:
            recommendations.append("建议增加应急基金至少3个月的支出")
        
        if metrics.savings_rate < 0.1:
            recommendations.append("建议提高储蓄率至收入的10%以上")
        
        if metrics.debt_to_income_ratio > 0.3:
            recommendations.append("建议降低债务收入比至30%以下")
        
        if metrics.income_stability < 0.7:
            recommendations.append("建议寻找更稳定的收入来源")
        
        if metrics.expense_stability < 0.7:
            recommendations.append("建议制定更稳定的支出计划")
        
        if not recommendations:
            recommendations.append("财务状况良好，建议保持当前水平")
        
        return recommendations
    
    def _identify_risk_factors(self, metrics: ResilienceMetrics) -> List[str]:
        """识别风险因素。"""
        risk_factors = []
        
        if metrics.emergency_fund_months < 1:
            risk_factors.append("应急基金严重不足")
        
        if metrics.savings_rate < 0:
            risk_factors.append("支出超过收入")
        
        if metrics.debt_to_income_ratio > 0.5:
            risk_factors.append("债务负担过重")
        
        if metrics.income_stability < 0.5:
            risk_factors.append("收入波动较大")
        
        if metrics.expense_stability < 0.5:
            risk_factors.append("支出不稳定")
        
        return risk_factors
    
    @optimized_cache('financial_health_summary', expire_minutes=25, priority=1)
    def get_comprehensive_health_summary(self) -> Dict[str, Any]:
        """获取综合财务健康摘要。"""
        try:
            cash_flow = self.analyze_cash_flow()
            resilience = self.analyze_resilience()
            
            return {
                'cash_flow': {
                    'total_balance': cash_flow.total_balance,
                    'gap_frequency': cash_flow.gap_frequency,
                    'avg_gap': cash_flow.avg_gap,
                    'volatility': cash_flow.metrics.cash_flow_volatility if cash_flow.metrics else 0
                },
                'resilience': {
                    'resilience_score': resilience.resilience_score,
                    'resilience_level': resilience.resilience_level,
                    'emergency_fund_months': resilience.metrics.emergency_fund_months if resilience.metrics else 0,
                    'savings_rate': resilience.metrics.savings_rate if resilience.metrics else 0
                },
                'overall_health_score': self._calculate_overall_health_score(cash_flow, resilience),
                'key_recommendations': resilience.recommendations[:3],  # 前3个最重要的建议
                'critical_risks': resilience.risk_factors
            }
        except Exception as e:
            logger.error(f"获取综合财务健康摘要失败: {e}")
            return {}
    
    def _calculate_overall_health_score(self, cash_flow: CashFlowHealth, resilience: FinancialResilience) -> float:
        """计算综合健康分数。"""
        try:
            scores = []
            
            # 现金流健康分数（50%权重）
            if cash_flow.metrics:
                cf_score = max(0, 100 - cash_flow.gap_frequency * 100)  # 缺口频率越低分数越高
                scores.append(cf_score * 0.5)
            
            # 韧性分数（50%权重）
            if resilience.resilience_score > 0:
                scores.append(resilience.resilience_score * 0.5)
            
            return sum(scores) if scores else 0.0
        except Exception as e:
            logger.error(f"计算综合健康分数失败: {e}")
            return 0.0