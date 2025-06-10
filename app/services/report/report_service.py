"""Financial Report Service.

This module provides comprehensive financial reporting functionality.
"""

from typing import List, Dict, Any, Optional, Tuple
from decimal import Decimal
from datetime import date, datetime, timedelta
import logging
from collections import defaultdict
import calendar

from app.models import Transaction, Account, Bank, db
# 查询构建器功能已移除，直接使用 SQLAlchemy 查询

class AnalysisException(Exception):
    """分析服务自定义异常类"""
    pass
# 缓存和性能监控功能已移除
from sqlalchemy import func, and_, or_, extract, case
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)

class FinancialReportService:
    """Service for generating financial reports."""
    
    @staticmethod
    def generate_financial_report(account_id: int = None, start_date: date = None, 
                                end_date: date = None) -> Dict[str, Any]:
        """Generate comprehensive financial report."""
        try:
            if not start_date:
                start_date = date.today().replace(day=1)  # First day of current month
            if not end_date:
                end_date = date.today()
            
            report = {
                'period': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat(),
                    'days': (end_date - start_date).days + 1
                },
                'summary': FinancialReportService._get_period_summary(account_id, start_date, end_date),
                'income_analysis': FinancialReportService._get_income_analysis(account_id, start_date, end_date),
                'expense_analysis': FinancialReportService._get_expense_analysis(account_id, start_date, end_date),
                'category_breakdown': FinancialReportService._get_category_breakdown(account_id, start_date, end_date),
                'trends': FinancialReportService._get_trend_analysis(account_id, start_date, end_date),
                'insights': FinancialReportService._generate_insights(account_id, start_date, end_date)
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
            logger.error(f"Error generating financial report: {e}")
            raise
    
    @staticmethod
    def _get_period_summary(account_id: int = None, start_date: date = None, 
                          end_date: date = None) -> Dict[str, Any]:
        """Get summary statistics for the period using optimized query."""
        try:
            # 直接使用 SQLAlchemy 查询替代查询构建器
            # 简单的参数验证
            if account_id and (not isinstance(account_id, int) or account_id <= 0):
                raise AnalysisException("无效的账户ID")
            if start_date and end_date and start_date > end_date:
                raise AnalysisException("开始日期不能晚于结束日期")
            
            # 使用聚合查询替代加载所有交易记录
            query = db.session.query(
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
            
            # 安全执行查询
            try:
                result = query.first()
            except Exception as e:
                logger.error(f"期间汇总查询执行失败: {e}")
                raise AnalysisException(f"期间汇总查询执行失败: {str(e)}")
            
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
            
        except AnalysisException as e:
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
    
    @staticmethod
    def _get_income_analysis(account_id: int = None, start_date: date = None, 
                           end_date: date = None) -> Dict[str, Any]:
        """Analyze income patterns using optimized query."""
        try:
            # 直接使用 SQLAlchemy 查询替代查询构建器
            # 简单的参数验证
            if account_id and (not isinstance(account_id, int) or account_id <= 0):
                raise AnalysisException("无效的账户ID")
            if start_date and end_date and start_date > end_date:
                raise AnalysisException("开始日期不能晚于结束日期")
            
            # 构建收入分析查询
            query = db.session.query(
                Transaction.transaction_type.label('type_enum'),
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
            query = query.group_by(Transaction.transaction_type).order_by(
                func.sum(Transaction.amount).desc()
            )
            
            # 安全执行查询
            try:
                results = query.all()
            except Exception as e:
                logger.error(f"收入分析查询执行失败: {e}")
                raise AnalysisException(f"收入分析查询执行失败: {str(e)}")
            
            # 格式化结果
            income_sources = []
            for result in results:
                income_sources.append({
                    'category': result.name,
                    'total': float(result.total_amount or 0),
                    'count': result.transaction_count,
                    'average': float(result.avg_amount or 0),
                    'color': result.color,
                    'icon': result.icon
                })
            
            total_income = sum(source['total'] for source in income_sources)
            
            # 计算百分比
            for source in income_sources:
                source['percentage'] = (source['total'] / total_income * 100) if total_income > 0 else 0
            
            return {
                'total_income': total_income,
                'income_sources': income_sources,
                'primary_source': income_sources[0] if income_sources else None,
                'source_diversity': len(income_sources)
            }
            
        except AnalysisException as e:
            logger.error(f"收入分析失败: {e}")
            return {
                'total_income': 0,
                'income_sources': [],
                'primary_source': None,
                'source_diversity': 0
            }
    
    @staticmethod
    def _get_expense_analysis(account_id: int = None, start_date: date = None, 
                            end_date: date = None) -> Dict[str, Any]:
        """Analyze expense patterns using optimized query."""
        try:
            # 直接使用 SQLAlchemy 查询替代查询构建器
            # 简单的参数验证
            if account_id and (not isinstance(account_id, int) or account_id <= 0):
                raise AnalysisException("无效的账户ID")
            if start_date and end_date and start_date > end_date:
                raise AnalysisException("开始日期不能晚于结束日期")
            
            # 构建支出分析查询
            query = db.session.query(
                Transaction.transaction_type.label('type_enum'),
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
            query = query.group_by(Transaction.transaction_type).order_by(
                func.sum(func.abs(Transaction.amount)).desc()
            )
            
            # 安全执行查询
            try:
                results = query.all()
            except Exception as e:
                logger.error(f"支出分析查询执行失败: {e}")
                raise AnalysisException(f"支出分析查询执行失败: {str(e)}")
            
            # 格式化结果（支出金额取绝对值）
            expense_categories = []
            for result in results:
                category_data = {
                    'category': result.name,
                    'count': result.count,
                    'total': abs(float(result.total)),  # 取绝对值
                    'average': abs(float(result.average)),
                    'maximum': abs(float(result.maximum)),
                    'minimum': abs(float(result.minimum))
                }
                expense_categories.append(category_data)
            
            total_expense = sum(category['total'] for category in expense_categories)
            
            # 计算百分比
            for category in expense_categories:
                category['percentage'] = (category['total'] / total_expense * 100) if total_expense > 0 else 0
            
            return {
                'total_expense': total_expense,
                'expense_categories': expense_categories,
                'largest_category': expense_categories[0] if expense_categories else None,
                'category_count': len(expense_categories)
            }
            
        except AnalysisException as e:
            logger.error(f"支出分析失败: {e}")
            return {
                'total_expense': 0,
                'expense_categories': [],
                'largest_category': None,
                'category_count': 0
            }
    
    @staticmethod
    def _get_category_breakdown(account_id: int = None, start_date: date = None, 
                              end_date: date = None) -> Dict[str, Any]:
        """Get detailed category breakdown using optimized query."""
        try:
            # 直接使用 SQLAlchemy 查询替代查询构建器
            # 简单的参数验证
            if account_id and (not isinstance(account_id, int) or account_id <= 0):
                raise AnalysisException("无效的账户ID")
            if start_date and end_date and start_date > end_date:
                raise AnalysisException("开始日期不能晚于结束日期")
            
            # 构建类别分析查询
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
            if account_id:
                query = query.filter(Transaction.account_id == account_id)
            if start_date:
                query = query.filter(Transaction.date >= start_date)
            if end_date:
                query = query.filter(Transaction.date <= end_date)
            
            # 分组和排序
            query = query.group_by(Transaction.transaction_type).order_by(
                func.sum(func.abs(Transaction.amount)).desc()
            )
            
            # 安全执行查询
            try:
                results = query.all()
            except Exception as e:
                logger.error(f"类别分析查询执行失败: {e}")
                raise AnalysisException(f"类别分析查询执行失败: {str(e)}")
            
            # 格式化结果
            categories = []
            for result in results:
                categories.append({
                    'category': result.name,
                    'total': float(result.total_amount or 0),
                    'count': result.transaction_count,
                    'average': float(result.avg_amount or 0),
                    'is_income': result.is_income,
                    'color': result.color,
                    'icon': result.icon
                })
            
            return {
                'categories': categories,
                'total_categories': len(categories)
            }
            
        except AnalysisException:
            raise
        except Exception as e:
            logger.error(f"类别分析失败: {e}")
            raise AnalysisException(f"类别分析失败: {str(e)}")
    
    @staticmethod
    def _get_trend_analysis(account_id: int = None, start_date: date = None, 
                          end_date: date = None) -> Dict[str, Any]:
        """Analyze trends over time using optimized queries."""
        try:
            # 直接使用 SQLAlchemy 查询替代查询构建器
            # 简单的参数验证
            if account_id and (not isinstance(account_id, int) or account_id <= 0):
                raise AnalysisException("无效的账户ID")
            if start_date and end_date and start_date > end_date:
                raise AnalysisException("开始日期不能晚于结束日期")
            
            # 构建日趋势分析查询
            daily_query = db.session.query(
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
            
            # 安全执行查询
            try:
                daily_results = daily_query.all()
            except Exception as e:
                logger.error(f"日趋势分析查询执行失败: {e}")
                raise AnalysisException(f"日趋势分析查询执行失败: {str(e)}")
            
            # 格式化日趋势数据
            daily_trends = []
            for result in daily_results:
                daily_trends.append({
                    'date': result.date.isoformat(),
                    'net_amount': float(result.net_amount or 0),
                    'income': float(result.income or 0),
                    'expense': float(result.expense or 0),
                    'transaction_count': result.transaction_count
                })
            
            # 生成周趋势和月趋势
            weekly_trends = FinancialReportService._aggregate_by_week(daily_trends)
            monthly_trends = FinancialReportService._aggregate_by_month(daily_trends)
            
            return {
                'daily': daily_trends,
                'weekly': weekly_trends,
                'monthly': monthly_trends
            }
            
        except AnalysisException:
            raise
        except Exception as e:
            logger.error(f"趋势分析失败: {e}")
            raise AnalysisException(f"趋势分析失败: {str(e)}")
    
    @staticmethod
    def _aggregate_by_week(daily_trends: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Aggregate daily trends into weekly trends."""
        weekly_data = defaultdict(lambda: {'income': 0, 'expense': 0, 'net': 0, 'count': 0})
        
        for day_data in daily_trends:
            # 假设日期格式为 'YYYY-MM-DD'
            date_obj = datetime.strptime(day_data['date'], '%Y-%m-%d').date()
            week_start = date_obj - timedelta(days=date_obj.weekday())
            week_key = week_start.strftime('%Y-W%U')
            
            weekly_data[week_key]['income'] += day_data.get('income', 0)
            weekly_data[week_key]['expense'] += day_data.get('expense', 0)
            weekly_data[week_key]['net'] += day_data.get('net', 0)
            weekly_data[week_key]['count'] += day_data.get('count', 0)
        
        return [{'week': week, **data} for week, data in sorted(weekly_data.items())]
    
    @staticmethod
    def _aggregate_by_month(daily_trends: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Aggregate daily trends into monthly trends."""
        monthly_data = defaultdict(lambda: {'income': 0, 'expense': 0, 'net': 0, 'count': 0})
        
        for day_data in daily_trends:
            # 假设日期格式为 'YYYY-MM-DD'
            date_obj = datetime.strptime(day_data['date'], '%Y-%m-%d').date()
            month_key = date_obj.strftime('%Y-%m')
            
            monthly_data[month_key]['income'] += day_data.get('income', 0)
            monthly_data[month_key]['expense'] += day_data.get('expense', 0)
            monthly_data[month_key]['net'] += day_data.get('net', 0)
            monthly_data[month_key]['count'] += day_data.get('count', 0)
        
        return [{'month': month, **data} for month, data in sorted(monthly_data.items())]
    
    @staticmethod
    def _generate_insights(account_id: int = None, start_date: date = None, 
                         end_date: date = None) -> List[Dict[str, Any]]:
        """Generate financial insights based on analysis."""
        insights = []
        
        try:
            # 获取基础数据
            summary = FinancialReportService._get_period_summary(account_id, start_date, end_date)
            income_analysis = FinancialReportService._get_income_analysis(account_id, start_date, end_date)
            expense_analysis = FinancialReportService._get_expense_analysis(account_id, start_date, end_date)
            
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