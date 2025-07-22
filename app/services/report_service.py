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

from .bank_service import BankService
from .account_service import AccountService
from .transaction_service import TransactionService
from .category_service import CategoryService
from app.utils import DataUtils
from app.utils.decorators import cached_query

logger = logging.getLogger(__name__)

class ReportService:
    """基础财务报告服务
    
    提供简化的财务分析和报告功能，专注于个人用户的核心需求。
    """
    
    def __init__(self, bank_service: BankService, account_service: AccountService, transaction_service: TransactionService, category_service: CategoryService, db_session: Optional[Session] = None):
        """初始化报告服务

        Args:
            bank_service: 银行服务实例
            account_service: 账户服务实例
            transaction_service: 交易服务实例
            category_service: 分类服务实例
            db_session: 数据库会话，如果为None则使用默认会话
        """
        self.bank_service = bank_service
        self.account_service = account_service
        self.transaction_service = transaction_service
        self.category_service = category_service
        self.db = db_session or db.session
        self.logger = logging.getLogger(__name__)

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
            transactions = self.transaction_service.get_transactions(
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
    
    @cached_query()
    def get_monthly_trend(self, months: int = 12) -> List[Dict[str, Any]]:
        """获取月度收支趋势"""
        try:
            # 使用DataUtils计算日期范围
            start_date, end_date = DataUtils.get_date_range(months)

            # 获取指定时间范围内的所有交易数据
            transactions = self.transaction_service.get_transactions(
                start_date=start_date,
                end_date=end_date
            )

            # 按月份分组统计数据
            monthly_data = {}

            # 初始化所有月份的数据结构
            current_date = start_date.replace(day=1)
            while current_date <= end_date:
                month_key = current_date.strftime('%Y-%m')
                monthly_data[month_key] = {
                    'date': month_key,
                    'income': 0.0,
                    'expense': 0.0,
                    'net': 0.0
                }
                # 使用 relativedelta 简化日期计算
                current_date = current_date + relativedelta(months=1)

            # 单次遍历所有交易，按月份累加
            for transaction in transactions:
                month_key = transaction.date.strftime('%Y-%m')
                if month_key in monthly_data:
                    amount = float(transaction.amount)
                    if amount > 0:
                        monthly_data[month_key]['income'] += amount
                    else:
                        monthly_data[month_key]['expense'] += abs(amount)

            # 计算净收入
            for data in monthly_data.values():
                data['net'] = data['income'] - data['expense']

            # 按日期排序返回
            return sorted(monthly_data.values(), key=lambda x: x['date'])

        except Exception as e:
            self.logger.error(f"Error getting monthly trend: {e}")
            return []

    # ==================== 分类统计 ====================
    
    @cached_query()
    def get_expense_composition(self, start_date: date, end_date: date, limit: int = 10) -> List[Dict[str, Any]]:
        """获取支出构成分析

        Args:
            start_date: 开始日期
            end_date: 结束日期
            limit: 返回结果数量限制，默认10条

        Returns:
            List[Dict[str, Any]]: 支出构成列表，每项包含：
                - name: 交易对手名称
                - amount: 支出金额
                - percentage: 占比百分比
                - count: 交易次数


        """
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

    @cached_query()
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
            # 计算时间范围 - 使用DataUtils
            start_date, end_date = DataUtils.get_date_range(months)
            
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
            accounts = self.account_service.get_all_accounts()
            balances = self.get_latest_balance_by_account()
            
            summary = []
            for account in accounts:
                balance = balances.get(account.id, Decimal('0.00'))
                summary.append({
                    'account_id': account.id,
                    'name': account.name or '未命名账户',
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

    def get_available_months(self) -> Dict[str, Any]:
        """获取有交易数据的月份列表

        Returns:
            Dict包含months列表和latest_month
        """
        try:
            # 查询所有交易的月份
            query = self.db.query(
                func.strftime('%Y-%m', Transaction.date).label('month')
            ).distinct().order_by(
                func.strftime('%Y-%m', Transaction.date).desc()
            )

            results = query.all()
            months = [result.month for result in results if result.month]

            return {
                'months': months,
                'latest_month': months[0] if months else None
            }

        except Exception as e:
            self.logger.error(f"Error getting available months: {e}")
            return {
                'months': [],
                'latest_month': None
            }

    def get_expense_analysis_by_category(self, start_date: Optional[date] = None,
                                       end_date: Optional[date] = None,
                                       category_filter: Optional[str] = None,
                                       search_term: Optional[str] = None) -> Dict[str, Any]:
        """获取按分类的支出分析

        Args:
            start_date: 开始日期，默认为6个月前
            end_date: 结束日期，默认为今天
            category_filter: 分类筛选
            search_term: 搜索词

        Returns:
            按商户类别组织的支出分析结果
        """
        try:
            # 设置默认日期范围
            if not start_date or not end_date:
                start_date, end_date = DataUtils.get_date_range(6)

            # 查询支出交易
            query = self.db.query(Transaction).filter(
                Transaction.amount < 0,
                Transaction.date >= start_date,
                Transaction.date <= end_date
            )

            # 应用搜索过滤
            if search_term:
                query = query.filter(
                    Transaction.counterparty.ilike(f'%{search_term}%')
                )

            transactions = query.all()

            # 按分类组织数据
            categories = {}
            total_expense = 0.0

            for transaction in transactions:
                amount = abs(float(transaction.amount))
                total_expense += amount

                # 获取商户分类和信息
                category_with_info = self.category_service.classify_merchant_with_info(transaction.counterparty or '')
                category = category_with_info['code']

                # 应用分类过滤
                if category_filter and category != category_filter:
                    continue

                # 初始化分类数据
                if category not in categories:
                    categories[category] = {
                        'name': category_with_info['name'],
                        'icon': category_with_info['icon'],
                        'color': category_with_info['color'],
                        'total_amount': 0.0,
                        'percentage': 0.0,
                        'merchants': {}
                    }

                # 累加分类总额
                categories[category]['total_amount'] += amount

                # 处理商户数据
                merchant_name = transaction.counterparty or '未知商户'
                if merchant_name not in categories[category]['merchants']:
                    categories[category]['merchants'][merchant_name] = {
                        'total_amount': 0.0,
                        'transaction_count': 0,
                        'avg_amount': 0.0
                    }

                categories[category]['merchants'][merchant_name]['total_amount'] += amount
                categories[category]['merchants'][merchant_name]['transaction_count'] += 1

            # 计算百分比和平均金额
            for category_data in categories.values():
                if total_expense > 0:
                    category_data['percentage'] = (category_data['total_amount'] / total_expense) * 100

                for merchant_data in category_data['merchants'].values():
                    if merchant_data['transaction_count'] > 0:
                        merchant_data['avg_amount'] = merchant_data['total_amount'] / merchant_data['transaction_count']

            return {
                'categories': categories,
                'summary': {
                    'total_expense': total_expense,
                    'analyzed_period': f"{start_date} to {end_date}",
                    'total_merchants': sum(len(cat['merchants']) for cat in categories.values()),
                    'total_transactions': len(transactions)
                }
            }

        except Exception as e:
            self.logger.error(f"Error in expense analysis by category: {e}")
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
        """获取指定月份的商户分类支出分析，包含历史月度数据

        Args:
            target_month: 目标月份，格式为 YYYY-MM
            category_filter: 分类筛选
            search_term: 搜索词

        Returns:
            包含当月分析和历史月度数据的结果
        """
        try:
            from datetime import datetime

            # 解析目标月份
            target_date = datetime.strptime(target_month, '%Y-%m').date()
            month_start = target_date.replace(day=1)

            # 计算月末
            if target_date.month == 12:
                month_end = target_date.replace(year=target_date.year + 1, month=1, day=1) - timedelta(days=1)
            else:
                month_end = target_date.replace(month=target_date.month + 1, day=1) - timedelta(days=1)

            # 获取当月的分类分析
            current_analysis = self.get_expense_analysis_by_category(
                start_date=month_start,
                end_date=month_end,
                category_filter=category_filter,
                search_term=search_term
            )

            # 获取历史月度数据（最近12个月）
            monthly_data = {}
            for i in range(12):
                hist_date = target_date - relativedelta(months=i)
                hist_month = hist_date.strftime('%Y-%m')
                hist_start = hist_date.replace(day=1)

                if hist_date.month == 12:
                    hist_end = hist_date.replace(year=hist_date.year + 1, month=1, day=1) - timedelta(days=1)
                else:
                    hist_end = hist_date.replace(month=hist_date.month + 1, day=1) - timedelta(days=1)

                # 查询该月的分类支出
                month_query = self.db.query(Transaction).filter(
                    Transaction.amount < 0,
                    Transaction.date >= hist_start,
                    Transaction.date <= hist_end
                )

                month_transactions = month_query.all()
                month_categories = {}

                for transaction in month_transactions:
                    category = self.category_service.classify_merchant(transaction.counterparty or '')
                    amount = abs(float(transaction.amount))

                    if category not in month_categories:
                        month_categories[category] = 0.0
                    month_categories[category] += amount

                monthly_data[hist_month] = month_categories

            # 将月度数据添加到分类中
            for category_key, category_data in current_analysis['categories'].items():
                category_data['monthly_data'] = {}
                for month, month_cats in monthly_data.items():
                    category_data['monthly_data'][month] = month_cats.get(category_key, 0.0)

            return current_analysis

        except Exception as e:
            self.logger.error(f"Error in month expense analysis: {e}")
            return {
                'categories': {},
                'summary': {
                    'total_expense': 0.0,
                    'analyzed_period': target_month,
                    'total_merchants': 0,
                    'total_transactions': 0
                }
            }

    def get_merchant_transactions(self, merchant_name: str, month: Optional[str] = None) -> Dict[str, Any]:
        """获取商户交易详情

        Args:
            merchant_name: 商户名称
            month: 可选的月份筛选，格式为 YYYY-MM

        Returns:
            商户详情和交易记录
        """
        try:
            # 构建查询
            query = self.db.query(Transaction).filter(
                Transaction.counterparty == merchant_name
            )

            # 应用月份筛选
            if month:
                from datetime import datetime
                target_date = datetime.strptime(month, '%Y-%m').date()
                month_start = target_date.replace(day=1)

                if target_date.month == 12:
                    month_end = target_date.replace(year=target_date.year + 1, month=1, day=1) - timedelta(days=1)
                else:
                    month_end = target_date.replace(month=target_date.month + 1, day=1) - timedelta(days=1)

                query = query.filter(
                    Transaction.date >= month_start,
                    Transaction.date <= month_end
                )

            transactions = query.order_by(Transaction.date.desc()).all()

            # 计算统计信息
            total_amount = sum(abs(float(t.amount)) for t in transactions if t.amount < 0)
            transaction_count = len([t for t in transactions if t.amount < 0])
            average_amount = total_amount / transaction_count if transaction_count > 0 else 0.0

            # 获取商户分类信息
            category_with_info = self.category_service.classify_merchant_with_info(merchant_name)
            category = category_with_info['code']
            category_info = {k: v for k, v in category_with_info.items() if k != 'code'}

            # 构建交易列表
            transaction_list = []
            for transaction in transactions:
                if transaction.amount < 0:  # 只显示支出交易
                    transaction_list.append({
                        'date': transaction.date.strftime('%Y-%m-%d'),
                        'amount': abs(float(transaction.amount)),
                        'account': transaction.account.name if transaction.account else None,
                        'description': transaction.description
                    })

            # 构建筛选信息
            filter_info = {}
            if month:
                filter_info['period_info'] = f"{month}月"
            else:
                filter_info['period_info'] = "所有时间"

            return {
                'merchant_name': merchant_name,
                'category_info': category_info,
                'statistics': {
                    'total_amount': total_amount,
                    'transaction_count': transaction_count,
                    'average_amount': average_amount
                },
                'transactions': transaction_list,
                'filter_info': filter_info
            }

        except Exception as e:
            self.logger.error(f"Error getting merchant transactions for {merchant_name}: {e}")
            return {
                'merchant_name': merchant_name,
                'category_info': self.category_service.get_category_display_info('other'),
                'statistics': {
                    'total_amount': 0.0,
                    'transaction_count': 0,
                    'average_amount': 0.0
                },
                'transactions': [],
                'filter_info': {'period_info': '无数据'}
            }




