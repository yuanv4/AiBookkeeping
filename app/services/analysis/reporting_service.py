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
from sqlalchemy import func, case
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

# 导入核心分析服务和工具函数
from .analysis_service import AnalysisService
from .utils import validate_date_range
from .models import (
    Period, CoreMetrics, CompositionItem, 
    TrendPoint, DashboardData, TopExpenseCategory,
    HeatmapPoint, MerchantRanking
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
    
    def get_financial_dashboard_data(self, start_date: date, end_date: date) -> DashboardData:
        """获取现金流健康仪表盘数据
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            DashboardData: 仪表盘所需的全部数据
        """
        try:
            # 验证日期范围
            validate_date_range(start_date, end_date)
            
            # 计算时间跨度，决定数据聚合粒度（三级策略）
            period_days = (end_date - start_date).days
            if period_days <= 7:
                granularity = 'day'
            elif period_days <= 90:
                granularity = 'week'
            else:
                granularity = 'month'
            
            # 计算上一个同等时长的周期，用于对比
            prev_end_date = start_date - relativedelta(days=1)
            prev_start_date = prev_end_date - relativedelta(days=period_days)
            
            # 1. 计算核心指标（当前周期和上一周期）
            current_metrics = self._calculate_core_metrics_direct(start_date, end_date)
            previous_metrics = self._calculate_core_metrics_direct(prev_start_date, prev_end_date)
            
            # 获取当前总现金
            current_total_assets = self.analysis_service.get_current_total_assets()
            
            # 2. 计算变化百分比
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
            
            # 3. 净现金趋势数据（根据粒度调整）
            net_worth_trend = self._calculate_net_worth_trend_direct(start_date, end_date, granularity)
            
            # 4. 资金流分析数据（根据粒度调整）
            cash_flow_data = self._calculate_cash_flow_direct(start_date, end_date, granularity)
            
            # 5. 收入构成分析
            income_composition = self._calculate_composition_direct(start_date, end_date, 'income')
            
            # 6. 支出构成分析
            expense_composition = self._calculate_composition_direct(start_date, end_date, 'expense')
            
            # 7. 计算应急储备月数
            emergency_reserve_months = self.analysis_service.calculate_emergency_reserve_months()
            
            # 8. 计算支出分类排行（Top 5）
            top_expense_categories = self._calculate_top_expense_categories(start_date, end_date, 5)
            
            # 9. 获取消费时段热力图数据
            heatmap_data = self.analysis_service.get_consumption_heatmap_data(start_date, end_date)
            consumption_heatmap = [HeatmapPoint(
                weekday=point['weekday'],
                hour=point['hour'],
                amount=point['amount']
            ) for point in heatmap_data]
            
            # 10. 获取主要支出商家排行数据
            merchants_data = self.analysis_service.get_top_merchants_data(start_date, end_date, 10)
            top_merchants = [MerchantRanking(
                merchant_name=merchant['merchant_name'],
                amount=merchant['amount'],
                transaction_count=merchant['transaction_count']
            ) for merchant in merchants_data]
            
            # 构建并返回数据类实例
            return DashboardData(
                period=Period(
                    start_date=start_date.isoformat(),
                    end_date=end_date.isoformat(),
                    days=period_days
                ),
                net_worth_trend=net_worth_trend,
                core_metrics=CoreMetrics(
                    current_total_assets=current_total_assets,
                    total_income=current_metrics['total_income'],
                    total_expense=current_metrics['total_expense'],
                    net_income=current_metrics['net_income'],
                    income_change_percentage=income_change,
                    expense_change_percentage=expense_change,
                    net_change_percentage=net_change,
                    emergency_reserve_months=emergency_reserve_months
                ),
                cash_flow=cash_flow_data,
                income_composition=income_composition,
                expense_composition=expense_composition,
                top_expense_categories=top_expense_categories,
                consumption_heatmap=consumption_heatmap,
                top_merchants=top_merchants
            )
            
        except ValueError as e:
            self.logger.error(f"数据验证失败: {e}")
            raise
        except Exception as e:
            self.logger.error(f"获取仪表盘数据失败: {e}")
            # 返回默认的空数据结构
            return DashboardData(
                period=Period(
                    start_date=start_date.isoformat(),
                    end_date=end_date.isoformat(),
                    days=0
                ),
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
                top_expense_categories=[],
                consumption_heatmap=[],
                top_merchants=[]
            )
    
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
    
    def _calculate_core_metrics_direct(self, start_date: date, end_date: date) -> Dict[str, float]:
        """直接通过数据库查询计算核心指标
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            Dict[str, float]: 核心指标
        """
        try:
            # 使用单个查询计算收入、支出和净收入
            result = self.db.query(
                func.sum(case((Transaction.amount > 0, Transaction.amount), else_=0)).label('total_income'),
                func.sum(case((Transaction.amount < 0, func.abs(Transaction.amount)), else_=0)).label('total_expense')
            ).filter(
                Transaction.date >= start_date,
                Transaction.date <= end_date
            ).first()
            
            total_income = float(result.total_income or 0)
            total_expense = float(result.total_expense or 0)
            net_income = total_income - total_expense
            
            return {
                'total_income': total_income,
                'total_expense': total_expense,
                'net_income': net_income
            }
            
        except Exception as e:
            self.logger.error(f"计算核心指标失败: {e}")
            return {
                'total_income': 0.0,
                'total_expense': 0.0,
                'net_income': 0.0
            }
    
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
                    name=r.name,
                    amount=amount,
                    percentage=round(percentage, 1),
                    count=r.count
                ))

            return top_categories
            
        except Exception as e:
            self.logger.error(f"计算支出分类排行失败: {e}")
            return []