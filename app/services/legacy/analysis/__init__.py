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
# FinancialAnalyzer已合并到FinancialService中
from ..business.financial.analysis_models import (
    AnalysisResult,
    MonthlyData,
    FinancialSummary,
    FinancialHealthMetrics,
    ComprehensiveReport
)
from ..business.financial.analysis_utils import (
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

# ==================== 便捷函数 ====================

def create_analyzer(db_session=None):
    """创建财务分析器实例（已弃用）
    
    注意：FinancialAnalyzer已合并到FinancialService中，
    请使用FinancialService替代。
    
    Args:
        db_session: 数据库会话，如果为None则使用默认会话
        
    Returns:
        FinancialService实例
    """
    from ..financial_service import FinancialService
    return FinancialService(db_session)


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
    # 数据模型
    'AnalysisResult',
    'MonthlyData', 
    'FinancialSummary',
    'FinancialHealthMetrics',
    'ComprehensiveReport',
    
    # 工具函数
    'cache_result',
    'handle_analysis_errors',
    'calculate_percentage',
    'format_currency',
    'format_percentage',
    'validate_date_range',
    
    # 便捷函数
    'create_analyzer',  # 兼容性函数，返回FinancialService
    'quick_analysis',
    'quick_summary',
    
    # 异常类
    'AnalysisError',
    'DataValidationError',
    'CalculationError',
    'InsufficientDataError'
]