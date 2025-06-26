"""报告服务

专门负责财务数据的聚合和报告生成，为前端页面提供格式化的数据。
"""

from typing import List, Dict, Any, Optional
from decimal import Decimal
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
import logging

from app.models import Transaction, db
from sqlalchemy import func, case
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

# 导入分析服务
from .financial_analysis_service import FinancialAnalysisService

logger = logging.getLogger(__name__)

class ReportingService:
    """报告服务
    
    负责聚合和格式化财务数据，为前端页面提供完整的报告数据。
    依赖 FinancialAnalysisService 进行底层计算。
    """
    
    def __init__(self, db_session: Optional[Session] = None):
        """初始化报告服务
        
        Args:
            db_session: 数据库会话，如果为None则使用默认会话
        """
        self.db = db_session or db.session
        self.logger = logging.getLogger(__name__)
        self.analysis_service = FinancialAnalysisService(db_session)
    
    # ==================== 仪表盘数据聚合 ====================
    
    def get_financial_dashboard_data(self, start_date: date, end_date: date) -> Dict[str, Any]:
        """获取财务健康仪表盘数据
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            Dict[str, Any]: 仪表盘所需的全部数据
        """
        try:
            # 计算上一个同等时长的周期，用于对比
            period_days = (end_date - start_date).days
            prev_end_date = start_date - relativedelta(days=1)
            prev_start_date = prev_end_date - relativedelta(days=period_days)
            
            # 1. 净资产趋势数据
            net_worth_trend = self.analysis_service.get_net_worth_trend(start_date, end_date)
            
            # 2. 核心健康指标
            current_metrics = self.analysis_service.calculate_period_metrics(start_date, end_date)
            previous_metrics = self.analysis_service.calculate_period_metrics(prev_start_date, prev_end_date)
            
            # 3. 资金流分析数据
            cash_flow_data = self.get_cash_flow_data(start_date, end_date)
            
            # 4. 收入构成分析
            income_composition = self.get_income_composition(start_date, end_date)
            
            # 5. 支出构成分析
            expense_composition = self.get_expense_composition(start_date, end_date)
            
            # 计算对比指标
            income_change = self.analysis_service.calculate_change_percentage(
                current_metrics['total_income'], 
                previous_metrics['total_income']
            )
            expense_change = self.analysis_service.calculate_change_percentage(
                current_metrics['total_expense'], 
                previous_metrics['total_expense']
            )
            net_change = self.analysis_service.calculate_change_percentage(
                current_metrics['net_income'], 
                previous_metrics['net_income']
            )
            
            return {
                'period': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat(),
                    'days': period_days
                },
                'net_worth_trend': net_worth_trend,
                'core_metrics': {
                    'current_total_assets': current_metrics['current_total_assets'],
                    'total_income': current_metrics['total_income'],
                    'total_expense': current_metrics['total_expense'],
                    'net_income': current_metrics['net_income'],
                    'income_change_percentage': income_change,
                    'expense_change_percentage': expense_change,
                    'net_change_percentage': net_change
                },
                'cash_flow': cash_flow_data,
                'income_composition': income_composition,
                'expense_composition': expense_composition
            }
            
        except Exception as e:
            self.logger.error(f"获取仪表盘数据失败: {e}")
            return {
                'period': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat(),
                    'days': 0
                },
                'net_worth_trend': [],
                'core_metrics': {
                    'current_total_assets': 0.0,
                    'total_income': 0.0,
                    'total_expense': 0.0,
                    'net_income': 0.0,
                    'income_change_percentage': 0.0,
                    'expense_change_percentage': 0.0,
                    'net_change_percentage': 0.0
                },
                'cash_flow': [],
                'income_composition': [],
                'expense_composition': []
            }
    
    # ==================== 数据组合方法 ====================
    
    def get_cash_flow_data(self, start_date: date, end_date: date) -> List[Dict[str, Any]]:
        """获取资金流数据，按日统计收支
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            List[Dict[str, Any]]: 资金流数据
        """
        try:
            query = self.db.query(
                func.date(Transaction.date).label('date'),
                func.sum(
                    case(
                        (Transaction.amount > 0, Transaction.amount),
                        else_=0
                    )
                ).label('income'),
                func.sum(
                    case(
                        (Transaction.amount < 0, func.abs(Transaction.amount)),
                        else_=0
                    )
                ).label('expense')
            ).filter(
                Transaction.date >= start_date,
                Transaction.date <= end_date
            ).group_by(
                func.date(Transaction.date)
            ).order_by(
                func.date(Transaction.date)
            )
            
            results = query.all()
            
            return [{
                'date': result.date.isoformat() if hasattr(result.date, 'isoformat') else str(result.date),
                'income': float(result.income or 0),
                'expense': float(result.expense or 0),
                'net': float((result.income or 0) - (result.expense or 0))
            } for result in results]
            
        except Exception as e:
            self.logger.error(f"获取资金流数据失败: {e}")
            return []
    
    def get_income_composition(self, start_date: date, end_date: date) -> List[Dict[str, Any]]:
        """获取收入构成分析
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            List[Dict[str, Any]]: 收入构成数据
        """
        try:
            query = self.db.query(
                func.coalesce(Transaction.description, '未分类').label('category'),
                func.sum(Transaction.amount).label('total_amount'),
                func.count(Transaction.id).label('transaction_count')
            ).filter(
                Transaction.amount > 0,  # 只查询收入
                Transaction.date >= start_date,
                Transaction.date <= end_date
            ).group_by(
                func.coalesce(Transaction.description, '未分类')
            ).order_by(
                func.sum(Transaction.amount).desc()
            )
            
            results = query.all()
            
            # 计算总收入用于百分比计算
            total_income = sum(Decimal(str(result.total_amount or 0)) for result in results)
            
            return [{
                'name': result.category,
                'amount': float(result.total_amount or 0),
                'percentage': float((Decimal(str(result.total_amount or 0)) / total_income * 100) if total_income > 0 else 0),
                'count': result.transaction_count or 0
            } for result in results]
            
        except Exception as e:
            self.logger.error(f"获取收入构成失败: {e}")
            return []
    
    def get_expense_composition(self, start_date: date, end_date: date) -> List[Dict[str, Any]]:
        """获取支出构成分析
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            List[Dict[str, Any]]: 支出构成数据
        """
        try:
            query = self.db.query(
                func.coalesce(Transaction.description, '未分类').label('category'),
                func.sum(func.abs(Transaction.amount)).label('total_amount'),
                func.count(Transaction.id).label('transaction_count')
            ).filter(
                Transaction.amount < 0,  # 只查询支出
                Transaction.date >= start_date,
                Transaction.date <= end_date
            ).group_by(
                func.coalesce(Transaction.description, '未分类')
            ).order_by(
                func.sum(func.abs(Transaction.amount)).desc()
            )
            
            results = query.all()
            
            # 计算总支出用于百分比计算
            total_expense = sum(Decimal(str(result.total_amount or 0)) for result in results)
            
            return [{
                'name': result.category,
                'amount': float(result.total_amount or 0),
                'percentage': float((Decimal(str(result.total_amount or 0)) / total_expense * 100) if total_expense > 0 else 0),
                'count': result.transaction_count or 0
            } for result in results]
            
        except Exception as e:
            self.logger.error(f"获取支出构成失败: {e}")
            return []
    
    # ==================== 专项报告 ====================
    
    def get_income_expense_analysis(self, duration_months: int = 12) -> Dict[str, Any]:
        """获取收支分析数据
        
        Args:
            duration_months: 查询月数，默认12个月
            
        Returns:
            Dict[str, Any]: 收支分析数据
        """
        try:
            # 计算起始日期
            end_date = date.today()
            start_date = end_date - relativedelta(months=duration_months)
            
            # 查询指定时间范围内的月度收支数据
            query = self.db.query(
                func.strftime('%Y-%m', Transaction.date).label('month'),
                func.sum(
                    case(
                        (Transaction.amount > 0, Transaction.amount),
                        else_=0
                    )
                ).label('income'),
                func.sum(
                    case(
                        (Transaction.amount < 0, func.abs(Transaction.amount)),
                        else_=0
                    )
                ).label('expense')
            ).filter(
                Transaction.date >= start_date,
                Transaction.date <= end_date
            ).group_by(
                func.strftime('%Y-%m', Transaction.date)
            ).order_by(
                func.strftime('%Y-%m', Transaction.date)
            )
            
            results = query.all()
            
            # 格式化月度数据
            monthly_data = []
            total_income = Decimal('0')
            total_expense = Decimal('0')
            
            for result in results:
                income = Decimal(str(result.income or 0))
                expense = Decimal(str(result.expense or 0))
                
                monthly_data.append({
                    'month': result.month,
                    'income': float(income),
                    'expense': float(expense),
                    'net': float(income - expense)
                })
                
                total_income += income
                total_expense += expense
            
            return {
                'monthly_income_expense': monthly_data,
                'total_income': float(total_income),
                'total_expense': float(total_expense),
                'net_income': float(total_income - total_expense),
                'duration_months': duration_months,
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat()
            }
            
        except SQLAlchemyError as e:
            self.logger.error(f"数据库查询异常 - 收支分析查询失败: {e}")
            return {
                'monthly_income_expense': [],
                'total_income': 0.0,
                'total_expense': 0.0,
                'net_income': 0.0,
                'duration_months': duration_months,
                'start_date': '',
                'end_date': ''
            }
        except Exception as e:
            self.logger.error(f"收支分析查询失败: {e}")
            return {
                'monthly_income_expense': [],
                'total_income': 0.0,
                'total_expense': 0.0,
                'net_income': 0.0,
                'duration_months': duration_months,
                'start_date': '',
                'end_date': ''
            }
    
    def get_expense_overview_report(self, start_date: Optional[date] = None, 
                                  end_date: Optional[date] = None, 
                                  account_id: Optional[int] = None) -> Dict[str, Any]:
        """获取支出概览报告
        
        Args:
            start_date: 开始日期，None表示查询所有历史数据
            end_date: 结束日期，默认为今天
            account_id: 账户ID，None表示所有账户
            
        Returns:
            Dict[str, Any]: 支出概览报告
        """
        try:
            # 设置默认日期范围
            if not end_date:
                end_date = date.today()
            
            # 构建基础查询
            query = self.db.query(Transaction).filter(
                Transaction.amount < 0  # 只查询支出
            )
            
            # 添加时间范围过滤
            if start_date:
                query = query.filter(Transaction.date >= start_date)
            query = query.filter(Transaction.date <= end_date)
            
            # 添加账户过滤
            if account_id:
                query = query.filter(Transaction.account_id == account_id)
            
            # 计算总支出金额
            total_expense = query.with_entities(
                func.sum(func.abs(Transaction.amount))
            ).scalar() or Decimal('0.00')
            
            # 计算支出交易笔数
            expense_count = query.count()
            
            # 计算平均每月支出
            if start_date:
                months_diff = (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month)
                if months_diff == 0:
                    months_diff = 1
            else:
                # 查询所有历史数据时，计算从最早交易到现在的月数
                earliest_date = self.db.query(func.min(Transaction.date)).filter(
                    Transaction.amount < 0
                ).scalar()
                if earliest_date:
                    months_diff = (end_date.year - earliest_date.year) * 12 + (end_date.month - earliest_date.month)
                    if months_diff == 0:
                        months_diff = 1
                else:
                    months_diff = 1
            
            avg_monthly_expense = total_expense / months_diff
            
            return {
                'total_expense': float(total_expense),
                'expense_count': expense_count,
                'avg_monthly_expense': float(avg_monthly_expense),
                'start_date': start_date.isoformat() if start_date else None,
                'end_date': end_date.isoformat(),
                'months': months_diff
            }
            
        except SQLAlchemyError as e:
            self.logger.error(f"数据库查询异常 - 支出概览查询失败: {e}")
            return {}
        except Exception as e:
            self.logger.error(f"支出概览查询失败: {e}")
            return {}
    
    def get_expense_trends_report(self, months: int = 12, 
                                account_id: Optional[int] = None,
                                all_history: bool = False) -> List[Dict[str, Any]]:
        """获取支出趋势报告
        
        Args:
            months: 查询月数，默认12个月
            account_id: 账户ID，None表示所有账户
            all_history: 是否查询所有历史数据
            
        Returns:
            List[Dict[str, Any]]: 支出趋势数据
        """
        try:
            # 构建查询
            query = self.db.query(
                func.strftime('%Y-%m', Transaction.date).label('month'),
                func.sum(func.abs(Transaction.amount)).label('expense_amount'),
                func.count(Transaction.id).label('expense_count')
            ).filter(
                Transaction.amount < 0  # 只查询支出
            )
            
            # 添加时间范围过滤
            if not all_history:
                query = query.filter(Transaction.date >= func.date('now', f'-{months} months'))
            
            # 添加账户过滤
            if account_id:
                query = query.filter(Transaction.account_id == account_id)
            
            # 分组和排序
            results = query.group_by(
                func.strftime('%Y-%m', Transaction.date)
            ).order_by(
                func.strftime('%Y-%m', Transaction.date)
            ).all()
            
            # 格式化结果
            return [{
                'month': result.month,
                'expense_amount': float(result.expense_amount or 0),
                'expense_count': result.expense_count or 0
            } for result in results]
            
        except SQLAlchemyError as e:
            self.logger.error(f"数据库查询异常 - 支出趋势查询失败: {e}")
            return []
        except Exception as e:
            self.logger.error(f"支出趋势查询失败: {e}")
            return []
    
    def get_category_transactions(self, category: str, start_date: date, end_date: date) -> List[Dict[str, Any]]:
        """获取指定分类的交易明细（用于下钻功能）
        
        Args:
            category: 分类名称
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            List[Dict[str, Any]]: 交易明细列表
        """
        try:
            # 处理未分类的情况
            if category == '未分类':
                query = self.db.query(Transaction).filter(
                    Transaction.description.is_(None),
                    Transaction.date >= start_date,
                    Transaction.date <= end_date
                )
            else:
                query = self.db.query(Transaction).filter(
                    Transaction.description == category,
                    Transaction.date >= start_date,
                    Transaction.date <= end_date
                )
            
            results = query.order_by(Transaction.date.desc()).limit(50).all()
            
            return [{
                'id': transaction.id,
                'date': transaction.date.isoformat(),
                'amount': float(transaction.amount),
                'counterparty': transaction.counterparty,
                'description': transaction.description or '未分类',
                'balance_after': float(transaction.balance_after or 0)
            } for transaction in results]
            
        except Exception as e:
            self.logger.error(f"获取分类交易明细失败: {e}")
            return [] 