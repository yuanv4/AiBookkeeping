"""合并后的财务分析服务

统一的财务分析服务类，提供完整的财务数据分析和报告生成功能。
同时内联了 query_helpers 和 validators 中的功能，简化架构。

主要功能:
- 核心财务指标计算（总资产、净收入、应急储备等）
- 现金流分析和趋势计算
- 收入支出构成分析
- 仪表盘数据聚合
- 数据验证和类型转换

设计原则:
- 避免过度工程化，保持代码简洁
- 复杂算法委托给 ExpenseAnalyzer 处理
- 统一的错误处理和日志记录
- 类型安全的数据传输对象
"""

from typing import List, Dict, Any, Optional
from decimal import Decimal
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
import logging

from app.models import Transaction, Account, db
from sqlalchemy import func, or_, and_
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from sqlalchemy.sql.expression import over

# 导入复杂算法模块和数据类
from .expense_analyzer import ExpenseAnalyzer
from .dto import (
    Period, CoreMetrics, CompositionItem,
    TrendPoint, DashboardData, RecurringExpense, ExpenseTrend, ExpenseAnalysisData
)
from .utils import normalize_decimal, validate_date_range, get_month_date_range, calculate_change_percentage

logger = logging.getLogger(__name__)

# ==================== 配置常量 ====================
MAX_DATE_RANGE_DAYS = 365 * 2  # 最大查询范围2年
DEFAULT_DECIMAL_PLACES = 2

