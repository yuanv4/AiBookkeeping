"""Income Diversity Analysis Module.

包含收入多样性分析器。
优化版本：使用新的基类和缓存策略。"""

from typing import Dict, List, Any
import logging
import math
from datetime import datetime
from sqlalchemy import func

from app.models import Transaction, db
from app.models.analysis_models import IncomeDiversityMetrics
from app.utils.query_builder import OptimizedQueryBuilder, AnalysisException
from app.utils.cache_manager import optimized_cache
from .base_analyzer import BaseAnalyzer, performance_monitor

logger = logging.getLogger(__name__)


class IncomeDiversityAnalyzer(BaseAnalyzer):
    """优化的收入多样性分析器。"""
    
    @performance_monitor("income_diversity_analysis")
    def analyze(self) -> IncomeDiversityMetrics:
        """分析收入多样性。"""
        try:
            # 使用优化的收入分析
            income_data = self._get_income_expense_totals()
            diversity_data = self._analyze_income_diversity()
            source_breakdown = self._get_income_source_breakdown()
            
            return IncomeDiversityMetrics(
                total_income=income_data.get('total_income', 0.0),
                source_count=diversity_data.get('source_count', 0),
                concentration_index=diversity_data.get('concentration_index', 0.0),
                passive_income_ratio=diversity_data.get('passive_income_ratio', 0.0),
                diversity_index=diversity_data.get('diversity_index', 0.0),
                source_breakdown=source_breakdown
            )
        except Exception as e:
            logger.error(f"收入多样性分析失败: {e}")
            return IncomeDiversityMetrics()
    
    @optimized_cache('income_diversity', expire_minutes=30, priority=2)
    def _analyze_income_diversity(self) -> Dict[str, Any]:
        """分析收入多样性指标。"""
        try:
            # 使用优化的查询构建器
            query_builder = OptimizedQueryBuilder()
            
            # 构建收入分类分析查询
            category_query = query_builder.build_category_analysis_query(
                account_id=self.account_id,
                start_date=self.start_date,
                end_date=self.end_date,
                income_only=True  # 只分析收入
            )
            
            # 执行查询
            results = query_builder.execute_with_error_handling(
                category_query, "收入分类分析查询"
            )
            
            if not results:
                return {
                    'source_count': 0,
                    'concentration_index': 0.0,
                    'passive_income_ratio': 0.0,
                    'diversity_index': 0.0
                }
            
            # 处理结果
            category_totals = {}
            total_income = 0.0
            
            for result in results:
                category = result.category
                amount = float(result.total_amount)
                category_totals[category] = amount
                total_income += amount
            
            source_count = len(category_totals)
            
            # 计算集中度指数（赫芬达尔指数）
            proportions = [amount / total_income for amount in category_totals.values()]
            concentration_index = sum(p ** 2 for p in proportions)
            
            # 计算被动收入比例
            passive_categories = {'投资', '利息', '分红', '租金', '股息', '基金收益'}
            passive_income = sum(
                amount for category, amount in category_totals.items()
                if category in passive_categories
            )
            passive_income_ratio = passive_income / total_income if total_income > 0 else 0.0
            
            # 计算多样性指数
            diversity_index = self._calculate_diversity_index(proportions)
            
            return {
                'source_count': source_count,
                'concentration_index': concentration_index,
                'passive_income_ratio': passive_income_ratio,
                'diversity_index': diversity_index,
                'category_totals': category_totals
            }
            
        except Exception as e:
            logger.error(f"收入多样性分析失败: {e}")
            return {}
    
    @optimized_cache('income_source_breakdown', expire_minutes=25, priority=2)
    def _get_income_source_breakdown(self) -> List[Dict[str, Any]]:
        """获取收入来源分解。"""
        try:
            # 使用基类的通用方法获取分类数据
            categories = self._get_transaction_categories(income_only=True)
            
            if not categories:
                return []
            
            # 计算总收入
            total_income = sum(cat['total_amount'] for cat in categories)
            
            # 构建分解数据
            breakdown = []
            for category_data in categories:
                amount = category_data['total_amount']
                percentage = (amount / total_income * 100) if total_income > 0 else 0
                
                breakdown.append({
                    'category': category_data['category'],
                    'amount': float(amount),
                    'percentage': round(percentage, 2),
                    'transaction_count': category_data['transaction_count'],
                    'average_amount': float(category_data['average_amount'])
                })
            
            # 按金额降序排列
            breakdown.sort(key=lambda x: x['amount'], reverse=True)
            
            return breakdown
            
        except Exception as e:
            logger.error(f"收入来源分解分析失败: {e}")
            return []