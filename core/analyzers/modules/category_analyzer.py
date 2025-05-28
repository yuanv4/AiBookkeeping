import pandas as pd
import numpy as np
from .base_analyzer import BaseAnalyzer

class CategoryAnalyzer(BaseAnalyzer):
    """类别分析器，负责交易类型、支出分布、收入来源的统计分析"""
    
    def analyze(self, start_date=None, end_date=None, account_number=None, 
               currency=None, account_name=None, **kwargs):
        """执行类别分析
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            account_number: 账号 (用于过滤)
            currency: 币种 (用于过滤)
            account_name: 户名 (用于过滤)
            
        Returns:
            dict: 包含类别分析结果的字典
        """
        try:
            # 获取分析所需的数据
            df = self.get_data(start_date, end_date, account_number, currency, account_name)
            if df is None or df.empty:
                return {
                    'category_stats': [],
                    'expense_distribution': [],
                    'income_sources': []
                }
            
            # 执行各类别分析
            category_stats = self.get_category_stats(df)
            expense_distribution = self.get_expense_distribution(df)
            income_sources = self.get_income_sources(df)
            
            # 返回结果
            return {
                'category_stats': self._format_results(category_stats),
                'expense_distribution': self._format_results(expense_distribution),
                'income_sources': self._format_results(income_sources)
            }
        except Exception as e:
            return self._handle_error("执行类别分析时出错", e)
    
    def get_category_stats(self, df):
        """获取按交易类型统计的支出数据
        
        Args:
            df: 交易数据DataFrame
            
        Returns:
            pandas.DataFrame: 交易类型统计数据
        """
        try:
            if df is None or df.empty:
                self.logger.warning("无法获取交易类型统计，数据为空")
                return pd.DataFrame(columns=['transaction_type', 'total', 'count', 'average', 'percentage'])
            
            # 筛选支出数据
            expense_df = df[df['amount'] < 0].copy()
            if expense_df.empty:
                return pd.DataFrame(columns=['transaction_type', 'total', 'count', 'average', 'percentage'])
            
            # 检查 transaction_type 列是否存在
            if 'transaction_type' not in expense_df.columns or expense_df['transaction_type'].isnull().all():
                self.logger.warning("支出数据中缺少有效的 'transaction_type' 列，无法按类型统计。")
                return pd.DataFrame(columns=['transaction_type', 'total', 'count', 'average', 'percentage'])
            
            # 填充缺失值
            expense_df.loc[:, 'transaction_type'] = expense_df['transaction_type'].fillna('未知类型')
            
            # 按交易类型分组计算统计数据
            category_stats = expense_df.groupby('transaction_type').agg(
                total=('amount', lambda x: abs(x.sum())),
                count=('amount', 'count'),
                average=('amount', lambda x: abs(x.mean()))
            ).reset_index()
            
            # 计算百分比
            total_expense = category_stats['total'].sum()
            category_stats['percentage'] = (category_stats['total'] / total_expense * 100) if total_expense > 0 else 0
            
            # 排序
            category_stats = category_stats.sort_values('total', ascending=False)
            
            return category_stats
        except Exception as e:
            self.logger.error(f"获取交易类型统计数据时出错: {e}")
            return pd.DataFrame(columns=['transaction_type', 'total', 'count', 'average', 'percentage'])
    
    def get_expense_distribution(self, df, use_transaction_type=True):
        """获取支出分布
        
        Args:
            df: 交易数据DataFrame
            use_transaction_type: 是否按交易类型分组
            
        Returns:
            pandas.DataFrame: 支出分布数据
        """
        try:
            if df is None or df.empty:
                self.logger.warning("无法获取支出分布，数据为空")
                return pd.DataFrame(columns=['group', 'total_amount', 'percentage'])
            
            # 筛选支出数据
            expense_df = df[df['amount'] < 0].copy()
            if expense_df.empty:
                return pd.DataFrame(columns=['group', 'total_amount', 'percentage'])
            
            # 确定分组列
            if use_transaction_type and 'transaction_type' in expense_df.columns:
                group_by_col = 'transaction_type'
                expense_df.loc[:, 'group'] = expense_df[group_by_col].fillna('未知类型')
            else:
                self.logger.warning("无法按类型进行支出分布，将返回空结果。")
                return pd.DataFrame(columns=['group', 'total_amount', 'percentage'])
            
            # 计算每个组的总金额
            distribution = expense_df.groupby('group')['amount'].sum().abs().reset_index(name='total_amount')
            
            # 计算百分比
            total_overall_expense = distribution['total_amount'].sum()
            if total_overall_expense == 0:
                distribution['percentage'] = 0.0
            else:
                distribution['percentage'] = (distribution['total_amount'] / total_overall_expense * 100).round(2)
            
            # 排序
            distribution = distribution.sort_values('total_amount', ascending=False)
            
            return distribution
        except Exception as e:
            self.logger.error(f"获取支出分布数据时出错: {e}")
            return pd.DataFrame(columns=['group', 'total_amount', 'percentage'])
    
    def get_income_sources(self, df, use_transaction_type=True):
        """获取收入来源分布
        
        Args:
            df: 交易数据DataFrame
            use_transaction_type: 是否按交易类型分组
            
        Returns:
            pandas.DataFrame: 收入来源分布数据
        """
        try:
            if df is None or df.empty:
                self.logger.warning("无法获取收入来源，数据为空")
                return pd.DataFrame(columns=['group', 'total_amount', 'percentage'])
            
            # 筛选收入数据
            income_df = df[df['amount'] > 0].copy()
            if income_df.empty:
                return pd.DataFrame(columns=['group', 'total_amount', 'percentage'])
            
            # 确定分组列
            if use_transaction_type and 'transaction_type' in income_df.columns:
                group_by_col = 'transaction_type'
                income_df.loc[:, 'group'] = income_df[group_by_col].fillna('未知类型')
            else:
                self.logger.warning("无法按类型进行收入来源分析，将返回空结果。")
                return pd.DataFrame(columns=['group', 'total_amount', 'percentage'])
            
            # 计算每个组的总金额
            distribution = income_df.groupby('group')['amount'].sum().reset_index(name='total_amount')
            
            # 计算百分比
            total_overall_income = distribution['total_amount'].sum()
            if total_overall_income == 0:
                distribution['percentage'] = 0.0
            else:
                distribution['percentage'] = (distribution['total_amount'] / total_overall_income * 100).round(2)
            
            # 排序
            distribution = distribution.sort_values('total_amount', ascending=False)
            
            return distribution
        except Exception as e:
            self.logger.error(f"获取收入来源数据时出错: {e}")
            return pd.DataFrame(columns=['group', 'total_amount', 'percentage']) 