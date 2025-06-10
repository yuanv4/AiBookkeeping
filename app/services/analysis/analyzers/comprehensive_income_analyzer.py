# -*- coding: utf-8 -*-
"""
综合收入分析器。
合并了收入支出分析、收入稳定性分析和收入多样性分析功能。
优化版本：使用新的基类和缓存策略。
"""

from typing import Dict, List, Any, Optional
from decimal import Decimal
import logging
from datetime import datetime, timedelta
from sqlalchemy import func, and_

from app.models import Transaction, db
from app.services.analysis.analysis_models import (
    IncomeExpenseAnalysis, OverallStats, MonthlyData,
    IncomeStability, StabilityMetrics,
    IncomeDiversity, DiversityMetrics
)
# 查询构建器功能已移除，直接使用 SQLAlchemy 查询
from .base_analyzer import BaseAnalyzer
# 缓存和性能监控功能已移除

logger = logging.getLogger(__name__)


class ComprehensiveIncomeAnalyzer(BaseAnalyzer):
    """综合收入分析器。
    
    整合收入支出分析、收入稳定性分析和收入多样性分析功能。
    """
    
    def analyze_income_expense(self) -> IncomeExpenseAnalysis:
        """分析收入支出状况。"""
        try:
            # 获取收支总计
            totals = self._get_income_expense_totals()
            
            # 获取月度明细
            monthly_data = self._get_monthly_breakdown()
            
            # 构建总体统计
            overall_stats = OverallStats(
                total_income=totals.get('total_income', 0.0),
                total_expense=totals.get('total_expense', 0.0),
                net_income=totals.get('net_income', 0.0),
                average_monthly_income=totals.get('average_monthly_income', 0.0),
                average_monthly_expense=totals.get('average_monthly_expense', 0.0)
            )
            
            # 构建月度数据
            monthly_data_objects = [
                MonthlyData(
                    period=month.get('period', ''),
                    income=month.get('income', 0.0),
                    expense=month.get('expense', 0.0),
                    net=month.get('net', 0.0)
                ) for month in monthly_data
            ]
            
            return IncomeExpenseAnalysis(
                overall_stats=overall_stats,
                monthly_data=monthly_data_objects
            )
        except Exception as e:
            logger.error(f"收入支出分析失败: {e}")
            return IncomeExpenseAnalysis(overall_stats=OverallStats(), monthly_data=[])
    
    def analyze_income_stability(self) -> IncomeStability:
        """分析收入稳定性。"""
        try:
            # 获取月度收入数据
            monthly_data = self._get_monthly_breakdown()
            monthly_incomes = [month['income'] for month in monthly_data]
            
            # 计算稳定性指标
            stability_metrics = self._calculate_stability_metrics(monthly_incomes)
            
            # 构建月度方差数据
            monthly_variance = [
                {
                    'period': month.get('period', ''),
                    'income': month.get('income', 0.0),
                    'variance': abs(month.get('income', 0.0) - stability_metrics.average_income)
                } for month in monthly_data
            ]
            
            return IncomeStability(
                metrics=stability_metrics,
                monthly_variance=monthly_variance
            )
        except Exception as e:
            logger.error(f"收入稳定性分析失败: {e}")
            return IncomeStability()
    
    def analyze_income_diversity(self) -> IncomeDiversity:
        """分析收入多样性。"""
        try:
            # 分析收入多样性
            diversity_data = self._analyze_income_diversity()
            
            # 获取收入来源明细
            source_breakdown = self._get_income_source_breakdown()
            
            # 构建多样性指标
            metrics = self._build_diversity_metrics(diversity_data, source_breakdown)
            
            return IncomeDiversity(
                metrics=metrics,
                source_breakdown=source_breakdown
            )
        except Exception as e:
            logger.error(f"收入多样性分析失败: {e}")
            return IncomeDiversity()
    
    def _build_income_expense_metrics(self, totals: Dict[str, Any], monthly_data: List[Dict[str, Any]]) -> OverallStats:
        """构建收入支出指标。"""
        try:
            monthly_nets = [month['net'] for month in monthly_data]
            
            return OverallStats(
                total_income=totals.get('total_income', 0.0),
                total_expense=abs(totals.get('total_expense', 0.0)),
                net_saving=totals.get('net_income', 0.0),
                avg_monthly_income=totals.get('total_income', 0.0) / max(len(monthly_data), 1),
                avg_monthly_expense=abs(totals.get('total_expense', 0.0)) / max(len(monthly_data), 1),
                avg_monthly_ratio=abs(totals.get('total_income', 0.0) / totals.get('total_expense', 1.0)) if totals.get('total_expense', 0.0) != 0 else 0.0,
                avg_monthly_saving_rate=(totals.get('net_income', 0.0) / totals.get('total_income', 1.0)) * 100 if totals.get('total_income', 0.0) != 0 else 0.0
            )
        except Exception as e:
            logger.error(f"构建收入支出指标失败: {e}")
            return OverallStats()
    
    def _calculate_stability_metrics(self, monthly_incomes: List[float]) -> StabilityMetrics:
        """计算稳定性指标。"""
        try:
            if not monthly_incomes:
                return StabilityMetrics()
            
            # 计算基础统计指标
            avg_income = sum(monthly_incomes) / len(monthly_incomes)
            variance = self._calculate_variance(monthly_incomes)
            cv = self._calculate_coefficient_of_variation(monthly_incomes)
            trend = self._calculate_trend(monthly_incomes)
            
            # 计算稳定性分数（0-100）
            stability_score = max(0, 100 - cv * 100)
            
            # 确定趋势方向
            if trend > 0.05:
                trend_direction = "上升"
            elif trend < -0.05:
                trend_direction = "下降"
            else:
                trend_direction = "稳定"
            
            return StabilityMetrics(
                average_income=avg_income,
                income_variance=variance,
                coefficient_of_variation=cv,
                stability_score=stability_score,
                trend_direction=trend_direction,
                trend_slope=trend,
                consistent_months=sum(1 for income in monthly_incomes if abs(income - avg_income) / avg_income < 0.2) if avg_income > 0 else 0
            )
        except Exception as e:
            logger.error(f"计算稳定性指标失败: {e}")
            return StabilityMetrics()
    
    def _analyze_income_diversity(self) -> Dict[str, Any]:
        """分析收入多样性。"""
        try:
            # 直接使用 SQLAlchemy 查询替代查询构建器
            from app.models.transaction import Transaction
            from sqlalchemy import func, case
            from app import db
            
            # 构建收入分类分析查询
            query = db.session.query(
                Transaction.transaction_type.label('type_enum'),
                func.count(Transaction.id).label('transaction_count'),
                func.sum(Transaction.amount).label('total_amount'),
                func.avg(Transaction.amount).label('avg_amount'),
                func.max(Transaction.amount).label('max_amount'),
                func.min(Transaction.amount).label('min_amount'),
                func.sum(func.abs(Transaction.amount)).label('abs_total'),
                func.count(func.distinct(Transaction.account_id)).label('account_count')
            )
            
            # 添加过滤条件
            if self.account_id:
                query = query.filter(Transaction.account_id == self.account_id)
            if self.start_date:
                query = query.filter(Transaction.date >= self.start_date)
            if self.end_date:
                query = query.filter(Transaction.date <= self.end_date)
            
            # 只分析收入交易
            query = query.filter(Transaction.amount > 0)
            
            # 分组和排序
            query = query.group_by(Transaction.transaction_type).order_by(
                func.sum(func.abs(Transaction.amount)).desc()
            )
            
            results = query.all()
            
            # 处理结果
            categories = []
            total_income = 0.0
            
            for result in results:
                amount = float(result.total_amount or 0)
                categories.append({
                    'category': result.category or '未分类',
                    'amount': amount,
                    'count': int(result.transaction_count or 0),
                    'avg_amount': float(result.avg_amount or 0)
                })
                total_income += amount
            
            # 计算比例
            for category in categories:
                category['percentage'] = (category['amount'] / total_income * 100) if total_income > 0 else 0
            
            # 计算多样性指数
            diversity_index = self._calculate_diversity_index([cat['amount'] for cat in categories])
            
            # 找出主要收入来源
            primary_source = max(categories, key=lambda x: x['amount']) if categories else None
            primary_ratio = (primary_source['amount'] / total_income) if primary_source and total_income > 0 else 0
            
            return {
                'categories': categories,
                'total_sources': len(categories),
                'diversity_index': diversity_index,
                'primary_source': primary_source,
                'primary_source_ratio': primary_ratio,
                'total_income': total_income
            }
            
        except Exception as e:
            logger.error(f"收入多样性分析失败: {e}")
            return {}
    
    def _get_income_source_breakdown(self) -> List[Dict[str, Any]]:
        """获取收入来源明细。"""
        try:
            diversity_data = self._analyze_income_diversity()
            return diversity_data.get('categories', [])
        except Exception as e:
            logger.error(f"获取收入来源明细失败: {e}")
            return []
    
    def _build_diversity_metrics(self, diversity_data: Dict[str, Any], source_breakdown: List[Dict[str, Any]]) -> DiversityMetrics:
        """构建多样性指标。"""
        try:
            return DiversityMetrics(
                total_sources=diversity_data.get('total_sources', 0),
                diversity_score=diversity_data.get('diversity_index', 0.0) * 100,  # 转换为百分制
                primary_source_ratio=diversity_data.get('primary_source_ratio', 0.0),
                source_concentration=1.0 - diversity_data.get('diversity_index', 0.0),  # 集中度 = 1 - 多样性
                effective_sources=len([s for s in source_breakdown if s.get('percentage', 0) >= 5.0]),  # 占比>=5%的来源
                balanced_distribution=diversity_data.get('diversity_index', 0.0) > 0.7  # 多样性指数>0.7认为分布均衡
            )
        except Exception as e:
            logger.error(f"构建多样性指标失败: {e}")
            return DiversityMetrics()
    
    def get_comprehensive_summary(self) -> Dict[str, Any]:
        """获取综合收入分析摘要。"""
        try:
            # 获取各项分析结果
            income_expense = self.analyze_income_expense()
            stability = self.analyze_income_stability()
            diversity = self.analyze_income_diversity()
            
            return {
                'income_expense': {
                    'total_income': income_expense.total_income,
                    'total_expense': income_expense.total_expense,
                    'net_income': income_expense.net_income,
                    'income_expense_ratio': income_expense.metrics.income_expense_ratio if income_expense.metrics else 0
                },
                'stability': {
                    'stability_score': stability.stability_score,
                    'trend_direction': stability.trend_direction,
                    'coefficient_of_variation': stability.metrics.coefficient_of_variation if stability.metrics else 0
                },
                'diversity': {
                    'diversity_score': diversity.diversity_score,
                    'total_sources': diversity.metrics.total_sources if diversity.metrics else 0,
                    'primary_source_ratio': diversity.primary_source_ratio
                },
                'overall_health_score': self._calculate_overall_health_score(income_expense, stability, diversity)
            }
        except Exception as e:
            logger.error(f"获取综合收入分析摘要失败: {e}")
            return {}
    
    def _calculate_overall_health_score(self, income_expense: IncomeExpenseAnalysis, 
                                      stability: IncomeStability, 
                                      diversity: IncomeDiversity) -> float:
        """计算综合健康分数。"""
        try:
            scores = []
            
            # 收支健康分数（30%权重）
            if income_expense.overall_stats.net_saving > 0:
                ie_score = min(100, income_expense.overall_stats.avg_monthly_ratio * 50)
                scores.append(ie_score * 0.3)
            
            # 稳定性分数（40%权重）
            if stability.metrics.stability_score > 0:
                scores.append(stability.metrics.stability_score * 0.4)
            
            # 多样性分数（30%权重）
            if diversity.metrics.diversity_index > 0:
                scores.append(diversity.metrics.diversity_index * 0.3)
            
            return sum(scores) if scores else 0.0
        except Exception as e:
            logger.error(f"计算综合健康分数失败: {e}")
            return 0.0