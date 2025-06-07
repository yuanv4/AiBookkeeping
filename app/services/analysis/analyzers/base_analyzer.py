"""优化后的财务分析器基类。

包含所有财务分析器的基类BaseAnalyzer，添加了通用方法以减少代码重复。
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import date, datetime, timedelta
from decimal import Decimal
import logging
import statistics
from collections import defaultdict
from functools import wraps

from app.models import Transaction, Account, TransactionType, db
from app.models.analysis_models import (
    IncomeExpenseAnalysis, OverallStats, MonthlyData,
    CashFlowHealth, CashFlowMetrics,
    IncomeDiversityMetrics,
    IncomeGrowthMetrics,
    FinancialResilience, ResilienceMetrics
)
from app.utils.query_builder import OptimizedQueryBuilder, AnalysisException
from app.utils.cache_manager import optimized_cache
from sqlalchemy import func, and_, or_, extract, case
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)


def performance_monitor(operation_name: str):
    """性能监控装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = datetime.now()
            try:
                result = func(*args, **kwargs)
                duration = (datetime.now() - start_time).total_seconds()
                logger.info(f"{operation_name} completed in {duration:.3f}s")
                return result
            except Exception as e:
                duration = (datetime.now() - start_time).total_seconds()
                logger.error(f"{operation_name} failed after {duration:.3f}s: {e}")
                raise
        return wrapper
    return decorator


