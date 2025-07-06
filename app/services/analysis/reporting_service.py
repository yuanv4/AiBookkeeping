"""报告服务

专门负责现金流数据的聚合和报告生成，为前端页面提供格式化的数据。
优化后移除了pandas依赖，使用原生Python进行数据处理。
"""

from typing import List, Dict, Any, Optional
from decimal import Decimal
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
import logging

from app.models import Transaction, db
from sqlalchemy import func, case, or_
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

# 导入核心分析服务和工具函数
from .analysis_service import AnalysisService
from .expense_analyzer import CalculationHelpers
from .validators import validate_date_range, get_month_date_range, get_expense_transactions
from .dto import (
    Period, CoreMetrics, CompositionItem, 
    TrendPoint, DashboardData,
    RecurringExpense, ExpenseTrend, ExpenseAnalysisData
)

logger = logging.getLogger(__name__)

class ReportingService:
    """报告服务
    
    负责聚合和格式化现金流数据，为前端页面提供完整的报告数据。
    依赖 AnalysisService 进行底层计算。
    """
    
    def __init__(self, db_session: Optional[Session] = None):
        """初始化报告服务
        
        Args:
            db_session: 数据库会话，如果为None则使用默认会话
        """
        self.db = db_session or db.session
        self.logger = logging.getLogger(__name__)
        self.analysis_service = AnalysisService(db_session)
    
    # ==================== 仪表盘数据聚合 ====================
    
    def get_initial_dashboard_data(self) -> DashboardData:
        """获取现金流健康仪表盘的初始静态数据
            
        Returns:
            DashboardData: 仪表盘所需的静态和全时段数据
        """
        try:
            # 1. 核心全时段指标
            current_total_assets = self.analysis_service.get_current_total_assets()
            emergency_reserve_months = self.analysis_service.calculate_emergency_reserve_months()
            all_time_net_income = self.analysis_service.get_all_time_net_income()

            # 2. 净现金趋势数据 (固定过去12个月)
            end_date = date.today()
            start_date = end_date - relativedelta(months=12)
            # 确保即使在少于12个月数据的情况下也能正常显示
            first_transaction_date = self.db.query(func.min(Transaction.date)).scalar()
            if first_transaction_date and start_date < first_transaction_date:
                start_date = first_transaction_date

            net_worth_trend = CalculationHelpers.calculate_net_worth_trend(self.db, start_date, end_date, 'month')

            # 3. 获取最新交易月份
            latest_transaction_month = self.get_latest_transaction_month()
            
            # 构建并返回数据类实例
            return DashboardData(
                period=Period(
                    start_date=start_date.isoformat(),
                    end_date=end_date.isoformat(),
                    days=(end_date - start_date).days
                ),
                net_worth_trend=net_worth_trend,
                core_metrics=CoreMetrics(
                    current_total_assets=current_total_assets,
                    total_income=0, # 不再在此处计算
                    total_expense=0, # 不再在此处计算
                    net_income=all_time_net_income, # 使用全时段净收入
                    income_change_percentage=0,
                    expense_change_percentage=0,
                    net_change_percentage=0,
                    emergency_reserve_months=emergency_reserve_months
                ),
                cash_flow=[],
                income_composition=[],
                expense_composition=[],
                latest_transaction_month=latest_transaction_month.strftime('%Y-%m') if latest_transaction_month else None
            )
            
        except ValueError as e:
            self.logger.error(f"数据验证失败: {e}")
            raise
        except Exception as e:
            self.logger.error(f"获取仪表盘初始数据失败: {e}")
            # 返回默认的空数据结构
            return DashboardData(
                period=Period(start_date='', end_date='', days=0),
                net_worth_trend=[],
                core_metrics=CoreMetrics(
                    current_total_assets=0.0,
                    total_income=0.0,
                    total_expense=0.0,
                    net_income=0.0,
                    income_change_percentage=0.0,
                    expense_change_percentage=0.0,
                    net_change_percentage=0.0,
                    emergency_reserve_months=0
                ),
                cash_flow=[],
                income_composition=[],
                expense_composition=[],
                latest_transaction_month=None
            )

    def get_cash_flow_data(self, start_date: date, end_date: date) -> Dict[str, Any]:
        """获取资金流分析和收入构成数据
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            Dict[str, Any]: 包含资金流和收入构成数据的字典
        """
        try:
            validate_date_range(start_date, end_date)
            
            period_days = (end_date - start_date).days
            if period_days <= 7:
                granularity = 'day'
            elif period_days <= 90:
                granularity = 'week'
            else:
                granularity = 'month'
            
            cash_flow_data = self._calculate_cash_flow_direct(start_date, end_date, granularity)
            income_composition = self._calculate_composition_direct(start_date, end_date, 'income')
            
            return {
                'cash_flow': cash_flow_data,
                'income_composition': income_composition
            }
        except Exception as e:
            self.logger.error(f"获取资金流数据失败: {e}")
            raise

    def get_expense_analysis_data(self, start_date: date, end_date: date) -> Dict[str, Any]:
        """获取支出分析数据
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            Dict[str, Any]: 包含支出分析数据的字典
        """
        try:
            validate_date_range(start_date, end_date)
            
            return {
                'top_expense_categories': []
            }
        except Exception as e:
            self.logger.error(f"获取支出分析数据失败: {e}")
            raise

    # ==================== 核心报告方法 ====================
    
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
    
    # ==================== 私有辅助方法 ====================
    
    def get_latest_transaction_month(self) -> Optional[date]:
        """获取数据库中最新交易数据的月份
        
        Returns:
            Optional[date]: 最新交易月份，如果没有数据则返回None
        """
        try:
            latest_transaction_date = self.db.query(func.max(Transaction.date)).scalar()
            if latest_transaction_date:
                # 返回该月份的第一天
                return latest_transaction_date.replace(day=1)
            return None
        except Exception as e:
            self.logger.error(f"获取最新交易月份失败: {e}")
            return None
    
    def _calculate_composition_direct(self, start_date: date, end_date: date, transaction_type: str) -> List[CompositionItem]:
        """直接通过数据库查询计算收入或支出构成
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            transaction_type: 'income' 或 'expense'
            
        Returns:
            List[CompositionItem]: 构成数据
        """
        try:
            # 根据类型设置过滤条件
            if transaction_type == 'income':
                amount_filter = Transaction.amount > 0
                amount_field = Transaction.amount
            else:  # expense
                amount_filter = Transaction.amount < 0
                amount_field = func.abs(Transaction.amount)
            
            # 按描述分组聚合
            results = self.db.query(
                func.coalesce(Transaction.description, '未分类').label('name'),
                func.sum(amount_field).label('amount'),
                func.count(Transaction.id).label('count')
            ).filter(
                Transaction.date >= start_date,
                Transaction.date <= end_date,
                amount_filter
            ).group_by(
                func.coalesce(Transaction.description, '未分类')
            ).order_by(
                func.sum(amount_field).desc()
            ).all()
            
            if not results:
                return []
            
            # 计算总金额用于百分比计算
            total_amount = sum(float(r.amount) for r in results)
            
            # 构建CompositionItem列表
            composition_items = []
            for r in results:
                amount = float(r.amount)
                percentage = (amount / total_amount * 100) if total_amount > 0 else 0
                
                composition_items.append(CompositionItem(
                    name=r.name,
                    amount=amount,
                    percentage=round(percentage, 1),
                    count=r.count
                ))
            
            return composition_items
            
        except Exception as e:
            self.logger.error(f"计算{transaction_type}构成失败: {e}")
            return []
    
    def _calculate_cash_flow_direct(self, start_date: date, end_date: date, granularity: str = 'day') -> List[TrendPoint]:
        """直接通过数据库查询计算资金流净值
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            granularity: 聚合粒度，'day' 或 'month'
            
        Returns:
            List[TrendPoint]: 资金流数据
        """
        try:
            if granularity == 'month':
                # 按月分组计算月度净流入
                results = self.db.query(
                    func.strftime('%Y-%m', Transaction.date).label('period'),
                    func.sum(Transaction.amount).label('net_flow')
                ).filter(
                    Transaction.date >= start_date,
                    Transaction.date <= end_date
                ).group_by(
                    func.strftime('%Y-%m', Transaction.date)
                ).order_by(
                    func.strftime('%Y-%m', Transaction.date)
                ).all()
            elif granularity == 'week':
                # 按周分组计算周度净流入
                results = self.db.query(
                    func.strftime('%Y-W%W', Transaction.date).label('period'),
                    func.sum(Transaction.amount).label('net_flow')
                ).filter(
                    Transaction.date >= start_date,
                    Transaction.date <= end_date
                ).group_by(
                    func.strftime('%Y-W%W', Transaction.date)
                ).order_by(
                    func.strftime('%Y-W%W', Transaction.date)
                ).all()
            else:
                # 按日期分组计算每日净流入
                results = self.db.query(
                    Transaction.date,
                    func.sum(Transaction.amount).label('net_flow')
                ).filter(
                    Transaction.date >= start_date,
                    Transaction.date <= end_date
                ).group_by(
                    Transaction.date
                ).order_by(
                    Transaction.date
                ).all()
            
            # 构建TrendPoint列表
            cash_flow_data = []
            for r in results:
                if granularity == 'month':
                    cash_flow_data.append(TrendPoint(
                        date=r.period,
                        value=float(r.net_flow)
                    ))
                elif granularity == 'week':
                    cash_flow_data.append(TrendPoint(
                        date=r.period,
                        value=float(r.net_flow)
                    ))
                else:
                    cash_flow_data.append(TrendPoint(
                        date=r.date.isoformat(),
                        value=float(r.net_flow)
                    ))
            
            return cash_flow_data
            
        except Exception as e:
            self.logger.error(f"计算资金流失败: {e}")
            return []
    






    def _calculate_expense_trend_12months(self, target_month: date) -> List[ExpenseTrend]:
        """计算近12个月支出趋势
        
        从指定目标月份向前推算12个月，计算每月的总支出金额。
        
        Args:
            target_month: 目标月份（通常是当前月份）
            
        Returns:
            List[ExpenseTrend]: 近12个月的支出趋势数据
        """
        try:
            # 计算12个月的时间范围
            end_month = target_month.replace(day=1)  # 目标月份的第一天
            start_month = end_month - relativedelta(months=11)  # 往前推11个月，总共12个月
            
            # 查询近12个月的支出数据，按月分组
            monthly_expenses = self.db.query(
                func.strftime('%Y-%m', Transaction.date).label('month'),
                func.sum(func.abs(Transaction.amount)).label('total_expense')
            ).filter(
                Transaction.amount < 0,  # 只计算支出
                Transaction.date >= start_month,
                Transaction.date < end_month + relativedelta(months=1)  # 包含目标月份
            ).group_by(
                func.strftime('%Y-%m', Transaction.date)
            ).order_by(
                func.strftime('%Y-%m', Transaction.date)
            ).all()
            
            # 构建完整的12个月数据（包括没有交易的月份）
            expense_trends = []
            current_month = start_month
            
            # 将查询结果转换为字典便于查找
            expense_dict = {r.month: float(r.total_expense) for r in monthly_expenses}
            
            for i in range(12):
                month_str = current_month.strftime('%Y-%m')
                expense_amount = expense_dict.get(month_str, 0.0)
                
                expense_trends.append(ExpenseTrend(
                    date=month_str,
                    value=round(expense_amount, 2),
                    category="total"
                ))
                
                current_month += relativedelta(months=1)
            
            return expense_trends
            
        except Exception as e:
            self.logger.error(f"计算支出趋势失败: {e}")
            return []



    def _get_recurring_expense_transactions(self, target_month: date, recurring_expenses: List[RecurringExpense]) -> List[Dict[str, Any]]:
        """获取周期性支出的具体交易明细（按组合键分组）
        
        Args:
            target_month: 目标月份
            recurring_expenses: 识别出的周期性支出列表
            
        Returns:
            List[Dict[str, Any]]: 按组合键分组的周期性支出交易明细
        """
        try:
            # 计算目标月份的时间范围
            month_start, month_end = get_month_date_range(target_month)
            
            # 构建周期性支出的组合键集合
            recurring_combination_keys = {recurring.combination_key for recurring in recurring_expenses}
            
            # 查询目标月份内符合周期性组合键的交易（基于counterparty匹配）
            transactions = self.db.query(Transaction).filter(
                Transaction.amount < 0,
                Transaction.date >= month_start,
                Transaction.date <= month_end,
                func.coalesce(Transaction.counterparty, '未知商家').in_(recurring_combination_keys)
            ).order_by(Transaction.date.desc()).all()
            
            # 按组合键分组交易明细
            grouped_transactions = {}
            for tx in transactions:
                combination_key = tx.counterparty or '未知商家'
                if combination_key not in grouped_transactions:
                    grouped_transactions[combination_key] = []
                
                grouped_transactions[combination_key].append({
                    'id': tx.id,
                    'date': tx.date.isoformat(),
                    'account_name': tx.account.account_name if tx.account else '',
                    'amount': float(tx.amount),
                    'counterparty': tx.counterparty or '',
                    'description': tx.description or ''
                })
            
            # 转换为前端需要的格式
            result = []
            for combination_key, tx_list in grouped_transactions.items():
                result.append({
                    'combination_key': combination_key,
                    'transactions': tx_list[:10]  # 限制每组最多10条交易明细
                })
            
            return result
            
        except Exception as e:
            self.logger.error(f"获取周期性支出交易明细失败: {e}")
            return []

    def _get_flexible_expense_transactions(self, target_month: date, recurring_expenses: List[RecurringExpense]) -> List[Dict[str, Any]]:
        """获取弹性支出的具体交易明细
        
        使用简单补集策略：弹性支出 = 所有支出 - 固定支出
        
        Args:
            target_month: 目标月份
            recurring_expenses: 识别出的周期性支出列表
            
        Returns:
            List[Dict[str, Any]]: 弹性支出的交易明细
        """
        try:
            # 计算目标月份的时间范围
            month_start, month_end = get_month_date_range(target_month)
            
            # 构建周期性支出的组合键集合
            recurring_combination_keys = {recurring.combination_key for recurring in recurring_expenses}
            
            # 查询非固定支出交易，按金额绝对值排序取前10
            # 简单补集逻辑：所有支出 - 固定支出 = 弹性支出
            transactions = self.db.query(Transaction).filter(
                Transaction.amount < 0,
                Transaction.date >= month_start,
                Transaction.date <= month_end,
                ~func.coalesce(Transaction.counterparty, '未知商家').in_(recurring_combination_keys)
            ).order_by(func.abs(Transaction.amount).desc()).limit(10).all()
            
            return [{
                'id': tx.id,
                'date': tx.date.isoformat(),
                'account_name': tx.account.account_name if tx.account else '',
                'amount': float(tx.amount),
                'counterparty': tx.counterparty or '',
                'description': tx.description or ''
            } for tx in transactions]
            
        except Exception as e:
            self.logger.error(f"获取弹性支出交易明细失败: {e}")
            return []

    def get_enhanced_expense_analysis_data(self, target_month: date) -> ExpenseAnalysisData:
        """获取增强的支出分析数据
        
        整合所有支出分析功能，为支出结构透视模块提供完整的分析数据。
        
        Args:
            target_month: 目标月份
            
        Returns:
            ExpenseAnalysisData: 综合支出分析数据
        """
        try:
            # 1. 计算目标月份的时间范围
            month_start, month_end = get_month_date_range(target_month)
            
            # 2. 计算目标月份的总支出
            total_expense_result = self.db.query(
                func.sum(func.abs(Transaction.amount))
            ).filter(
                Transaction.amount < 0,
                Transaction.date >= month_start,
                Transaction.date <= month_end
            ).scalar()
            
            total_expense = float(total_expense_result or 0)
            
            # 3. 计算近12个月支出趋势
            expense_trend = self._calculate_expense_trend_12months(target_month)
            
            # 4. 识别周期性支出（基于全量历史数据）
            # 根据配置选择算法方法
            from flask import current_app
            method = getattr(current_app.config, 'RECURRING_EXPENSE_METHOD', 'adaptive')
            
            if method == 'adaptive':
                recurring_expenses = CalculationHelpers.identify_recurring_expenses_adaptive(self.db)
            else:
                recurring_expenses = CalculationHelpers.identify_recurring_expenses(self.db)
            
            # 5. 计算弹性支出分类占比（传递周期性支出参数）
            flexible_composition = CalculationHelpers.calculate_flexible_expense_composition(self.db, target_month, recurring_expenses)
            
            # 6. 获取交易明细
            recurring_transactions = self._get_recurring_expense_transactions(target_month, recurring_expenses)
            flexible_transactions = self._get_flexible_expense_transactions(target_month, recurring_expenses)
            
            # 6.1. 过滤出当月实际发生的周期性支出
            current_month_recurring_keys = {group.get('combination_key') for group in recurring_transactions}
            current_month_recurring_expenses = [
                expense for expense in recurring_expenses 
                if expense.combination_key in current_month_recurring_keys
            ]
            
            # 6.2. 重新计算当月实际总金额
            for expense in current_month_recurring_expenses:
                # 找到对应的交易明细分组
                matching_group = next(
                    (group for group in recurring_transactions 
                     if group.get('combination_key') == expense.combination_key), 
                    None
                )
                
                if matching_group and matching_group.get('transactions'):
                    # 计算当月实际总金额
                    current_month_total = sum(
                        abs(float(tx.get('amount', 0))) 
                        for tx in matching_group['transactions']
                    )
                    # 更新total_amount为当月实际金额
                    expense.total_amount = round(current_month_total, 2)
                else:
                    # 如果没有找到交易明细，设为0
                    expense.total_amount = 0.0
            
            # 6.3. 按当月总金额重新排序
            current_month_recurring_expenses.sort(key=lambda x: x.total_amount, reverse=True)
            

            
            # 8. 构建综合分析数据
            return ExpenseAnalysisData(
                target_month=target_month.strftime('%Y-%m'),
                total_expense=round(total_expense, 2),
                expense_trend=expense_trend,
                recurring_expenses=current_month_recurring_expenses,
                flexible_composition=flexible_composition,
                recurring_transactions=recurring_transactions,
                flexible_transactions=flexible_transactions
            )
            
        except Exception as e:
            self.logger.error(f"获取增强支出分析数据失败: {e}")
            # 返回空数据结构
            return ExpenseAnalysisData(
                target_month=target_month.strftime('%Y-%m'),
                total_expense=0.0,
                expense_trend=[],
                recurring_expenses=[],
                flexible_composition=[],
                recurring_transactions=[],
                flexible_transactions=[]
            )