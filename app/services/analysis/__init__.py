"""简化的财务分析服务包

提供统一、简洁的财务分析接口，替代原有的复杂架构。
主要特点：
- 单一分析器类，消除过度分离
- 简化的数据模型，减少复杂性
- 整合的工具函数，提高维护性
- 保持向后兼容性

Created: 2024-12-19
Author: AI Assistant
"""

# 简化的核心接口（推荐使用）
from .financial_analyzer import FinancialAnalyzer
from .data_models import (
    AnalysisResult,
    MonthlyData,
    FinancialSummary,
    FinancialHealthMetrics,
    ComprehensiveReport
)
from .analysis_utils import (
    # 缓存功能
    cache_result,
    SimpleCache,
    
    # 错误处理
    handle_analysis_errors,
    AnalysisError,
    DataValidationError,
    CalculationError,
    InsufficientDataError,
    
    # 计算工具
    calculate_growth_rate,
    calculate_percentage,
    calculate_average,
    calculate_stability_score,
    
    # 格式化工具
    format_currency,
    format_percentage,
    format_number,
    
    # 验证工具
    validate_date_range,
    validate_amount,
    validate_account_id
)

# 向后兼容性导入（保留原有接口）
try:
    # 导入原有的复杂接口以保持兼容性
    from .financial_analyzer import FinancialAnalyzer
    from .data_models import OverallStats, MonthlyData, AnalysisResult
    
    # 创建兼容性别名
    LegacyFinancialAnalyzer = FinancialAnalyzer
    LegacyOverallStats = OverallStats
    LegacyMonthlyData = MonthlyData
    LegacyAnalysisResult = AnalysisResult
    
except ImportError:
    # 如果原有模块不存在，创建占位符
    LegacyFinancialAnalyzer = None
    LegacyOverallStats = None
    LegacyMonthlyData = None
    LegacyAnalysisResult = None


# ==================== 兼容性服务类 ====================

class ComprehensiveService:
    """综合分析服务类 - 向后兼容接口
    
    这个类提供与原有 ComprehensiveService 兼容的接口，
    内部使用简化的 SimplifiedFinancialAnalyzer 实现。
    """
    
    def __init__(self, db_session=None):
        """初始化综合分析服务
        
        Args:
            db_session: 数据库会话，可选
        """
        self.analyzer = FinancialAnalyzer(db_session)
        self.db_session = db_session
    
    def get_comprehensive_analysis(self, user_id: int, months: int = 12) -> dict:
        """获取综合分析报告
        
        Args:
            user_id: 用户ID
            months: 分析月份数，默认12个月
            
        Returns:
            综合分析结果字典
        """
        return self.analyzer.get_comprehensive_analysis(user_id, months)
    
    def analyze_income(self, user_id: int, start_date, end_date) -> AnalysisResult:
        """分析收入情况
        
        Args:
            user_id: 用户ID
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            收入分析结果
        """
        return self.analyzer.analyze_income(user_id, start_date, end_date)
    
    def analyze_expenses(self, user_id: int, start_date, end_date) -> AnalysisResult:
        """分析支出情况
        
        Args:
            user_id: 用户ID
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            支出分析结果
        """
        return self.analyzer.analyze_expenses(user_id, start_date, end_date)
    
    def generate_summary(self, user_id: int) -> FinancialSummary:
        """生成财务总览
        
        Args:
            user_id: 用户ID
            
        Returns:
            财务总览对象
        """
        return self.analyzer.generate_summary(user_id)
    
    def calculate_health_metrics(self, user_id: int, months: int = 12) -> FinancialHealthMetrics:
        """计算财务健康指标
        
        Args:
            user_id: 用户ID
            months: 分析月份数，默认12个月
            
        Returns:
            财务健康指标
        """
        return self.analyzer.calculate_health_metrics(user_id, months)
    
    def generate_financial_report(self, account_id: int = None, start_date=None, end_date=None) -> dict:
        """生成财务报告
        
        Args:
            account_id: 账户ID，可选
            start_date: 开始日期，可选
            end_date: 结束日期，可选
            
        Returns:
            财务报告字典
        """
        from ..report.report_service import FinancialReportService
        return FinancialReportService.generate_financial_report(account_id, start_date, end_date)