class BaseAnalyzer(ABC):
    """优化后的财务分析器基类。"""
    
    def __init__(self, start_date: date, end_date: date, account_id: Optional[int] = None):
        self.start_date = start_date
        self.end_date = end_date
        self.account_id = account_id
        self._cache = {}
        self._query_builder = OptimizedQueryBuilder()
    
    @abstractmethod
    def analyze(self) -> Any:
        """执行分析并返回结构化数据。"""
        pass
    
    def _get_base_query(self):
        """获取带有通用过滤器的基础查询。"""
        return self._query_builder.build_transaction_query(
            account_id=self.account_id,
            start_date=self.start_date,
            end_date=self.end_date
        )
    
    # 通用数据获取方法
    @performance_monitor("income_expense_totals")
    @optimized_cache(cache_name='income_expense_totals', expire_minutes=15)
    def _get_income_expense_totals(self) -> Tuple[float, float, int, int]:
        """获取收入支出总计 - 通用方法"""
        def _calc():
            try:
                query = db.session.query(
                    func.sum(case((Transaction.amount > 0, Transaction.amount), else_=0)).label('total_income'),
                    func.sum(case((Transaction.amount < 0, func.abs(Transaction.amount)), else_=0)).label('total_expense'),
                    func.count(case((Transaction.amount > 0, 1))).label('income_count'),
                    func.count(case((Transaction.amount < 0, 1))).label('expense_count')
                ).filter(
                    Transaction.date >= self.start_date,
                    Transaction.date <= self.end_date
                )
                
                if self.account_id:
                    query = query.filter(Transaction.account_id == self.account_id)
                
                result = query.first()
                
                if not result:
                    return 0.0, 0.0, 0, 0
                
                return (
                    float(result.total_income or 0),
                    float(result.total_expense or 0),
                    result.income_count or 0,
                    result.expense_count or 0
                )
                
            except Exception as e:
                logger.error(f"获取收支总计失败: {e}")
                return 0.0, 0.0, 0, 0
        
        return self._get_cached_data('income_expense_totals', _calc)
    
    @performance_monitor("monthly_breakdown")
    @optimized_cache(cache_name='monthly_breakdown', expire_minutes=20)
    def _get_monthly_breakdown(self) -> List[Dict[str, Any]]:
        """获取月度分解数据 - 通用方法"""
        def _calc():
            try:
                query = db.session.query(
                    extract('year', Transaction.date).label('year'),
                    extract('month', Transaction.date).label('month'),
                    func.sum(case((Transaction.amount > 0, Transaction.amount), else_=0)).label('income'),
                    func.sum(case((Transaction.amount < 0, func.abs(Transaction.amount)), else_=0)).label('expense'),
                    func.count(Transaction.id).label('transaction_count')
                ).filter(
                    Transaction.date >= self.start_date,
                    Transaction.date <= self.end_date
                )
                
                if self.account_id:
                    query = query.filter(Transaction.account_id == self.account_id)
                
                query = query.group_by(
                    extract('year', Transaction.date),
                    extract('month', Transaction.date)
                ).order_by(
                    extract('year', Transaction.date),
                    extract('month', Transaction.date)
                )
                
                results = query.all()
                
                monthly_data = []
                for result in results:
                    income = float(result.income or 0)
                    expense = float(result.expense or 0)
                    monthly_data.append({
                        'year': int(result.year),
                        'month': int(result.month),
                        'income': income,
                        'expense': expense,
                        'net': income - expense,
                        'transaction_count': result.transaction_count or 0
                    })
                
                return monthly_data
                
            except Exception as e:
                logger.error(f"获取月度分解数据失败: {e}")
                return []
        
        return self._get_cached_data('monthly_breakdown', _calc)
    
    @performance_monitor("transaction_categories")
    @optimized_cache(cache_name='transaction_categories', expire_minutes=25)
    def _get_transaction_categories(self, income_only: bool = False, expense_only: bool = False) -> List[Dict[str, Any]]:
        """获取交易类别分析 - 通用方法"""
        def _calc():
            try:
                query = db.session.query(
                    TransactionType.name,
                    TransactionType.is_income,
                    func.sum(Transaction.amount).label('total_amount'),
                    func.count(Transaction.id).label('transaction_count'),
                    func.avg(Transaction.amount).label('avg_amount')
                ).join(Transaction.transaction_type).filter(
                    Transaction.date >= self.start_date,
                    Transaction.date <= self.end_date
                )
                
                if self.account_id:
                    query = query.filter(Transaction.account_id == self.account_id)
                
                if income_only:
                    query = query.filter(Transaction.amount > 0)
                elif expense_only:
                    query = query.filter(Transaction.amount < 0)
                
                query = query.group_by(
                    TransactionType.name,
                    TransactionType.is_income
                ).order_by(func.sum(func.abs(Transaction.amount)).desc())
                
                results = query.all()
                
                categories = []
                for result in results:
                    categories.append({
                        'name': result.name,
                        'is_income': result.is_income,
                        'total_amount': float(result.total_amount or 0),
                        'transaction_count': result.transaction_count or 0,
                        'avg_amount': float(result.avg_amount or 0)
                    })
                
                return categories
                
            except Exception as e:
                logger.error(f"获取交易类别分析失败: {e}")
                return []
        
        return self._get_cached_data('transaction_categories', _calc)
    
    # 通用计算方法
    def _calculate_growth_rate(self, current_value: float, previous_value: float) -> float:
        """计算增长率 - 通用方法"""
        if previous_value == 0:
            return 0.0 if current_value == 0 else 100.0
        return ((current_value - previous_value) / previous_value) * 100
    
    def _calculate_variance(self, values: List[float]) -> float:
        """计算方差 - 通用方法"""
        if len(values) < 2:
            return 0.0
        return statistics.variance(values)
    
    def _calculate_coefficient_of_variation(self, values: List[float]) -> float:
        """计算变异系数 - 通用方法"""
        if len(values) < 2:
            return 0.0
        mean_val = statistics.mean(values)
        if mean_val == 0:
            return 0.0
        std_dev = statistics.stdev(values)
        return (std_dev / mean_val) * 100
    
    def _calculate_trend(self, values: List[float]) -> str:
        """计算趋势方向 - 通用方法"""
        if len(values) < 2:
            return 'stable'
        
        # 简单线性趋势计算
        n = len(values)
        x_values = list(range(n))
        
        # 计算斜率
        x_mean = statistics.mean(x_values)
        y_mean = statistics.mean(values)
        
        numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(x_values, values))
        denominator = sum((x - x_mean) ** 2 for x in x_values)
        
        if denominator == 0:
            return 'stable'
        
        slope = numerator / denominator
        
        if slope > 0.1:
            return 'increasing'
        elif slope < -0.1:
            return 'decreasing'
        else:
            return 'stable'
    
    def _calculate_diversity_index(self, amounts: List[float]) -> float:
        """计算多样性指数（基于香农熵）- 通用方法"""
        if not amounts or sum(amounts) == 0:
            return 0.0
        
        total = sum(amounts)
        proportions = [amount / total for amount in amounts if amount > 0]
        
        if len(proportions) <= 1:
            return 0.0
        
        # 香农熵计算
        import math
        entropy = -sum(p * math.log2(p) for p in proportions)
        
        # 标准化到0-1范围
        max_entropy = math.log2(len(proportions))
        return entropy / max_entropy if max_entropy > 0 else 0.0
    
    # 缓存辅助方法
    def _get_cached_data(self, cache_key: str, calc_func) -> Any:
        """获取缓存数据的辅助方法"""
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        result = calc_func()
        self._cache[cache_key] = result
        return result
    
    def _clear_cache(self):
        """清除本地缓存"""
        self._cache.clear()
    
    # 错误处理辅助方法
    def _safe_execute(self, operation_name: str, func, default_value=None):
        """安全执行操作的辅助方法"""
        try:
            return func()
        except Exception as e:
            logger.error(f"{operation_name} 执行失败: {e}")
            return default_value