class FinancialAnalysisService:
    """财务分析服务
    
    合并了原来的分析和报告功能，提供完整的财务数据分析和报告生成。
    """
    
    def __init__(self, db_session: Optional[Session] = None):
        """初始化财务分析服务
        
        Args:
            db_session: 数据库会话，如果为None则使用默认会话
        """
        self.db = db_session or db.session
        self.logger = logging.getLogger(__name__)
    

    
    # ==================== 数据库查询辅助方法 ====================
    
    def get_latest_balance_by_account(self, target_date: Optional[date] = None) -> Dict[int, Decimal]:
        """获取每个账户的最新余额
        
        使用窗口函数获取每个账户的最新余额。
        
        Args:
            target_date: 目标日期，如果为None则获取最新余额
            
        Returns:
            Dict[int, Decimal]: 账户ID到余额的映射
        """
        try:
            # 构建基础查询
            query = self.db.query(
                Transaction.account_id,
                Transaction.balance_after
            )
            
            # 如果指定了目标日期，则过滤日期
            if target_date:
                query = query.filter(Transaction.date <= target_date)
            
            # 使用窗口函数获取每个账户的最新余额
            window_func = over(
                func.row_number(),
                partition_by=Transaction.account_id,
                order_by=[Transaction.date.desc(), Transaction.created_at.desc()]
            )
            
            # 子查询：获取每个账户的最新交易记录
            latest_balances = query.add_columns(
                window_func.label('rn')
            ).subquery()
            
            # 主查询：获取每个账户的最新余额
            results = self.db.query(
                latest_balances.c.account_id,
                latest_balances.c.balance_after
            ).filter(
                latest_balances.c.rn == 1
            ).all()
            
            # 转换为字典格式，确保余额为Decimal类型
            balance_dict = {}
            for account_id, balance_after in results:
                balance_dict[account_id] = normalize_decimal(balance_after)
            
            self.logger.debug(f"获取最新余额完成，账户数量: {len(balance_dict)}")
            return balance_dict
            
        except SQLAlchemyError as e:
            self.logger.error(f"数据库查询异常 - 获取最新余额失败: {e}")
            raise
        except Exception as e:
            self.logger.error(f"获取最新余额失败: {e}")
            raise
    

    
    def get_transactions_by_criteria(self, filters: Dict[str, Any]) -> List[Transaction]:
        """通用交易查询
        
        根据提供的过滤条件查询交易记录。
        
        Args:
            filters: 过滤条件字典，支持的键：
                - start_date: 开始日期
                - end_date: 结束日期
                - account_id: 账户ID
                - amount_min: 最小金额
                - amount_max: 最大金额
                - counterparty: 交易对方
                - description: 交易描述
                
        Returns:
            List[Transaction]: 符合条件的交易记录列表
        """
        try:
            query = self.db.query(Transaction)
            
            # 应用过滤条件
            if 'start_date' in filters and filters['start_date']:
                query = query.filter(Transaction.date >= filters['start_date'])
            
            if 'end_date' in filters and filters['end_date']:
                query = query.filter(Transaction.date <= filters['end_date'])
            
            if 'account_id' in filters and filters['account_id']:
                query = query.filter(Transaction.account_id == filters['account_id'])
            
            if 'amount_min' in filters and filters['amount_min'] is not None:
                query = query.filter(Transaction.amount >= filters['amount_min'])
            
            if 'amount_max' in filters and filters['amount_max'] is not None:
                query = query.filter(Transaction.amount <= filters['amount_max'])
            
            if 'counterparty' in filters and filters['counterparty']:
                query = query.filter(Transaction.counterparty == filters['counterparty'])
            
            if 'description' in filters and filters['description']:
                query = query.filter(Transaction.description == filters['description'])
            
            # 按日期排序
            query = query.order_by(Transaction.date.desc(), Transaction.created_at.desc())
            
            results = query.all()
            self.logger.debug(f"通用查询完成，结果数量: {len(results)}")
            
            return results
            
        except SQLAlchemyError as e:
            self.logger.error(f"数据库查询异常 - 通用交易查询失败: {e}")
            raise
        except Exception as e:
            self.logger.error(f"通用交易查询失败: {e}")
            raise
    
    def calculate_period_aggregation(self, start_date: date, end_date: date, 
                                   group_by: str = 'month') -> List[Dict[str, Any]]:
        """计算时间段聚合数据
        
        按指定的时间粒度聚合交易数据。
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            group_by: 聚合粒度，支持 'day', 'week', 'month'
            
        Returns:
            List[Dict[str, Any]]: 聚合结果列表
        """
        try:
            # 根据聚合粒度构建不同的查询
            if group_by == 'day':
                date_group = func.date(Transaction.date)
                date_format = '%Y-%m-%d'
            elif group_by == 'week':
                date_group = func.strftime('%Y-%W', Transaction.date)
                date_format = '%Y-%W'
            elif group_by == 'month':
                date_group = func.strftime('%Y-%m', Transaction.date)
                date_format = '%Y-%m'
            else:
                raise ValueError(f"不支持的聚合粒度: {group_by}")
            
            # 聚合查询
            results = self.db.query(
                date_group.label('period'),
                func.sum(Transaction.amount).label('total_amount'),
                func.count(Transaction.id).label('transaction_count')
            ).filter(
                and_(
                    Transaction.date >= start_date,
                    Transaction.date <= end_date
                )
            ).group_by(
                date_group
            ).order_by(
                date_group
            ).all()
            
            # 转换为字典格式
            aggregated_data = []
            for period, total_amount, transaction_count in results:
                aggregated_data.append({
                    'period': period,
                    'total_amount': normalize_decimal(total_amount or 0),
                    'transaction_count': transaction_count
                })
            
            self.logger.debug(f"时间段聚合完成，结果数量: {len(aggregated_data)}")
            return aggregated_data
            
        except SQLAlchemyError as e:
            self.logger.error(f"数据库查询异常 - 时间段聚合失败: {e}")
            raise
        except Exception as e:
            self.logger.error(f"时间段聚合失败: {e}")
            raise
    
    # ==================== 核心分析功能 ====================
    
    def get_current_total_assets(self) -> float:
        """获取当前总现金（所有账户最新余额之和）
        
        Returns:
            float: 当前总现金
        """
        try:
            # 获取每个账户的最新余额
            balance_dict = self.get_latest_balance_by_account()
            
            # 计算总现金
            total_assets = sum(balance_dict.values())
            
            result = float(total_assets)
            self.logger.debug(f"计算当前总现金: {result}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"获取当前总现金失败: {e}")
            raise
    
    def get_total_assets_at_date(self, target_date: date) -> float:
        """获取截至指定日期的总现金
        
        Args:
            target_date: 目标日期
            
        Returns:
            float: 截至指定日期的总现金
        """
        try:
            # 获取指定日期前每个账户的最新余额
            balance_dict = self.get_latest_balance_by_account(target_date)
            
            # 计算总现金
            total_assets = sum(balance_dict.values())
            
            result = float(total_assets)
            self.logger.debug(f"计算截至{target_date}的总现金: {result}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"获取指定日期总现金失败: {e}")
            raise
    
    def get_all_time_net_income(self) -> float:
        """计算所有时间范围内的总净收入
        
        Returns:
            float: 总净收入
        """
        try:
            total_net_income = self.db.query(func.sum(Transaction.amount)).scalar() or 0
            return float(total_net_income)
        except SQLAlchemyError as e:
            self.logger.error(f"数据库查询异常 - 计算总净收入失败: {e}")
            raise
        except Exception as e:
            self.logger.error(f"计算总净收入失败: {e}")
            raise



    def calculate_daily_average_expense(self, start_date: date, end_date: date) -> float:
        """计算指定时间范围内的日均支出
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            float: 日均支出金额（正数）
        """
        try:
            # 计算时间范围内的总支出（负数金额的绝对值）
            total_expense = self.db.query(
                func.sum(func.abs(Transaction.amount))
            ).filter(
                Transaction.amount < 0,
                Transaction.date >= start_date,
                Transaction.date <= end_date
            ).scalar() or 0
            
            # 计算天数
            days = (end_date - start_date).days + 1  # 包含结束日期
            
            if days <= 0:
                return 0.0
                
            daily_average = float(total_expense) / days
            self.logger.debug(f"计算日均支出: 总支出={total_expense}, 天数={days}, 日均={daily_average}")
            
            return daily_average
            
        except SQLAlchemyError as e:
            self.logger.error(f"数据库查询异常 - 计算日均支出失败: {e}")
            raise
        except Exception as e:
            self.logger.error(f"计算日均支出失败: {e}")
            raise

    def calculate_emergency_reserve_months(self, daily_average_expense: float = None, 
                                        calculation_period_days: int = None) -> float:
        """计算应急储备月数
        
        Args:
            daily_average_expense: 日均支出，如果为None则自动计算
            calculation_period_days: 用于计算日均支出的天数。如果为None，则使用全部历史数据。
            
        Returns:
            float: 应急储备月数，如果日均支出为0则返回-1表示无限
        """
        try:
            # 获取当前总现金作为应急储备资金
            current_assets = self.get_current_total_assets()
            
            # 如果没有提供日均支出，则进行计算
            if daily_average_expense is None:
                end_date = date.today()
                if calculation_period_days:
                    start_date = end_date - timedelta(days=calculation_period_days - 1)
                else:
                    # 如果未指定天数，则从第一笔交易开始计算
                    first_transaction_date = self.db.query(func.min(Transaction.date)).scalar()
                    if not first_transaction_date:
                        return -1.0 # 没有交易，无法计算
                    start_date = first_transaction_date
                
                daily_average_expense = self.calculate_daily_average_expense(start_date, end_date)
            
            # 处理日均支出为0的情况
            if daily_average_expense <= 0:
                self.logger.debug("日均支出为0，应急储备月数设为无限")
                return -1.0  # 返回-1表示无限月数
            
            # 计算应急储备月数（按30天/月计算）
            reserve_months = current_assets / (daily_average_expense * 30)
            self.logger.debug(f"计算应急储备月数: 总现金={current_assets}, 日均支出={daily_average_expense}, 储备月数={reserve_months}")
            
            return reserve_months
            
        except Exception as e:
            self.logger.error(f"计算应急储备月数失败: {e}")
            raise
    
    # ==================== 报告生成功能 ====================
    
    def get_initial_dashboard_data(self) -> DashboardData:
        """获取现金流健康仪表盘的初始静态数据
        
        Returns:
            DashboardData: 仪表盘所需的静态和全时段数据
        """
        try:
            # 1. 核心全时段指标
            current_total_assets = self.get_current_total_assets()
            emergency_reserve_months = self.calculate_emergency_reserve_months()
            all_time_net_income = self.get_all_time_net_income()

            # 2. 净现金趋势数据 (固定过去12个月)
            end_date = date.today()
            start_date = end_date - relativedelta(months=12)

            # 确保即使在少于12个月数据的情况下也能正常显示
            first_transaction_date = self.db.query(func.min(Transaction.date)).scalar()
            if first_transaction_date and start_date < first_transaction_date:
                start_date = first_transaction_date

            net_worth_trend = ExpenseAnalyzer.calculate_net_worth_trend(
                self.db, start_date, end_date, 'month'
            )

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
            
        except ValueError as e:
            self.logger.error(f"数据验证失败: {e}")
            raise
        except Exception as e:
            self.logger.error(f"获取资金流数据失败: {e}")
            raise
    
    def get_expense_analysis_data(self, target_month: date) -> ExpenseAnalysisData:
        """获取支出分析数据
        
        Args:
            target_month: 目标月份
            
        Returns:
            ExpenseAnalysisData: 支出分析数据
        """
        try:
            # 获取目标月份的日期范围
            start_date, end_date = get_month_date_range(target_month)
            
            # 计算目标月份总支出
            total_expense = self.db.query(
                func.sum(func.abs(Transaction.amount))
            ).filter(
                Transaction.amount < 0,
                Transaction.date >= start_date,
                Transaction.date <= end_date
            ).scalar() or 0
            
            # 获取近12个月的支出趋势
            trend_start = start_date - relativedelta(months=11)
            expense_trend = self._calculate_expense_trend(trend_start, end_date)
            
            # 获取周期性支出（使用复杂算法）
            recurring_expenses = ExpenseAnalyzer.identify_recurring_expenses(self.db)
            
            # 计算弹性支出构成
            flexible_composition = self._calculate_composition_direct(start_date, end_date, 'expense')

            # 获取弹性支出交易明细（Top 10）
            flexible_transactions = self._get_top_flexible_transactions(start_date, end_date, limit=10)

            # 获取周期性支出交易明细（可选，暂时为空）
            recurring_transactions = []

            return ExpenseAnalysisData(
                target_month=target_month.strftime('%Y-%m'),
                total_expense=normalize_decimal(total_expense),
                expense_trend=expense_trend,
                recurring_expenses=recurring_expenses,
                flexible_composition=flexible_composition,
                recurring_transactions=recurring_transactions,
                flexible_transactions=flexible_transactions
            )
            
        except Exception as e:
            self.logger.error(f"获取支出分析数据失败: {e}")
            raise
    
    def get_category_transactions(self, category: str, start_date: date, end_date: date, 
                                limit: int = 50) -> List[Dict[str, Any]]:
        """获取指定分类的交易明细
        
        Args:
            category: 分类名称，"未分类"表示获取未分类交易
            start_date: 开始日期
            end_date: 结束日期
            limit: 返回记录数限制
            
        Returns:
            List[Dict[str, Any]]: 交易明细列表
        """
        try:
            query = self.db.query(Transaction).filter(
                Transaction.date >= start_date,
                Transaction.date <= end_date
            )
            
            # 处理未分类情况 - 使用description字段作为分类依据
            if category == "未分类":
                query = query.filter(
                    or_(Transaction.description.is_(None), Transaction.description == '')
                )
            else:
                query = query.filter(Transaction.description.like(f'%{category}%'))
            
            transactions = query.order_by(Transaction.date.desc()).limit(limit).all()
            
            # 转换为字典格式
            result = []
            for t in transactions:
                result.append({
                    'id': t.id,
                    'date': t.date.isoformat(),
                    'description': t.description,
                    'amount': float(t.amount),
                    'category': t.description or '未分类',  # 使用description作为分类
                    'account_id': t.account_id
                })
            
            return result
            
        except Exception as e:
            self.logger.error(f"获取分类交易明细失败: {e}")
            raise
    
    def get_latest_transaction_month(self) -> Optional[date]:
        """获取最新交易月份
        
        Returns:
            Optional[date]: 最新交易的月份，如果没有交易则返回None
        """
        try:
            latest_date = self.db.query(func.max(Transaction.date)).scalar()
            return latest_date
        except Exception as e:
            self.logger.error(f"获取最新交易月份失败: {e}")
            return None
    
    # ==================== 私有辅助方法 ====================
    
    def _calculate_composition_direct(self, start_date: date, end_date: date, 
                                    transaction_type: str) -> List[CompositionItem]:
        """直接计算收入或支出构成
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            transaction_type: 'income' 或 'expense'
            
        Returns:
            List[CompositionItem]: 构成项目列表
        """
        try:
            # 根据类型设置过滤条件
            if transaction_type == 'income':
                amount_filter = Transaction.amount > 0
            else:
                amount_filter = Transaction.amount < 0
            
            # 按描述分组聚合
            results = self.db.query(
                Transaction.description,
                func.sum(func.abs(Transaction.amount)).label('total_amount'),
                func.count(Transaction.id).label('count')
            ).filter(
                amount_filter,
                Transaction.date >= start_date,
                Transaction.date <= end_date
            ).group_by(Transaction.description).all()
            
            # 计算总金额
            total_amount = sum(result.total_amount for result in results)
            
            # 构建构成项目列表
            composition_items = []
            for result in results:
                name = result.description or '未分类'
                amount = normalize_decimal(result.total_amount)
                percentage = normalize_decimal(
                    (result.total_amount / total_amount * 100) if total_amount > 0 else 0
                )
                
                composition_items.append(CompositionItem(
                    name=name,
                    amount=amount,
                    percentage=percentage,
                    count=result.count
                ))
            
            # 按金额降序排序
            composition_items.sort(key=lambda x: x.amount, reverse=True)
            
            return composition_items
            
        except Exception as e:
            self.logger.error(f"计算构成数据失败: {e}")
            raise
    
    def _calculate_cash_flow_direct(self, start_date: date, end_date: date, 
                                  granularity: str) -> List[TrendPoint]:
        """直接计算资金流净值
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            granularity: 时间粒度 ('day', 'week', 'month')
            
        Returns:
            List[TrendPoint]: 资金流趋势点列表
        """
        try:
            # 根据粒度设置日期格式（SQLite兼容）
            if granularity == 'day':
                date_format = func.date(Transaction.date)
            elif granularity == 'week':
                # 按周聚合（使用SQLite的strftime函数）
                date_format = func.strftime('%Y-%W', Transaction.date)
            else:  # month
                date_format = func.strftime('%Y-%m', Transaction.date)
            
            # 查询每个时间段的净现金流
            results = self.db.query(
                date_format.label('period'),
                func.sum(Transaction.amount).label('net_flow')
            ).filter(
                Transaction.date >= start_date,
                Transaction.date <= end_date
            ).group_by(date_format).order_by(date_format).all()
            
            # 构建趋势点列表
            trend_points = []
            for result in results:
                trend_points.append(TrendPoint(
                    date=result.period.isoformat(),
                    value=normalize_decimal(result.net_flow)
                ))
            
            return trend_points
            
        except Exception as e:
            self.logger.error(f"计算资金流数据失败: {e}")
            raise
    
    def _calculate_expense_trend(self, start_date: date, end_date: date) -> List[ExpenseTrend]:
        """计算支出趋势
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            List[ExpenseTrend]: 支出趋势列表
        """
        try:
            # 按月聚合支出数据（SQLite兼容）
            results = self.db.query(
                func.strftime('%Y-%m', Transaction.date).label('month'),
                func.sum(func.abs(Transaction.amount)).label('total_expense')
            ).filter(
                Transaction.amount < 0,
                Transaction.date >= start_date,
                Transaction.date <= end_date
            ).group_by(
                func.strftime('%Y-%m', Transaction.date)
            ).order_by(
                func.strftime('%Y-%m', Transaction.date)
            ).all()
            
            # 构建趋势点列表
            expense_trends = []
            for result in results:
                expense_trends.append(ExpenseTrend(
                    date=result.month,  # 现在已经是字符串格式 'YYYY-MM'
                    value=normalize_decimal(result.total_expense),
                    category='total'
                ))
            
            return expense_trends
            
        except Exception as e:
            self.logger.error(f"计算支出趋势失败: {e}")
            raise

    def _get_top_flexible_transactions(self, start_date: date, end_date: date, limit: int = 10) -> List[Dict[str, Any]]:
        """获取弹性支出交易明细Top N

        Args:
            start_date: 开始日期
            end_date: 结束日期
            limit: 返回记录数限制

        Returns:
            List[Dict[str, Any]]: 弹性支出交易明细列表
        """
        try:
            # 查询支出交易，按金额降序排列
            transactions = self.db.query(Transaction).join(Account).filter(
                Transaction.amount < 0,  # 只要支出
                Transaction.date >= start_date,
                Transaction.date <= end_date
            ).order_by(Transaction.amount.asc()).limit(limit).all()  # asc因为负数，最小的是最大支出

            # 转换为字典格式
            result = []
            for t in transactions:
                result.append({
                    'id': t.id,
                    'date': t.date.isoformat(),
                    'description': t.description or '未知交易',
                    'amount': float(t.amount),
                    'category': t.description or '未分类',  # 使用description作为分类
                    'account_id': t.account_id,
                    'account_name': t.account.account_name if t.account else '未知账户',
                    'counterparty': t.counterparty or '未知对手方'
                })

            return result

        except Exception as e:
            self.logger.error(f"获取弹性支出交易明细失败: {e}")
            return []