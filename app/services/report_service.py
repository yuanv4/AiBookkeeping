"""基础财务报告服务

简化了原来的 FinancialAnalysisService，保留基础分析功能，
移除过度复杂的算法，专注于个人用户的核心需求。

主要功能:
- 基础财务指标计算
- 收支统计和趋势分析
- 简单的分类汇总
- 仪表盘数据生成
"""

from typing import List, Dict, Any, Optional
from decimal import Decimal
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
import logging

from app.models import Transaction, Account, db
from sqlalchemy import func
from sqlalchemy.orm import Session

from .data_service import DataService
from .merchant_classification_service import MerchantClassificationService
from .models import (
    Period, CompositionItem, TrendPoint, PeriodSummary,
    AccountSummary, DashboardData, ExpenseItem,
    create_period, create_composition_item, create_trend_point,
    decimal_to_float, ReportConstants
)

logger = logging.getLogger(__name__)

class ReportService:
    """基础财务报告服务
    
    提供简化的财务分析和报告功能，专注于个人用户的核心需求。
    """
    
    def __init__(self, data_service: DataService = None, db_session: Optional[Session] = None):
        """初始化报告服务

        Args:
            data_service: 数据服务实例
            db_session: 数据库会话，如果为None则使用默认会话
        """
        self.data_service = data_service or DataService()
        self.db = db_session or db.session
        self.logger = logging.getLogger(__name__)
        self.merchant_service = MerchantClassificationService(db_session)

    # ==================== 基础财务指标 ====================
    
    def get_current_total_assets(self) -> Decimal:
        """获取当前总资产"""
        try:
            # 获取每个账户的最新余额
            latest_balances = self.get_latest_balance_by_account()
            total_assets = sum(latest_balances.values())
            return Decimal(str(total_assets))
        except Exception as e:
            self.logger.error(f"Error getting current total assets: {e}")
            return Decimal('0.00')

    def get_latest_balance_by_account(self, target_date: Optional[date] = None) -> Dict[int, Decimal]:
        """获取每个账户的最新余额"""
        try:
            # 简化的实现：获取每个账户的最新交易记录的余额
            accounts = Account.query.all()
            balances = {}
            
            for account in accounts:
                query = Transaction.query.filter_by(account_id=account.id)
                if target_date:
                    query = query.filter(Transaction.date <= target_date)
                
                latest_transaction = query.order_by(
                    Transaction.date.desc(), 
                    Transaction.created_at.desc()
                ).first()
                
                if latest_transaction and latest_transaction.balance_after:
                    balances[account.id] = latest_transaction.balance_after
                else:
                    balances[account.id] = Decimal('0.00')
            
            return balances
        except Exception as e:
            self.logger.error(f"Error getting latest balances: {e}")
            return {}

    def get_period_summary(self, start_date: date, end_date: date) -> Dict[str, Any]:
        """获取指定期间的收支汇总"""
        try:
            # 获取期间内的所有交易
            transactions = self.data_service.get_transactions(
                start_date=start_date,
                end_date=end_date
            )
            
            total_income = Decimal('0.00')
            total_expense = Decimal('0.00')
            
            for transaction in transactions:
                if transaction.amount > 0:
                    total_income += transaction.amount
                elif transaction.amount < 0:
                    total_expense += abs(transaction.amount)
            
            net_income = total_income - total_expense
            
            return {
                'period': {
                    'start_date': start_date.strftime('%Y-%m-%d'),
                    'end_date': end_date.strftime('%Y-%m-%d'),
                    'days': (end_date - start_date).days + 1
                },
                'total_income': total_income,
                'total_expense': total_expense,
                'net_income': net_income,
                'transaction_count': len(transactions)
            }
        except Exception as e:
            self.logger.error(f"Error getting period summary: {e}")
            return {
                'period': {
                    'start_date': start_date.strftime('%Y-%m-%d'),
                    'end_date': end_date.strftime('%Y-%m-%d'),
                    'days': (end_date - start_date).days + 1
                },
                'total_income': Decimal('0.00'),
                'total_expense': Decimal('0.00'),
                'net_income': Decimal('0.00'),
                'transaction_count': 0
            }

    # ==================== 趋势分析 ====================
    
    def get_monthly_trend(self, months: int = 12) -> List[Dict[str, Any]]:
        """获取月度收支趋势"""
        try:
            end_date = date.today()
            start_date = end_date - relativedelta(months=months)
            
            trends = []
            current_date = start_date.replace(day=1)  # 从月初开始
            
            while current_date <= end_date:
                # 计算当月的开始和结束日期
                month_start = current_date
                if current_date.month == 12:
                    month_end = current_date.replace(year=current_date.year + 1, month=1, day=1) - timedelta(days=1)
                else:
                    month_end = current_date.replace(month=current_date.month + 1, day=1) - timedelta(days=1)
                
                # 获取当月汇总
                summary = self.get_period_summary(month_start, month_end)
                
                trends.append({
                    'date': current_date.strftime('%Y-%m'),
                    'income': float(summary['total_income']),
                    'expense': float(summary['total_expense']),
                    'net': float(summary['net_income'])
                })
                
                # 移动到下个月
                if current_date.month == 12:
                    current_date = current_date.replace(year=current_date.year + 1, month=1)
                else:
                    current_date = current_date.replace(month=current_date.month + 1)
            
            return trends
        except Exception as e:
            self.logger.error(f"Error getting monthly trend: {e}")
            return []

    # ==================== 分类统计 ====================
    
    def get_expense_composition(self, start_date: date, end_date: date, limit: int = 10) -> List[Dict[str, Any]]:
        """获取支出构成分析"""
        try:
            # 按交易对手分组统计支出
            query = self.db.query(
                Transaction.counterparty,
                func.sum(func.abs(Transaction.amount)).label('total_amount'),
                func.count(Transaction.id).label('transaction_count')
            ).filter(
                Transaction.amount < 0,
                Transaction.date >= start_date,
                Transaction.date <= end_date,
                Transaction.counterparty.isnot(None),
                Transaction.counterparty != ''
            ).group_by(Transaction.counterparty).order_by(
                func.sum(func.abs(Transaction.amount)).desc()
            ).limit(limit)
            
            results = query.all()
            total_expense = sum(result.total_amount for result in results)
            
            composition = []
            for result in results:
                percentage = (result.total_amount / total_expense * 100) if total_expense > 0 else 0
                composition.append({
                    'name': result.counterparty,
                    'amount': float(result.total_amount),
                    'percentage': round(percentage, 2),
                    'count': result.transaction_count
                })
            
            return composition
        except Exception as e:
            self.logger.error(f"Error getting expense composition: {e}")
            return []

    def get_income_composition(self, start_date: date, end_date: date, limit: int = 10) -> List[Dict[str, Any]]:
        """获取收入构成分析"""
        try:
            # 按交易对手分组统计收入
            query = self.db.query(
                Transaction.counterparty,
                func.sum(Transaction.amount).label('total_amount'),
                func.count(Transaction.id).label('transaction_count')
            ).filter(
                Transaction.amount > 0,
                Transaction.date >= start_date,
                Transaction.date <= end_date,
                Transaction.counterparty.isnot(None),
                Transaction.counterparty != ''
            ).group_by(Transaction.counterparty).order_by(
                func.sum(Transaction.amount).desc()
            ).limit(limit)
            
            results = query.all()
            total_income = sum(result.total_amount for result in results)
            
            composition = []
            for result in results:
                percentage = (result.total_amount / total_income * 100) if total_income > 0 else 0
                composition.append({
                    'name': result.counterparty,
                    'amount': float(result.total_amount),
                    'percentage': round(percentage, 2),
                    'count': result.transaction_count
                })
            
            return composition
        except Exception as e:
            self.logger.error(f"Error getting income composition: {e}")
            return []

    # ==================== 仪表盘数据 ====================
    
    def get_dashboard_data(self, months: int = 12) -> Dict[str, Any]:
        """获取仪表盘数据"""
        try:
            # 计算时间范围
            end_date = date.today()
            start_date = end_date - relativedelta(months=months)
            
            # 获取当前总资产
            current_assets = self.get_current_total_assets()
            
            # 获取期间汇总
            period_summary = self.get_period_summary(start_date, end_date)
            
            # 获取月度趋势
            monthly_trend = self.get_monthly_trend(months)
            
            # 获取收支构成
            expense_composition = self.get_expense_composition(start_date, end_date)
            income_composition = self.get_income_composition(start_date, end_date)
            
            # 计算应急储备月数（简化计算）
            avg_monthly_expense = 0
            if monthly_trend:
                total_expense = sum(month['expense'] for month in monthly_trend)
                avg_monthly_expense = total_expense / len(monthly_trend) if len(monthly_trend) > 0 else 0
            
            emergency_reserve_months = float(current_assets) / avg_monthly_expense if avg_monthly_expense > 0 else 0
            
            # 转换月度趋势为净值趋势格式
            net_worth_trend = []
            for month_data in monthly_trend:
                net_worth_trend.append({
                    'date': month_data['date'],
                    'value': month_data['net']  # 使用净收支作为净值趋势
                })

            # 获取最新交易月份
            latest_transaction_month = None
            if monthly_trend:
                # 找到最近有交易的月份
                for month_data in reversed(monthly_trend):
                    if month_data['income'] > 0 or month_data['expense'] > 0:
                        latest_transaction_month = month_data['date']
                        break

            return {
                # 前端期望的核心指标格式
                'core_metrics': {
                    'current_total_assets': float(current_assets),
                    'total_income': float(period_summary['total_income']),
                    'total_expense': float(period_summary['total_expense']),
                    'net_income': float(period_summary['net_income']),
                    'emergency_reserve_months': round(emergency_reserve_months, 1),
                    'net_change_percentage': 0.0  # 简化版本，暂不计算变化百分比
                },
                # 前端期望的净值趋势格式
                'net_worth_trend': net_worth_trend,
                # 其他数据保持原格式
                'period': period_summary['period'],
                'monthly_trend': monthly_trend,
                'expense_composition': expense_composition,
                'income_composition': income_composition,
                'transaction_count': period_summary['transaction_count'],
                'latest_transaction_month': latest_transaction_month
            }
        except Exception as e:
            self.logger.error(f"Error getting dashboard data: {e}")
            return {
                # 前端期望的核心指标格式
                'core_metrics': {
                    'current_total_assets': 0.0,
                    'total_income': 0.0,
                    'total_expense': 0.0,
                    'net_income': 0.0,
                    'emergency_reserve_months': 0.0,
                    'net_change_percentage': 0.0
                },
                # 前端期望的净值趋势格式
                'net_worth_trend': [],
                # 其他数据
                'period': {
                    'start_date': start_date.strftime('%Y-%m-%d'),
                    'end_date': end_date.strftime('%Y-%m-%d'),
                    'days': (end_date - start_date).days + 1
                },
                'monthly_trend': [],
                'expense_composition': [],
                'income_composition': [],
                'transaction_count': 0,
                'latest_transaction_month': None
            }

    # ==================== 简单统计方法 ====================
    
    def get_top_expenses(self, start_date: date, end_date: date, limit: int = 10) -> List[Dict[str, Any]]:
        """获取最大支出项目"""
        try:
            transactions = self.db.query(Transaction).filter(
                Transaction.amount < 0,
                Transaction.date >= start_date,
                Transaction.date <= end_date
            ).order_by(Transaction.amount.asc()).limit(limit).all()
            
            return [{
                'date': transaction.date.strftime('%Y-%m-%d'),
                'amount': float(abs(transaction.amount)),
                'counterparty': transaction.counterparty or '未知',
                'description': transaction.description or ''
            } for transaction in transactions]
        except Exception as e:
            self.logger.error(f"Error getting top expenses: {e}")
            return []

    def get_account_summary(self) -> List[Dict[str, Any]]:
        """获取账户汇总信息"""
        try:
            accounts = self.data_service.get_all_accounts()
            balances = self.get_latest_balance_by_account()
            
            summary = []
            for account in accounts:
                balance = balances.get(account.id, Decimal('0.00'))
                summary.append({
                    'account_id': account.id,
                    'account_name': account.account_name or '未命名账户',
                    'account_number': account.account_number,
                    'bank_name': account.bank.name if account.bank else '未知银行',
                    'balance': float(balance),
                    'currency': account.currency or 'CNY'
                })
            
            return summary
        except Exception as e:
            self.logger.error(f"Error getting account summary: {e}")
            return []

    # ==================== 商户分类分析 ====================

    def get_merchant_expense_analysis(self, start_date: Optional[date] = None,
                                    end_date: Optional[date] = None,
                                    category_filter: Optional[str] = None,
                                    search_term: Optional[str] = None) -> Dict[str, Any]:
        """
        获取基于商户分类的支出分析数据

        Args:
            start_date: 开始日期，默认为6个月前
            end_date: 结束日期，默认为今天
            category_filter: 分类筛选，只返回指定分类的数据
            search_term: 搜索词，筛选包含该词的商户

        Returns:
            按商户类别组织的支出分析结果
        """
        try:
            self.logger.info(f"开始执行商户分类支出分析 - 分类筛选: {category_filter}, 搜索词: {search_term}")

            # 调用商户分类服务进行分析
            analysis_result = self.merchant_service.get_expense_analysis_by_category(
                start_date=start_date,
                end_date=end_date,
                category_filter=category_filter,
                search_term=search_term
            )

            self.logger.info("商户分类支出分析完成")
            return analysis_result

        except Exception as e:
            self.logger.error(f"商户分类支出分析失败: {e}")
            return {
                'categories': {},
                'summary': {
                    'total_expense': 0.0,
                    'analyzed_period': f"{start_date} to {end_date}",
                    'total_merchants': 0,
                    'total_transactions': 0
                }
            }

    def get_month_expense_analysis(self, target_month: str,
                                 category_filter: Optional[str] = None,
                                 search_term: Optional[str] = None) -> Dict[str, Any]:
        """
        获取指定月份的支出分析数据，包含完整的历史月度数据

        Args:
            target_month: 目标月份 (YYYY-MM格式)
            category_filter: 分类筛选
            search_term: 搜索词筛选

        Returns:
            指定月份的支出分析结果，包含所有历史月度数据
        """
        try:
            self.logger.info(f"开始执行月份支出分析 - 目标月份: {target_month}, 分类筛选: {category_filter}, 搜索词: {search_term}")

            # 调用商户分类服务的月份分析方法
            result = self.merchant_service.get_month_expense_analysis(
                target_month=target_month,
                category_filter=category_filter,
                search_term=search_term
            )

            self.logger.info(f"月份支出分析完成 - {target_month}")
            return result

        except Exception as e:
            self.logger.error(f"月份支出分析失败: {e}")
            return {
                'categories': {},
                'summary': {
                    'total_expense': 0.0,
                    'analyzed_period': target_month,
                    'total_merchants': 0,
                    'total_transactions': 0
                },
                'target_month': target_month,
                'period': {
                    'start_date': None,
                    'end_date': None,
                    'month': target_month
                }
            }


