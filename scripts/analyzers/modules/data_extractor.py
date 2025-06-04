import pandas as pd
import numpy as np
import logging
from datetime import datetime

class DataExtractor:
    """数据提取器，负责从数据库获取原始交易数据并进行基础处理"""
    
    def __init__(self, db_facade):
        """初始化数据提取器
        
        Args:
            db_facade: DBFacade实例，用于数据库操作
        """
        if db_facade is None:
            raise ValueError("DBManager instance must be provided to DataExtractor")
        self.db_facade = db_facade
        self.logger = logging.getLogger(self.__class__.__name__)
        self.cached_transactions = {}  # 用于缓存最近的查询结果
        
    def get_transactions(self, start_date=None, end_date=None, account_number=None, 
                         currency=None, account_name=None, use_cache=True):
        """从数据库获取交易数据并转换为DataFrame
        
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
        # 生成缓存键
        cache_key = f"{start_date}_{end_date}_{account_number}_{currency}_{account_name}"
        
        # 如果启用缓存且缓存中存在数据，直接返回
        if use_cache and cache_key in self.cached_transactions:
            self.logger.info(f"Using cached transaction data for key: {cache_key}")
            return self.cached_transactions[cache_key].copy()
            
        self.logger.info(
            f"Fetching transactions: start_date={start_date}, end_date={end_date}, "
            f"account_number={account_number}, currency={currency}, account_name={account_name}"
        )
        
        # 从数据库获取交易数据
        transactions = self.db_facade.get_transactions(
            account_number_filter=account_number, 
            start_date=start_date,
            end_date=end_date,
            currency_filter=currency,
            account_name_filter=account_name,
            limit=1000000,  # 获取足够多的数据进行分析
            offset=0
        )
        
        if not transactions:
            self.logger.warning("No transactions found for fetching.")
            return pd.DataFrame()
        
        # 转换为DataFrame
        df = pd.DataFrame(transactions)
        
        # 标准化日期列
        if 'transaction_date' in df.columns:
            try:
                df['transaction_date'] = pd.to_datetime(df['transaction_date'], errors='coerce')
                # 移除转换后仍为NaT的行，这些通常是无效日期
                df.dropna(subset=['transaction_date'], inplace=True)
            except Exception as e:
                self.logger.error(f"Error converting transaction_date to datetime: {e}")
                return pd.DataFrame()
        else:
            self.logger.warning("transaction_date column not found in fetched data.")
            return pd.DataFrame()
        
        # 添加年、月、周几等时间维度列，方便后续分析
        df['year'] = df['transaction_date'].dt.year
        df['month'] = df['transaction_date'].dt.month
        df['weekday'] = df['transaction_date'].dt.dayofweek
        
        # 缓存结果
        if use_cache:
            self.cached_transactions[cache_key] = df.copy()
            
        self.logger.info(f"Successfully fetched and processed {len(df)} transactions.")
        return df
    
    def clear_cache(self):
        """清除交易数据缓存"""
        self.cached_transactions = {}
        self.logger.info("Transaction cache cleared.")
        
    def get_accounts(self):
        """获取账户信息"""
        accounts = self.db_facade.get_accounts()
        if accounts:
            return pd.DataFrame(accounts)
        return pd.DataFrame()