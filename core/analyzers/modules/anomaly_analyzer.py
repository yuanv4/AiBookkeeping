import pandas as pd
import numpy as np
from .base_analyzer import BaseAnalyzer

class AnomalyAnalyzer(BaseAnalyzer):
    """异常分析器，负责核心交易和异常交易的分析"""
    
    def analyze(self, start_date=None, end_date=None, account_number=None, 
               currency=None, account_name=None, **kwargs):
        """执行异常分析
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            account_number: 账号 (用于过滤)
            currency: 币种 (用于过滤)
            account_name: 户名 (用于过滤)
            percentile_threshold: 核心交易百分位阈值，默认为95
            strategy: 核心交易识别策略，默认为'percentile'
            fixed_threshold: 固定金额阈值
            recurring_only: 是否仅考虑重复交易
            outlier_method: 异常值检测方法，默认为'iqr'
            outlier_threshold: 异常值检测阈值，默认为1.5
            
        Returns:
            dict: 包含异常分析结果的字典
        """
        try:
            # 获取参数
            percentile_threshold = kwargs.get('percentile_threshold', 95)
            strategy = kwargs.get('strategy', 'percentile')
            fixed_threshold = kwargs.get('fixed_threshold', None)
            recurring_only = kwargs.get('recurring_only', False)
            outlier_method = kwargs.get('outlier_method', 'iqr')
            outlier_threshold = kwargs.get('outlier_threshold', 1.5)
            
            # 获取分析所需的数据
            df = self.get_data(start_date, end_date, account_number, currency, account_name)
            if df is None or df.empty:
                return {
                    'core_transactions': {},
                    'outlier_stats': {}
                }
            
            # 执行核心交易和异常交易分析
            core_transactions = self.get_core_transaction_stats(
                df, 
                percentile_threshold=percentile_threshold,
                strategy=strategy,
                fixed_threshold=fixed_threshold,
                recurring_only=recurring_only
            )
            
            outlier_stats = self.get_outlier_stats(
                df, 
                method=outlier_method, 
                threshold=outlier_threshold
            )
            
            # 返回结果
            return {
                'core_transactions': core_transactions,
                'outlier_stats': outlier_stats
            }
        except Exception as e:
            return self._handle_error("执行异常分析时出错", e)
    
    def get_core_transaction_stats(self, df, percentile_threshold=95, strategy='percentile', 
                                 fixed_threshold=None, recurring_only=False):
        """获取核心交易统计
        
        Args:
            df: 交易数据DataFrame
            percentile_threshold: 百分位阈值
            strategy: 识别策略
            fixed_threshold: 固定阈值
            recurring_only: 是否仅考虑重复交易
            
        Returns:
            dict: 核心交易统计结果
        """
        try:
            if df is None or df.empty:
                self.logger.warning("无法获取核心交易统计，数据为空")
                return {
                    'core_income': 0, 'core_expense': 0, 'core_net': 0,
                    'core_transaction_count': 0, 'core_percentage': 0,
                    'core_income_count': 0, 'core_expense_count': 0,
                    'core_transactions': []
                }
            
            # 分离核心交易
            core_trans, _ = self.separate_core_transactions(
                df, 
                percentile_threshold=percentile_threshold,
                strategy=strategy,
                fixed_threshold=fixed_threshold,
                recurring_only=recurring_only
            )
            
            if core_trans.empty:
                return {
                    'core_income': 0, 'core_expense': 0, 'core_net': 0,
                    'core_transaction_count': 0, 'core_percentage': 0,
                    'core_income_count': 0, 'core_expense_count': 0,
                    'core_transactions': []
                }
            
            # 计算核心交易统计
            core_income_df = core_trans[core_trans['amount'] > 0]
            core_expense_df = core_trans[core_trans['amount'] < 0]
            
            core_income = core_income_df['amount'].sum()
            core_expense = core_expense_df['amount'].sum()
            
            # 格式化日期列
            core_trans_copy = core_trans.copy()
            if 'transaction_date' in core_trans_copy.columns:
                core_trans_copy.loc[:, 'transaction_date'] = pd.to_datetime(
                    core_trans_copy['transaction_date']
                ).dt.strftime('%Y-%m-%d')
            
            # 处理numpy数据类型
            core_transactions_list = self._format_results(core_trans_copy)
            
            return {
                'core_income': core_income.item() if pd.notna(core_income) else 0,
                'core_expense': core_expense.item() if pd.notna(core_expense) else 0,
                'core_net': (core_income + core_expense).item() if pd.notna(core_income + core_expense) else 0,
                'core_transaction_count': len(core_trans),
                'core_percentage': (len(core_trans) / len(df) * 100) if not df.empty else 0,
                'core_income_count': len(core_income_df),
                'core_expense_count': len(core_expense_df),
                'core_transactions': core_transactions_list
            }
        except Exception as e:
            self.logger.error(f"获取核心交易统计时出错: {e}")
            return {
                'core_income': 0, 'core_expense': 0, 'core_net': 0,
                'core_transaction_count': 0, 'core_percentage': 0,
                'core_income_count': 0, 'core_expense_count': 0,
                'core_transactions': []
            }
    
    def get_outlier_stats(self, df, method='iqr', threshold=1.5):
        """获取异常交易统计
        
        Args:
            df: 交易数据DataFrame
            method: 异常检测方法
            threshold: 异常检测阈值
            
        Returns:
            dict: 异常交易统计结果
        """
        try:
            if df is None or df.empty:
                return {
                    'outlier_count': 0, 'outlier_income_count': 0, 'outlier_expense_count': 0,
                    'outlier_income_amount': 0, 'outlier_expense_amount': 0,
                    'outlier_percentage': 0, 'outliers': []
                }
            
            # 检测异常交易
            result_df_with_outliers = self.detect_outlier_transactions(df, method, threshold)
            
            if result_df_with_outliers.empty or not result_df_with_outliers['是否异常'].any():
                return {
                    'outlier_count': 0, 'outlier_income_count': 0, 'outlier_expense_count': 0,
                    'outlier_income_amount': 0, 'outlier_expense_amount': 0,
                    'outlier_percentage': 0, 'outliers': []
                }
            
            # 筛选异常交易
            outliers_df = result_df_with_outliers[result_df_with_outliers['是否异常']]
            outliers_df = outliers_df.sort_values('异常分数', ascending=False)
            
            # 分别统计收入和支出的异常交易
            outlier_income_df = outliers_df[outliers_df['amount'] > 0]
            outlier_expense_df = outliers_df[outliers_df['amount'] < 0]
            
            # 取前10个异常交易
            outliers_head_df = outliers_df.head(10).copy()
            if 'transaction_date' in outliers_head_df.columns:
                outliers_head_df['transaction_date'] = outliers_head_df['transaction_date'].dt.strftime('%Y-%m-%d')
            
            # 处理numpy数据类型
            outliers_list = self._format_results(outliers_head_df)
            
            return {
                'outlier_count': len(outliers_df),
                'outlier_income_count': len(outlier_income_df),
                'outlier_expense_count': len(outlier_expense_df),
                'outlier_income_amount': outlier_income_df['amount'].sum() if not outlier_income_df.empty else 0,
                'outlier_expense_amount': outlier_expense_df['amount'].sum() if not outlier_expense_df.empty else 0,
                'outlier_percentage': len(outliers_df) / len(df) * 100 if not df.empty else 0,
                'outliers': outliers_list
            }
        except Exception as e:
            self.logger.error(f"获取异常交易统计时出错: {e}")
            return {
                'outlier_count': 0, 'outlier_income_count': 0, 'outlier_expense_count': 0,
                'outlier_income_amount': 0, 'outlier_expense_amount': 0,
                'outlier_percentage': 0, 'outliers': []
            }
    
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
        if df is None or df.empty:
            return pd.DataFrame(), pd.DataFrame()
        
        if len(df) < min_transaction_count:
            self.logger.warning(f"交易数量({len(df)})不足，无法可靠地识别核心交易，返回所有交易作为核心交易")
            return df.copy(), pd.DataFrame()
        
        # 分别处理收入和支出
        income_df = df[df['amount'] > 0]
        expense_df = df[df['amount'] < 0]
        
        # 识别核心收入
        if len(income_df) < min_transaction_count / 2:
            income_is_core = pd.Series(True, index=income_df.index) if not income_df.empty else pd.Series(dtype=bool)
        else:
            income_is_core = self._identify_core_transactions(
                income_df, 
                is_income=True,
                percentile_threshold=percentile_threshold,
                strategy=strategy,
                fixed_threshold=fixed_threshold[0] if fixed_threshold else None,
                recurring_only=recurring_only
            )
        
        # 识别核心支出
        if len(expense_df) < min_transaction_count / 2:
            expense_is_core = pd.Series(True, index=expense_df.index) if not expense_df.empty else pd.Series(dtype=bool)
        else:
            expense_is_core = self._identify_core_transactions(
                expense_df,
                is_income=False,
                percentile_threshold=percentile_threshold,
                strategy=strategy,
                fixed_threshold=fixed_threshold[1] if fixed_threshold else None,
                recurring_only=recurring_only
            )
        
        # 合并核心标记
        is_core = pd.Series(False, index=df.index)
        if not income_is_core.empty:
            is_core.loc[income_is_core.index] = income_is_core
        if not expense_is_core.empty:
            is_core.loc[expense_is_core.index] = expense_is_core
        
        # 分离核心交易和非核心交易
        core_transactions = df[is_core]
        non_core_transactions = df[~is_core]
        
        self.logger.info(f"核心交易识别完成: 总交易={len(df)}, 核心交易={len(core_transactions)}, 非核心交易={len(non_core_transactions)}")
        return core_transactions, non_core_transactions
    
    def _identify_core_transactions(self, df, is_income=True, percentile_threshold=95, strategy='percentile',
                                   fixed_threshold=None, recurring_only=False):
        """识别核心交易
        
        Args:
            df: 交易数据DataFrame
            is_income: 是否是收入
            percentile_threshold: 百分位阈值
            strategy: 识别策略
            fixed_threshold: 固定金额阈值
            recurring_only: 是否仅考虑重复交易
            
        Returns:
            pandas.Series: 布尔值Series，标记是否为核心交易
        """
        if df.empty:
            return pd.Series(dtype=bool)
        
        # 获取金额绝对值
        amounts = df['amount'].abs()
        
        # 处理recurring_only
        if recurring_only:
            self.logger.warning("'recurring_only' 功能受影响，因 'category' 列已移除。当前实现可能不准确。")
            if 'counterparty' in df.columns and 'transaction_type' in df.columns:
                # 基于对手方和交易类型识别重复交易
                df_copy = df.copy()
                df_copy['recurring_key'] = df_copy['counterparty'].fillna('') + "_" + df_copy['transaction_type'].fillna('')
                key_counts = df_copy['recurring_key'].value_counts()
                recurring_keys = key_counts[key_counts > 1].index
                is_recurring = df_copy['recurring_key'].isin(recurring_keys)
            elif 'counterparty' in df.columns:
                # 仅基于对手方识别重复交易
                repeat_counter = df['counterparty'].value_counts()
                repeat_merchants = set(repeat_counter[repeat_counter > 1].index)
                is_recurring = df['counterparty'].isin(repeat_merchants)
            else:
                self.logger.warning("缺少 'counterparty' 或 'transaction_type'，无法应用 'recurring_only' 筛选。")
                is_recurring = pd.Series(True, index=df.index)
        else:
            is_recurring = pd.Series(True, index=df.index)
        
        # 根据策略识别核心交易
        if strategy == 'percentile':
            threshold = amounts.quantile(percentile_threshold/100)
            is_core = (amounts <= threshold) & is_recurring
        elif strategy == 'fixed':
            if fixed_threshold is None:
                fixed_threshold = 10000 if is_income else 5000
            is_core = (amounts <= fixed_threshold) & is_recurring
        elif strategy == 'iqr':
            Q1 = amounts.quantile(0.25)
            Q3 = amounts.quantile(0.75)
            IQR = Q3 - Q1
            upper_bound = Q3 + 1.5 * IQR
            is_core = (amounts <= upper_bound) & is_recurring
        elif strategy == 'zmm':
            median = amounts.median()
            deviations = abs(amounts - median)
            mad = deviations.median()
            robust_z = 0.6745 * deviations / mad if mad > 0 else pd.Series(0, index=deviations.index)
            is_core = (robust_z <= 3.5) & is_recurring
        elif strategy == 'combo':
            p_threshold = amounts.quantile(percentile_threshold/100)
            is_core_p = amounts <= p_threshold
            Q1 = amounts.quantile(0.25)
            Q3 = amounts.quantile(0.75)
            IQR = Q3 - Q1
            upper_bound = Q3 + 1.5 * IQR
            is_core_iqr = amounts <= upper_bound
            is_core = (is_core_p & is_core_iqr) & is_recurring
        else:
            # 默认使用百分位策略
            threshold = amounts.quantile(percentile_threshold/100)
            is_core = (amounts <= threshold) & is_recurring
            
        return is_core
    
    def detect_outlier_transactions(self, df, method='iqr', threshold=1.5):
        """检测异常交易
        
        Args:
            df: 交易数据DataFrame
            method: 异常检测方法
            threshold: 异常检测阈值
            
        Returns:
            pandas.DataFrame: 带有异常标记的DataFrame
        """
        if df is None or df.empty:
            return pd.DataFrame()
            
        # 创建结果DataFrame
        result_df = df.copy()
        result_df['是否异常'] = False
        result_df['异常类型'] = ''
        result_df['异常分数'] = 0.0
        
        # 分别处理收入和支出
        for trans_type, condition_func in [('收入', lambda d: d['amount'] > 0), ('支出', lambda d: d['amount'] < 0)]:
            condition = condition_func(df)
            type_df = df[condition]
            if type_df.empty:
                continue
                
            amounts = type_df['amount'].abs()
            
            # 使用IQR方法检测异常
            if method == 'iqr':
                Q1 = amounts.quantile(0.25)
                Q3 = amounts.quantile(0.75)
                IQR = Q3 - Q1
                if IQR == 0: 
                    continue  # 避免除零错误
                    
                lower_bound = Q1 - threshold * IQR
                upper_bound = Q3 + threshold * IQR
                
                outliers_indices = type_df[(amounts < lower_bound) | (amounts > upper_bound)].index
                for idx in outliers_indices:
                    amount_val = amounts.loc[idx]
                    score = (amount_val - upper_bound) / IQR if amount_val > upper_bound else (lower_bound - amount_val) / IQR
                    result_df.loc[idx, '异常分数'] = score
                    result_df.loc[idx, '异常类型'] = f'异常{trans_type}'
                    result_df.loc[idx, '是否异常'] = True
            
            # 使用Z-score方法检测异常
            elif method == 'zscore':
                mean = amounts.mean()
                std = amounts.std()
                if std == 0: 
                    continue  # 避免除零错误
                    
                z_scores = (amounts - mean) / std
                outliers_indices = type_df[abs(z_scores) > threshold].index
                
                for idx in outliers_indices:
                    result_df.loc[idx, '异常分数'] = abs(z_scores.loc[idx])
                    result_df.loc[idx, '异常类型'] = f'异常{trans_type}'
                    result_df.loc[idx, '是否异常'] = True
        
        return result_df 