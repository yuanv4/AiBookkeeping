"""分析器工厂模块，负责创建和管理各种分析器"""
import logging
from typing import Dict, Any, List, Optional, Union, Type

# 导入分析器
from core.analyzers.modules.data_extractor import DataExtractor
from core.analyzers.modules.base_analyzer import BaseAnalyzer
from core.analyzers.modules.time_analyzer import TimeAnalyzer
from core.analyzers.modules.category_analyzer import CategoryAnalyzer
from core.analyzers.modules.merchant_analyzer import MerchantAnalyzer
from core.analyzers.modules.anomaly_analyzer import AnomalyAnalyzer
from core.analyzers.modules.summary_analyzer import SummaryAnalyzer

# 导入错误处理机制
from core.common.exceptions import AnalyzerError, InvalidParameterError
from core.common.error_handler import error_handler, safe_operation

# 导入配置管理器
# from core.common.config import get_config_manager # Removed

# 配置日志
logger = logging.getLogger('analyzer_factory')

class AnalyzerFactory:
    """分析器工厂类，负责创建和管理各种分析器"""
    
    def __init__(self, app, db_manager):
        """初始化分析器工厂
        
        Args:
            app: Flask application instance.
            db_manager: 数据库管理器实例
        """
        self.app = app
        self.db_manager = db_manager
        self.logger = logger
        
        # 使用 app.config 替代 config_manager
        self.config_manager = self.app.config 
        
        # 创建数据提取器
        self.data_extractor = DataExtractor(db_manager)
        
        # 创建各种分析器
        self._create_analyzers()
        
        # 分析器字典，保存分析器名称到实例的映射
        self.analyzers = {}
        self._register_analyzers()
    
    def _create_analyzers(self):
        """创建各种分析器实例"""
        # 检查配置中是否启用各种分析模块
        time_enabled = self.config_manager.get('ANALYSIS_TIME_ANALYSIS_ENABLED', True)
        category_enabled = self.config_manager.get('ANALYSIS_CATEGORY_ANALYSIS_ENABLED', True)
        merchant_enabled = self.config_manager.get('ANALYSIS_MERCHANT_ANALYSIS_ENABLED', True)
        anomaly_enabled = self.config_manager.get('ANALYSIS_ANOMALY_DETECTION_ENABLED', True)
        summary_enabled = self.config_manager.get('ANALYSIS_SUMMARY_ENABLED', True)
        
        # 创建分析器实例，如果配置中启用了相应模块
        if time_enabled:
            self.time_analyzer = TimeAnalyzer(self.data_extractor)
        
        if category_enabled:
            self.category_analyzer = CategoryAnalyzer(self.data_extractor)
        
        if merchant_enabled:
            self.merchant_analyzer = MerchantAnalyzer(self.data_extractor)
        
        if anomaly_enabled:
            self.anomaly_analyzer = AnomalyAnalyzer(self.data_extractor)
        
        if summary_enabled:
            self.summary_analyzer = SummaryAnalyzer(self.data_extractor)
    
    def _register_analyzers(self):
        """注册各种分析器到分析器字典"""
        # 注册分析器实例
        self.analyzers = {
            'time': getattr(self, 'time_analyzer', None),
            'category': getattr(self, 'category_analyzer', None),
            'merchant': getattr(self, 'merchant_analyzer', None),
            'anomaly': getattr(self, 'anomaly_analyzer', None),
            'summary': getattr(self, 'summary_analyzer', None)
        }
        
        # 过滤掉未启用的分析器
        self.analyzers = {k: v for k, v in self.analyzers.items() if v is not None}
        
        self.logger.info(f"已注册 {len(self.analyzers)} 个分析器: {', '.join(self.analyzers.keys())}")
    
    def get_analyzer(self, analyzer_type: str) -> Optional[BaseAnalyzer]:
        """获取指定类型的分析器
        
        Args:
            analyzer_type: 分析器类型，如'time', 'category'等
            
        Returns:
            BaseAnalyzer: 分析器实例，如果不存在返回None
        """
        analyzer = self.analyzers.get(analyzer_type)
        if not analyzer:
            self.logger.warning(f"未找到指定类型的分析器: {analyzer_type}")
        return analyzer
    
    @error_handler(fallback_value={}, expected_exceptions=InvalidParameterError)
    def analyze_all(self, **kwargs) -> Dict[str, Any]:
        """执行所有分析器的分析
        
        Args:
            **kwargs: 传递给分析器的参数
            
        Returns:
            dict: 包含所有分析结果的字典
        """
        # 验证参数
        if 'start_date' in kwargs and 'end_date' in kwargs:
            if kwargs['start_date'] and kwargs['end_date'] and kwargs['start_date'] > kwargs['end_date']:
                raise InvalidParameterError("开始日期不能晚于结束日期")
        
        # 从配置中获取默认日期范围
        if 'start_date' not in kwargs and 'end_date' not in kwargs:
            default_days = self.config_manager.get('ANALYSIS_DEFAULT_DATE_RANGE_DAYS', 90)
            self.logger.info(f"使用默认日期范围: 最近 {default_days} 天")
            
            # 让db_manager根据默认天数计算日期范围
            date_range = self.db_manager.get_default_date_range(default_days)
            kwargs.update(date_range)
        
        # 首先获取交易数据
        transactions_df = self.data_extractor.get_transactions(**kwargs)
        
        results = {
            'transactions': transactions_df.to_dict('records') if not transactions_df.empty else []
        }
        
        # 对每个分析器执行分析
        for analyzer_type, analyzer in self.analyzers.items():
            try:
                result = analyzer.analyze(**kwargs)
                results[analyzer_type] = result
            except Exception as e:
                self.logger.error(f"执行 {analyzer_type} 分析器时出错: {str(e)}")
                results[analyzer_type] = {'error': str(e)}
        
        return results
    
    @safe_operation("清除分析器缓存")
    def clear_cache(self):
        """清除所有分析器的缓存"""
        for analyzer_type, analyzer in self.analyzers.items():
            if hasattr(analyzer, 'clear_cache'):
                analyzer.clear_cache()
                self.logger.info(f"已清除 {analyzer_type} 分析器缓存")
        
        self.logger.info("所有分析器缓存已清除")

# 全局工厂实例管理调整
def get_analyzer_factory(app, db_manager) -> AnalyzerFactory:
    """获取分析器工厂的实例

    Args:
        app: Flask application instance.
        db_manager: DBManager instance.

    Returns:
        AnalyzerFactory: The AnalyzerFactory instance.
    """
    if not hasattr(app, 'analyzer_factory_instance'):
        factory = AnalyzerFactory(app, db_manager)
        app.analyzer_factory_instance = factory
    return app.analyzer_factory_instance