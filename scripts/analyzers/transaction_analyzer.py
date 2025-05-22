import os
import sys
import logging
from datetime import datetime
import pandas as pd
import numpy as np
import re
import jieba
from collections import defaultdict, Counter
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
import seaborn as sns
import calendar
import json
import logging

# 添加项目根目录到PYTHONPATH以解决导入问题
current_dir = os.path.dirname(os.path.abspath(__file__))
scripts_dir = os.path.dirname(current_dir)
root_dir = os.path.dirname(scripts_dir)
if root_dir not in sys.path:
    sys.path.append(root_dir)
if scripts_dir not in sys.path:
    sys.path.append(scripts_dir)

from scripts.db.db_manager import DBManager

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('transaction_analyzer')

# 设置中文字体
try:
    font = FontProperties(fname=r"C:\Windows\Fonts\simhei.ttf")
except:
    font = None

# 导入模块化分析器
from scripts.analyzers.modules.analyzer_factory import AnalyzerFactory

class TransactionAnalyzer:
    """交易分析器门面类，统一管理和调用各种分析功能"""
    
    def __init__(self, db_manager=None):
        """初始化交易分析器
        
        Args:
            db_manager: DBManager实例，如果为None则创建新实例
        """
        if db_manager is None:
            raise ValueError("DBManager instance must be provided to TransactionAnalyzer")
        
        # 创建分析器工厂
        self.analyzer_factory = AnalyzerFactory(db_manager)
        self.logger = logger
    
    def get_transactions_direct(self, start_date=None, end_date=None, account_number=None, currency=None, account_name=None):
        """直接从数据库获取交易数据并转换为DataFrame
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            account_number: 账号 (用于过滤)
            currency: 币种 (用于过滤)
            account_name: 户名 (用于过滤)
        
        Returns:
            pandas.DataFrame: 包含交易数据的DataFrame
        """
        self.logger.info(
            f"Fetching transactions direct: start_date={start_date}, end_date={end_date}, account_number={account_number}, currency={currency}, account_name={account_name}"
        )
        
        # 通过数据提取器获取数据
        return self.analyzer_factory.data_extractor.get_transactions(
            start_date=start_date,
            end_date=end_date,
            account_number=account_number,
            currency=currency,
            account_name=account_name
        )
    
    def get_summary_direct(self, start_date=None, end_date=None, account_number=None, currency=None, account_name=None):
        """获取交易摘要统计
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            account_number: 账号 (用于过滤)
            currency: 币种 (用于过滤)
            account_name: 户名 (用于过滤)
            
        Returns:
            dict: 摘要统计信息
        """
        # 通过摘要分析器获取结果
        return self.analyzer_factory.summary_analyzer.analyze(
            start_date=start_date,
            end_date=end_date,
            account_number=account_number,
            currency=currency,
            account_name=account_name
        )
    
    def get_monthly_stats_direct(self, start_date=None, end_date=None, account_number=None, currency=None, account_name=None):
        """获取月度统计数据
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            account_number: 账号 (用于过滤)
            currency: 币种 (用于过滤)
            account_name: 户名 (用于过滤)
            
        Returns:
            pandas.DataFrame: 月度统计数据
        """
        # 通过时间分析器获取数据
        df = self.get_transactions_direct(start_date, end_date, account_number, currency, account_name)
        if df is None or df.empty:
            return pd.DataFrame()
        
        return self.analyzer_factory.time_analyzer.get_monthly_stats(df)
    
    def get_yearly_stats_direct(self, start_date=None, end_date=None, account_number=None, currency=None, account_name=None):
        """获取年度统计数据
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            account_number: 账号 (用于过滤)
            currency: 币种 (用于过滤)
            account_name: 户名 (用于过滤)
            
        Returns:
            pandas.DataFrame: 年度统计数据
        """
        # 通过时间分析器获取数据
        df = self.get_transactions_direct(start_date, end_date, account_number, currency, account_name)
        if df is None or df.empty:
            return pd.DataFrame()
        
        return self.analyzer_factory.time_analyzer.get_yearly_stats(df)
    
    def get_category_stats_direct(self, start_date=None, end_date=None, account_number=None, currency=None, account_name=None):
        """获取按交易类型统计的支出数据
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            account_number: 账号 (用于过滤)
            currency: 币种 (用于过滤)
            account_name: 户名 (用于过滤)
            
        Returns:
            pandas.DataFrame: 交易类型统计数据
        """
        # 通过类别分析器获取数据
        df = self.get_transactions_direct(start_date, end_date, account_number, currency, account_name)
        if df is None or df.empty:
            return pd.DataFrame(columns=['transaction_type', 'total', 'count', 'average', 'percentage'])
        
        return self.analyzer_factory.category_analyzer.get_category_stats(df)
    
    def get_weekly_stats_direct(self, start_date=None, end_date=None, account_number=None, currency=None, account_name=None):
        """获取周度统计数据
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            account_number: 账号 (用于过滤)
            currency: 币种 (用于过滤)
            account_name: 户名 (用于过滤)
            
        Returns:
            pandas.DataFrame: 周度统计数据
        """
        # 通过时间分析器获取数据
        df = self.get_transactions_direct(start_date, end_date, account_number, currency, account_name)
        if df is None or df.empty:
            return pd.DataFrame()
        
        return self.analyzer_factory.time_analyzer.get_weekly_stats(df)
    
    def get_daily_stats_direct(self, start_date=None, end_date=None, account_number=None, currency=None, account_name=None):
        """获取日度统计数据
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            account_number: 账号 (用于过滤)
            currency: 币种 (用于过滤)
            account_name: 户名 (用于过滤)
            
        Returns:
            pandas.DataFrame: 日度统计数据
        """
        # 通过时间分析器获取数据
        df = self.get_transactions_direct(start_date, end_date, account_number, currency, account_name)
        if df is None or df.empty:
            return pd.DataFrame()
        
        return self.analyzer_factory.time_analyzer.get_daily_stats(df)
    
    def get_top_merchants_direct(self, start_date=None, end_date=None, account_number=None, currency=None, account_name=None, n=10):
        """获取热门商户
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            account_number: 账号 (用于过滤)
            currency: 币种 (用于过滤)
            account_name: 户名 (用于过滤)
            n: 返回的热门商户数量
            
        Returns:
            dict: 包含按交易次数和金额排序的热门商户
        """
        # 通过商户分析器获取数据
        df = self.get_transactions_direct(start_date, end_date, account_number, currency, account_name)
        if df is None or df.empty:
            return {'by_count': pd.DataFrame(), 'by_amount': pd.DataFrame()}
        
        return self.analyzer_factory.merchant_analyzer.get_top_merchants(df, n)
    
    def separate_core_transactions(self, df, percentile_threshold=95, strategy='percentile', 
                                  min_transaction_count=10, fixed_threshold=None, recurring_only=False):
        """将交易分为核心交易和非常规交易
        
        Args:
            df: 交易数据DataFrame
            percentile_threshold: 金额百分位阈值
            strategy: 识别策略
            min_transaction_count: 最小交易数量
            fixed_threshold: 固定金额阈值
            recurring_only: 是否仅考虑重复交易
            
        Returns:
            tuple: (核心交易DataFrame, 非核心交易DataFrame)
        """
        # 通过异常分析器执行
        return self.analyzer_factory.anomaly_analyzer.separate_core_transactions(
            df, 
            percentile_threshold=percentile_threshold,
            strategy=strategy,
            min_transaction_count=min_transaction_count,
            fixed_threshold=fixed_threshold,
            recurring_only=recurring_only
        )
    
    def detect_outlier_transactions(self, df, method='iqr', threshold=1.5):
        """检测异常交易
        
        Args:
            df: 交易数据DataFrame
            method: 异常检测方法
            threshold: 异常检测阈值
            
        Returns:
            pandas.DataFrame: 带有异常标记的DataFrame
        """
        # 通过异常分析器执行
        return self.analyzer_factory.anomaly_analyzer.detect_outlier_transactions(df, method, threshold)
    
    def analyze_transaction_data_direct(self, start_date=None, end_date=None, account_number=None, currency=None, account_name=None):
        """综合分析交易数据
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            account_number: 账号 (用于过滤)
            currency: 币种 (用于过滤)
            account_name: 户名 (用于过滤)
            
        Returns:
            dict: 包含各种分析结果的字典
        """
        self.logger.info(f"开始直接分析交易数据: start_date={start_date}, end_date={end_date}, account_number={account_number}, currency={currency}, account_name={account_name}")
        
        try:
            # 通过分析器工厂执行所有分析
            results = self.analyzer_factory.analyze_all(
                start_date=start_date,
                end_date=end_date,
                account_number=account_number,
                currency=currency,
                account_name=account_name
            )
            
            # 兼容旧版API，重新组织结果结构
            return {
                'summary': results['summary'],
                'monthly_stats': results['time_analysis']['monthly_stats'],
                'yearly_stats': results['time_analysis']['yearly_stats'],
                'category_stats': results['category_analysis']['category_stats'],
                'weekly_stats': results['time_analysis']['weekly_stats'],
                'daily_stats': results['time_analysis']['daily_stats'],
                'top_merchants': results['merchant_analysis'],
                'transactions': results['transactions']
            }
        except Exception as e:
            self.logger.error(f"直接分析交易数据时出错: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            return {}
    
    def get_core_transaction_stats_direct(self, start_date=None, end_date=None, account_number=None, currency=None, account_name=None,
                                         percentile_threshold=95, strategy='percentile', 
                                         fixed_threshold=None, recurring_only=False):
        """获取核心交易统计
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            account_number: 账号 (用于过滤)
            currency: 币种 (用于过滤)
            account_name: 户名 (用于过滤)
            percentile_threshold: 核心交易百分位阈值
            strategy: 核心交易识别策略
            fixed_threshold: 固定金额阈值
            recurring_only: 是否仅考虑重复交易
            
        Returns:
            dict: 核心交易统计结果
        """
        df = self.get_transactions_direct(start_date, end_date, account_number, currency, account_name)
        if df is None or df.empty:
            return {
                'core_income': 0, 'core_expense': 0, 'core_net': 0,
                'core_transaction_count': 0, 'core_percentage': 0,
                'core_income_count': 0, 'core_expense_count': 0,
                'core_transactions': []
            }
        
        # 通过异常分析器获取核心交易统计
        return self.analyzer_factory.anomaly_analyzer.get_core_transaction_stats(
            df, 
            percentile_threshold=percentile_threshold,
            strategy=strategy,
            fixed_threshold=fixed_threshold,
            recurring_only=recurring_only
        )
    
    def get_outlier_stats_direct(self, start_date=None, end_date=None, account_number=None, currency=None, account_name=None,
                                method='iqr', threshold=1.5):
        """获取异常交易统计
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            account_number: 账号 (用于过滤)
            currency: 币种 (用于过滤)
            account_name: 户名 (用于过滤)
            method: 异常检测方法
            threshold: 异常检测阈值
            
        Returns:
            dict: 异常交易统计结果
        """
        df = self.get_transactions_direct(start_date, end_date, account_number, currency, account_name)
        if df is None or df.empty:
            return {
                'outlier_count': 0, 'outlier_income_count': 0, 'outlier_expense_count': 0,
                'outlier_income_amount': 0, 'outlier_expense_amount': 0,
                'outlier_percentage': 0, 'outliers': []
            }
        
        # 通过异常分析器获取异常交易统计
        return self.analyzer_factory.anomaly_analyzer.get_outlier_stats(df, method, threshold)
    
    def get_expense_distribution_direct(self, start_date=None, end_date=None, account_number=None, currency=None, account_name=None, use_transaction_type=True):
        """获取支出分布
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            account_number: 账号 (用于过滤)
            currency: 币种 (用于过滤)
            account_name: 户名 (用于过滤)
            use_transaction_type: 是否按交易类型分组
            
        Returns:
            list: 支出分布数据
        """
        df = self.get_transactions_direct(start_date, end_date, account_number, currency, account_name)
        if df is None or df.empty:
            return []
        
        # 通过类别分析器获取支出分布
        distribution = self.analyzer_factory.category_analyzer.get_expense_distribution(df, use_transaction_type)
        if distribution is None or distribution.empty:
            return []
        
        # 处理numpy数据类型
        results = []
        for record in distribution.to_dict('records'):
            for key, value in record.items():
                if isinstance(value, np.generic):
                    record[key] = value.item()
            results.append(record)
        
        return results
    
    def get_income_sources_direct(self, start_date=None, end_date=None, account_number=None, currency=None, account_name=None, use_transaction_type=True):
        """获取收入来源分布
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            account_number: 账号 (用于过滤)
            currency: 币种 (用于过滤)
            account_name: 户名 (用于过滤)
            use_transaction_type: 是否按交易类型分组
            
        Returns:
            list: 收入来源分布数据
        """
        df = self.get_transactions_direct(start_date, end_date, account_number, currency, account_name)
        if df is None or df.empty:
            return []
        
        # 通过类别分析器获取收入来源分布
        distribution = self.analyzer_factory.category_analyzer.get_income_sources(df, use_transaction_type)
        if distribution is None or distribution.empty:
            return []
        
        # 处理numpy数据类型
        results = []
        for record in distribution.to_dict('records'):
            for key, value in record.items():
                if isinstance(value, np.generic):
                    record[key] = value.item()
            results.append(record)
        
        return results
    
    def clear_cache(self):
        """清除所有缓存"""
        self.analyzer_factory.clear_cache()

# 使用示例
if __name__ == "__main__":
    from scripts.db.db_manager import DBManager
    db_manager = DBManager()
    analyzer = TransactionAnalyzer(db_manager)
    # 示例使用
    # results = analyzer.analyze_transaction_data_direct(start_date='2023-01-01', end_date='2023-12-31')
    # print(results)