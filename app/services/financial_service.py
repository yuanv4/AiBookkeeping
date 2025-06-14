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

from app.models import Transaction, Account, Bank, db
from sqlalchemy import func, and_, or_, extract, case
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

# 导入分析相关的数据模型和工具
try:
    from app.services.analysis.data_models import (
        AnalysisResult, MonthlyData, FinancialSummary, 
        FinancialHealthMetrics, ComprehensiveReport
    )
    from app.services.analysis.analysis_utils import (
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
    
    def _validate_parameters(self, account_id: Optional[int] = None, 
                           start_date: Optional[date] = None, 
                           end_date: Optional[date] = None):
        """验证输入参数"""
        if account_id and (not isinstance(account_id, int) or account_id <= 0):
            raise AnalysisError("无效的账户ID")
        if start_date and end_date and start_date > end_date:
            raise AnalysisError("开始日期不能晚于结束日期")
    
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
    def analyze_cash_flow(self, start_date: date, end_date: date, 
                         account_id: Optional[int] = None) -> Dict[str, Any]:
        """分析现金流情况"""
        self._validate_parameters(account_id, start_date, end_date)
        
        # 构建日趋势分析查询
        daily_query = self.db.query(
            Transaction.date,
            func.sum(Transaction.amount).label('net_amount'),
            func.sum(case((Transaction.amount > 0, Transaction.amount), else_=0)).label('income'),
            func.sum(case((Transaction.amount < 0, func.abs(Transaction.amount)), else_=0)).label('expense'),
            func.count(Transaction.id).label('transaction_count')
        )
        
        # 添加过滤条件
        if account_id:
            daily_query = daily_query.filter(Transaction.account_id == account_id)
        if start_date:
            daily_query = daily_query.filter(Transaction.date >= start_date)
        if end_date:
            daily_query = daily_query.filter(Transaction.date <= end_date)
        
        daily_query = daily_query.group_by(Transaction.date).order_by(Transaction.date.asc())
        
        try:
            daily_results = daily_query.all()
        except Exception as e:
            logger.error(f"现金流分析查询执行失败: {e}")
            raise AnalysisError(f"现金流分析查询执行失败: {str(e)}")
        
        # 按月计算现金流
        monthly_flow = defaultdict(float)
        daily_trends = []
        
        for result in daily_results:
            daily_trends.append({
                'date': result.date.isoformat(),
                'net_amount': float(result.net_amount or 0),
                'income': float(result.income or 0),
                'expense': float(result.expense or 0),
                'transaction_count': result.transaction_count
            })
            
            month_key = f"{result.date.year}-{result.date.month:02d}"
            monthly_flow[month_key] += float(result.net_amount or 0)
        
        # 计算现金流稳定性（正现金流月份比例）
        positive_months = sum(1 for flow in monthly_flow.values() if flow > 0)
        stability = positive_months / len(monthly_flow) if monthly_flow else 0
        
        return {
            'monthly_cash_flow': dict(monthly_flow),
            'daily_trends': daily_trends,
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
        
        # 处理可能的AnalysisResult对象
        if hasattr(income_result, 'to_dict'):
            income_data = income_result.to_dict()
        else:
            income_data = income_result
            
        if hasattr(expense_result, 'to_dict'):
            expense_data = expense_result.to_dict()
        else:
            expense_data = expense_result
            
        if hasattr(cash_flow_result, 'to_dict'):
            cash_flow_data = cash_flow_result.to_dict()
        else:
            cash_flow_data = cash_flow_result
        
        # 计算关键指标
        total_income = income_data.get('total_income', 0)
        total_expense = expense_data.get('total_expense', 0)
        
        savings_rate = (total_income - total_expense) / total_income if total_income > 0 else 0
        expense_ratio = total_expense / total_income if total_income > 0 else 0
        
        # 评估健康等级
        health_score = 0
        if savings_rate > 0.2: health_score += 30
        elif savings_rate > 0.1: health_score += 20
        elif savings_rate > 0: health_score += 10
        
        cash_flow_stability = cash_flow_data.get('cash_flow_stability', 0)
        if cash_flow_stability > 0.8: health_score += 30
        elif cash_flow_stability > 0.6: health_score += 20
        elif cash_flow_stability > 0.4: health_score += 10
        
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
            'cash_flow_stability': cash_flow_stability,
            'total_income': total_income,
            'total_expense': total_expense,
            'net_saving': total_income - total_expense
        }
    
    # ==================== 报告生成方法 ====================
    
    def generate_financial_report(self, account_id: int = None, start_date: date = None, 
                                end_date: date = None) -> Dict[str, Any]:
        """生成综合财务报告"""
        try:
            if not start_date:
                start_date = date.today().replace(day=1)  # 当月第一天
            if not end_date:
                end_date = date.today()
            
            # 获取各项分析结果
            period_summary = self._get_period_summary(account_id, start_date, end_date)
            income_analysis = self.analyze_income(start_date, end_date, account_id)
            expense_analysis = self.analyze_expenses(start_date, end_date, account_id)
            cash_flow_analysis = self.analyze_cash_flow(start_date, end_date, account_id)
            category_breakdown = self._get_category_breakdown(account_id, start_date, end_date)
            trends = self._get_trend_analysis(account_id, start_date, end_date)
            insights = self._generate_insights(account_id, start_date, end_date)
            
            report = {
                'period': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat(),
                    'days': (end_date - start_date).days + 1
                },
                'summary': period_summary,
                'income_analysis': income_analysis,
                'expense_analysis': expense_analysis,
                'cash_flow_analysis': cash_flow_analysis,
                'category_breakdown': category_breakdown,
                'trends': trends,
                'insights': insights
            }
            
            if account_id:
                account = Account.query.get(account_id)
                if account:
                    report['account_info'] = {
                        'id': account.id,
                        'name': account.account_name,
                        'number': account.account_number,
                        'bank': account.bank.name if account.bank else None,
                        'current_balance': float(account.balance or 0)
                    }
            
            return report
            
        except Exception as e:
            logger.error(f"生成财务报告失败: {e}")
            raise
    
    def _get_period_summary(self, account_id: int = None, start_date: date = None, 
                          end_date: date = None) -> Dict[str, Any]:
        """获取期间汇总统计"""
        try:
            self._validate_parameters(account_id, start_date, end_date)
            
            # 使用聚合查询替代加载所有交易记录
            query = self.db.query(
                func.count(Transaction.id).label('total_count'),
                func.sum(case((Transaction.amount > 0, Transaction.amount), else_=0)).label('total_income'),
                func.sum(case((Transaction.amount < 0, func.abs(Transaction.amount)), else_=0)).label('total_expense'),
                func.count(case((Transaction.amount > 0, 1))).label('income_count'),
                func.count(case((Transaction.amount < 0, 1))).label('expense_count'),
                func.avg(func.abs(Transaction.amount)).label('avg_transaction')
            )
            
            # 应用过滤条件
            if account_id:
                query = query.filter(Transaction.account_id == account_id)
            if start_date:
                query = query.filter(Transaction.date >= start_date)
            if end_date:
                query = query.filter(Transaction.date <= end_date)
            
            try:
                result = query.first()
            except Exception as e:
                logger.error(f"期间汇总查询执行失败: {e}")
                raise AnalysisError(f"期间汇总查询执行失败: {str(e)}")
            
            if not result:
                return {
                    'total_transactions': 0,
                    'total_income': 0.0,
                    'total_expense': 0.0,
                    'net_income': 0.0,
                    'average_transaction': 0.0,
                    'income_transactions': 0,
                    'expense_transactions': 0
                }
            
            total_income = float(result.total_income or 0)
            total_expense = float(result.total_expense or 0)
            
            return {
                'total_transactions': result.total_count or 0,
                'total_income': total_income,
                'total_expense': total_expense,
                'net_income': total_income - total_expense,
                'average_transaction': float(result.avg_transaction or 0),
                'income_transactions': result.income_count or 0,
                'expense_transactions': result.expense_count or 0
            }
            
        except AnalysisError:
            raise
        except Exception as e:
            logger.error(f"期间汇总分析失败: {e}")
            return {
                'total_transactions': 0,
                'total_income': 0.0,
                'total_expense': 0.0,
                'net_income': 0.0,
                'average_transaction': 0.0,
                'income_transactions': 0,
                'expense_transactions': 0
            }
    
    def _get_category_breakdown(self, account_id: int = None, start_date: date = None, 
                              end_date: date = None) -> Dict[str, Any]:
        """获取详细类别分解"""
        try:
            self._validate_parameters(account_id, start_date, end_date)
            
            # 构建类别分析查询
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
                func.min(Transaction.amount).label('min_amount'),
                func.sum(func.abs(Transaction.amount)).label('abs_total'),
                func.count(func.distinct(Transaction.account_id)).label('account_count')
            )
            
            # 添加过滤条件
            if account_id:
                query = query.filter(Transaction.account_id == account_id)
            if start_date:
                query = query.filter(Transaction.date >= start_date)
            if end_date:
                query = query.filter(Transaction.date <= end_date)
            
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
                logger.error(f"类别分析查询执行失败: {e}")
                raise AnalysisError(f"类别分析查询执行失败: {str(e)}")
            
            # 格式化结果
            categories = []
            for result in results:
                categories.append({
                    'category': result.type_enum,
                    'total': float(result.total_amount or 0),
                    'count': result.transaction_count,
                    'average': float(result.avg_amount or 0),
                    'is_income': float(result.total_amount or 0) > 0
                })
            
            return {
                'categories': categories,
                'total_categories': len(categories)
            }
            
        except AnalysisError:
            raise
        except Exception as e:
            logger.error(f"类别分析失败: {e}")
            raise AnalysisError(f"类别分析失败: {str(e)}")
    
    def _get_trend_analysis(self, account_id: int = None, start_date: date = None, 
                          end_date: date = None) -> Dict[str, Any]:
        """获取趋势分析"""
        try:
            cash_flow_result = self.analyze_cash_flow(start_date, end_date, account_id)
            
            # 生成周趋势和月趋势
            daily_trends = cash_flow_result['daily_trends']
            weekly_trends = self._aggregate_by_week(daily_trends)
            monthly_trends = self._aggregate_by_month(daily_trends)
            
            return {
                'daily': daily_trends,
                'weekly': weekly_trends,
                'monthly': monthly_trends
            }
            
        except Exception as e:
            logger.error(f"趋势分析失败: {e}")
            raise AnalysisError(f"趋势分析失败: {str(e)}")
    
    def _aggregate_by_week(self, daily_trends: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """将日趋势聚合为周趋势"""
        weekly_data = defaultdict(lambda: {'income': 0, 'expense': 0, 'net': 0, 'count': 0})
        
        for day_data in daily_trends:
            date_obj = datetime.strptime(day_data['date'], '%Y-%m-%d').date()
            week_start = date_obj - timedelta(days=date_obj.weekday())
            week_key = week_start.strftime('%Y-W%U')
            
            weekly_data[week_key]['income'] += day_data.get('income', 0)
            weekly_data[week_key]['expense'] += day_data.get('expense', 0)
            weekly_data[week_key]['net'] += day_data.get('net_amount', 0)
            weekly_data[week_key]['count'] += day_data.get('transaction_count', 0)
        
        return [{'week': week, **data} for week, data in sorted(weekly_data.items())]
    
    def _aggregate_by_month(self, daily_trends: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """将日趋势聚合为月趋势"""
        monthly_data = defaultdict(lambda: {'income': 0, 'expense': 0, 'net': 0, 'count': 0})
        
        for day_data in daily_trends:
            date_obj = datetime.strptime(day_data['date'], '%Y-%m-%d').date()
            month_key = date_obj.strftime('%Y-%m')
            
            monthly_data[month_key]['income'] += day_data.get('income', 0)
            monthly_data[month_key]['expense'] += day_data.get('expense', 0)
            monthly_data[month_key]['net'] += day_data.get('net_amount', 0)
            monthly_data[month_key]['count'] += day_data.get('transaction_count', 0)
        
        return [{'month': month, **data} for month, data in sorted(monthly_data.items())]
    
    def _generate_insights(self, account_id: int = None, start_date: date = None, 
                         end_date: date = None) -> List[Dict[str, Any]]:
        """生成财务洞察"""
        insights = []
        
        try:
            # 获取基础数据
            summary = self._get_period_summary(account_id, start_date, end_date)
            income_analysis = self.analyze_income(start_date, end_date, account_id)
            expense_analysis = self.analyze_expenses(start_date, end_date, account_id)
            
            # 生成收支平衡洞察
            if summary['net_income'] > 0:
                insights.append({
                    'type': 'positive',
                    'title': '收支平衡良好',
                    'description': f'本期净收入为 {summary["net_income"]:.2f} 元，财务状况健康。',
                    'priority': 'high'
                })
            elif summary['net_income'] < 0:
                insights.append({
                    'type': 'warning',
                    'title': '支出超过收入',
                    'description': f'本期净支出为 {abs(summary["net_income"]):.2f} 元，建议控制支出。',
                    'priority': 'high'
                })
            
            # 生成收入来源洞察
            if income_analysis['source_diversity'] == 1:
                insights.append({
                    'type': 'info',
                    'title': '收入来源单一',
                    'description': '建议多元化收入来源以降低财务风险。',
                    'priority': 'medium'
                })
            elif income_analysis['source_diversity'] >= 3:
                insights.append({
                    'type': 'positive',
                    'title': '收入来源多元化',
                    'description': f'拥有 {income_analysis["source_diversity"]} 个收入来源，风险分散良好。',
                    'priority': 'low'
                })
            
            # 生成支出洞察
            if expense_analysis['largest_category']:
                largest_cat = expense_analysis['largest_category']
                if largest_cat['percentage'] > 50:
                    insights.append({
                        'type': 'warning',
                        'title': '支出过于集中',
                        'description': f'{largest_cat["category"]} 占总支出的 {largest_cat["percentage"]:.1f}%，建议优化支出结构。',
                        'priority': 'medium'
                    })
            
        except Exception as e:
            logger.error(f"生成洞察失败: {e}")
            insights.append({
                'type': 'error',
                'title': '洞察生成失败',
                'description': '无法生成财务洞察，请稍后重试。',
                'priority': 'low'
            })
        
        return insights
    
    # ==================== 综合分析方法 ====================
    
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
        
        # 处理可能的AnalysisResult对象
        if hasattr(income_analysis, 'to_dict'):
            income_data = income_analysis.to_dict()
        else:
            income_data = income_analysis
            
        if hasattr(expense_analysis, 'to_dict'):
            expense_data = expense_analysis.to_dict()
        else:
            expense_data = expense_analysis
        
        return {
            'period': {'start_date': start_date, 'end_date': end_date, 'months': months},
            'income_summary': {
                'total_income': income_data.get('total_income', 0),
                'avg_monthly_income': income_data.get('total_income', 0) / months,
                'top_categories': sorted(
                    [(source['category'], source['total']) for source in income_data.get('income_sources', [])], 
                    key=lambda x: x[1], reverse=True
                )[:5]
            },
            'expense_summary': {
                'total_expense': expense_data.get('total_expense', 0),
                'avg_monthly_expense': expense_data.get('total_expense', 0) / months,
                'top_categories': sorted(
                    [(cat['category'], cat['total']) for cat in expense_data.get('expense_categories', [])], 
                    key=lambda x: x[1], reverse=True
                )[:5]
            },
            'cash_flow_summary': cash_flow_analysis,
            'financial_health': financial_health,
            'monthly_trends': monthly_trends,
            'key_insights': self._generate_key_insights(income_data, expense_data, cash_flow_analysis, financial_health)
        }
    
    def _generate_monthly_trends(self, start_date: date, end_date: date) -> List[Dict[str, Any]]:
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
        
        # 转换为字典列表
        trends = []
        for (year, month), data in sorted(monthly_data.items()):
            trends.append({
                'year': year,
                'month': month,
                'income': data['income'],
                'expense': data['expense'],
                'net_amount': data['income'] - data['expense'],
                'transaction_count': data['count']
            })
        
        return trends
    
    def _generate_key_insights(self, income_analysis, expense_analysis, cash_flow_analysis, financial_health) -> List[str]:
        """生成关键洞察"""
        insights = []
        
        # 处理可能的AnalysisResult对象
        if hasattr(financial_health, 'to_dict'):
            health_data = financial_health.to_dict()
        else:
            health_data = financial_health
            
        if hasattr(cash_flow_analysis, 'to_dict'):
            cash_flow_data = cash_flow_analysis.to_dict()
        else:
            cash_flow_data = cash_flow_analysis
        
        # 收入洞察
        income_sources = income_analysis.get('income_sources', [])
        if income_sources:
            top_income = income_sources[0]
            insights.append(f"主要收入来源：{top_income['category']}（{top_income['percentage']:.1f}%）")
        
        # 支出洞察
        expense_categories = expense_analysis.get('expense_categories', [])
        if expense_categories:
            top_expense = expense_categories[0]
            insights.append(f"最大支出类别：{top_expense['category']}（{top_expense['percentage']:.1f}%）")
        
        # 财务健康洞察
        health_level = health_data.get('health_level', 'unknown')
        if health_level == 'excellent':
            insights.append("财务状况优秀，继续保持")
        elif health_level == 'poor':
            insights.append("财务状况需要改善，建议制定理财计划")
        
        # 现金流洞察
        stability = cash_flow_data.get('cash_flow_stability', 0)
        if stability > 0.8:
            insights.append("现金流非常稳定")
        elif stability < 0.5:
            insights.append("现金流不够稳定，需要关注")
        
        return insights
    
    def generate_summary(self) -> Dict[str, Any]:
        """生成财务总览"""
        analysis = self.get_comprehensive_analysis(12)
        
        income_summary = analysis['income_summary']
        expense_summary = analysis['expense_summary']
        financial_health = analysis['financial_health']
        
        return {
            'total_income': income_summary['total_income'],
            'total_expense': expense_summary['total_expense'],
            'net_saving': income_summary['total_income'] - expense_summary['total_expense'],
            'avg_monthly_income': income_summary['avg_monthly_income'],
            'avg_monthly_expense': expense_summary['avg_monthly_expense'],
            'savings_rate': financial_health['savings_rate'],
            'expense_ratio': financial_health['expense_ratio'],
            'health_level': financial_health['health_level'],
            'health_score': financial_health['health_score']
        }