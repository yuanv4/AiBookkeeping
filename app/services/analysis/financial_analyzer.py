"""简化的财务分析器

将原有的复杂分析器架构简化为单一的、功能完整的分析器类。
消除了重复代码，简化了接口，提高了维护性。

Created: 2024-12-19
Author: AI Assistant
"""

from datetime import date, datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from collections import defaultdict
import logging

# 导入数据库模型
try:
    from app.models import Transaction, Account, db
except ImportError:
    Transaction = None
    Account = None
    db = None

from .data_models import AnalysisResult, MonthlyData, FinancialSummary, FinancialHealthMetrics, ComprehensiveReport
from .analysis_utils import cache_result, handle_analysis_errors


class FinancialAnalyzer:
    """财务分析器
    
    将所有财务分析功能整合到单一类中，消除了复杂的协调器模式和重复代码。
    提供清晰、简洁的API接口，同时保持功能完整性。
    """
    
    def __init__(self, db_session: Optional[Session] = None):
        """初始化分析器
        
        Args:
            db_session: 数据库会话，如果为None则使用默认会话
        """
        self.db = db_session or db.session
        self.logger = logging.getLogger(__name__)
    
    # ==================== 核心查询方法 ====================
    
    def _get_transactions(self, start_date: date, end_date: date, 
                         account_id: Optional[int] = None,
                         transaction_type: Optional[str] = None) -> List:
        """获取交易数据的通用方法
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            account_id: 可选的账户ID
            transaction_type: 交易类型 ('income', 'expense', None为全部)
            
        Returns:
            交易记录列表
        """
        query = self.db.query(Transaction).filter(
            Transaction.date >= start_date,
            Transaction.date <= end_date
        )
        
        if account_id:
            query = query.filter(Transaction.account_id == account_id)
        
        if transaction_type == 'income':
            query = query.filter(Transaction.amount > 0)
        elif transaction_type == 'expense':
            query = query.filter(Transaction.amount < 0)
        
        return query.all()
    
    def _group_by_category(self, transactions: List, abs_amount: bool = False) -> Dict[str, float]:
        """按类别分组交易
        
        Args:
            transactions: 交易记录列表
            abs_amount: 是否使用绝对值
            
        Returns:
            按类别分组的金额字典
        """
        result = defaultdict(float)
        for t in transactions:
            amount = abs(t.amount) if abs_amount else float(t.amount)
            result[t.category] += amount
        return dict(result)
    
    def _group_by_month(self, transactions: List, abs_amount: bool = False) -> Dict[str, float]:
        """按月份分组交易
        
        Args:
            transactions: 交易记录列表
            abs_amount: 是否使用绝对值
            
        Returns:
            按月份分组的金额字典
        """
        result = defaultdict(float)
        for t in transactions:
            month_key = f"{t.date.year}-{t.date.month:02d}"
            amount = abs(t.amount) if abs_amount else float(t.amount)
            result[month_key] += amount
        return dict(result)
    
    # ==================== 分析方法 ====================
    
    @cache_result(ttl=300)
    @handle_analysis_errors
    def analyze_income(self, start_date: date, end_date: date, 
                      account_id: Optional[int] = None) -> AnalysisResult:
        """分析收入情况"""
        transactions = self._get_transactions(start_date, end_date, account_id, 'income')
        total_amount = sum(float(t.amount) for t in transactions)
        
        return AnalysisResult(
            total_amount=total_amount,
            by_category=self._group_by_category(transactions),
            by_month=self._group_by_month(transactions),
            transaction_count=len(transactions),
            average_amount=total_amount / len(transactions) if transactions else 0.0
        )
    
    @cache_result(ttl=300)
    @handle_analysis_errors
    def analyze_expenses(self, start_date: date, end_date: date, 
                        account_id: Optional[int] = None) -> AnalysisResult:
        """分析支出情况"""
        transactions = self._get_transactions(start_date, end_date, account_id, 'expense')
        total_amount = sum(abs(t.amount) for t in transactions)
        
        return AnalysisResult(
            total_amount=total_amount,
            by_category=self._group_by_category(transactions, abs_amount=True),
            by_month=self._group_by_month(transactions, abs_amount=True),
            transaction_count=len(transactions),
            average_amount=total_amount / len(transactions) if transactions else 0.0
        )
    
    @cache_result(ttl=300)
    @handle_analysis_errors
    def analyze_cash_flow(self, start_date: date, end_date: date, 
                         account_id: Optional[int] = None) -> Dict[str, Any]:
        """分析现金流情况"""
        transactions = self._get_transactions(start_date, end_date, account_id)
        
        # 按月计算现金流
        monthly_flow = defaultdict(float)
        for t in transactions:
            month_key = f"{t.date.year}-{t.date.month:02d}"
            monthly_flow[month_key] += float(t.amount)
        
        # 计算现金流稳定性（正现金流月份比例）
        positive_months = sum(1 for flow in monthly_flow.values() if flow > 0)
        stability = positive_months / len(monthly_flow) if monthly_flow else 0
        
        return {
            'monthly_cash_flow': dict(monthly_flow),
            'total_cash_flow': sum(monthly_flow.values()),
            'cash_flow_stability': stability,
            'positive_months': positive_months,
            'total_months': len(monthly_flow)
        }
    
    @cache_result(ttl=300)
    @handle_analysis_errors
    def analyze_financial_health(self, months: int = 12) -> Dict[str, Any]:
        """分析财务健康状况"""
        end_date = date.today()
        start_date = end_date - timedelta(days=months * 30)
        
        income_result = self.analyze_income(start_date, end_date)
        expense_result = self.analyze_expenses(start_date, end_date)
        cash_flow_result = self.analyze_cash_flow(start_date, end_date)
        
        # 计算关键指标
        savings_rate = (income_result.total_amount - expense_result.total_amount) / income_result.total_amount if income_result.total_amount > 0 else 0
        expense_ratio = expense_result.total_amount / income_result.total_amount if income_result.total_amount > 0 else 0
        
        # 评估健康等级
        health_score = 0
        if savings_rate > 0.2: health_score += 30
        elif savings_rate > 0.1: health_score += 20
        elif savings_rate > 0: health_score += 10
        
        if cash_flow_result['cash_flow_stability'] > 0.8: health_score += 30
        elif cash_flow_result['cash_flow_stability'] > 0.6: health_score += 20
        elif cash_flow_result['cash_flow_stability'] > 0.4: health_score += 10
        
        if expense_ratio < 0.7: health_score += 25
        elif expense_ratio < 0.8: health_score += 15
        elif expense_ratio < 0.9: health_score += 10
        
        # 确定健康等级
        if health_score >= 80: health_level = 'excellent'
        elif health_score >= 60: health_level = 'good'
        elif health_score >= 40: health_level = 'fair'
        else: health_level = 'poor'
        
        return {
            'health_score': health_score,
            'health_level': health_level,
            'savings_rate': savings_rate,
            'expense_ratio': expense_ratio,
            'cash_flow_stability': cash_flow_result['cash_flow_stability']
        }
    
    @cache_result(ttl=600)
    @handle_analysis_errors
    def get_comprehensive_analysis(self, months: int = 12) -> Dict[str, Any]:
        """获取综合财务分析
        
        Args:
            months: 分析月份数
            
        Returns:
            包含所有分析结果的综合报告
        """
        end_date = date.today()
        start_date = end_date - timedelta(days=months * 30)
        
        # 执行各项分析
        income_analysis = self.analyze_income(start_date, end_date)
        expense_analysis = self.analyze_expenses(start_date, end_date)
        cash_flow_analysis = self.analyze_cash_flow(start_date, end_date)
        financial_health = self.analyze_financial_health(months)
        
        # 生成月度趋势数据
        monthly_trends = self._generate_monthly_trends(start_date, end_date)
        
        return {
            'period': {'start_date': start_date, 'end_date': end_date, 'months': months},
            'income_summary': {
                'total_income': income_analysis.total_amount,
                'avg_monthly_income': income_analysis.total_amount / months,
                'top_categories': sorted(income_analysis.by_category.items(), key=lambda x: x[1], reverse=True)[:5]
            },
            'expense_summary': {
                'total_expense': expense_analysis.total_amount,
                'avg_monthly_expense': expense_analysis.total_amount / months,
                'top_categories': sorted(expense_analysis.by_category.items(), key=lambda x: x[1], reverse=True)[:5]
            },
            'cash_flow_summary': cash_flow_analysis,
            'financial_health': financial_health,
            'monthly_trends': monthly_trends,
            'key_insights': self._generate_insights(income_analysis, expense_analysis, cash_flow_analysis, financial_health)
        }
    
    def _generate_monthly_trends(self, start_date: date, end_date: date) -> List[MonthlyData]:
        """生成月度趋势数据"""
        transactions = self._get_transactions(start_date, end_date)
        
        # 按月分组
        monthly_data = defaultdict(lambda: {'income': 0, 'expense': 0, 'count': 0})
        
        for t in transactions:
            month_key = (t.date.year, t.date.month)
            if t.amount > 0:
                monthly_data[month_key]['income'] += float(t.amount)
            else:
                monthly_data[month_key]['expense'] += abs(t.amount)
            monthly_data[month_key]['count'] += 1
        
        # 转换为MonthlyData对象
        trends = []
        for (year, month), data in sorted(monthly_data.items()):
            trends.append(MonthlyData(
                year=year,
                month=month,
                income=data['income'],
                expense=data['expense'],
                net_amount=data['income'] - data['expense'],
                transaction_count=data['count']
            ))
        
        return trends
    
    def _generate_insights(self, income_analysis, expense_analysis, cash_flow_analysis, financial_health) -> List[str]:
        """生成关键洞察"""
        insights = []
        
        # 收入洞察
        if income_analysis.by_category:
            top_income = max(income_analysis.by_category.items(), key=lambda x: x[1])
            insights.append(f"主要收入来源：{top_income[0]}（{top_income[1]/income_analysis.total_amount*100:.1f}%）")
        
        # 支出洞察
        if expense_analysis.by_category:
            top_expense = max(expense_analysis.by_category.items(), key=lambda x: x[1])
            insights.append(f"最大支出类别：{top_expense[0]}（{top_expense[1]/expense_analysis.total_amount*100:.1f}%）")
        
        # 财务健康洞察
        health_level = financial_health['health_level']
        if health_level == 'excellent':
            insights.append("财务状况优秀，继续保持")
        elif health_level == 'poor':
            insights.append("财务状况需要改善，建议制定理财计划")
        
        # 现金流洞察
        stability = cash_flow_analysis['cash_flow_stability']
        if stability > 0.8:
            insights.append("现金流非常稳定")
        elif stability < 0.5:
            insights.append("现金流不够稳定，需要关注")
        
        return insights
    
    def generate_summary(self) -> FinancialSummary:
        """生成财务总览"""
        analysis = self.get_comprehensive_analysis(12)
        
        income_summary = analysis['income_summary']
        expense_summary = analysis['expense_summary']
        financial_health = analysis['financial_health']
        
        return FinancialSummary(
            total_income=income_summary['total_income'],
            total_expense=expense_summary['total_expense'],
            net_saving=income_summary['total_income'] - expense_summary['total_expense'],
            avg_monthly_income=income_summary['avg_monthly_income'],
            avg_monthly_expense=expense_summary['avg_monthly_expense'],
            savings_rate=financial_health['savings_rate'],
            expense_ratio=financial_health['expense_ratio']
        )