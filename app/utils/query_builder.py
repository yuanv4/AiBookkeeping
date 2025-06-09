"""优化后的查询构建器模块。

提供高效的数据库查询构建器，包括查询优化、批量操作和智能索引使用。
"""

import logging
from datetime import datetime, date
from typing import Optional, List, Dict, Any, Tuple, Union
from sqlalchemy import func, extract, case, and_, or_, text, select
from sqlalchemy.orm import Query, joinedload, selectinload
from sqlalchemy.sql import Select
from app.models.transaction import Transaction
from app.models.account import Account
from app import db
from app.utils.cache_manager import optimized_cache

logger = logging.getLogger(__name__)

class AnalysisException(Exception):
    """分析服务自定义异常类"""
    pass

class OptimizedQueryBuilder:
    """优化的查询构建器，提供高效的查询接口和优化策略"""
    
    def __init__(self):
        self.query = None
        self.filters = []
        self._query_cache = {}
        
    @staticmethod
    def validate_date_range(start_date: Optional[date], end_date: Optional[date]) -> Tuple[date, date]:
        """验证和标准化日期范围"""
        if start_date and end_date and start_date > end_date:
            raise AnalysisException("开始日期不能晚于结束日期")
        
        if not start_date:
            start_date = date.today().replace(day=1)  # 当月第一天
        if not end_date:
            end_date = date.today()
            
        return start_date, end_date
    
    @staticmethod
    def validate_account_id(account_id: Optional[int]) -> Optional[int]:
        """验证账户ID"""
        if account_id is not None:
            if not isinstance(account_id, int) or account_id <= 0:
                raise AnalysisException("无效的账户ID")
            
            # 使用缓存检查账户存在性
            @optimized_cache('account_exists', expire_minutes=60, priority=3)
            def check_account_exists(acc_id):
                return Account.query.get(acc_id) is not None
            
            if not check_account_exists(account_id):
                raise AnalysisException(f"账户ID {account_id} 不存在")
        
        return account_id
    
    def build_optimized_transaction_query(self, 
                                        account_id: Optional[int] = None, 
                                        start_date: Optional[date] = None,
                                        end_date: Optional[date] = None,
                                        amount_filter: Optional[str] = None,
                                        include_type: bool = False,
                                        include_account: bool = False) -> Query:
        """构建优化的交易查询
        
        Args:
            account_id: 账户ID
            start_date: 开始日期
            end_date: 结束日期
            amount_filter: 金额过滤器 ('positive', 'negative', 'all')
            include_type: 是否包含交易类型信息
            include_account: 是否包含账户信息
        
        Returns:
            优化的SQLAlchemy Query对象
        """
        # 验证参数
        account_id = self.validate_account_id(account_id)
        start_date, end_date = self.validate_date_range(start_date, end_date)
        
        # 构建基础查询，使用预加载优化
        query = Transaction.query
        
        # 根据需要添加预加载
        if include_type:
            query = query.options(joinedload(Transaction.transaction_type))
        if include_account:
            query = query.options(joinedload(Transaction.account))
        
        # 添加过滤条件（按选择性排序，最具选择性的条件放在前面）
        if account_id:
            query = query.filter(Transaction.account_id == account_id)
        
        # 日期过滤使用索引友好的方式
        if start_date:
            query = query.filter(Transaction.date >= start_date)
        
        if end_date:
            query = query.filter(Transaction.date <= end_date)
        
        # 金额过滤
        if amount_filter == 'positive':
            query = query.filter(Transaction.amount > 0)
        elif amount_filter == 'negative':
            query = query.filter(Transaction.amount < 0)
        
        return query
    
    def build_aggregated_analysis_query(self, 
                                      account_id: Optional[int] = None,
                                      start_date: Optional[date] = None,
                                      end_date: Optional[date] = None,
                                      group_by: str = 'month') -> Query:
        """构建聚合分析查询，一次性获取多个统计指标"""
        # 验证参数
        account_id = self.validate_account_id(account_id)
        start_date, end_date = self.validate_date_range(start_date, end_date)
        
        # 根据分组类型选择分组字段
        if group_by == 'month':
            group_fields = [
                extract('year', Transaction.date).label('year'),
                extract('month', Transaction.date).label('month')
            ]
            order_fields = [
                extract('year', Transaction.date),
                extract('month', Transaction.date)
            ]
        elif group_by == 'week':
            group_fields = [
                extract('year', Transaction.date).label('year'),
                extract('week', Transaction.date).label('week')
            ]
            order_fields = [
                extract('year', Transaction.date),
                extract('week', Transaction.date)
            ]
        elif group_by == 'day':
            group_fields = [Transaction.date.label('date')]
            order_fields = [Transaction.date]
        else:
            raise AnalysisException(f"不支持的分组类型: {group_by}")
        
        # 构建聚合查询
        query = db.session.query(
            *group_fields,
            # 收入统计
            func.sum(case((Transaction.amount > 0, Transaction.amount), else_=0)).label('total_income'),
            func.count(case((Transaction.amount > 0, 1))).label('income_count'),
            func.avg(case((Transaction.amount > 0, Transaction.amount))).label('avg_income'),
            func.max(case((Transaction.amount > 0, Transaction.amount))).label('max_income'),
            
            # 支出统计
            func.sum(case((Transaction.amount < 0, func.abs(Transaction.amount)), else_=0)).label('total_expense'),
            func.count(case((Transaction.amount < 0, 1))).label('expense_count'),
            func.avg(case((Transaction.amount < 0, func.abs(Transaction.amount)))).label('avg_expense'),
            func.max(case((Transaction.amount < 0, func.abs(Transaction.amount)))).label('max_expense'),
            
            # 总体统计
            func.count(Transaction.id).label('total_transactions'),
            func.sum(Transaction.amount).label('net_amount')
        )
        
        # 添加过滤条件
        if account_id:
            query = query.filter(Transaction.account_id == account_id)
        
        if start_date:
            query = query.filter(Transaction.date >= start_date)
        
        if end_date:
            query = query.filter(Transaction.date <= end_date)
        
        # 分组和排序
        query = query.group_by(*group_fields).order_by(*order_fields)
        
        return query
    
    def build_category_analysis_query(self, 
                                    account_id: Optional[int] = None,
                                    start_date: Optional[date] = None,
                                    end_date: Optional[date] = None,
                                    income_only: bool = False,
                                    expense_only: bool = False,
                                    min_amount: Optional[float] = None) -> Query:
        """构建类别分析查询，使用高效的JOIN和聚合"""
        # 验证参数
        account_id = self.validate_account_id(account_id)
        start_date, end_date = self.validate_date_range(start_date, end_date)
        
        # 构建优化的查询（不再需要JOIN TransactionType）
        query = db.session.query(
            Transaction.transaction_type.label('type_enum'),
            
            # 聚合统计
            func.count(Transaction.id).label('transaction_count'),
            func.sum(Transaction.amount).label('total_amount'),
            func.avg(Transaction.amount).label('avg_amount'),
            func.max(Transaction.amount).label('max_amount'),
            func.min(Transaction.amount).label('min_amount'),
            
            # 高级统计
            func.sum(func.abs(Transaction.amount)).label('abs_total'),
            func.count(func.distinct(Transaction.account_id)).label('account_count')
        )
        
        # 添加过滤条件
        if account_id:
            query = query.filter(Transaction.account_id == account_id)
        
        if start_date:
            query = query.filter(Transaction.date >= start_date)
        
        if end_date:
            query = query.filter(Transaction.date <= end_date)
        
        if income_only:
            query = query.filter(Transaction.amount > 0)
        elif expense_only:
            query = query.filter(Transaction.amount < 0)
        
        if min_amount is not None:
            query = query.filter(func.abs(Transaction.amount) >= min_amount)
        
        # 分组和排序
        query = query.group_by(
            Transaction.transaction_type
        ).order_by(
            func.sum(func.abs(Transaction.amount)).desc()
        )
        
        return query
    
    def build_cash_flow_analysis_query(self, 
                                     account_id: Optional[int] = None,
                                     start_date: Optional[date] = None,
                                     end_date: Optional[date] = None) -> Query:
        """构建现金流分析查询"""
        # 验证参数
        account_id = self.validate_account_id(account_id)
        start_date, end_date = self.validate_date_range(start_date, end_date)
        
        # 使用窗口函数计算累计余额
        query = db.session.query(
            Transaction.date,
            Transaction.amount,
            func.sum(Transaction.amount).over(
                order_by=Transaction.date.asc()
            ).label('running_balance'),
            
            # 每日汇总
            func.sum(Transaction.amount).over(
                partition_by=Transaction.date
            ).label('daily_net'),
            
            func.sum(case((Transaction.amount > 0, Transaction.amount), else_=0)).over(
                partition_by=Transaction.date
            ).label('daily_income'),
            
            func.sum(case((Transaction.amount < 0, func.abs(Transaction.amount)), else_=0)).over(
                partition_by=Transaction.date
            ).label('daily_expense')
        )
        
        # 添加过滤条件
        if account_id:
            query = query.filter(Transaction.account_id == account_id)
        
        if start_date:
            query = query.filter(Transaction.date >= start_date)
        
        if end_date:
            query = query.filter(Transaction.date <= end_date)
        
        # 排序
        query = query.order_by(Transaction.date.asc(), Transaction.id.asc())
        
        return query
    
    def execute_with_error_handling(self, query: Query, operation_name: str) -> Any:
        """安全执行查询并处理错误"""
        try:
            start_time = datetime.now()
            result = query.all() if hasattr(query, 'all') else query
            duration = (datetime.now() - start_time).total_seconds()
            
            logger.info(f"{operation_name} 查询执行成功，耗时 {duration:.3f}s")
            return result
            
        except Exception as e:
            logger.error(f"{operation_name} 查询执行失败: {e}")
            raise AnalysisException(f"{operation_name} 执行失败: {str(e)}")
    
    @optimized_cache('query_plan', expire_minutes=120, priority=2)
    def get_query_execution_plan(self, query: Query) -> str:
        """获取查询执行计划（用于性能调优）"""
        try:
            # 获取编译后的SQL
            compiled = query.statement.compile(
                dialect=db.engine.dialect,
                compile_kwargs={"literal_binds": True}
            )
            
            # 执行EXPLAIN（仅适用于支持的数据库）
            explain_query = text(f"EXPLAIN QUERY PLAN {compiled}")
            result = db.session.execute(explain_query)
            
            plan_lines = []
            for row in result:
                plan_lines.append(str(row))
            
            return "\n".join(plan_lines)
            
        except Exception as e:
            logger.warning(f"获取查询执行计划失败: {e}")
            return "查询计划不可用"
    
    def build_batch_insert_query(self, transactions: List[Dict[str, Any]]) -> None:
        """构建批量插入查询"""
        try:
            if not transactions:
                return
            
            # 使用bulk_insert_mappings进行批量插入
            db.session.bulk_insert_mappings(Transaction, transactions)
            db.session.commit()
            
            logger.info(f"批量插入 {len(transactions)} 条交易记录")
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"批量插入失败: {e}")
            raise AnalysisException(f"批量插入失败: {str(e)}")
    
    def build_batch_update_query(self, updates: List[Dict[str, Any]], 
                               filter_field: str = 'id') -> None:
        """构建批量更新查询"""
        try:
            if not updates:
                return
            
            # 使用bulk_update_mappings进行批量更新
            db.session.bulk_update_mappings(Transaction, updates)
            db.session.commit()
            
            logger.info(f"批量更新 {len(updates)} 条记录")
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"批量更新失败: {e}")
            raise AnalysisException(f"批量更新失败: {str(e)}")
    
    def optimize_query_for_large_dataset(self, query: Query, 
                                       limit: int = 10000,
                                       use_streaming: bool = False) -> Query:
        """为大数据集优化查询"""
        if use_streaming:
            # 使用流式查询处理大数据集
            query = query.execution_options(stream_results=True)
        
        if limit > 0:
            query = query.limit(limit)
        
        # 添加查询提示（如果数据库支持）
        query = query.execution_options(
            compiled_cache={},  # 禁用编译缓存以节省内存
            autocommit=True     # 自动提交以减少锁定时间
        )
        
        return query
    
    def get_query_statistics(self) -> Dict[str, Any]:
        """获取查询统计信息"""
        return {
            'cached_queries': len(self._query_cache),
            'database_engine': str(db.engine.dialect.name),
            'connection_pool_size': db.engine.pool.size(),
            'connection_pool_checked_out': db.engine.pool.checkedout()
        }