# ==================== 便捷函数 ====================

def create_analyzer(db_session=None) -> FinancialAnalyzer:
    """创建财务分析器实例
    
    Args:
        db_session: 数据库会话，可选
        
    Returns:
        FinancialAnalyzer实例
    """
    return FinancialAnalyzer(db_session)


def quick_analysis(months: int = 12, db_session=None) -> dict:
    """快速财务分析
    
    Args:
        months: 分析月份数，默认12个月
        db_session: 数据库会话，可选
        
    Returns:
        综合分析结果字典
    """
    analyzer = create_analyzer(db_session)
    return analyzer.get_comprehensive_analysis(months)


def quick_summary(db_session=None) -> FinancialSummary:
    """快速财务总览
    
    Args:
        db_session: 数据库会话，可选
        
    Returns:
        FinancialSummary对象
    """
    analyzer = create_analyzer(db_session)
    return analyzer.generate_summary()


# ==================== 版本信息 ====================

__version__ = '2.0.0-simplified'
__author__ = 'AI Assistant'
__description__ = 'Simplified Financial Analysis Services'

# 导出的公共接口
__all__ = [
    # 核心类
    'FinancialAnalyzer',
    'ComprehensiveService',  # 兼容性服务类
    
    # 数据模型
    'AnalysisResult',
    'MonthlyData', 
    'FinancialSummary',
    'FinancialHealthMetrics',
    'ComprehensiveReport',
    
    # 工具函数
    'cache_result',
    'handle_analysis_errors',
    'calculate_growth_rate',
    'calculate_percentage',
    'format_currency',
    'format_percentage',
    'validate_date_range',
    
    # 便捷函数
    'create_analyzer',
    'quick_analysis',
    'quick_summary',
    
    # 向后兼容
    'LegacyFinancialAnalyzer',
    'LegacyOverallStats',
    'LegacyMonthlyData',
    'LegacyAnalysisResult',
    
    # 异常类
    'AnalysisError',
    'DataValidationError',
    'CalculationError',
    'InsufficientDataError'
]


# ==================== 向后兼容别名 ====================

# 为了保持向后兼容性，提供旧类名的别名
SimplifiedFinancialAnalyzer = FinancialAnalyzer
SimpleAnalysisResult = AnalysisResult
SimpleMonthlyData = MonthlyData
SimpleFinancialSummary = FinancialSummary

# 将别名添加到导出列表
__all__.extend([
    'SimplifiedFinancialAnalyzer',
    'SimpleAnalysisResult', 
    'SimpleMonthlyData',
    'SimpleFinancialSummary'
])

# ==================== 使用示例 ====================

"""
使用示例：

# 1. 基本使用（推荐新接口）
from app.services.analysis import create_analyzer

analyzer = create_analyzer()
result = analyzer.get_comprehensive_analysis(12)

# 2. 快速分析
from app.services.analysis import quick_analysis, quick_summary

analysis = quick_analysis(6)  # 分析最近6个月
summary = quick_summary()     # 生成财务总览

# 3. 具体分析（新接口）
from datetime import date
from app.services.analysis import FinancialAnalyzer

analyzer = FinancialAnalyzer()
income = analyzer.analyze_income(date(2024, 1, 1), date(2024, 12, 31))
expense = analyzer.analyze_expenses(date(2024, 1, 1), date(2024, 12, 31))
health = analyzer.analyze_financial_health(12)

# 4. 向后兼容使用（仍然支持旧接口）
from app.services.analysis import SimplifiedFinancialAnalyzer

analyzer = SimplifiedFinancialAnalyzer()  # 实际上是FinancialAnalyzer的别名
# 使用原有接口...
"""