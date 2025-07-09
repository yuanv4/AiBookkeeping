"""计算辅助工具

提取自FinancialAnalysisService的复杂计算逻辑，专门处理重型数据分析任务。
使用静态方法设计，便于在不同服务中复用计算逻辑。

周期性支出识别算法说明：
========================

本模块实现了基于多维度特征融合和自适应阈值的智能周期性支出识别算法。

算法核心思想：
1. 多维度特征提取：从交易频率、金额稳定性、时间规律性、消费连续性等维度提取特征
2. 自适应阈值计算：基于所有商家的特征分布，动态计算判断阈值
3. 综合评分机制：使用加权评分方式，避免单一维度的局限性
4. 无需用户干预：完全自动化，能适应不同用户的消费习惯差异

特征维度说明：
- 频率特征：平均间隔、间隔变异系数、频率得分
- 金额特征：平均金额、金额变异系数、金额范围比例、稳定性得分
- 时间特征：消费连续性、最近活跃度、活跃度得分
- 规模特征：交易次数、总金额、规模得分

自适应阈值机制：
- 百分位数方法：选择前25%的商家作为周期性支出
- Z-score方法：选择Z-score > 1.0的商家
- 混合策略：结合两种方法，取平均值作为最终阈值

权重分配：
- 频率规律性：40%（时间间隔的规律性最重要）
- 金额稳定性：30%（金额的稳定性次之）
- 活跃度：20%（近期活跃度）
- 规模：10%（交易次数和总金额）

优势：
- 能识别瑞幸咖啡等高频但不完全规律的消费
- 自动适应不同用户的消费习惯
- 无需手动调整参数
- 可解释性强，每个维度都有明确的得分
"""

from typing import List, Dict, Any
from decimal import Decimal
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
import logging
import statistics
import numpy as np

from app.models import Transaction
from sqlalchemy import func
from sqlalchemy.orm import Session

from .dto import CompositionItem, TrendPoint, RecurringExpense



logger = logging.getLogger(__name__)

# 导入工具函数
from .utils import get_month_date_range

