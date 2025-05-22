import pandas as pd
import numpy as np
from .base_analyzer import BaseAnalyzer

class TimeAnalyzer(BaseAnalyzer):
    """时间维度分析器，负责日、周、月、年的统计分析"""
    
    def analyze(self, start_date=None, end_date=None, account_number=None, 
               currency=None, account_name=None, **kwargs):
        """执行时间维度分析
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            account_number: 账号 (用于过滤)
            currency: 币种 (用于过滤)
            account_name: 户名 (用于过滤)
            
        Returns:
            dict: 包含各时间维度分析结果的字典
        """
        try:
            # 获取分析所需的数据
            df = self.get_data(start_date, end_date, account_number, currency, account_name)
            if df is None or df.empty:
                return {
                    'monthly_stats': [],
                    'yearly_stats': [],
                    'weekly_stats': [],
                    'daily_stats': []
                }
            
            # 执行各维度分析
            monthly_stats = self.get_monthly_stats(df)
            yearly_stats = self.get_yearly_stats(df)
            weekly_stats = self.get_weekly_stats(df)
            daily_stats = self.get_daily_stats(df)
            
            # 返回结果
            return {
                'monthly_stats': self._format_results(monthly_stats),
                'yearly_stats': self._format_results(yearly_stats),
                'weekly_stats': self._format_results(weekly_stats),
                'daily_stats': self._format_results(daily_stats)
            }
        except Exception as e:
            return self._handle_error("执行时间维度分析时出错", e)
    
    def get_monthly_stats(self, df):
        """获取月度统计数据
        
        Args:
            df: 交易数据DataFrame
            
        Returns:
            pandas.DataFrame: 月度统计数据
        """
        try:
            if df is None or df.empty:
                self.logger.warning("无法获取月度统计，数据为空")
                return pd.DataFrame()
            
            # 按年月分组计算统计数据
            monthly_data = df.groupby(['year', 'month']).agg({
                'amount': [
                    ('income', lambda x: x[x > 0].sum()),
                    ('expense', lambda x: abs(x[x < 0].sum())),
                    ('net', 'sum')
                ]
            })
            
            # 重置索引和设置列名
            monthly_data = monthly_data.reset_index()
            monthly_data.columns = ['year', 'month', 'income', 'expense', 'net']
            
            # 添加月份标签
            monthly_data['month_label'] = monthly_data.apply(
                lambda row: f"{int(row['year'])}-{int(row['month']):02d}", axis=1
            )
            
            # 排序
            monthly_data = monthly_data.sort_values(['year', 'month'])
            
            return monthly_data
        except Exception as e:
            self.logger.error(f"获取月度统计数据时出错: {e}")
            return pd.DataFrame()
    
    def get_yearly_stats(self, df):
        """获取年度统计数据
        
        Args:
            df: 交易数据DataFrame
            
        Returns:
            pandas.DataFrame: 年度统计数据
        """
        try:
            if df is None or df.empty:
                self.logger.warning("无法获取年度统计，数据为空")
                return pd.DataFrame()
            
            # 按年分组计算统计数据
            yearly_data = df.groupby(['year']).agg({
                'amount': [
                    ('income', lambda x: x[x > 0].sum()),
                    ('expense', lambda x: abs(x[x < 0].sum())),
                    ('net', 'sum')
                ]
            })
            
            # 重置索引和设置列名
            yearly_data = yearly_data.reset_index()
            yearly_data.columns = ['year', 'income', 'expense', 'net']
            
            # 添加年份标签
            yearly_data['year_label'] = yearly_data['year'].astype(str)
            
            # 排序
            yearly_data = yearly_data.sort_values(['year'])
            
            return yearly_data
        except Exception as e:
            self.logger.error(f"获取年度统计数据时出错: {e}")
            return pd.DataFrame()
    
    def get_weekly_stats(self, df):
        """获取周度统计数据
        
        Args:
            df: 交易数据DataFrame
            
        Returns:
            pandas.DataFrame: 周度统计数据
        """
        try:
            if df is None or df.empty:
                self.logger.warning("无法获取周度统计，数据为空")
                return pd.DataFrame()
            
            # 筛选支出数据
            expense_df = df[df['amount'] < 0]
            if expense_df.empty:
                return pd.DataFrame(columns=['weekday', 'total', 'count', 'average', 'weekday_name'])
            
            # 按周几分组计算统计数据
            weekday_stats = expense_df.groupby('weekday').agg({
                'amount': [
                    ('total', lambda x: abs(x.sum())),
                    ('count', 'count'),
                    ('average', lambda x: abs(x.mean()))
                ]
            })
            
            # 重置索引和设置列名
            weekday_stats = weekday_stats.reset_index()
            weekday_stats.columns = ['weekday', 'total', 'count', 'average']
            
            # 添加周几名称
            weekday_names = {0: '周一', 1: '周二', 2: '周三', 3: '周四', 4: '周五', 5: '周六', 6: '周日'}
            weekday_stats['weekday_name'] = weekday_stats['weekday'].map(weekday_names)
            
            # 排序
            weekday_stats = weekday_stats.sort_values('weekday')
            
            return weekday_stats
        except Exception as e:
            self.logger.error(f"获取周度统计数据时出错: {e}")
            return pd.DataFrame()
    
    def get_daily_stats(self, df):
        """获取日度统计数据
        
        Args:
            df: 交易数据DataFrame
            
        Returns:
            pandas.DataFrame: 日度统计数据
        """
        try:
            if df is None or df.empty:
                self.logger.warning("无法获取日度统计，数据为空")
                return pd.DataFrame()
            
            # 筛选支出数据
            expense_df = df[df['amount'] < 0]
            if expense_df.empty:
                return pd.DataFrame(columns=['date', 'total', 'count'])
            
            # 按交易日期分组计算统计数据
            daily_stats = expense_df.groupby('transaction_date').agg({
                'amount': [
                    ('total', lambda x: abs(x.sum())),
                    ('count', 'count')
                ]
            })
            
            # 重置索引和设置列名
            daily_stats = daily_stats.reset_index()
            daily_stats.columns = ['date', 'total', 'count']
            
            # 格式化日期
            daily_stats['date'] = daily_stats['date'].dt.strftime('%Y-%m-%d')
            
            # 排序
            daily_stats = daily_stats.sort_values('date')
            
            return daily_stats
        except Exception as e:
            self.logger.error(f"获取日度统计数据时出错: {e}")
            return pd.DataFrame() 