import pandas as pd
import numpy as np
from .base_analyzer import BaseAnalyzer

class MerchantAnalyzer(BaseAnalyzer):
    """商户分析器，负责热门商户的统计分析"""
    
    def analyze(self, start_date=None, end_date=None, account_number=None, 
               currency=None, account_name=None, **kwargs):
        """执行商户分析
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            account_number: 账号 (用于过滤)
            currency: 币种 (用于过滤)
            account_name: 户名 (用于过滤)
            top_n: 返回的热门商户数量，默认为10
            
        Returns:
            dict: 包含商户分析结果的字典
        """
        try:
            # 获取参数
            top_n = kwargs.get('top_n', 10)
            
            # 获取分析所需的数据
            df = self.get_data(start_date, end_date, account_number, currency, account_name)
            if df is None or df.empty:
                return {
                    'by_count': [],
                    'by_amount': []
                }
            
            # 执行商户分析
            merchants_data = self.get_top_merchants(df, top_n)
            
            # 返回结果
            return {
                'by_count': self._format_results(merchants_data['by_count']),
                'by_amount': self._format_results(merchants_data['by_amount'])
            }
        except Exception as e:
            return self._handle_error("执行商户分析时出错", e)
    
    def get_top_merchants(self, df, n=10):
        """获取热门商户
        
        Args:
            df: 交易数据DataFrame
            n: 返回的热门商户数量
            
        Returns:
            dict: 包含按交易次数和金额排序的热门商户
        """
        try:
            if df is None or df.empty:
                self.logger.warning("无法获取热门商户，数据为空")
                return {'by_count': pd.DataFrame(), 'by_amount': pd.DataFrame()}
            
            # 筛选支出数据
            expense_df = df[df['amount'] < 0]
            if expense_df.empty:
                return {
                    'by_count': pd.DataFrame(columns=['merchant', 'total', 'count', 'average']),
                    'by_amount': pd.DataFrame(columns=['merchant', 'total', 'count', 'average'])
                }
            
            # 检查 counterparty 列是否存在
            if 'counterparty' not in expense_df.columns:
                self.logger.warning("支出数据中缺少 'counterparty' 列，无法分析商户。")
                return {
                    'by_count': pd.DataFrame(columns=['merchant', 'total', 'count', 'average']),
                    'by_amount': pd.DataFrame(columns=['merchant', 'total', 'count', 'average'])
                }
            
            # 按商户分组计算统计数据
            merchant_stats = expense_df.groupby('counterparty').agg({
                'amount': [
                    ('total', lambda x: abs(x.sum())),
                    ('count', 'count'),
                    ('average', lambda x: abs(x.mean()))
                ]
            })
            
            # 重置索引和设置列名
            merchant_stats = merchant_stats.reset_index()
            merchant_stats.columns = ['merchant', 'total', 'count', 'average']
            
            # 按交易次数和金额排序，各取前 n 个
            top_by_count = merchant_stats.sort_values('count', ascending=False).head(n)
            top_by_amount = merchant_stats.sort_values('total', ascending=False).head(n)
            
            return {'by_count': top_by_count, 'by_amount': top_by_amount}
        except Exception as e:
            self.logger.error(f"获取热门商户数据时出错: {e}")
            return {'by_count': pd.DataFrame(), 'by_amount': pd.DataFrame()} 