class ExpenseAnalyzer:
    """计算辅助工具类
    
    专门处理复杂的数据计算逻辑，从FinancialAnalysisService中提取最重型的方法。
    使用静态方法设计，保持无状态和高度可复用性。
    """
    
    @staticmethod
    def extract_merchant_features(transactions: List[Dict[str, Any]]) -> Dict[str, float]:
        """提取商家的多维度特征
        
        计算每个商家的多维特征指标，用于周期性支出识别。
        
        Args:
            transactions: 商家交易记录列表
            
        Returns:
            Dict[str, float]: 特征字典，包含各种统计指标
        """
        if len(transactions) < 3:
            return {}
        
        # 提取基础数据
        amounts = [tx['amount'] for tx in transactions]
        dates = [tx['date'] for tx in transactions]
        dates.sort()
        
        # 1. 交易频率特征
        intervals = [(dates[i] - dates[i-1]).days for i in range(1, len(dates))]
        avg_interval = statistics.mean(intervals) if intervals else 0
        interval_cv = statistics.stdev(intervals) / avg_interval if avg_interval > 0 else float('inf')
        
        # 2. 金额特征
        avg_amount = statistics.mean(amounts)
        amount_std = statistics.stdev(amounts) if len(amounts) > 1 else 0
        amount_cv = amount_std / avg_amount if avg_amount > 0 else float('inf')
        amount_range = max(amounts) - min(amounts)
        amount_range_ratio = amount_range / avg_amount if avg_amount > 0 else float('inf')
        
        # 3. 时间特征
        total_days = (max(dates) - min(dates)).days
        frequency = total_days / len(transactions) if len(transactions) > 1 else 0
        
        # 消费连续性：计算最长连续消费天数
        consecutive_days = 1
        max_consecutive = 1
        for i in range(1, len(dates)):
            if (dates[i] - dates[i-1]).days == 1:
                consecutive_days += 1
                max_consecutive = max(max_consecutive, consecutive_days)
            else:
                consecutive_days = 1
        
        # 最近活跃度：距离今天的天数
        days_since_last = (date.today() - max(dates)).days
        
        # 4. 规模特征
        total_amount = sum(amounts)
        transaction_count = len(transactions)
        
        # 5. 计算综合特征
        features = {
            # 频率特征
            'avg_interval': avg_interval,
            'interval_cv': interval_cv,
            'frequency': frequency,
            
            # 金额特征
            'avg_amount': avg_amount,
            'amount_cv': amount_cv,
            'amount_range_ratio': amount_range_ratio,
            
            # 时间特征
            'max_consecutive_days': max_consecutive,
            'days_since_last': days_since_last,
            'total_days_span': total_days,
            
            # 规模特征
            'transaction_count': transaction_count,
            'total_amount': total_amount,
            
            # 复合特征
            'frequency_score': 1.0 / (1.0 + interval_cv) if interval_cv != float('inf') else 0,
            'stability_score': 1.0 / (1.0 + amount_cv) if amount_cv != float('inf') else 0,
            'activity_score': 1.0 / (1.0 + days_since_last / 30.0),  # 30天为基准
            'scale_score': min(transaction_count / 10.0, 1.0),  # 10次交易为满分
        }
        
        return features

    @staticmethod
    def calculate_adaptive_threshold(all_features: List[Dict[str, float]]) -> Dict[str, float]:
        """计算自适应阈值
        
        基于所有商家的特征分布，动态计算判断阈值。
        使用百分位数和Z-score方法确定合适的阈值。
        
        Args:
            all_features: 所有商家的特征列表
            
        Returns:
            Dict[str, float]: 各维度的阈值字典
        """
        if not all_features:
            return {}
        
        # 提取所有商家的特征值
        feature_names = ['frequency_score', 'stability_score', 'activity_score', 'scale_score']
        feature_values = {name: [] for name in feature_names}
        
        for features in all_features:
            for name in feature_names:
                if name in features:
                    feature_values[name].append(features[name])
        
        thresholds = {}
        
        for name in feature_names:
            values = feature_values[name]
            if not values:
                continue
                
            # 计算百分位数阈值（前25%）
            sorted_values = sorted(values, reverse=True)
            percentile_index = int(len(sorted_values) * 0.25)
            percentile_threshold = sorted_values[percentile_index] if percentile_index < len(sorted_values) else sorted_values[-1]
            
            # 计算Z-score阈值
            mean_val = statistics.mean(values)
            std_val = statistics.stdev(values) if len(values) > 1 else 0
            zscore_threshold = mean_val + std_val if std_val > 0 else mean_val
            
            # 取两种方法的平均值作为最终阈值
            thresholds[name] = (percentile_threshold + zscore_threshold) / 2
        
        return thresholds

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
        
        使用自适应阈值算法，基于多维度特征融合来识别固定支出。
        无需用户干预，能自动适应不同用户的消费习惯差异。
        
        Args:
            db: 数据库会话
            
        Returns:
            List[RecurringExpense]: 识别出的周期性支出列表
        """
        # 调用新的自适应算法
        return ExpenseAnalyzer.identify_recurring_expenses_adaptive(db)
    
    @staticmethod
    def calculate_flexible_expense_composition(db: Session, target_month: date, recurring_expenses: List[RecurringExpense] = None) -> List[CompositionItem]:
        """计算弹性支出分类占比
        
        使用简单补集策略：从指定目标月份的支出中排除周期性支出，计算剩余支出的分类占比。
        基于counterparty字段进行匹配，确保与固定支出逻辑一致。
        
        Args:
            db: 数据库会话
            target_month: 目标分析月份
            recurring_expenses: 周期性支出列表，如果为None则自动识别
            
        Returns:
            List[CompositionItem]: 弹性支出分类占比列表
        """
        try:
            # 1. 计算目标月份的时间范围
            month_start, month_end = get_month_date_range(target_month)
            
            # 2. 获取周期性支出模式（如果未提供则自动识别）
            if recurring_expenses is None:
                recurring_expenses = ExpenseAnalyzer.identify_recurring_expenses(db)
            
            # 3. 构建周期性支出的组合键集合
            recurring_combination_keys = {recurring.combination_key for recurring in recurring_expenses}
            
            # 4. 查询非固定支出，按counterparty分组统计
            # 简单补集逻辑：所有支出 - 固定支出 = 弹性支出
            flexible_expenses = db.query(
                func.coalesce(Transaction.counterparty, '未知商家').label('category'),
                func.sum(func.abs(Transaction.amount)).label('amount'),
                func.count(Transaction.id).label('count')
            ).filter(
                Transaction.amount < 0,
                Transaction.date >= month_start,
                Transaction.date <= month_end,
                ~func.coalesce(Transaction.counterparty, '未知商家').in_(recurring_combination_keys)
            ).group_by(
                func.coalesce(Transaction.counterparty, '未知商家')
            ).order_by(func.sum(func.abs(Transaction.amount)).desc()).limit(10).all()
            
            if not flexible_expenses:
                return []
            
            # 5. 计算总金额和百分比
            total_flexible = sum(float(expense.amount) for expense in flexible_expenses)
            
            composition_items = []
            for expense in flexible_expenses:
                percentage = (float(expense.amount) / total_flexible * 100) if total_flexible > 0 else 0
                
                composition_items.append(CompositionItem(
                    name=expense.category,
                    amount=round(float(expense.amount), 2),
                    percentage=round(percentage, 1),
                    count=expense.count
                ))
            
            return composition_items
            
        except Exception as e:
            logger.error(f"计算弹性支出分类占比失败: {e}")
            return []

    @staticmethod
    def identify_recurring_expenses_adaptive(db: Session) -> List[RecurringExpense]:
        """使用自适应阈值识别周期性支出
        
        基于多维度特征融合和自适应阈值的智能识别算法。
        无需用户干预，能自动适应不同用户的消费习惯差异。
        
        Args:
            db: 数据库会话
            
        Returns:
            List[RecurringExpense]: 识别出的周期性支出列表
        """
        try:
            # 1. 获取数据库中所有支出交易
            expense_transactions = db.query(
                Transaction.counterparty,
                Transaction.description,
                Transaction.amount,
                Transaction.date
            ).filter(
                Transaction.amount < 0
            ).order_by(Transaction.date).all()

            if not expense_transactions:
                return []

            # 2. 按商家分组
            expense_groups = {}
            for tx in expense_transactions:
                key = tx.counterparty or '未知商家'
                if key not in expense_groups:
                    expense_groups[key] = []
                expense_groups[key].append({
                    'amount': abs(float(tx.amount)),
                    'date': tx.date,
                    'counterparty': tx.counterparty or '未知商家',
                    'description': tx.description or '未分类'
                })

            # 3. 提取所有商家的特征
            all_features = []
            merchant_features = {}
            
            for key, transactions in expense_groups.items():
                if len(transactions) < 3:
                    continue
                    
                features = ExpenseAnalyzer.extract_merchant_features(transactions)
                if features:
                    all_features.append(features)
                    merchant_features[key] = features

            # 4. 计算自适应阈值
            thresholds = ExpenseAnalyzer.calculate_adaptive_threshold(all_features)
            
            # 5. 基于阈值判断周期性支出
            recurring_expenses = []
            
            for key, transactions in expense_groups.items():
                if key not in merchant_features:
                    continue
                    
                features = merchant_features[key]
                
                # 计算综合得分
                scores = []
                weights = {
                    'frequency_score': 0.4,    # 频率规律性权重
                    'stability_score': 0.3,    # 金额稳定性权重
                    'activity_score': 0.2,     # 活跃度权重
                    'scale_score': 0.1         # 规模权重
                }
                
                total_score = 0
                for feature_name, weight in weights.items():
                    if feature_name in features and feature_name in thresholds:
                        feature_value = features[feature_name]
                        threshold = thresholds[feature_name]
                        
                        # 计算该维度的得分（0-100分）
                        if feature_value >= threshold:
                            dimension_score = 100
                        else:
                            # 线性插值计算得分
                            dimension_score = max(0, (feature_value / threshold) * 100)
                        
                        scores.append(dimension_score)
                        total_score += dimension_score * weight
                
                # 判断是否为周期性支出（综合得分 >= 60分）
                if total_score >= 60:
                    # 计算平均金额和频率
                    amounts = [tx['amount'] for tx in transactions]
                    dates = [tx['date'] for tx in transactions]
                    dates.sort()
                    
                    avg_amount = statistics.mean(amounts)
                    total_amount = sum(amounts)
                    
                    # 计算频率（平均间隔天数）
                    intervals = [(dates[i] - dates[i-1]).days for i in range(1, len(dates))]
                    frequency = round(statistics.mean(intervals), 1) if intervals else 0
                    
                    # 确定支出类别
                    category = ExpenseAnalyzer._determine_expense_category(key, avg_amount, frequency)
                    
                    recurring_expenses.append(RecurringExpense(
                        category=category,
                        total_amount=round(total_amount, 2),
                        amount=round(avg_amount, 2),
                        frequency=frequency,
                        confidence_score=round(total_score, 1),
                        last_occurrence=max(dates).isoformat(),
                        count=len(transactions),
                        combination_key=key
                    ))
            
            # 6. 按置信度排序
            recurring_expenses.sort(key=lambda x: x.confidence_score, reverse=True)
            
            return recurring_expenses
            
        except Exception as e:
            logger.error(f"自适应周期性支出识别失败: {e}", exc_info=True)
            return []

    @staticmethod
    def _determine_expense_category(merchant_name: str, avg_amount: float, frequency: float) -> str:
        """确定支出类别
        
        Args:
            merchant_name: 商家名称
            avg_amount: 平均金额
            frequency: 频率（天数）
            
        Returns:
            str: 支出类别
        """
        # 基于商家名称和金额特征判断类别
        merchant_lower = merchant_name.lower()
        
        if any(keyword in merchant_lower for keyword in ['咖啡', '奶茶', 'luckin', 'starbucks']):
            return '餐饮'
        elif any(keyword in merchant_lower for keyword in ['餐厅', '饭店', '美食', '外卖']):
            return '餐饮'
        elif any(keyword in merchant_lower for keyword in ['地铁', '公交', '交通', '深圳通']):
            return '交通'
        elif any(keyword in merchant_lower for keyword in ['医院', '药店', '社康']):
            return '医疗'
        elif any(keyword in merchant_lower for keyword in ['快递', '顺丰', '圆通', '申通']):
            return '快递'
        elif any(keyword in merchant_lower for keyword in ['超市', '便利店', '商场']):
            return '购物'
        elif frequency <= 7 and avg_amount <= 100:
            return '日常消费'
        elif frequency <= 30 and avg_amount <= 1000:
            return '月度支出'
        else:
            return '其他'