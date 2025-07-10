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
from app.utils.expense_algorithm import ExpenseAlgorithm
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
        self.expense_algorithm = ExpenseAlgorithm()

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

    # ==================== 支出分析算法 ====================

    def get_fixed_expenses_analysis(self) -> Dict[str, Any]:
        """
        获取固定支出分析数据

        Returns:
            包含日常固定支出和大额固定支出的分析结果
        """
        try:
            self.logger.info("开始执行固定支出分析")

            # 获取所有有重复交易的商户
            merchants = self.db.query(Transaction.counterparty, func.count(Transaction.id).label('count')).filter(
                Transaction.amount < 0,
                Transaction.counterparty.isnot(None)
            ).group_by(Transaction.counterparty).having(
                func.count(Transaction.id) >= 3
            ).all()

            self.logger.info(f"找到 {len(merchants)} 个有重复交易的商户")

            # 分析每个商户
            results = []
            for merchant_info in merchants:
                merchant_name = merchant_info.counterparty

                transactions = self.db.query(Transaction).filter(
                    Transaction.amount < 0,
                    Transaction.counterparty == merchant_name
                ).order_by(Transaction.date.asc()).all()

                if len(transactions) >= 3:
                    try:
                        score_info = self.expense_algorithm.calculate_optimized_score(transactions)
                        if score_info and score_info['total_score'] > 0:
                            score_info['merchant'] = merchant_name
                            score_info['last_date'] = transactions[-1].date
                            results.append(score_info)
                    except Exception as e:
                        self.logger.error(f"分析商户 {merchant_name} 时出错: {e}")
                        continue

            self.logger.info(f"成功分析 {len(results)} 个商户")

            # 按总评分排序
            results.sort(key=lambda x: x['total_score'], reverse=True)

            # 分类固定支出
            try:
                daily_fixed_merchants, large_fixed_merchants = self.expense_algorithm.classify_fixed_expenses(results)
                self.logger.info(f"分类结果: 日常固定支出 {len(daily_fixed_merchants)} 个，大额固定支出 {len(large_fixed_merchants)} 个")
            except Exception as e:
                self.logger.error(f"分类固定支出时出错: {e}")
                daily_fixed_merchants, large_fixed_merchants = [], []

            # 计算月度数据
            try:
                daily_monthly_data = self._get_monthly_expenses(daily_fixed_merchants) if daily_fixed_merchants else []
                large_monthly_data = self._get_monthly_expenses(large_fixed_merchants) if large_fixed_merchants else []
                self.logger.info(f"月度数据: 日常 {len(daily_monthly_data)} 个月，大额 {len(large_monthly_data)} 个月")
            except Exception as e:
                self.logger.error(f"计算月度数据时出错: {e}")
                daily_monthly_data, large_monthly_data = [], []

            # 为商户数据添加月度明细
            daily_merchants_with_details = []
            for r in results:
                if r['merchant'] in daily_fixed_merchants:
                    merchant_data = r.copy()
                    merchant_data['monthly_details'] = self._get_merchant_monthly_details(r['merchant'])
                    daily_merchants_with_details.append(merchant_data)

            large_merchants_with_details = []
            for r in results:
                if r['merchant'] in large_fixed_merchants:
                    merchant_data = r.copy()
                    merchant_data['monthly_details'] = self._get_merchant_monthly_details(r['merchant'])
                    large_merchants_with_details.append(merchant_data)

            result = {
                'daily_fixed_expenses': {
                    'merchants': daily_merchants_with_details,
                    'monthly_data': daily_monthly_data,
                    'monthly_average': sum(d['amount'] for d in daily_monthly_data) / len(daily_monthly_data) if daily_monthly_data else 0
                },
                'large_fixed_expenses': {
                    'merchants': large_merchants_with_details,
                    'monthly_data': large_monthly_data,
                    'monthly_average': sum(d['amount'] for d in large_monthly_data) / len(large_monthly_data) if large_monthly_data else 0
                },
                'algorithm_summary': {
                    'total_merchants_analyzed': len(merchants),
                    'fixed_merchants_identified': len(daily_fixed_merchants) + len(large_fixed_merchants),
                    'daily_fixed_count': len(daily_fixed_merchants),
                    'large_fixed_count': len(large_fixed_merchants)
                }
            }

            self.logger.info("固定支出分析完成")
            return result
        except Exception as e:
            self.logger.error(f"Error in fixed expenses analysis: {e}")
            return {
                'daily_fixed_expenses': {'merchants': [], 'monthly_data': [], 'monthly_average': 0},
                'large_fixed_expenses': {'merchants': [], 'monthly_data': [], 'monthly_average': 0},
                'algorithm_summary': {'total_merchants_analyzed': 0, 'fixed_merchants_identified': 0}
            }

    def _get_monthly_expenses(self, merchant_names: List[str]) -> List[Dict[str, Any]]:
        """
        获取指定商户的月度支出数据

        Args:
            merchant_names: 商户名称列表

        Returns:
            月度支出数据列表
        """
        if not merchant_names:
            return []

        try:
            monthly_data = self.db.query(
                func.strftime('%Y-%m', Transaction.date).label('month'),
                func.sum(func.abs(Transaction.amount)).label('amount'),
                func.count(Transaction.id).label('transaction_count')
            ).filter(
                Transaction.amount < 0,
                Transaction.counterparty.in_(merchant_names)
            ).group_by(
                func.strftime('%Y-%m', Transaction.date)
            ).order_by(
                func.strftime('%Y-%m', Transaction.date).desc()
            ).all()

            return [
                {
                    'month': record.month,
                    'amount': float(record.amount),
                    'transaction_count': record.transaction_count
                }
                for record in monthly_data
            ]
        except Exception as e:
            self.logger.error(f"Error getting monthly expenses: {e}")
            return []

    def _get_merchant_monthly_details(self, merchant_name: str) -> Dict[str, Dict[str, Any]]:
        """
        获取单个商户的月度明细数据

        Args:
            merchant_name: 商户名称

        Returns:
            按月份分组的详细交易数据
        """
        try:
            # 获取该商户的所有交易记录
            transactions = self.db.query(Transaction).filter(
                Transaction.amount < 0,
                Transaction.counterparty == merchant_name
            ).order_by(Transaction.date.desc()).all()

            if not transactions:
                return {}

            # 按月份分组
            monthly_details = {}
            for transaction in transactions:
                month_key = transaction.date.strftime('%Y-%m')

                if month_key not in monthly_details:
                    monthly_details[month_key] = {
                        'total_amount': 0.0,
                        'transaction_count': 0,
                        'avg_amount': 0.0,
                        'transactions': []
                    }

                # 累加金额和次数
                amount = float(abs(transaction.amount))
                monthly_details[month_key]['total_amount'] += amount
                monthly_details[month_key]['transaction_count'] += 1

                # 添加交易明细
                monthly_details[month_key]['transactions'].append({
                    'date': transaction.date.strftime('%Y-%m-%d'),
                    'amount': amount,
                    'description': transaction.description or ''
                })

            # 计算每月平均金额
            for month_data in monthly_details.values():
                if month_data['transaction_count'] > 0:
                    month_data['avg_amount'] = month_data['total_amount'] / month_data['transaction_count']

            return monthly_details

        except Exception as e:
            self.logger.error(f"Error getting merchant monthly details for {merchant_name}: {e}")
            return {}
