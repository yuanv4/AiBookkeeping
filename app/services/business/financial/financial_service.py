"""统一财务服务

将原有的FinancialAnalyzer和FinancialReportService合并为单一的、功能完整的财务服务类。
消除了重复代码，简化了接口，提高了维护性。

Created: 2024-12-19
Author: AI Assistant
"""

from typing import List, Dict, Any, Optional, Tuple
from decimal import Decimal
from datetime import date, datetime, timedelta
import logging
from collections import defaultdict
import calendar
from dateutil.relativedelta import relativedelta

from app.models import Transaction, Account, Bank, db
from sqlalchemy import func, and_, or_, extract, case
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from sqlalchemy.sql import text as sql_text
from app.services.core.transaction_service import TransactionService
from app.services.core.account_service import AccountService
from app.services.core.bank_service import BankService

# 导入分析相关的数据模型和工具
try:
    from app.services.business.financial.analysis_models import (
        AnalysisResult, MonthlyData, FinancialSummary, 
        ComprehensiveReport
    )
    from app.services.business.financial.analysis_utils import (
        cache_result, handle_analysis_errors, AnalysisError
    )
except ImportError:
    # 如果导入失败，定义基本的异常类
    class AnalysisError(Exception):
        pass
    
    def cache_result(ttl=300):
        def decorator(func):
            return func
        return decorator
    
    def handle_analysis_errors(func):
        return func

logger = logging.getLogger(__name__)


