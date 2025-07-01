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
from .utils import validate_date_range
from .models import (
    Period, CoreMetrics, CompositionItem, 
    TrendPoint, DashboardData, TopExpenseCategory,
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

            net_worth_trend = self._calculate_net_worth_trend_direct(start_date, end_date, 'month')

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
                top_expense_categories=[]
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
                top_expense_categories=[]
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
            
            top_expense_categories = self._calculate_top_expense_categories(start_date, end_date, 10)
            
            return {
                'top_expense_categories': top_expense_categories
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
    
    def _calculate_net_worth_trend_direct(self, start_date: date, end_date: date, granularity: str = 'day') -> List[TrendPoint]:
        """直接通过数据库查询计算净现金趋势

        最终修正版: 采用基于`balance_after`的每日现金历史构建模型，
        确保在所有时间范围和粒度下数据的一致性和准确性。
        """
        try:
            # 1. 一次性获取所需时间范围内所有账户的交易历史
            # 为了构建准确历史，需要从第一笔交易开始
            all_transactions = self.db.query(
                Transaction.account_id,
                Transaction.date,
                Transaction.balance_after
            ).order_by(Transaction.date, Transaction.created_at).all()

            if not all_transactions:
                return []

            # 2. 在内存中构建完整的每日现金历史
            # 这是为了避免在循环中执行N+1次数据库查询
            first_tx_date = all_transactions[0].date
            
            txs_by_date = {}
            for tx in all_transactions:
                txs_by_date.setdefault(tx.date, []).append(tx)

            daily_assets_history = {}
            latest_balances = {}
            total_assets = Decimal('0.0')

            current_date = first_tx_date
            while current_date <= end_date:
                if current_date in txs_by_date:
                    for tx in txs_by_date[current_date]:
                        old_balance = latest_balances.get(tx.account_id, Decimal('0.0'))
                        total_assets -= old_balance
                        total_assets += tx.balance_after
                        latest_balances[tx.account_id] = tx.balance_after
                
                if current_date >= start_date:
                    daily_assets_history[current_date] = total_assets
                
                current_date += timedelta(days=1)
            
            # 3. 根据粒度对每日现金历史进行采样
            trend_data = []
            
            # 重新从start_date开始循环以进行采样
            current_date = start_date
            while current_date <= end_date:
                current_assets = daily_assets_history.get(current_date, Decimal('0.0'))
                is_last_day = (current_date == end_date)
                
                if granularity == 'day':
                    trend_data.append(TrendPoint(date=current_date.isoformat(), value=round(current_assets, 2)))
                
                elif granularity == 'week':
                    is_end_of_week = (current_date.weekday() == 6)
                    if is_end_of_week or is_last_day:
                        week_str = current_date.strftime('%Y-W%W')
                        if not trend_data or trend_data[-1].date != week_str:
                             trend_data.append(TrendPoint(date=week_str, value=round(current_assets, 2)))

                elif granularity == 'month':
                    next_day = current_date + timedelta(days=1)
                    is_end_of_month = (next_day.month != current_date.month)
                    if is_end_of_month or is_last_day:
                        month_str = current_date.strftime('%Y-%m')
                        if not trend_data or trend_data[-1].date != month_str:
                            trend_data.append(TrendPoint(date=month_str, value=round(current_assets, 2)))

                current_date += timedelta(days=1)

            # 4. 如果采样后仍然没有数据（例如，时间范围内没有交易）
            if not trend_data and start_date <= end_date:
                # 获取该区间的初始值
                initial_assets = self.analysis_service.get_total_assets_at_date(start_date - timedelta(days=1))
                if granularity == 'month':
                    date_format = start_date.strftime('%Y-%m')
                elif granularity == 'week':
                    date_format = start_date.strftime('%Y-W%W')
                else:
                    date_format = start_date.isoformat()
                return [TrendPoint(date=date_format, value=round(initial_assets, 2))]

            return trend_data
            
        except Exception as e:
            self.logger.error(f"计算净现金趋势失败: {e}", exc_info=True)
            return []

    def _calculate_top_expense_categories(self, start_date: date, end_date: date, top_n: int) -> List[TopExpenseCategory]:
        """计算支出分类排行（Top N）
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            top_n: 要返回的前N个分类
            
        Returns:
            List[TopExpenseCategory]: 支出分类排行
        """
        try:
            # 按描述分组聚合支出数据
            results = self.db.query(
                func.coalesce(Transaction.description, '未分类').label('name'),
                func.sum(func.abs(Transaction.amount)).label('amount'),
                func.count(Transaction.id).label('count')
            ).filter(
                Transaction.amount < 0,
                Transaction.date >= start_date,
                Transaction.date <= end_date
            ).group_by(
                func.coalesce(Transaction.description, '未分类')
            ).order_by(
                func.sum(func.abs(Transaction.amount)).desc()
            ).limit(top_n).all()

            if not results:
                return []

            # 计算总支出用于百分比计算
            total_expense = sum(float(r.amount) for r in results)

            # 构建TopExpenseCategory列表
            top_categories = []
            for r in results:
                amount = float(r.amount)
                percentage = (amount / total_expense * 100) if total_expense > 0 else 0
                
                top_categories.append(TopExpenseCategory(
                    category=r.name,
                    total_amount=amount,
                    percentage=round(percentage, 1),
                    count=r.count
                ))

            return top_categories
            
        except Exception as e:
            self.logger.error(f"计算支出分类排行失败: {e}")
            return []

    def _identify_recurring_expenses(self) -> List[RecurringExpense]:
        """识别周期性支出
        
        使用智能模糊匹配算法，基于商家名称相似度、金额波动范围和时间间隔规律性
        来识别固定周期性支出。基于数据库中所有历史交易数据进行分析。
        
        Returns:
            List[RecurringExpense]: 识别出的周期性支出列表
        """
        try:
            # 1. 获取数据库中所有支出交易（全量数据分析）
            expense_transactions = self.db.query(
                Transaction.counterparty,
                Transaction.description,
                Transaction.amount,
                Transaction.date
            ).filter(
                Transaction.amount < 0  # 只查询支出交易
            ).order_by(Transaction.date).all()

            if not expense_transactions:
                return []

            # 2. 按商家+描述组合进行分组
            expense_groups = {}
            for tx in expense_transactions:
                # 创建组合键：商家名称 + 交易描述
                key = f"{tx.counterparty or ''}|{tx.description or ''}"
                if key not in expense_groups:
                    expense_groups[key] = []
                expense_groups[key].append({
                    'amount': abs(float(tx.amount)),
                    'date': tx.date,
                    'counterparty': tx.counterparty or '未知商家',
                    'description': tx.description or '未分类'
                })

            # 3. 分析每个组合的周期性特征
            recurring_expenses = []
            for key, transactions in expense_groups.items():
                if len(transactions) < 3:  # 至少需要3次交易才能判断周期性
                    continue
                
                # 计算时间间隔
                dates = [tx['date'] for tx in transactions]
                dates.sort()
                intervals = []
                for i in range(1, len(dates)):
                    interval = (dates[i] - dates[i-1]).days
                    intervals.append(interval)
                
                if not intervals:
                    continue
                
                # 计算金额统计
                amounts = [tx['amount'] for tx in transactions]
                avg_amount = sum(amounts) / len(amounts)
                amount_variance = sum((amt - avg_amount) ** 2 for amt in amounts) / len(amounts)
                amount_cv = (amount_variance ** 0.5) / avg_amount if avg_amount > 0 else 1  # 变异系数
                
                # 计算时间间隔统计
                avg_interval = sum(intervals) / len(intervals)
                interval_variance = sum((intv - avg_interval) ** 2 for intv in intervals) / len(intervals)
                interval_cv = (interval_variance ** 0.5) / avg_interval if avg_interval > 0 else 1
                
                # 4. 周期性判断逻辑
                confidence_score = 0
                frequency = 'unknown'
                
                # 金额稳定性评分 (0-40分)
                if amount_cv < 0.1:  # 变异系数小于10%
                    confidence_score += 40
                elif amount_cv < 0.2:  # 变异系数小于20%
                    confidence_score += 25
                elif amount_cv < 0.3:  # 变异系数小于30%
                    confidence_score += 10
                
                # 时间间隔规律性评分 (0-60分)
                if 28 <= avg_interval <= 32:  # 月度周期 (28-32天)
                    frequency = 'monthly'
                    if interval_cv < 0.15:  # 间隔很规律
                        confidence_score += 60
                    elif interval_cv < 0.25:
                        confidence_score += 40
                    else:
                        confidence_score += 20
                elif 6 <= avg_interval <= 8:  # 周度周期 (6-8天)
                    frequency = 'weekly'
                    if interval_cv < 0.2:
                        confidence_score += 50
                    elif interval_cv < 0.3:
                        confidence_score += 30
                    else:
                        confidence_score += 15
                elif 85 <= avg_interval <= 95:  # 季度周期 (85-95天)
                    frequency = 'quarterly'
                    if interval_cv < 0.2:
                        confidence_score += 45
                    elif interval_cv < 0.3:
                        confidence_score += 25
                    else:
                        confidence_score += 10
                
                # 只保留置信度大于60分的周期性支出
                if confidence_score >= 60:
                    category = transactions[0]['description'] or transactions[0]['counterparty']
                    recurring_expenses.append(RecurringExpense(
                        category=category,
                        amount=round(avg_amount, 2),
                        frequency=frequency,
                        confidence_score=round(confidence_score, 1),
                        last_occurrence=dates[-1].isoformat(),
                        count=len(transactions)
                    ))
            
            # 5. 按金额排序并返回前10个
            recurring_expenses.sort(key=lambda x: x.amount, reverse=True)
            return recurring_expenses[:10]
            
        except Exception as e:
            self.logger.error(f"识别周期性支出失败: {e}")
            return []

    def _calculate_expense_trend_6months(self, target_month: date) -> List[ExpenseTrend]:
        """计算近6个月支出趋势
        
        从指定目标月份向前推算6个月，计算每月的总支出金额。
        
        Args:
            target_month: 目标月份（通常是当前月份）
            
        Returns:
            List[ExpenseTrend]: 近6个月的支出趋势数据
        """
        try:
            # 计算6个月的时间范围
            end_month = target_month.replace(day=1)  # 目标月份的第一天
            start_month = end_month - relativedelta(months=5)  # 往前推5个月，总共6个月
            
            # 查询近6个月的支出数据，按月分组
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
            
            # 构建完整的6个月数据（包括没有交易的月份）
            expense_trends = []
            current_month = start_month
            
            # 将查询结果转换为字典便于查找
            expense_dict = {r.month: float(r.total_expense) for r in monthly_expenses}
            
            for i in range(6):
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

    def _calculate_flexible_expense_composition(self, target_month: date) -> List[CompositionItem]:
        """计算弹性支出分类占比
        
        从指定目标月份的支出中排除周期性支出，计算剩余支出的分类占比。
        
        Args:
            target_month: 目标月份
            
        Returns:
            List[CompositionItem]: 弹性支出分类占比数据
        """
        try:
            # 1. 计算目标月份的时间范围
            month_start = target_month.replace(day=1)
            if target_month.month == 12:
                month_end = target_month.replace(year=target_month.year + 1, month=1, day=1) - timedelta(days=1)
            else:
                month_end = target_month.replace(month=target_month.month + 1, day=1) - timedelta(days=1)
            
            # 2. 识别周期性支出模式（基于全量历史数据）
            recurring_expenses = self._identify_recurring_expenses()
            
            # 4. 构建周期性支出的过滤条件
            # 收集所有被识别为周期性的商家和描述组合
            recurring_patterns = set()
            for recurring in recurring_expenses:
                # 由于周期性识别是基于商家+描述组合，我们需要重建这个组合
                # 但是RecurringExpense只有category字段，这里做简化处理
                # 将category作为描述或商家名称来匹配
                recurring_patterns.add(recurring.category)
            
            # 5. 查询目标月份的所有支出
            month_expenses = self.db.query(
                func.coalesce(Transaction.description, '未分类').label('name'),
                Transaction.counterparty,
                func.sum(func.abs(Transaction.amount)).label('amount'),
                func.count(Transaction.id).label('count')
            ).filter(
                Transaction.amount < 0,
                Transaction.date >= month_start,
                Transaction.date <= month_end
            ).group_by(
                func.coalesce(Transaction.description, '未分类'),
                Transaction.counterparty
            ).all()
            
            if not month_expenses:
                return []
            
            # 6. 排除周期性支出，聚合弹性支出
            flexible_groups = {}
            for expense in month_expenses:
                category = expense.name
                counterparty = expense.counterparty or ''
                
                # 检查是否为周期性支出
                is_recurring = False
                for pattern in recurring_patterns:
                    if (pattern == category or 
                        pattern == counterparty or 
                        pattern in f"{counterparty}|{category}"):
                        is_recurring = True
                        break
                
                # 如果不是周期性支出，加入弹性支出统计
                if not is_recurring:
                    if category not in flexible_groups:
                        flexible_groups[category] = {
                            'amount': 0.0,
                            'count': 0
                        }
                    flexible_groups[category]['amount'] += float(expense.amount)
                    flexible_groups[category]['count'] += expense.count
            
            if not flexible_groups:
                return []
            
            # 7. 计算总金额和百分比
            total_flexible = sum(group['amount'] for group in flexible_groups.values())
            
            composition_items = []
            for category, data in flexible_groups.items():
                percentage = (data['amount'] / total_flexible * 100) if total_flexible > 0 else 0
                
                composition_items.append(CompositionItem(
                    name=category,
                    amount=round(data['amount'], 2),
                    percentage=round(percentage, 1),
                    count=data['count']
                ))
            
            # 8. 按金额排序并返回前10个
            composition_items.sort(key=lambda x: x.amount, reverse=True)
            return composition_items[:10]
            
        except Exception as e:
            self.logger.error(f"计算弹性支出分类占比失败: {e}")
            return []

    def _get_recurring_expense_transactions(self, target_month: date, recurring_expenses: List[RecurringExpense]) -> List[Dict[str, Any]]:
        """获取周期性支出的具体交易明细
        
        Args:
            target_month: 目标月份
            recurring_expenses: 识别出的周期性支出列表
            
        Returns:
            List[Dict[str, Any]]: 周期性支出的交易明细
        """
        try:
            # 计算目标月份的时间范围
            month_start = target_month.replace(day=1)
            if target_month.month == 12:
                month_end = target_month.replace(year=target_month.year + 1, month=1, day=1) - timedelta(days=1)
            else:
                month_end = target_month.replace(month=target_month.month + 1, day=1) - timedelta(days=1)
            
            # 构建周期性支出的分类集合
            recurring_categories = {recurring.category for recurring in recurring_expenses}
            
            # 查询目标月份内符合周期性分类的交易
            transactions = self.db.query(Transaction).filter(
                Transaction.amount < 0,
                Transaction.date >= month_start,
                Transaction.date <= month_end,
                or_(
                    Transaction.description.in_(recurring_categories),
                    Transaction.counterparty.in_(recurring_categories)
                )
            ).order_by(Transaction.date.desc()).limit(50).all()
            
            return [{
                'id': tx.id,
                'date': tx.date.isoformat(),
                'account_name': tx.account.account_name if tx.account else '',
                'amount': float(tx.amount),
                'counterparty': tx.counterparty or '',
                'description': tx.description or ''
            } for tx in transactions]
            
        except Exception as e:
            self.logger.error(f"获取周期性支出交易明细失败: {e}")
            return []

    def _get_flexible_expense_transactions(self, target_month: date, flexible_composition: List[CompositionItem]) -> List[Dict[str, Any]]:
        """获取弹性支出的具体交易明细
        
        Args:
            target_month: 目标月份
            flexible_composition: 弹性支出分类数据
            
        Returns:
            List[Dict[str, Any]]: 弹性支出的交易明细
        """
        try:
            # 计算目标月份的时间范围
            month_start = target_month.replace(day=1)
            if target_month.month == 12:
                month_end = target_month.replace(year=target_month.year + 1, month=1, day=1) - timedelta(days=1)
            else:
                month_end = target_month.replace(month=target_month.month + 1, day=1) - timedelta(days=1)
            
            # 构建弹性支出的分类集合
            flexible_categories = {comp.name for comp in flexible_composition}
            
            # 查询目标月份内符合弹性分类的交易
            transactions = self.db.query(Transaction).filter(
                Transaction.amount < 0,
                Transaction.date >= month_start,
                Transaction.date <= month_end,
                or_(
                    func.coalesce(Transaction.description, '未分类').in_(flexible_categories)
                )
            ).order_by(Transaction.date.desc()).limit(50).all()
            
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
            month_start = target_month.replace(day=1)
            if target_month.month == 12:
                month_end = target_month.replace(year=target_month.year + 1, month=1, day=1) - timedelta(days=1)
            else:
                month_end = target_month.replace(month=target_month.month + 1, day=1) - timedelta(days=1)
            
            # 2. 计算目标月份的总支出
            total_expense_result = self.db.query(
                func.sum(func.abs(Transaction.amount))
            ).filter(
                Transaction.amount < 0,
                Transaction.date >= month_start,
                Transaction.date <= month_end
            ).scalar()
            
            total_expense = float(total_expense_result or 0)
            
            # 3. 计算近6个月支出趋势
            expense_trend = self._calculate_expense_trend_6months(target_month)
            
            # 4. 识别周期性支出（基于全量历史数据）
            recurring_expenses = self._identify_recurring_expenses()
            
            # 5. 计算弹性支出分类占比
            flexible_composition = self._calculate_flexible_expense_composition(target_month)
            
            # 6. 获取交易明细
            recurring_transactions = self._get_recurring_expense_transactions(target_month, recurring_expenses)
            flexible_transactions = self._get_flexible_expense_transactions(target_month, flexible_composition)
            
            # 7. 计算支出分类排行（保持向后兼容）
            top_categories = self._calculate_top_expense_categories(month_start, month_end, 10)
            
            # 8. 构建综合分析数据
            return ExpenseAnalysisData(
                target_month=target_month.strftime('%Y-%m'),
                total_expense=round(total_expense, 2),
                expense_trend=expense_trend,
                recurring_expenses=recurring_expenses,
                flexible_composition=flexible_composition,
                top_categories=top_categories,
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
                top_categories=[],
                recurring_transactions=[],
                flexible_transactions=[]
            )