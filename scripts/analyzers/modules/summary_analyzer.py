import pandas as pd
import numpy as np
from .base_analyzer import BaseAnalyzer

class SummaryAnalyzer(BaseAnalyzer):
    """摘要统计器，负责提供交易摘要统计信息"""
    
    def analyze(self, start_date=None, end_date=None, account_number=None, 
               currency=None, account_name=None, **kwargs):
        """执行摘要分析
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            account_number: 账号 (用于过滤)
            currency: 币种 (用于过滤)
            account_name: 户名 (用于过滤)
            
        Returns:
            dict: 交易摘要统计信息
        """
        try:
            # 获取分析所需的数据
            df = self.get_data(start_date, end_date, account_number, currency, account_name)
            if df is None or df.empty:
                return self._get_empty_summary(start_date, end_date)
            
            # 计算交易摘要
            summary = self.get_summary(df, account_number)
            
            # 返回结果
            return summary
        except Exception as e:
            return self._handle_error("执行摘要分析时出错", e)
    
    def get_summary(self, df, account_number=None):
        """获取交易摘要统计
        
        Args:
            df: 交易数据DataFrame
            account_number: 账号 (用于提取余额)
            
        Returns:
            dict: 摘要统计信息
        """
        try:
            if df is None or df.empty:
                self.logger.warning("无法获取摘要，数据为空")
                return self._get_empty_summary(None, None)
            
            # 计算基本统计信息
            summary = {}
            summary['start_date'] = df['transaction_date'].min()
            summary['end_date'] = df['transaction_date'].max()
            summary['total_transactions'] = len(df)
            
            # 收入、支出和净流量
            summary['total_income'] = df[df['amount'] > 0]['amount'].sum()
            summary['total_expense'] = abs(df[df['amount'] < 0]['amount'].sum())
            summary['net_flow'] = summary['total_income'] - summary['total_expense']
            
            # 日期范围
            if pd.notna(summary['start_date']) and pd.notna(summary['end_date']):
                # 确保日期是 datetime 对象
                start_date_val = pd.to_datetime(summary['start_date'])
                end_date_val = pd.to_datetime(summary['end_date'])
                summary['days_count'] = (end_date_val - start_date_val).days + 1  # 加1天以包含首尾
            else:
                summary['days_count'] = 0
            
            # 日均支出
            summary['avg_daily_expense'] = summary['total_expense'] / summary['days_count'] if summary['days_count'] > 0 else 0
            
            # 转账统计
            transfer_df_out = df[(df['transaction_type'].astype(str).str.contains('转账', case=False, na=False)) & (df['amount'] < 0)]
            summary['transfer_amount_out'] = abs(transfer_df_out['amount'].sum())
            summary['transfer_count_out'] = len(transfer_df_out)
            
            # 最新余额
            latest_balance_sum = 0
            if account_number and not df.empty:
                # 按日期和ID排序，获取最新的一条记录
                latest_transaction_for_account = df[df['account_number'] == account_number].sort_values(
                    by=['transaction_date', 'id'], ascending=[False, False]
                ).head(1)
                
                if not latest_transaction_for_account.empty and pd.notna(latest_transaction_for_account['balance'].iloc[0]):
                    latest_balance_sum = latest_transaction_for_account['balance'].iloc[0]
            elif not df.empty:
                # 如果没有指定账户，则获取每个账户的最新余额并求和
                if 'balance' in df.columns:
                    latest_balances_per_account = df.sort_values('transaction_date').groupby('account_number').last()['balance']
                    latest_balance_sum = latest_balances_per_account.sum()
            
            summary['latest_balance_sum'] = latest_balance_sum
            
            # 计算剩余资金可维持天数
            summary['remaining_funds_coverage_days'] = (
                latest_balance_sum / summary['avg_daily_expense'] 
                if summary['avg_daily_expense'] > 0 
                else float('inf') if latest_balance_sum > 0 
                else 0
            )
            
            # 确保所有数值都是 Python 原生类型，以便 JSON 序列化
            for key, value in summary.items():
                if isinstance(value, (np.generic, pd.Timestamp)):
                    if pd.isna(value):
                        summary[key] = None  # 将 NaT 或 NaN 转换为 None
                    elif isinstance(value, pd.Timestamp):
                        summary[key] = value.strftime('%Y-%m-%d')  # 格式化日期
                    else:
                        summary[key] = value.item()  # 转换 numpy 类型为 Python 原生类型
                elif isinstance(value, float) and key != 'remaining_funds_coverage_days':
                    summary[key] = round(value, 2)  # 四舍五入保留两位小数，但对于 remaining_funds_coverage_days 保持原值
            
            return summary
        except Exception as e:
            self.logger.error(f"计算交易摘要时出错: {e}", exc_info=True)
            return self._get_empty_summary(None, None)
    
    def _get_empty_summary(self, start_date, end_date):
        """获取空的摘要统计信息
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            dict: 空的摘要统计信息
        """
        return {
            'start_date': start_date,
            'end_date': end_date,
            'total_transactions': 0,
            'total_income': 0,
            'total_expense': 0,
            'net_flow': 0,
            'avg_daily_expense': 0,
            'days_count': 0,
            'transfer_amount_out': 0,
            'transfer_count_out': 0,
            'latest_balance_sum': 0,
            'remaining_funds_coverage_days': 0
        } 