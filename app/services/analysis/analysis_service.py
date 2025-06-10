"""Comprehensive Analysis Service Module.

包含综合分析服务。
优化版本：使用优化后的分析器和缓存策略。
"""
 
from typing import List, Dict, Any, Optional
from datetime import date, datetime, timedelta
import logging
import calendar

from app.models import Transaction, Account, Bank, db
from app.models.analysis_models import ComprehensiveAnalysisData
from app.services.analysis.analysis_factory import AnalyzerFactory, AnalyzerType
from app.utils.query_builder import OptimizedQueryBuilder, AnalysisException
from app.utils.cache_manager import optimized_cache
from app.utils.performance_monitor import monitor_performance
from sqlalchemy import func, and_, or_, extract, case
from sqlalchemy.exc import SQLAlchemyError

# 导入分析结果类，避免在异常处理中重复导入
from app.models.analysis_models import (
    IncomeExpenseAnalysis, IncomeStability, CashFlowHealth,
    IncomeDiversityMetrics, IncomeGrowthMetrics, FinancialResilience
)

# 导入报告服务
from app.services.report.report_service import FinancialReportService

logger = logging.getLogger(__name__)

class ComprehensiveService:
    """优化的综合分析服务。"""
    
    @staticmethod
    @monitor_performance("comprehensive_analysis")
    @optimized_cache('comprehensive_income_analysis', expire_minutes=45, priority=1)
    def get_comprehensive_income_analysis(account_id: Optional[int] = None) -> Dict[str, Any]:
        """获取综合收入分析数据，返回模板所需的完整data结构
        
        Args:
            account_id: 可选的账户ID，用于分析特定账户
            
        Returns:
            Dict[str, Any]: 包含所有分析模块数据的字典
        """
        try:
            # 获取基础数据
            today = date.today()
            start_date = today.replace(year=today.year - 1, month=1, day=1)  # 过去一年
            end_date = today
            
            # 创建优化后的分析器
            analyzers = ComprehensiveService._create_analyzers(start_date, end_date, account_id)
            
            # 并行执行分析（如果可能）
            analysis_results = ComprehensiveService._execute_parallel_analysis(analyzers)
            
            # 构建综合分析数据结构
            # 将IncomeExpenseAnalysis转换为IncomeExpenseBalance以保持模板兼容性
            from app.models.analysis_models import IncomeExpenseBalance
            income_expense_result = analysis_results[AnalyzerType.INCOME_EXPENSE]
            income_expense_balance = IncomeExpenseBalance(
                overall_stats=income_expense_result.overall_stats,
                monthly_data=income_expense_result.monthly_data
            )
            
            comprehensive_data = ComprehensiveAnalysisData(
                income_expense_balance=income_expense_balance,
                income_stability=analysis_results[AnalyzerType.INCOME_STABILITY],
                cash_flow_health=analysis_results[AnalyzerType.CASH_FLOW],
                income_diversity=analysis_results[AnalyzerType.INCOME_DIVERSITY],
                income_growth=analysis_results[AnalyzerType.INCOME_GROWTH],
                financial_resilience=analysis_results[AnalyzerType.FINANCIAL_RESILIENCE]
            )
            
            # 返回对象以支持属性访问
            return comprehensive_data
            
        except Exception as e:
            logger.error(f"Error getting comprehensive income analysis: {e}")
            # 返回默认对象以防止模板错误
            return ComprehensiveAnalysisData()
    
    @staticmethod
    def _create_analyzers(start_date: date, end_date: date, account_id: Optional[int]) -> Dict[str, Any]:
        """使用工厂模式创建分析器实例。"""
        try:
            # 使用工厂模式创建所有分析器
            return AnalyzerFactory.create_all_analyzers(start_date, end_date, account_id)
        except Exception as e:
            logger.error(f"使用工厂模式创建分析器失败: {e}")
            # 降级到手动创建关键分析器
            return {
                # 使用新的合并分析器
                AnalyzerType.COMPREHENSIVE_INCOME: AnalyzerFactory.create_analyzer(
                    AnalyzerType.COMPREHENSIVE_INCOME, start_date, end_date, account_id
                ),
                AnalyzerType.FINANCIAL_HEALTH: AnalyzerFactory.create_analyzer(
                    AnalyzerType.FINANCIAL_HEALTH, start_date, end_date, account_id
                ),
                AnalyzerType.INCOME_GROWTH: AnalyzerFactory.create_analyzer(
                    AnalyzerType.INCOME_GROWTH, start_date, end_date, account_id
                ),
                
                # 向后兼容映射
                AnalyzerType.INCOME_EXPENSE: AnalyzerFactory.create_analyzer(
                    AnalyzerType.INCOME_EXPENSE, start_date, end_date, account_id
                ),
                AnalyzerType.INCOME_STABILITY: AnalyzerFactory.create_analyzer(
                    AnalyzerType.INCOME_STABILITY, start_date, end_date, account_id
                ),
                AnalyzerType.CASH_FLOW: AnalyzerFactory.create_analyzer(
                    AnalyzerType.CASH_FLOW, start_date, end_date, account_id
                ),
                AnalyzerType.INCOME_DIVERSITY: AnalyzerFactory.create_analyzer(
                    AnalyzerType.INCOME_DIVERSITY, start_date, end_date, account_id
                ),
                AnalyzerType.FINANCIAL_RESILIENCE: AnalyzerFactory.create_analyzer(
                    AnalyzerType.FINANCIAL_RESILIENCE, start_date, end_date, account_id
                )
            }
    
    @staticmethod
    def _execute_parallel_analysis(analyzers: Dict[str, Any]) -> Dict[str, Any]:
        """执行并行分析（当前为顺序执行，可扩展为真正的并行）。"""
        results = {}
        
        try:
            # 顺序执行各个分析器
            results[AnalyzerType.INCOME_EXPENSE] = analyzers[AnalyzerType.INCOME_EXPENSE].analyze()
            results[AnalyzerType.INCOME_STABILITY] = analyzers[AnalyzerType.INCOME_STABILITY].analyze()
            results[AnalyzerType.CASH_FLOW] = analyzers[AnalyzerType.CASH_FLOW].analyze()
            results[AnalyzerType.INCOME_DIVERSITY] = analyzers[AnalyzerType.INCOME_DIVERSITY].analyze()
            results[AnalyzerType.INCOME_GROWTH] = analyzers[AnalyzerType.INCOME_GROWTH].analyze()
            results[AnalyzerType.FINANCIAL_RESILIENCE] = analyzers[AnalyzerType.FINANCIAL_RESILIENCE].analyze()
            
            return results
            
        except Exception as e:
            logger.error(f"并行分析执行失败: {e}")
            # 返回默认结果对象
            return {
                AnalyzerType.INCOME_EXPENSE: IncomeExpenseAnalysis(),
                AnalyzerType.INCOME_STABILITY: IncomeStability(),
                AnalyzerType.CASH_FLOW: CashFlowHealth(),
                AnalyzerType.INCOME_DIVERSITY: IncomeDiversityMetrics(),
                AnalyzerType.INCOME_GROWTH: IncomeGrowthMetrics(),
                AnalyzerType.FINANCIAL_RESILIENCE: FinancialResilience()
            }
    
    @staticmethod
    def generate_financial_report(account_id: int = None, start_date: date = None, 
                                end_date: date = None) -> Dict[str, Any]:
        """生成财务报告，委托给FinancialReportService处理。
        
        Args:
            account_id: 可选的账户ID
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            Dict[str, Any]: 财务报告数据
        """
        try:
            return FinancialReportService.generate_financial_report(
                account_id=account_id,
                start_date=start_date,
                end_date=end_date
            )
        except Exception as e:
            logger.error(f"生成财务报告时出错: {e}")
            # 返回默认的空报告结构
            return {
                'period': {
                    'start_date': start_date.isoformat() if start_date else None,
                    'end_date': end_date.isoformat() if end_date else None,
                    'days': 0
                },
                'summary': {
                    'total_income': 0,
                    'total_expense': 0,
                    'net_income': 0
                },
                'income_analysis': {},
                'expense_analysis': {},
                'category_breakdown': {},
                'trends': {},
                'insights': []
            }