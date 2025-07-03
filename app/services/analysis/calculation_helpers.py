"""计算辅助工具

提取自ReportingService的复杂计算逻辑，专门处理重型数据分析任务。
使用静态方法设计，便于在不同服务中复用计算逻辑。
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

from .models import (
    CompositionItem, TrendPoint, RecurringExpense, ExpenseTrend
)

logger = logging.getLogger(__name__)

class CalculationHelpers:
    """计算辅助工具类
    
    专门处理复杂的数据计算逻辑，从ReportingService中提取最重型的方法。
    使用静态方法设计，保持无状态和高度可复用性。
    """
    
    @staticmethod
    def calculate_net_worth_trend(db: Session, start_date: date, end_date: date, granularity: str = 'day') -> List[TrendPoint]:
        """直接通过数据库查询计算净现金趋势

        最终修正版: 采用基于`balance_after`的每日现金历史构建模型，
        确保在所有时间范围和粒度下数据的一致性和准确性。
        
        Args:
            db: 数据库会话
            start_date: 开始日期
            end_date: 结束日期
            granularity: 聚合粒度，'day', 'week', 或 'month'
            
        Returns:
            List[TrendPoint]: 净现金趋势数据点列表
        """
        try:
            # 1. 一次性获取所需时间范围内所有账户的交易历史
            # 为了构建准确历史，需要从第一笔交易开始
            all_transactions = db.query(
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
            
            # 3. 根据粒度聚合数据
            if granularity == 'month':
                # 按月聚合：取每月最后一天的数据
                monthly_data = {}
                for date_key, assets in daily_assets_history.items():
                    month_key = date_key.strftime('%Y-%m')
                    monthly_data[month_key] = (date_key, assets)
                
                # 取每月最后一天的数据
                final_monthly = {}
                for month_key, (date_val, assets) in monthly_data.items():
                    if month_key not in final_monthly or date_val > final_monthly[month_key][0]:
                        final_monthly[month_key] = (date_val, assets)
                
                trend_data = []
                for month_key in sorted(final_monthly.keys()):
                    _, assets = final_monthly[month_key]
                    trend_data.append(TrendPoint(
                        date=month_key,
                        value=float(assets)
                    ))
                
                return trend_data
                
            elif granularity == 'week':
                # 按周聚合：取每周最后一天的数据
                weekly_data = {}
                for date_key, assets in daily_assets_history.items():
                    # 获取周数（ISO周）
                    year, week, _ = date_key.isocalendar()
                    week_key = f"{year}-W{week:02d}"
                    
                    if week_key not in weekly_data or date_key > weekly_data[week_key][0]:
                        weekly_data[week_key] = (date_key, assets)
                
                trend_data = []
                for week_key in sorted(weekly_data.keys()):
                    _, assets = weekly_data[week_key]
                    trend_data.append(TrendPoint(
                        date=week_key,
                        value=float(assets)
                    ))
                
                return trend_data
                
            else:
                # 日粒度：直接返回每日数据
                trend_data = []
                for date_key in sorted(daily_assets_history.keys()):
                    assets = daily_assets_history[date_key]
                    trend_data.append(TrendPoint(
                        date=date_key.isoformat(),
                        value=float(assets)
                    ))
                
                return trend_data
                
        except Exception as e:
            logger.error(f"计算净现金趋势失败: {e}")
            return []
    
    @staticmethod  
    def identify_recurring_expenses(db: Session) -> List[RecurringExpense]:
        """识别周期性支出
        
        使用智能匹配算法，基于商家名称（counterparty）、金额波动范围和时间间隔规律性
        来识别固定支出。基于数据库中所有历史交易数据进行分析。
        
        算法核心：
        - 以商家名称（counterparty）作为分组键，忽略支付方式（description）的差异
        - 通过时间间隔规律性、金额稳定性等多维度判断周期性特征
        - 精确记录支付周期天数，支持任意频率的周期性支出识别
        
        Args:
            db: 数据库会话
            
        Returns:
            List[RecurringExpense]: 识别出的周期性支出列表
        """
        try:
            # 1. 获取数据库中所有支出交易（全量数据分析）
            expense_transactions = db.query(
                Transaction.counterparty,
                Transaction.description,
                Transaction.amount,
                Transaction.date
            ).filter(
                Transaction.amount < 0  # 只查询支出交易
            ).order_by(Transaction.date).all()

            if not expense_transactions:
                return []

            # 2. 按商家进行分组
            expense_groups = {}
            for tx in expense_transactions:
                # 使用商家名称作为组合键
                key = tx.counterparty or '未知商家'
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
                amount_cv = (amount_variance ** 0.5) / avg_amount if avg_amount > 0 else float('inf')

                # 计算时间间隔统计
                avg_interval = sum(intervals) / len(intervals)
                interval_variance = sum((intv - avg_interval) ** 2 for intv in intervals) / len(intervals)
                interval_cv = (interval_variance ** 0.5) / avg_interval if avg_interval > 0 else float('inf')

                # 4. 周期性判断规则
                confidence_score = 0.0
                frequency = round(avg_interval) if avg_interval > 0 else 0
                
                # 规则1：时间间隔规律性（权重40%）
                if interval_cv < 0.3:  # 时间间隔变异系数 < 30%
                    confidence_score += 40.0

                # 规则2：金额稳定性（权重35%）
                if amount_cv < 0.2:  # 金额变异系数 < 20%
                    confidence_score += 35.0
                elif amount_cv < 0.4:  # 金额变异系数 < 40%
                    confidence_score += 20.0

                # 规则3：交易次数加成（权重15%）
                if len(transactions) >= 6:
                    confidence_score += 15.0
                elif len(transactions) >= 4:
                    confidence_score += 10.0

                # 规则4：近期活跃度加成（权重10%）
                last_transaction_date = max(dates)
                days_since_last = (date.today() - last_transaction_date).days
                if days_since_last <= 60:  # 近两个月有交易
                    confidence_score += 10.0

                # 5. 只保留置信度 >= 60% 的周期性支出
                if confidence_score >= 60.0:
                    # 取描述或商家名称作为分类名
                    category = transactions[0]['description']
                    if not category or category == '未分类':
                        category = transactions[0]['counterparty']
                    
                    # 计算总金额
                    total_amount = sum(amounts)
                    
                    recurring_expenses.append(RecurringExpense(
                        category=category,
                        total_amount=round(total_amount, 2),
                        amount=round(avg_amount, 2),
                        frequency=frequency,
                        confidence_score=round(confidence_score, 1),
                        last_occurrence=last_transaction_date.isoformat(),
                        count=len(transactions),
                        combination_key=key  # 保存商家名称用于精确匹配
                    ))

            # 6. 按总金额排序并返回
            recurring_expenses.sort(key=lambda x: x.total_amount, reverse=True)
            return recurring_expenses
            
        except Exception as e:
            logger.error(f"识别周期性支出失败: {e}")
            return []
    
    @staticmethod
    def calculate_flexible_expense_composition(db: Session, target_month: date) -> List[CompositionItem]:
        """计算弹性支出分类占比
        
        从指定目标月份的支出中排除周期性支出，计算剩余支出的分类占比。
        周期性支出的识别基于商家名称（counterparty）进行匹配。
        
        Args:
            db: 数据库会话
            target_month: 目标分析月份
            
        Returns:
            List[CompositionItem]: 弹性支出分类占比列表
        """
        try:
            # 1. 计算目标月份的时间范围
            month_start = target_month.replace(day=1)
            if target_month.month == 12:
                month_end = target_month.replace(year=target_month.year + 1, month=1, day=1) - timedelta(days=1)
            else:
                month_end = target_month.replace(month=target_month.month + 1, day=1) - timedelta(days=1)
            
            # 2. 识别周期性支出模式（基于全量历史数据）
            recurring_expenses = CalculationHelpers.identify_recurring_expenses(db)
            
            # 3. 获取目标月份的所有支出交易
            month_expenses = db.query(
                func.coalesce(Transaction.description, '未分类').label('category'),
                func.coalesce(Transaction.counterparty, '未知商家').label('counterparty'),
                func.sum(func.abs(Transaction.amount)).label('amount'),
                func.count(Transaction.id).label('count')
            ).filter(
                Transaction.amount < 0,
                Transaction.date >= month_start,
                Transaction.date <= month_end
            ).group_by(
                func.coalesce(Transaction.description, '未分类'),
                func.coalesce(Transaction.counterparty, '未知商家')
            ).all()
            
            if not month_expenses:
                return []
            
            # 4. 构建周期性支出匹配模式
            recurring_patterns = set()
            for recurring in recurring_expenses:
                recurring_patterns.add(recurring.category)
            
            # 5. 按分类聚合支出（排除周期性支出）
            flexible_groups = {}
            for expense in month_expenses:
                category = expense.category
                counterparty = expense.counterparty
                
                # 检查是否为周期性支出（基于counterparty匹配）
                is_recurring = counterparty in recurring_patterns
                
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
            
            # 6. 计算总金额和百分比
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
            
            # 7. 按金额排序并返回前10个
            composition_items.sort(key=lambda x: x.amount, reverse=True)
            return composition_items[:10]
            
        except Exception as e:
            logger.error(f"计算弹性支出分类占比失败: {e}")
            return [] 