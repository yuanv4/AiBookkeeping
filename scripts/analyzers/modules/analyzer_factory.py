import logging
from .data_extractor import DataExtractor
from .time_analyzer import TimeAnalyzer
from .category_analyzer import CategoryAnalyzer
from .merchant_analyzer import MerchantAnalyzer
from .anomaly_analyzer import AnomalyAnalyzer
from .summary_analyzer import SummaryAnalyzer

class AnalyzerFactory:
    """分析器工厂，负责创建和组织各种分析器"""
    
    def __init__(self, db_manager):
        """初始化分析器工厂
        
        Args:
            db_manager: DBManager实例，用于数据库操作
        """
        if db_manager is None:
            raise ValueError("DBManager instance must be provided to AnalyzerFactory")
        
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # 创建数据提取器
        self.data_extractor = DataExtractor(db_manager)
        
        # 创建各种分析器
        self.time_analyzer = TimeAnalyzer(self.data_extractor)
        self.category_analyzer = CategoryAnalyzer(self.data_extractor)
        self.merchant_analyzer = MerchantAnalyzer(self.data_extractor)
        self.anomaly_analyzer = AnomalyAnalyzer(self.data_extractor)
        self.summary_analyzer = SummaryAnalyzer(self.data_extractor)
        
        # 分析器字典，用于快速访问
        self.analyzers = {
            'time': self.time_analyzer,
            'category': self.category_analyzer,
            'merchant': self.merchant_analyzer,
            'anomaly': self.anomaly_analyzer,
            'summary': self.summary_analyzer
        }
    
    def get_analyzer(self, analyzer_type):
        """获取指定类型的分析器
        
        Args:
            analyzer_type: 分析器类型，可选值：'time', 'category', 'merchant', 'anomaly', 'summary'
            
        Returns:
            BaseAnalyzer: 分析器实例
        """
        if analyzer_type not in self.analyzers:
            self.logger.error(f"Unsupported analyzer type: {analyzer_type}")
            raise ValueError(f"Unsupported analyzer type: {analyzer_type}")
        
        return self.analyzers[analyzer_type]
    
    def analyze_all(self, start_date=None, end_date=None, account_number=None, 
                   currency=None, account_name=None, **kwargs):
        """执行所有分析
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            account_number: 账号 (用于过滤)
            currency: 币种 (用于过滤)
            account_name: 户名 (用于过滤)
            **kwargs: 其他参数
            
        Returns:
            dict: 包含所有分析结果的字典
        """
        self.logger.info(
            f"Analyzing all data: start_date={start_date}, end_date={end_date}, "
            f"account_number={account_number}, currency={currency}, account_name={account_name}"
        )
        
        try:
            # 获取交易数据（共享同一份数据，避免重复查询）
            df = self.data_extractor.get_transactions(
                start_date, end_date, account_number, currency, account_name
            )
            
            if df is None or df.empty:
                self.logger.warning("No transactions found for analysis.")
                return {
                    'summary': self.summary_analyzer._get_empty_summary(start_date, end_date),
                    'time_analysis': {
                        'monthly_stats': [],
                        'yearly_stats': [],
                        'weekly_stats': [],
                        'daily_stats': []
                    },
                    'category_analysis': {
                        'category_stats': [],
                        'expense_distribution': [],
                        'income_sources': []
                    },
                    'merchant_analysis': {
                        'by_count': [],
                        'by_amount': []
                    },
                    'anomaly_analysis': {
                        'core_transactions': {},
                        'outlier_stats': {}
                    },
                    'transactions': []
                }
            
            # 执行各种分析
            summary = self.summary_analyzer.analyze(
                start_date, end_date, account_number, currency, account_name, **kwargs
            )
            
            time_analysis = self.time_analyzer.analyze(
                start_date, end_date, account_number, currency, account_name, **kwargs
            )
            
            category_analysis = self.category_analyzer.analyze(
                start_date, end_date, account_number, currency, account_name, **kwargs
            )
            
            merchant_analysis = self.merchant_analyzer.analyze(
                start_date, end_date, account_number, currency, account_name, **kwargs
            )
            
            anomaly_analysis = self.anomaly_analyzer.analyze(
                start_date, end_date, account_number, currency, account_name, **kwargs
            )
            
            # 格式化交易记录
            transactions = []
            if not df.empty:
                df_copy = df.copy()
                if 'transaction_date' in df_copy.columns:
                    df_copy['transaction_date'] = df_copy['transaction_date'].dt.strftime('%Y-%m-%d')
                
                # 处理numpy数据类型
                for record in df_copy.to_dict('records'):
                    for key, value in record.items():
                        if isinstance(value, (float, int)):
                            record[key] = round(value, 2) if isinstance(value, float) else value
                    transactions.append(record)
            
            # 返回综合结果
            return {
                'summary': summary,
                'time_analysis': time_analysis,
                'category_analysis': category_analysis,
                'merchant_analysis': merchant_analysis,
                'anomaly_analysis': anomaly_analysis,
                'transactions': transactions
            }
        except Exception as e:
            self.logger.error(f"Error analyzing all data: {e}", exc_info=True)
            return {
                'error': str(e),
                'summary': self.summary_analyzer._get_empty_summary(start_date, end_date),
                'time_analysis': {},
                'category_analysis': {},
                'merchant_analysis': {},
                'anomaly_analysis': {},
                'transactions': []
            }
    
    def clear_cache(self):
        """清除所有缓存"""
        self.data_extractor.clear_cache() 