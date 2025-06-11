"""Comprehensive Analysis Service Module.

包含综合分析服务。
优化版本：使用优化后的分析器和缓存策略。
"""
 
from typing import List, Dict, Any, Optional
from datetime import date, datetime, timedelta
import calendar

from app.models import Transaction, Account, Bank, db
from app.services.analysis.analysis_models import ComprehensiveAnalysisData
from app.services.analysis.analyzers import AnalyzerFactory, AnalyzerContext
from sqlalchemy import func, and_, or_, extract, case
from sqlalchemy.exc import SQLAlchemyError
import logging

# 导入分析结果类，避免在异常处理中重复导入
from app.services.analysis.analysis_models import (
    IncomeExpenseAnalysis, IncomeStability, CashFlowHealth,
    BalanceAnalysis, IncomeGrowth, DatabaseStats
)
from app.services.report import FinancialReportService

logger = logging.getLogger(__name__)

class ComprehensiveService:
    """优化的综合分析服务。"""
    
    @staticmethod
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
            
            # 创建分析器上下文
            context = AnalyzerContext(
                db_session=db.session,
                user_id=account_id or 1,  # 如果没有指定账户ID，使用默认值
                start_date=datetime.combine(start_date, datetime.min.time()),
                end_date=datetime.combine(end_date, datetime.min.time())
            )
            
            # 创建分析器工厂
            factory = AnalyzerFactory(context)
            
            # 创建综合分析器
            comprehensive_analyzer = factory.create_comprehensive_income_analyzer()
            financial_health_analyzer = factory.create_financial_health_analyzer()
            
            # 执行分析
            income_expense_result = comprehensive_analyzer.analyze_income_expense()
            income_stability_result = comprehensive_analyzer.analyze_income_stability()
            income_diversity_result = comprehensive_analyzer.analyze_income_diversity()
            cash_flow_result = financial_health_analyzer.analyze_cash_flow()
            financial_resilience_result = financial_health_analyzer.analyze_resilience()
            
            # 获取综合摘要
            comprehensive_summary = comprehensive_analyzer.get_comprehensive_summary()
            
            # 构建综合分析数据结构
            # 将IncomeExpenseAnalysis转换为IncomeExpenseBalance以保持模板兼容性
            from app.services.analysis.analysis_models import IncomeExpenseBalance
            income_expense_balance = IncomeExpenseBalance(
                overall_stats=getattr(income_expense_result, 'overall_stats', {}),
                monthly_data=getattr(income_expense_result, 'monthly_data', [])
            )
            
            comprehensive_data = ComprehensiveAnalysisData(
                income_expense_balance=income_expense_balance,
                income_stability=income_stability_result,
                cash_flow_health=cash_flow_result,
                income_diversity=income_diversity_result,
                income_growth=getattr(comprehensive_summary, 'income_growth', None),
                financial_resilience=financial_resilience_result
            )
            
            # 返回对象以支持属性访问
            return comprehensive_data
            
        except Exception as e:
            logger.error(f"Error getting comprehensive income analysis: {e}")
            # 返回默认对象以防止模板错误
            return ComprehensiveAnalysisData()
    
    # 旧的方法已移除，现在使用新的AnalyzerFactory和AnalyzerContext架构
    
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