class FinancialService:
    """统一财务服务
    
    整合了财务分析和报告生成功能，提供一站式的财务数据处理服务。
    消除了原有架构中的功能重复和接口复杂性。
    """
    
    def __init__(self, db_session: Optional[Session] = None):
        """初始化财务服务
        
        Args:
            db_session: 数据库会话，如果为None则使用默认会话
        """
        self.db = db_session or db.session
        self.logger = logging.getLogger(__name__)
    
    # ==================== 核心查询方法 ====================

    def _validate_parameters(self, account_id: Optional[int] = None, 
                           start_date: Optional[date] = None, 
                           end_date: Optional[date] = None):
        """验证输入参数"""
        if account_id and (not isinstance(account_id, int) or account_id <= 0):
            raise AnalysisError("无效的账户ID")
        if start_date and end_date and start_date > end_date:
            raise AnalysisError("开始日期不能晚于结束日期")
     
    # ==================== 分析方法 ====================
    
    @cache_result(ttl=300)
    @handle_analysis_errors
    def analyze_income(self, start_date: date, end_date: date, 
                      account_id: Optional[int] = None) -> Dict[str, Any]:
        """分析收入情况"""
        self._validate_parameters(account_id, start_date, end_date)
        
        # 使用优化的聚合查询
        query = self.db.query(
            case(
                (Transaction.amount > 0, 'income'),
                (Transaction.amount < 0, 'expense'),
                else_='transfer'
            ).label('type_enum'),
            func.count(Transaction.id).label('transaction_count'),
            func.sum(Transaction.amount).label('total_amount'),
            func.avg(Transaction.amount).label('avg_amount'),
            func.max(Transaction.amount).label('max_amount'),
            func.min(Transaction.amount).label('min_amount')
        )
        
        # 添加过滤条件
        if account_id:
            query = query.filter(Transaction.account_id == account_id)
        if start_date:
            query = query.filter(Transaction.date >= start_date)
        if end_date:
            query = query.filter(Transaction.date <= end_date)
        
        # 只查询收入
        query = query.filter(Transaction.amount > 0)
        
        # 分组和排序
        query = query.group_by(
            case(
                (Transaction.amount > 0, 'income'),
                (Transaction.amount < 0, 'expense'),
                else_='transfer'
            )
        ).order_by(
            func.sum(Transaction.amount).desc()
        )
        
        try:
            results = query.all()
        except Exception as e:
            logger.error(f"收入分析查询执行失败: {e}")
            raise AnalysisError(f"收入分析查询执行失败: {str(e)}")
        
        # 格式化结果
        income_sources = []
        for result in results:
            income_sources.append({
                'category': result.type_enum,
                'total': float(result.total_amount or 0),
                'count': result.transaction_count,
                'average': float(result.avg_amount or 0),
                'maximum': float(result.max_amount or 0),
                'minimum': float(result.min_amount or 0)
            })
        
        total_income = sum(source['total'] for source in income_sources)
        
        # 计算百分比
        for source in income_sources:
            source['percentage'] = (source['total'] / total_income * 100) if total_income > 0 else 0
        
        return {
            'total_income': total_income,
            'income_sources': income_sources,
            'primary_source': income_sources[0] if income_sources else None,
            'source_diversity': len(income_sources),
            'transaction_count': sum(source['count'] for source in income_sources),
            'average_amount': total_income / sum(source['count'] for source in income_sources) if income_sources else 0
        }
    
    @cache_result(ttl=300)
    @handle_analysis_errors
    def analyze_expenses(self, start_date: date, end_date: date, 
                        account_id: Optional[int] = None) -> Dict[str, Any]:
        """分析支出情况"""
        self._validate_parameters(account_id, start_date, end_date)
        
        # 使用优化的聚合查询
        query = self.db.query(
            case(
                (Transaction.amount > 0, 'income'),
                (Transaction.amount < 0, 'expense'),
                else_='transfer'
            ).label('type_enum'),
            func.count(Transaction.id).label('transaction_count'),
            func.sum(func.abs(Transaction.amount)).label('total_amount'),
            func.avg(func.abs(Transaction.amount)).label('avg_amount'),
            func.max(func.abs(Transaction.amount)).label('max_amount'),
            func.min(func.abs(Transaction.amount)).label('min_amount')
        )
        
        # 添加过滤条件
        if account_id:
            query = query.filter(Transaction.account_id == account_id)
        if start_date:
            query = query.filter(Transaction.date >= start_date)
        if end_date:
            query = query.filter(Transaction.date <= end_date)
        
        # 只查询支出
        query = query.filter(Transaction.amount < 0)
        
        # 分组和排序
        query = query.group_by(
            case(
                (Transaction.amount > 0, 'income'),
                (Transaction.amount < 0, 'expense'),
                else_='transfer'
            )
        ).order_by(
            func.sum(func.abs(Transaction.amount)).desc()
        )
        
        try:
            results = query.all()
        except Exception as e:
            logger.error(f"支出分析查询执行失败: {e}")
            raise AnalysisError(f"支出分析查询执行失败: {str(e)}")
        
        # 格式化结果
        expense_categories = []
        for result in results:
            expense_categories.append({
                'category': result.type_enum,
                'total': float(result.total_amount or 0),
                'count': result.transaction_count,
                'average': float(result.avg_amount or 0),
                'maximum': float(result.max_amount or 0),
                'minimum': float(result.min_amount or 0)
            })
        
        total_expense = sum(category['total'] for category in expense_categories)
        
        # 计算百分比
        for category in expense_categories:
            category['percentage'] = (category['total'] / total_expense * 100) if total_expense > 0 else 0
        
        return {
            'total_expense': total_expense,
            'expense_categories': expense_categories,
            'largest_category': expense_categories[0] if expense_categories else None,
            'category_count': len(expense_categories),
            'transaction_count': sum(category['count'] for category in expense_categories),
            'average_amount': total_expense / sum(category['count'] for category in expense_categories) if expense_categories else 0
        }
    
    @cache_result(ttl=300)
    @handle_analysis_errors
    def analyze_overview(self) -> Dict[str, Any]:
        """分析总览情况
        
        Args:
            months: 分析月份数，默认12个月
            
        Returns:
            Dict[str, Any]: 包含总览数据的字典
        """
        return {
            'balance': self.get_all_accounts_balance(),
            'monthly_trends': self.get_monthly_balance_trends(12),
        }
        
    # ==================== 计算方法 ====================

    def get_all_accounts_balance(self) -> Decimal:
        """获取所有账户的当前余额总和"""
        try:
            """使用窗口函数获取所有账户的当前余额总和"""
            # 使用原生SQL窗口函数查询
            query = sql_text("""
                WITH ranked_transactions AS (
                    SELECT 
                        account_id,
                        balance_after,
                        ROW_NUMBER() OVER (
                            PARTITION BY account_id 
                            ORDER BY date DESC, created_at DESC
                        ) as rn
                    FROM transactions
                )
                SELECT account_id, balance_after 
                FROM ranked_transactions 
                WHERE rn = 1
            """)
            
            result = self.db.execute(query)
            account_balances = result.fetchall()
            
            return sum(Decimal(str(balance)) for _, balance in account_balances) if account_balances else Decimal('0.00')
        except Exception as e:
            self.logger.error(f"窗口函数获取余额失败 {e}")
    
    def get_monthly_balance_trends(self, months: int = 12) -> List[Dict[str, Any]]:
        """获取所有账户的月度余额趋势"""
        try:
            monthly_trends = self.db.query(
                func.strftime('%Y-%m', Transaction.date).label('month'),
                func.sum(Transaction.balance_after).label('balance')
            ).filter(
                Transaction.date >= func.date('now', f'-{months} months')
            ).group_by(
                func.strftime('%Y-%m', Transaction.date)
            ).order_by(
                func.strftime('%Y-%m', Transaction.date)
            ).all()
            
            return [{
                'month': month,
                'balance': float(balance)
            } for month, balance in monthly_trends]
        except Exception as e:
            self.logger.error(f"获取月度余额趋势失败: {e}")
            return []