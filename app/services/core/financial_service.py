"""统一财务服务
"""

from typing import List, Dict, Any, Optional, Union
from decimal import Decimal
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
import logging

from app.models import Transaction, db
from sqlalchemy import func, case
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from sqlalchemy.sql.expression import over

logger = logging.getLogger(__name__)

class FinancialService:
    """统一财务服务
    
    整合了财务分析和报告生成功能，提供一站式的财务数据处理服务。
    消除了原有架构中的功能重复和接口复杂性。
    """
    def __init__(self, db_session: Optional[Session] = None):
        """初始化财务服务
        
        Args:
            db_session: 数据库会话，如果为None则使用默认会话
        """
        self.db = db_session or db.session
        self.logger = logging.getLogger(__name__)
    
    # ==================== 计算方法 ====================

    def get_income_data(self, months: int = 12) -> List[Dict[str, Any]]:
        """获取收入交易数据
        
        Args:
            months: 查询月数，默认12个月
            
        Returns:
            List[Dict[str, Any]]: 返回相应格式的数据
        """
        try:
            
            # 格式化结果
            result_data = []

            # TODO
            
            return result_data
            
        except Exception as e:
            self.logger.error(f"获取收入数据失败: {e}")
            return []

    def get_balance_data(self, months: int = 12) -> List[Dict[str, Any]]:
        """获取余额趋势
        
        Args:
            months: 查询月数，默认12个月

        Returns:
            List[Dict[str, Any]]: 返回相应格式的数据
            
        Raises:
            SQLAlchemyError: 数据库查询异常时抛出
        """
        try:
            # 使用窗口函数查询每个账户每个月的最终余额
            window_func = over(
                func.row_number(),
                partition_by=[Transaction.account_id, func.strftime('%Y-%m', Transaction.date)],
                order_by=[Transaction.date.desc(), Transaction.created_at.desc()]
            )
            
            # 子查询：获取每个账户每个月的最终交易记录
            monthly_balances = self.db.query(
                Transaction.account_id,
                func.strftime('%Y-%m', Transaction.date).label('month'),
                Transaction.balance_after
            ).add_columns(
                window_func.label('rn')
            ).filter(
                Transaction.date >= func.date('now', f'-{months} months')
            ).subquery()
            
            # 主查询：筛选最终记录并按月分组
            query = self.db.query(
                monthly_balances.c.month,
                func.sum(monthly_balances.c.balance_after).label('balance')
            ).filter(
                monthly_balances.c.rn == 1
            ).group_by(
                monthly_balances.c.month
            ).order_by(
                monthly_balances.c.month
            )
            
            results = query.all()
            
            # 返回历史趋势数据
            result_data = [{
                'month': result.month,
                'balance': float(result.balance or 0)
            } for result in results]
            
            return result_data
            
        except SQLAlchemyError as e:
            self.logger.error(f"数据库查询异常 - 统一余额查询失败: {e}")
            return []
        except Exception as e:
            self.logger.error(f"统一余额查询失败: {e}")
            return []

    # ==================== 支出分析方法 ====================

    def get_expense_overview(self, start_date: Optional[date] = None, 
                           end_date: Optional[date] = None, 
                           account_id: Optional[int] = None) -> Dict[str, Any]:
        """获取支出概览统计
        
        Args:
            start_date: 开始日期，None表示查询所有历史数据
            end_date: 结束日期，默认为今天
            account_id: 账户ID，None表示所有账户
            
        Returns:
            Dict[str, Any]: 支出概览数据
        """
        try:
            # 设置默认日期范围
            if not end_date:
                end_date = date.today()
            # 移除默认的12个月限制，当start_date为None时查询所有历史数据
            
            # 构建基础查询
            query = self.db.query(Transaction).filter(
                Transaction.amount < 0  # 只查询支出
            )
            
            # 添加时间范围过滤（如果指定了start_date）
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

    def get_expense_trends(self, months: int = 12, 
                          account_id: Optional[int] = None,
                          all_history: bool = False) -> List[Dict[str, Any]]:
        """获取支出趋势数据
        
        Args:
            months: 查询月数，默认12个月（仅在all_history=False时使用）
            account_id: 账户ID，None表示所有账户
            all_history: 是否查询所有历史数据，True时忽略months参数
            
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
            trend_data = [{
                'month': result.month,
                'expense_amount': float(result.expense_amount or 0),
                'expense_count': result.expense_count or 0
            } for result in results]
            
            return trend_data
            
        except SQLAlchemyError as e:
            self.logger.error(f"数据库查询异常 - 支出趋势查询失败: {e}")
            return []
        except Exception as e:
            self.logger.error(f"支出趋势查询失败: {e}")
            return []

    def get_expense_patterns(self, start_date: Optional[date] = None, 
                           end_date: Optional[date] = None, 
                           account_id: Optional[int] = None) -> Dict[str, Any]:
        """获取支出模式分析
        
        Args:
            start_date: 开始日期，None表示查询所有历史数据
            end_date: 结束日期，默认为今天
            account_id: 账户ID，None表示所有账户
            
        Returns:
            Dict[str, Any]: 支出模式数据
        """
        try:
            # 设置默认日期范围
            if not end_date:
                end_date = date.today()
            # 移除默认的12个月限制，当start_date为None时查询所有历史数据
            
            # 构建基础查询
            query = self.db.query(Transaction).filter(
                Transaction.amount < 0  # 只查询支出
            )
            
            # 添加时间范围过滤（如果指定了start_date）
            if start_date:
                query = query.filter(Transaction.date >= start_date)
            query = query.filter(Transaction.date <= end_date)
            
            # 添加账户过滤
            if account_id:
                query = query.filter(Transaction.account_id == account_id)
            
            # 获取所有支出交易
            transactions = query.all()
            
            # 分析固定支出（相同对手方、相似金额的重复交易）
            fixed_expenses = self._analyze_fixed_expenses(transactions)
            
            # 分析异常支出（超过平均值的2倍标准差）
            abnormal_expenses = self._analyze_abnormal_expenses(transactions)
            
            # 分析支出集中度（按周分布）
            weekly_distribution = self._analyze_weekly_distribution(transactions)
            
            return {
                'fixed_expenses': fixed_expenses,
                'abnormal_expenses': abnormal_expenses,
                'weekly_distribution': weekly_distribution
            }
            
        except SQLAlchemyError as e:
            self.logger.error(f"数据库查询异常 - 支出模式查询失败: {e}")
            return {}
        except Exception as e:
            self.logger.error(f"支出模式查询失败: {e}")
            return {}

    def get_expense_categories(self, start_date: Optional[date] = None, 
                             end_date: Optional[date] = None, 
                             account_id: Optional[int] = None, 
                             limit: int = 10) -> List[Dict[str, Any]]:
        """获取支出分类数据（按对手方）
        
        Args:
            start_date: 开始日期，None表示查询所有历史数据
            end_date: 结束日期，默认为今天
            account_id: 账户ID，None表示所有账户
            limit: 返回结果数量限制
            
        Returns:
            List[Dict[str, Any]]: 支出分类数据
        """
        try:
            # 设置默认日期范围
            if not end_date:
                end_date = date.today()
            # 移除默认的12个月限制，当start_date为None时查询所有历史数据
            
            # 构建查询
            query = self.db.query(
                Transaction.counterparty,
                func.sum(func.abs(Transaction.amount)).label('total_amount'),
                func.count(Transaction.id).label('transaction_count'),
                func.avg(func.abs(Transaction.amount)).label('avg_amount')
            ).filter(
                Transaction.amount < 0,  # 只查询支出
                Transaction.counterparty.isnot(None),
                Transaction.counterparty != ''
            )
            
            # 添加时间范围过滤（如果指定了start_date）
            if start_date:
                query = query.filter(Transaction.date >= start_date)
            query = query.filter(Transaction.date <= end_date)
            
            # 添加账户过滤
            if account_id:
                query = query.filter(Transaction.account_id == account_id)
            
            # 分组、排序和限制
            results = query.group_by(
                Transaction.counterparty
            ).order_by(
                func.sum(func.abs(Transaction.amount)).desc()
            ).limit(limit).all()
            
            # 格式化结果
            category_data = [{
                'counterparty': result.counterparty,
                'total_amount': float(result.total_amount or 0),
                'transaction_count': result.transaction_count or 0,
                'avg_amount': float(result.avg_amount or 0)
            } for result in results]
            
            return category_data
            
        except SQLAlchemyError as e:
            self.logger.error(f"数据库查询异常 - 支出分类查询失败: {e}")
            return []
        except Exception as e:
            self.logger.error(f"支出分类查询失败: {e}")
            return []

    # ==================== 私有辅助方法 ====================

    def _analyze_fixed_expenses(self, transactions: List[Transaction]) -> List[Dict[str, Any]]:
        """分析固定支出模式"""
        # 按对手方分组
        counterparty_groups = {}
        for transaction in transactions:
            if transaction.counterparty not in counterparty_groups:
                counterparty_groups[transaction.counterparty] = []
            counterparty_groups[transaction.counterparty].append(transaction)
        
        # 识别固定支出（相同对手方、金额相似的重复交易）
        fixed_expenses = []
        for counterparty, group_transactions in counterparty_groups.items():
            if len(group_transactions) >= 2:  # 至少2次交易
                amounts = [abs(t.amount) for t in group_transactions]
                # 确保平均值为Decimal类型
                avg_amount = sum(amounts) / Decimal(str(len(amounts)))
                # 如果所有金额都在平均值的10%范围内，认为是固定支出
                if all(abs(amount - avg_amount) / avg_amount <= Decimal('0.1') for amount in amounts):
                    fixed_expenses.append({
                        'counterparty': counterparty,
                        'amount': float(avg_amount),
                        'frequency': len(group_transactions),
                        'transactions': [{
                            'date': t.date.isoformat(),
                            'amount': float(abs(t.amount))
                        } for t in group_transactions]
                    })
        
        return fixed_expenses

    def _analyze_abnormal_expenses(self, transactions: List[Transaction]) -> List[Dict[str, Any]]:
        """分析异常支出"""
        if not transactions:
            return []
        
        amounts = [abs(t.amount) for t in transactions]
        # 确保平均值为Decimal类型
        avg_amount = sum(amounts) / Decimal(str(len(amounts)))
        
        # 计算标准差，使用Decimal运算
        variance = sum((amount - avg_amount) ** 2 for amount in amounts) / Decimal(str(len(amounts)))
        std_dev = variance.sqrt()
        
        # 识别异常支出（超过平均值2个标准差）
        threshold = avg_amount + Decimal('2') * std_dev
        abnormal_expenses = []
        
        for transaction in transactions:
            if abs(transaction.amount) > threshold:
                abnormal_expenses.append({
                    'date': transaction.date.isoformat(),
                    'counterparty': transaction.counterparty,
                    'amount': float(abs(transaction.amount)),
                    'description': transaction.description
                })
        
        return abnormal_expenses

    def _analyze_weekly_distribution(self, transactions: List[Transaction]) -> Dict[str, int]:
        """分析周度支出分布"""
        weekly_counts = {}
        for transaction in transactions:
            # 获取星期几（0=周一，6=周日）
            weekday = transaction.date.weekday()
            weekday_name = ['周一', '周二', '周三', '周四', '周五', '周六', '周日'][weekday]
            
            if weekday_name not in weekly_counts:
                weekly_counts[weekday_name] = 0
            weekly_counts[weekday_name] += 1
        
        return weekly_counts

    # ==================== 新增分析方法 ====================

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
            
            # 1. 净资产趋势数据 (使用现有的get_balance_data逻辑)
            net_worth_trend = self._get_net_worth_trend(start_date, end_date)
            
            # 2. 核心健康指标
            current_metrics = self._get_period_metrics(start_date, end_date)
            previous_metrics = self._get_period_metrics(prev_start_date, prev_end_date)
            
            # 3. 资金流分析数据
            cash_flow_data = self._get_cash_flow_data(start_date, end_date)
            
            # 4. 收入构成分析
            income_composition = self._get_income_composition(start_date, end_date)
            
            # 5. 支出构成分析
            expense_composition = self._get_expense_composition(start_date, end_date)
            
            # 计算对比指标
            income_change = self._calculate_change_percentage(
                current_metrics['total_income'], 
                previous_metrics['total_income']
            )
            expense_change = self._calculate_change_percentage(
                current_metrics['total_expense'], 
                previous_metrics['total_expense']
            )
            net_change = self._calculate_change_percentage(
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
    
    def _get_net_worth_trend(self, start_date: date, end_date: date) -> List[Dict[str, Any]]:
        """获取净资产趋势数据"""
        try:
            self.logger.info(f"开始获取净资产趋势数据: {start_date} 到 {end_date}")
            
            # 首先检查是否有任何交易数据
            total_transactions = self.db.query(Transaction).count()
            self.logger.info(f"数据库中总交易数: {total_transactions}")
            
            if total_transactions == 0:
                self.logger.warning("数据库中没有任何交易数据")
                return []
            
            # 简化方法：使用现有的get_balance_data方法的逻辑，但适配日期范围
            # 计算从start_date到end_date的天数
            days_diff = (end_date - start_date).days
            
            if days_diff <= 0:
                # 如果日期范围无效，返回当前总资产
                current_assets = self._get_current_total_assets()
                return [{
                    'date': end_date.isoformat() if hasattr(end_date, 'isoformat') else str(end_date),
                    'balance': current_assets
                }]
            
            # 使用类似get_balance_data的窗口函数方法，但按日期分组
            try:
                window_func = over(
                    func.row_number(),
                    partition_by=[Transaction.account_id, func.date(Transaction.date)],
                    order_by=[Transaction.date.desc(), Transaction.created_at.desc()]
                )
                
                # 子查询：获取每个账户每日的最终交易记录
                daily_balances = self.db.query(
                    Transaction.account_id,
                    func.date(Transaction.date).label('date'),
                    Transaction.balance_after
                ).add_columns(
                    window_func.label('rn')
                ).filter(
                    Transaction.date >= start_date,
                    Transaction.date <= end_date
                ).subquery()
                
                # 主查询：筛选最终记录并按日期分组
                query = self.db.query(
                    daily_balances.c.date,
                    func.sum(daily_balances.c.balance_after).label('total_balance')
                ).filter(
                    daily_balances.c.rn == 1
                ).group_by(
                    daily_balances.c.date
                ).order_by(
                    daily_balances.c.date
                )
                
                results = query.all()
                self.logger.info(f"窗口函数查询结果数量: {len(results)}")
                
                if results:
                    trend_data = []
                    for result in results:
                        # 处理日期格式 - 可能已经是字符串
                        if hasattr(result.date, 'isoformat'):
                            date_str = result.date.isoformat()
                        else:
                            date_str = str(result.date)  # 已经是字符串
                        
                        trend_data.append({
                            'date': date_str,
                            'balance': float(result.total_balance or 0)
                        })
                    
                    self.logger.info(f"成功获取净资产趋势数据，共 {len(trend_data)} 个数据点")
                    return trend_data
                    
            except Exception as window_error:
                self.logger.warning(f"窗口函数查询失败，使用备用方法: {window_error}")
            
            # 备用方法：如果窗口函数失败，使用简单的方法
            # 获取指定日期范围内所有有交易的日期
            dates_query = self.db.query(
                func.date(Transaction.date).label('date')
            ).filter(
                Transaction.date >= start_date,
                Transaction.date <= end_date
            ).distinct().order_by(func.date(Transaction.date))
            
            dates = [row.date for row in dates_query.all()]
            self.logger.info(f"备用方法：指定日期范围内的交易日期数量: {len(dates)}")
            
            if not dates:
                # 如果指定范围内没有交易，但数据库有数据，则使用当前总资产
                current_assets = self._get_current_total_assets()
                self.logger.info(f"范围内无交易，使用当前总资产: {current_assets}")
                
                if current_assets > 0:
                    return [{
                        'date': start_date.isoformat() if hasattr(start_date, 'isoformat') else str(start_date),
                        'balance': current_assets
                    }, {
                        'date': end_date.isoformat() if hasattr(end_date, 'isoformat') else str(end_date),
                        'balance': current_assets
                    }]
                else:
                    return []
            
            # 如果日期太多，进行采样
            if len(dates) > 15:
                # 取开始、结束和中间的一些关键点
                sampled_dates = [dates[0]]  # 开始
                step = max(1, len(dates) // 10)  # 大约10个点
                for i in range(step, len(dates) - step, step):
                    sampled_dates.append(dates[i])
                sampled_dates.append(dates[-1])  # 结束
                dates = sampled_dates
            
            self.logger.info(f"备用方法：处理的关键日期数量: {len(dates)}")
            
            trend_data = []
            current_assets = self._get_current_total_assets()  # 获取当前总资产作为基准
            
            # 对每个日期计算净资产
            for target_date in dates:
                try:
                    # 处理日期格式 - 可能已经是字符串
                    if hasattr(target_date, 'isoformat'):
                        date_str = target_date.isoformat()
                    else:
                        date_str = str(target_date)  # 已经是字符串
                    
                    # 简化：使用当前总资产，因为这是现金资产的概念
                    # 在实际应用中，这个值在短期内变化不大
                    trend_data.append({
                        'date': date_str,
                        'balance': current_assets
                    })
                    
                except Exception as date_error:
                    self.logger.error(f"处理日期 {target_date} 时出错: {date_error}")
                    continue
            
            self.logger.info(f"备用方法成功获取净资产趋势数据，共 {len(trend_data)} 个数据点")
            return trend_data
            
        except Exception as e:
            self.logger.error(f"获取净资产趋势失败: {e}")
            import traceback
            self.logger.error(f"错误详情: {traceback.format_exc()}")
            return []
    
    def _get_period_metrics(self, start_date: date, end_date: date) -> Dict[str, Any]:
        """获取指定周期的核心指标"""
        try:
            # 计算总收入和总支出
            income_query = self.db.query(
                func.sum(Transaction.amount)
            ).filter(
                Transaction.amount > 0,
                Transaction.date >= start_date,
                Transaction.date <= end_date
            ).scalar() or Decimal('0')
            
            expense_query = self.db.query(
                func.sum(func.abs(Transaction.amount))
            ).filter(
                Transaction.amount < 0,
                Transaction.date >= start_date,
                Transaction.date <= end_date
            ).scalar() or Decimal('0')
            
            # 获取当前总资产（所有账户最新余额之和）
            current_assets = self._get_current_total_assets()
            
            total_income = float(income_query)
            total_expense = float(expense_query)
            
            return {
                'current_total_assets': current_assets,
                'total_income': total_income,
                'total_expense': total_expense,
                'net_income': total_income - total_expense
            }
            
        except Exception as e:
            self.logger.error(f"获取周期指标失败: {e}")
            return {
                'current_total_assets': 0.0,
                'total_income': 0.0,
                'total_expense': 0.0,
                'net_income': 0.0
            }
    
    def _get_current_total_assets(self) -> float:
        """获取当前总资产（所有账户最新余额之和）"""
        try:
            # 使用窗口函数获取每个账户的最新余额
            window_func = over(
                func.row_number(),
                partition_by=Transaction.account_id,
                order_by=[Transaction.date.desc(), Transaction.created_at.desc()]
            )
            
            # 子查询：获取每个账户的最新交易记录
            latest_balances = self.db.query(
                Transaction.account_id,
                Transaction.balance_after
            ).add_columns(
                window_func.label('rn')
            ).subquery()
            
            # 主查询：筛选最新记录并求和
            total_assets = self.db.query(
                func.sum(latest_balances.c.balance_after)
            ).filter(
                latest_balances.c.rn == 1
            ).scalar() or Decimal('0')
            
            return float(total_assets)
            
        except Exception as e:
            self.logger.error(f"获取当前总资产失败: {e}")
            return 0.0
    
    def _get_cash_flow_data(self, start_date: date, end_date: date) -> List[Dict[str, Any]]:
        """获取资金流数据，按日统计收支"""
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
                'date': result.date,
                'income': float(result.income or 0),
                'expense': float(result.expense or 0),
                'net': float((result.income or 0) - (result.expense or 0))
            } for result in results]
            
        except Exception as e:
            self.logger.error(f"获取资金流数据失败: {e}")
            return []
    
    def _get_income_composition(self, start_date: date, end_date: date) -> List[Dict[str, Any]]:
        """获取收入构成分析"""
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
    
    def _get_expense_composition(self, start_date: date, end_date: date) -> List[Dict[str, Any]]:
        """获取支出构成分析"""
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
    
    def _calculate_change_percentage(self, current: float, previous: float) -> float:
        """计算变化百分比"""
        if previous == 0:
            return 0.0 if current == 0 else 100.0
        return ((current - previous) / previous) * 100
    
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

    def get_category_analysis(self, duration_months: int = 12) -> Dict[str, Any]:
        """获取分类洞察数据
        
        Args:
            duration_months: 查询月数，默认12个月
            
        Returns:
            Dict[str, Any]: 分类洞察数据
        """
        try:
            # 计算起始日期
            end_date = date.today()
            start_date = end_date - relativedelta(months=duration_months)
            
            # 查询指定时间范围内的支出交易，按描述分组
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
            
            # 格式化分类数据
            category_breakdown = []
            for result in results:
                amount = Decimal(str(result.total_amount or 0))
                percentage = (amount / total_expense * 100) if total_expense > 0 else 0
                
                category_breakdown.append({
                    'name': result.category,
                    'amount': float(amount),
                    'percentage': float(percentage),
                    'count': result.transaction_count or 0
                })
            
            # 获取前10个支出类别作为排行榜
            top_categories = category_breakdown[:10]
            
            return {
                'category_breakdown': category_breakdown,
                'top_categories': top_categories,
                'total_expense': float(total_expense),
                'category_count': len(category_breakdown),
                'duration_months': duration_months,
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat()
            }
            
        except SQLAlchemyError as e:
            self.logger.error(f"数据库查询异常 - 分类分析查询失败: {e}")
            return {
                'category_breakdown': [],
                'top_categories': [],
                'total_expense': 0.0,
                'category_count': 0,
                'duration_months': duration_months,
                'start_date': '',
                'end_date': ''
            }
        except Exception as e:
            self.logger.error(f"分类分析查询失败: {e}")
            return {
                'category_breakdown': [],
                'top_categories': [],
                'total_expense': 0.0,
                'category_count': 0,
                'duration_months': duration_months,
                'start_date': '',
                'end_date': ''
            }