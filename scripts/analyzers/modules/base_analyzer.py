import pandas as pd
import numpy as np
import logging
from abc import ABC, abstractmethod

class BaseAnalyzer(ABC):
    """分析器基类，定义通用接口和方法"""
    
    def __init__(self, data_extractor):
        """初始化分析器
        
        Args:
            data_extractor: DataExtractor实例，用于获取数据
        """
        if data_extractor is None:
            raise ValueError("DataExtractor instance must be provided to BaseAnalyzer")
        self.data_extractor = data_extractor
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def get_data(self, start_date=None, end_date=None, account_number=None, 
                currency=None, account_name=None, use_cache=True):
        """获取分析所需的数据
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            account_number: 账号 (用于过滤)
            currency: 币种 (用于过滤)
            account_name: 户名 (用于过滤)
            use_cache: 是否使用缓存
            
        Returns:
            pandas.DataFrame: 包含交易数据的DataFrame
        """
        return self.data_extractor.get_transactions(
            start_date=start_date,
            end_date=end_date,
            account_number=account_number,
            currency=currency,
            account_name=account_name,
            use_cache=use_cache
        )
    
    @abstractmethod
    def analyze(self, start_date=None, end_date=None, account_number=None, 
               currency=None, account_name=None, **kwargs):
        """执行分析
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            account_number: 账号 (用于过滤)
            currency: 币种 (用于过滤)
            account_name: 户名 (用于过滤)
            **kwargs: 其他参数
            
        Returns:
            dict/DataFrame: 分析结果
        """
        pass
    
    def _format_results(self, df):
        """将DataFrame格式化为JSON可序列化的字典列表
        
        Args:
            df: pandas DataFrame
            
        Returns:
            list: 字典列表
        """
        if df is None or df.empty:
            return []
            
        # 确保所有列都是JSON可序列化的
        df_copy = df.copy()
        
        # 处理日期列
        date_columns = df_copy.select_dtypes(include=['datetime64']).columns
        for col in date_columns:
            df_copy[col] = df_copy[col].dt.strftime('%Y-%m-%d')
        
        # 转换为记录列表
        records = df_copy.to_dict('records')
        
        # 处理numpy数据类型
        for record in records:
            for key, value in record.items():
                if isinstance(value, (np.generic)):
                    if pd.isna(value):
                        record[key] = None
                    else:
                        record[key] = value.item()  # 转换为Python原生类型
                        
        return records
    
    def _handle_error(self, error_message, error=None):
        """处理错误，记录日志并返回空结果
        
        Args:
            error_message: 错误信息
            error: 异常对象
            
        Returns:
            dict/list: 空结果
        """
        if error:
            self.logger.error(f"{error_message}: {error}", exc_info=True)
        else:
            self.logger.error(error_message)
        
        # 默认返回空字典，子类可以重写此方法返回特定的空结果结构
        return {} 