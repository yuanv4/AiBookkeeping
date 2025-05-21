import pandas as pd
import numpy as np
import os
import re
import jieba
from collections import defaultdict, Counter
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
import seaborn as sns
from datetime import datetime, timedelta
import calendar
import json
import logging
import sys

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

class TransactionAnalyzer:
    def __init__(self, db_manager=None):
        """初始化交易分析器
        
        Args:
            db_manager: DBManager实例，如果为None则创建新实例
        """
        self.categories = {
            '餐饮': ['餐', '饮', '食', '厅', '粉', '小吃', '肉', '面', '饭', '咖啡', '外卖', '美团', '肯德基', '金拱门', '瑞幸', '喜茶'],
            '交通': ['地铁', '公交', '出行', '滴滴', '顺风车', '深圳通'],
            '购物': ['购', '商城', '店', '京东', '淘宝', '天猫', '拼多多', '电商', '超市', '便利店', '服装', '鞋', '电子', '数码'],
            '娱乐': ['娱乐', '电影', '游戏', '网盘', '会员', '视频', '音乐', '直播', '平台'],
            '住房': ['房', '租', '装修', '家具', '维意', '定制', '水电', '物业', '宽带'],
            '医疗': ['药', '医', '诊所', '医院', '保健', '健康'],
            '教育': ['学', '书', '教育', '培训', '课程'],
            '通讯': ['通讯', '话费', '手机', '流量', '电信', '移动', '联通'],
            '投资': ['基金', '股票', '理财', '投资'],
            '保险': ['保险', '太平洋人寿'],
            '工资': ['工资', '奖金', '薪资'],
            '转账': ['转账', '汇款'],
            '退款': ['退款'],
            '其他': []
        }
        
        self.db_manager = db_manager if db_manager else DBManager()
        self.cached_transactions = {}  # 用于缓存最近的查询结果
    
    def get_transactions_direct(self, start_date=None, end_date=None, account_id=None, limit=100000):
        """直接从数据库获取交易数据并返回DataFrame，而不缓存在实例中
        
        Args:
            start_date: 开始日期，格式：YYYY-MM-DD
            end_date: 结束日期，格式：YYYY-MM-DD
            account_id: A账户ID，如果为None则加载所有账户数据
            limit: 最大记录数限制
            
        Returns:
            DataFrame: 包含交易数据的DataFrame，获取失败则返回None
        """
        try:
            cache_key = f"{start_date}_{end_date}_{account_id}_{limit}"
            if cache_key in self.cached_transactions:
                logger.info(f"从缓存获取交易数据: {cache_key}")
                df = self.cached_transactions[cache_key]
                logger.info(f"缓存命中，返回{len(df)}条交易记录")
                return df
                
            logger.info(f"直接从数据库获取交易数据: start_date={start_date}, end_date={end_date}, account_id={account_id}")
            transactions = self.db_manager.get_transactions(
                account_id=account_id,
                start_date=start_date,
                end_date=end_date,
                limit=limit
            )
            if not transactions:
                logger.warning("从数据库查询未找到交易数据")
                return None
            
            df = pd.DataFrame(transactions)
            df = df.reset_index(drop=True)
            if 'transaction_date' in df.columns:
                df['transaction_date'] = pd.to_datetime(df['transaction_date'])
                df['year'] = df['transaction_date'].dt.year
                df['month'] = df['transaction_date'].dt.month
                df['day'] = df['transaction_date'].dt.day
                df['weekday'] = df['transaction_date'].dt.dayofweek
            else:
                logger.error("数据中不存在transaction_date列！")
            
            self._categorize_transactions_df(df)
            logger.info(f"数据样本：\n{df.head(3)}")
            logger.info(f"交易日期取值范围: {df['transaction_date'].min()} 至 {df['transaction_date'].max()}")
            self.cached_transactions[cache_key] = df
            if len(self.cached_transactions) > 10:
                oldest_key = list(self.cached_transactions.keys())[0]
                del self.cached_transactions[oldest_key]
            logger.info(f"成功从数据库获取并处理 {len(df)} 条交易记录")
            return df
        except Exception as e:
            logger.error(f"直接从数据库获取数据失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None
    
    def _categorize_transactions_df(self, df):
        def get_category(row):
            if row['amount'] > 0:
                if '工资' in str(row.get('transaction_type', '')) or '工资' in str(row.get('counterparty', '')):
                    return '工资'
                elif '退款' in str(row.get('transaction_type', '')):
                    return '退款'
                elif '结息' in str(row.get('transaction_type', '')):
                    return '利息'
                else:
                    return '其他收入'
            else:
                if '转账' in str(row.get('transaction_type', '')) or '转账' in str(row.get('counterparty', '')) or '汇款' in str(row.get('transaction_type', '')):
                    return '转账'
                transaction_info = f"{row.get('transaction_type', '')} {row.get('counterparty', '')}"
                for category, keywords in self.categories.items():
                    for keyword in keywords:
                        if keyword in transaction_info:
                            return category
                return '其他'
        df['category'] = df.apply(get_category, axis=1)
        
    def get_summary_direct(self, start_date=None, end_date=None, account_id=None):
        df = self.get_transactions_direct(start_date, end_date, account_id)
        if df is None or len(df) == 0:
            logger.warning("无法获取摘要，数据为空")
            return None # Return None instead of {} for consistency if df is None
        
        try:
            start_date_val = df['transaction_date'].min()
            end_date_val = df['transaction_date'].max()
            total_income = df[df['amount'] > 0]['amount'].sum()
            total_expense = abs(df[df['amount'] < 0]['amount'].sum())
            
            if not isinstance(start_date_val, datetime):
                start_date_val = pd.to_datetime(start_date_val)
            if not isinstance(end_date_val, datetime):
                end_date_val = pd.to_datetime(end_date_val)
            
            days_count = (end_date_val - start_date_val).days
            avg_daily_expense = total_expense / days_count if days_count > 0 else 0
            
            transfer_df = df[df['category'] == '转账']
            transfer_amount = abs(transfer_df[transfer_df['amount'] < 0]['amount'].sum())
            transfer_count = len(transfer_df[transfer_df['amount'] < 0])
            
            latest_balance = 0
            try:
                balance_summary = self.db_manager.get_balance_summary()
                latest_balance = sum(float(account.get('latest_balance', 0) or 0) for account in balance_summary)
            except Exception as e:
                logger.error(f"获取账户余额时出错: {e}")
            
            remaining_funds = latest_balance
            days_coverage = remaining_funds / avg_daily_expense if avg_daily_expense > 0 else 0
            
            return {
                'start_date': start_date_val.strftime('%Y-%m-%d') if not pd.isna(start_date_val) else '',
                'end_date': end_date_val.strftime('%Y-%m-%d') if not pd.isna(end_date_val) else '',
                'total_income': float(total_income) if not pd.isna(total_income) else 0,
                'total_expense': float(total_expense) if not pd.isna(total_expense) else 0,
                'net_amount': float(total_income - total_expense) if not (pd.isna(total_income) or pd.isna(total_expense)) else 0,
                'daily_avg_expense': float(avg_daily_expense) if not pd.isna(avg_daily_expense) else 0,
                'transaction_count': int(len(df)),
                'income_count': int(len(df[df['amount'] > 0])),
                'expense_count': int(len(df[df['amount'] < 0])),
                'transfer_amount': float(transfer_amount) if not pd.isna(transfer_amount) else 0,
                'transfer_count': int(transfer_count),
                'remaining_funds': float(remaining_funds),
                'days_coverage': float(days_coverage)
            }
        except Exception as e:
            logger.error(f"获取摘要数据时出错: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {} # Keep returning {} on exception for now
    
    def get_monthly_stats_direct(self, start_date=None, end_date=None, account_id=None):
        df = self.get_transactions_direct(start_date, end_date, account_id)
        if df is None or len(df) == 0:
            logger.warning("无法获取月度统计，数据为空")
            return pd.DataFrame()
        
        try:
            if 'year' not in df.columns or 'month' not in df.columns:
                df['year'] = df['transaction_date'].dt.year
                df['month'] = df['transaction_date'].dt.month
            
            monthly_data = df.groupby(['year', 'month']).agg({
                'amount': [
                    ('income', lambda x: x[x > 0].sum()),
                    ('expense', lambda x: abs(x[x < 0].sum())),
                    ('net', 'sum')
                ]
            })
            monthly_data = monthly_data.reset_index()
            monthly_data.columns = ['year', 'month', 'income', 'expense', 'net']
            monthly_data['month_label'] = monthly_data.apply(lambda row: f"{int(row['year'])}-{int(row['month']):02d}", axis=1)
            monthly_data = monthly_data.sort_values(['year', 'month'])
            return monthly_data
        except Exception as e:
            logger.error(f"获取月度统计数据时出错: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return pd.DataFrame()
    
    def get_yearly_stats_direct(self, start_date=None, end_date=None, account_id=None):
        df = self.get_transactions_direct(start_date, end_date, account_id)
        if df is None or len(df) == 0:
            logger.warning("无法获取年度统计，数据为空")
            return pd.DataFrame()
        try:
            if 'year' not in df.columns:
                df['year'] = df['transaction_date'].dt.year
            yearly_data = df.groupby(['year']).agg({
                'amount': [
                    ('income', lambda x: x[x > 0].sum()),
                    ('expense', lambda x: abs(x[x < 0].sum())),
                    ('net', 'sum')
                ]
            })
            yearly_data = yearly_data.reset_index()
            yearly_data.columns = ['year', 'income', 'expense', 'net']
            yearly_data['year_label'] = yearly_data['year'].astype(str)
            yearly_data = yearly_data.sort_values(['year'])
            return yearly_data
        except Exception as e:
            logger.error(f"获取年度统计数据时出错: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return pd.DataFrame()
    
    def get_category_stats_direct(self, start_date=None, end_date=None, account_id=None):
        df = self.get_transactions_direct(start_date, end_date, account_id)
        if df is None or len(df) == 0:
            logger.warning("无法获取分类统计，数据为空")
            return pd.DataFrame()
        try:
            expense_df = df[df['amount'] < 0]
            if expense_df.empty: # Handle case with no expenses
                return pd.DataFrame(columns=['category', 'total', 'count', 'average', 'percentage'])

            category_stats = expense_df.groupby('category').agg({
                'amount': [
                    ('total', lambda x: abs(x.sum())),
                    ('count', 'count'),
                    ('average', lambda x: abs(x.mean()))
                ]
            })
            category_stats = category_stats.reset_index()
            category_stats.columns = ['category', 'total', 'count', 'average']
            total_expense = category_stats['total'].sum()
            category_stats['percentage'] = (category_stats['total'] / total_expense * 100) if total_expense > 0 else 0
            category_stats = category_stats.sort_values('total', ascending=False)
            return category_stats
        except Exception as e:
            logger.error(f"获取分类统计数据时出错: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return pd.DataFrame()
            
    def get_weekly_stats_direct(self, start_date=None, end_date=None, account_id=None):
        df = self.get_transactions_direct(start_date, end_date, account_id)
        if df is None or len(df) == 0:
            logger.warning("无法获取周度统计，数据为空")
            return pd.DataFrame()
        try:
            expense_df = df[df['amount'] < 0]
            if expense_df.empty:
                return pd.DataFrame(columns=['weekday', 'total', 'count', 'average', 'weekday_name'])

            if 'weekday' not in expense_df.columns: # Check on expense_df
                 if 'transaction_date' in expense_df.columns:
                      expense_df.loc[:, 'weekday'] = pd.to_datetime(expense_df['transaction_date']).dt.dayofweek
                 else:
                      logger.error("周度统计：支出数据中缺少transaction_date列，无法添加weekday")
                      return pd.DataFrame()

            weekday_stats = expense_df.groupby('weekday').agg({
                'amount': [
                    ('total', lambda x: abs(x.sum())),
                    ('count', 'count'),
                    ('average', lambda x: abs(x.mean()))
                ]
            })
            weekday_stats = weekday_stats.reset_index()
            weekday_stats.columns = ['weekday', 'total', 'count', 'average']
            weekday_names = {0: '周一', 1: '周二', 2: '周三', 3: '周四', 4: '周五', 5: '周六', 6: '周日'}
            weekday_stats['weekday_name'] = weekday_stats['weekday'].map(weekday_names)
            weekday_stats = weekday_stats.sort_values('weekday')
            return weekday_stats
        except Exception as e:
            logger.error(f"获取周度统计数据时出错: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return pd.DataFrame()
            
    def get_daily_stats_direct(self, start_date=None, end_date=None, account_id=None):
        df = self.get_transactions_direct(start_date, end_date, account_id)
        if df is None or len(df) == 0:
            logger.warning("无法获取日度统计，数据为空")
            return pd.DataFrame()
        try:
            expense_df = df[df['amount'] < 0]
            if expense_df.empty:
                 return pd.DataFrame(columns=['date', 'total', 'count'])
            daily_stats = expense_df.groupby('transaction_date').agg({
                'amount': [
                    ('total', lambda x: abs(x.sum())),
                    ('count', 'count')
                ]
            })
            daily_stats = daily_stats.reset_index()
            daily_stats.columns = ['date', 'total', 'count']
            daily_stats['date'] = daily_stats['date'].dt.strftime('%Y-%m-%d')
            daily_stats = daily_stats.sort_values('date')
            return daily_stats
        except Exception as e:
            logger.error(f"获取日度统计数据时出错: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return pd.DataFrame()
    
    def get_top_merchants_direct(self, start_date=None, end_date=None, account_id=None, n=10):
        df = self.get_transactions_direct(start_date, end_date, account_id)
        if df is None or len(df) == 0:
            logger.warning("无法获取热门商户，数据为空")
            return {'by_count': pd.DataFrame(), 'by_amount': pd.DataFrame()}
        try:
            expense_df = df[df['amount'] < 0]
            if expense_df.empty:
                 return {'by_count': pd.DataFrame(columns=['merchant', 'total', 'count', 'average']), 
                         'by_amount': pd.DataFrame(columns=['merchant', 'total', 'count', 'average'])}

            merchant_stats = expense_df.groupby('counterparty').agg({
                'amount': [
                    ('total', lambda x: abs(x.sum())),
                    ('count', 'count'),
                    ('average', lambda x: abs(x.mean()))
                ]
            })
            merchant_stats = merchant_stats.reset_index()
            merchant_stats.columns = ['merchant', 'total', 'count', 'average']
            top_by_count = merchant_stats.sort_values('count', ascending=False).head(n)
            top_by_amount = merchant_stats.sort_values('total', ascending=False).head(n)
            return {'by_count': top_by_count, 'by_amount': top_by_amount}
        except Exception as e:
            logger.error(f"获取热门商户数据时出错: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {'by_count': pd.DataFrame(), 'by_amount': pd.DataFrame()}

    def _debug_find_non_serializable(self, data, path="root"):
        if isinstance(data, dict):
            for k, v in data.items():
                self._debug_find_non_serializable(v, f"{path}.{k}")
        elif isinstance(data, list):
            for i, item in enumerate(data):
                self._debug_find_non_serializable(item, f"{path}[{i}]")
        else:
            try:
                json.dumps(data)
            except TypeError:
                logger.error(f"路径 {path} 存在不可序列化的值: {type(data)} - {data}")

    def separate_core_transactions(self, df, percentile_threshold=95, strategy='percentile', min_transaction_count=10, fixed_threshold=None, recurring_only=False):
        """
        将交易分为核心交易和非常规交易
        
        Args:
            df: 包含交易数据的DataFrame
            percentile_threshold: 金额百分位阈值，高于此百分位的交易被视为非常规交易
            strategy: 识别核心交易的策略，可选值：
                - 'percentile': 基于百分位数识别（默认）
                - 'fixed': 使用固定金额阈值
                - 'iqr': 基于四分位距（IQR）识别异常值
                - 'zmm': 基于均值和中位数偏差识别
                - 'combo': 综合多种策略
            min_transaction_count: 最小交易数量，低于此数量时使用所有交易
            fixed_threshold: 固定金额阈值，仅当strategy='fixed'时使用，格式为(收入阈值,支出阈值)
            recurring_only: 是否仅将重复出现的交易视为核心交易
            
        Returns:
            tuple: (核心交易DataFrame, 非常规交易DataFrame)
        """
        if df.empty:
            return pd.DataFrame(), pd.DataFrame()
        if len(df) < min_transaction_count:
            logger.warning(f"交易数量({len(df)})不足，无法可靠地识别核心交易，返回所有交易作为核心交易")
            return df.copy(), pd.DataFrame()
        
        income_df = df[df['amount'] > 0]
        expense_df = df[df['amount'] < 0]
        
        if len(income_df) < min_transaction_count / 2:
            income_is_core = pd.Series(True, index=income_df.index) if not income_df.empty else pd.Series(dtype=bool)
        else:
            income_is_core = self._identify_core_transactions(income_df, is_income=True, 
                                                           percentile_threshold=percentile_threshold,
                                                           strategy=strategy, 
                                                           fixed_threshold=fixed_threshold[0] if fixed_threshold else None,
                                                           recurring_only=recurring_only)
            
        if len(expense_df) < min_transaction_count / 2:
            expense_is_core = pd.Series(True, index=expense_df.index) if not expense_df.empty else pd.Series(dtype=bool)
        else:
            expense_is_core = self._identify_core_transactions(expense_df, is_income=False, 
                                                            percentile_threshold=percentile_threshold,
                                                            strategy=strategy,
                                                            fixed_threshold=fixed_threshold[1] if fixed_threshold else None,
                                                            recurring_only=recurring_only)
        
        is_core = pd.Series(False, index=df.index)
        if not income_is_core.empty:
             is_core.loc[income_is_core.index] = income_is_core
        if not expense_is_core.empty:
             is_core.loc[expense_is_core.index] = expense_is_core
        
        core_transactions = df[is_core]
        non_core_transactions = df[~is_core]
        
        logger.info(f"核心交易识别完成: 总交易={len(df)}, 核心交易={len(core_transactions)}, 非核心交易={len(non_core_transactions)}")
        return core_transactions, non_core_transactions
    
    def _identify_core_transactions(self, df, is_income=True, percentile_threshold=95, strategy='percentile', 
                                   fixed_threshold=None, recurring_only=False):
        if df.empty:
            return pd.Series(dtype=bool)
        amounts = df['amount'].abs()
        if recurring_only:
            if 'counterparty' in df.columns and 'description' in df.columns:
                repeat_counter = df['counterparty'].value_counts()
                repeat_merchants = set(repeat_counter[repeat_counter > 1].index)
                is_recurring = df['counterparty'].isin(repeat_merchants)
                if 'description' in df.columns:
                    simplified_desc = df['description'].str.replace(r'\d+', '').str.replace(r'[.-]', '')
                    repeat_desc = simplified_desc.value_counts()
                    repeat_descriptions = set(repeat_desc[repeat_desc > 1].index)
                    is_recurring = is_recurring | simplified_desc.isin(repeat_descriptions)
            else:
                logger.warning("缺少交易对象或交易描述字段，无法可靠识别重复交易，忽略recurring_only要求")
                is_recurring = pd.Series(True, index=df.index)
        else:
            is_recurring = pd.Series(True, index=df.index)
        
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
            robust_z = 0.6745 * deviations / mad if mad > 0 else pd.Series(0, index=deviations.index) # Handle mad=0
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
        else: # Default to percentile
            threshold = amounts.quantile(percentile_threshold/100)
            is_core = (amounts <= threshold) & is_recurring
        return is_core
    
    def detect_outlier_transactions(self, df, method='iqr', threshold=1.5):
        if df.empty:
            return pd.DataFrame()
        result_df = df.copy()
        result_df['是否异常'] = False
        result_df['异常类型'] = ''
        result_df['异常分数'] = 0.0
        
        for trans_type, condition_func in [('收入', lambda d: d['amount'] > 0), ('支出', lambda d: d['amount'] < 0)]:
            condition = condition_func(df)
            type_df = df[condition]
            if type_df.empty:
                continue
            amounts = type_df['amount'].abs()
            
            if method == 'iqr':
                Q1 = amounts.quantile(0.25)
                Q3 = amounts.quantile(0.75)
                IQR = Q3 - Q1
                if IQR == 0: continue # Avoid division by zero or meaningless bounds
                lower_bound = Q1 - threshold * IQR
                upper_bound = Q3 + threshold * IQR
                outliers_indices = type_df[(amounts < lower_bound) | (amounts > upper_bound)].index
                for idx in outliers_indices:
                    amount_val = amounts.loc[idx]
                    score = (amount_val - upper_bound) / IQR if amount_val > upper_bound else (lower_bound - amount_val) / IQR
                    result_df.loc[idx, '异常分数'] = score
                    result_df.loc[idx, '异常类型'] = f'异常{trans_type}'
                    result_df.loc[idx, '是否异常'] = True
            elif method == 'zscore':
                mean = amounts.mean()
                std = amounts.std()
                if std == 0: continue
                z_scores = (amounts - mean) / std
                outliers_indices = type_df[abs(z_scores) > threshold].index
                for idx in outliers_indices:
                    result_df.loc[idx, '异常分数'] = abs(z_scores.loc[idx])
                    result_df.loc[idx, '异常类型'] = f'异常{trans_type}'
                    result_df.loc[idx, '是否异常'] = True
        return result_df
    
    def analyze_transaction_data_direct(self, start_date=None, end_date=None, account_id=None):
        logger.info(f"开始直接分析交易数据: start_date={start_date}, end_date={end_date}, account_id={account_id}")
        df = self.get_transactions_direct(start_date, end_date, account_id)
        if df is None or df.empty:
            logger.warning("无法获取交易数据，返回空结果")
            return {}
        try:
            summary = self.get_summary_direct(start_date, end_date, account_id)
            monthly_stats_df = self.get_monthly_stats_direct(start_date, end_date, account_id)
            yearly_stats_df = self.get_yearly_stats_direct(start_date, end_date, account_id)
            category_stats_df = self.get_category_stats_direct(start_date, end_date, account_id)
            weekly_stats_df = self.get_weekly_stats_direct(start_date, end_date, account_id)
            daily_stats_df = self.get_daily_stats_direct(start_date, end_date, account_id)
            top_merchants_dict = self.get_top_merchants_direct(start_date, end_date, account_id)
            
            transactions_list = []
            if not df.empty:
                transaction_df_copy = df.copy()
                if 'transaction_date' in transaction_df_copy.columns:
                    transaction_df_copy['transaction_date'] = transaction_df_copy['transaction_date'].dt.strftime('%Y-%m-%d')
                transactions_list = transaction_df_copy.to_dict('records')

            results = {
                'summary': summary if summary is not None else {},
                'monthly_stats': monthly_stats_df.to_dict('records') if not monthly_stats_df.empty else [],
                'yearly_stats': yearly_stats_df.to_dict('records') if not yearly_stats_df.empty else [],
                'category_stats': category_stats_df.to_dict('records') if not category_stats_df.empty else [],
                'weekly_stats': weekly_stats_df.to_dict('records') if not weekly_stats_df.empty else [],
                'daily_stats': daily_stats_df.to_dict('records') if not daily_stats_df.empty else [],
                'top_merchants': {
                    'by_count': top_merchants_dict['by_count'].to_dict('records') if not top_merchants_dict['by_count'].empty else [],
                    'by_amount': top_merchants_dict['by_amount'].to_dict('records') if not top_merchants_dict['by_amount'].empty else []
                },
                'transactions': transactions_list
            }
            logger.info("交易数据直接分析完成")
            return results
        except Exception as e:
            logger.error(f"直接分析交易数据时出错: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {}
            
    def get_core_transaction_stats_direct(self, start_date=None, end_date=None, account_id=None,
                                         percentile_threshold=95, strategy='percentile', 
                                         fixed_threshold=None, recurring_only=False):
        df = self.get_transactions_direct(start_date, end_date, account_id)
        if df is None or df.empty:
            return {
                'core_income': 0, 'core_expense': 0, 'core_net': 0,
                'core_transaction_count': 0, 'core_percentage': 0,
                'core_income_count': 0, 'core_expense_count': 0,
                'core_transactions': [] 
            }
        
        core_trans, _ = self.separate_core_transactions( # Use renamed df
            df, percentile_threshold=percentile_threshold, strategy=strategy,
            fixed_threshold=fixed_threshold, recurring_only=recurring_only
        )
            
        if core_trans.empty:
            return {
                'core_income': 0, 'core_expense': 0, 'core_net': 0,
                'core_transaction_count': 0, 'core_percentage': 0,
                'core_income_count': 0, 'core_expense_count': 0,
                'core_transactions': []
            }
        else:
            core_income_df = core_trans[core_trans['amount'] > 0]
            core_expense_df = core_trans[core_trans['amount'] < 0]
            core_income = core_income_df['amount'].sum()
            core_expense = core_expense_df['amount'].sum()
            
            core_trans_copy = core_trans.copy()
            if 'transaction_date' in core_trans_copy.columns:
                core_trans_copy['transaction_date'] = core_trans_copy['transaction_date'].dt.strftime('%Y-%m-%d')
            core_transactions_list = core_trans_copy.to_dict('records')
            
            return {
                'core_income': core_income,
                'core_expense': core_expense, # This was abs(core_expense_df['amount'].sum()) before, fixed to be sum.
                'core_net': core_income + core_expense,
                'core_transaction_count': len(core_trans),
                'core_percentage': len(core_trans) / len(df) * 100 if not df.empty else 0,
                'core_income_count': len(core_income_df),
                'core_expense_count': len(core_expense_df),
                'core_transactions': core_transactions_list
            }
        
    def get_outlier_stats_direct(self, start_date=None, end_date=None, account_id=None, 
                                method='iqr', threshold=1.5):
        df = self.get_transactions_direct(start_date, end_date, account_id)
        if df is None or df.empty:
            return {
                'outlier_count': 0, 'outlier_income_count': 0, 'outlier_expense_count': 0,
                'outlier_income_amount': 0, 'outlier_expense_amount': 0,
                'outlier_percentage': 0, 'outliers': []
            }
            
        result_df_with_outliers = self.detect_outlier_transactions(df, method, threshold)
            
        if result_df_with_outliers.empty or not result_df_with_outliers['是否异常'].any(): # Check if any outliers found
            return {
                'outlier_count': 0, 'outlier_income_count': 0, 'outlier_expense_count': 0,
                'outlier_income_amount': 0, 'outlier_expense_amount': 0,
                'outlier_percentage': 0, 'outliers': []
            }
                
        outliers_df = result_df_with_outliers[result_df_with_outliers['是否异常']]
        outliers_df = outliers_df.sort_values('异常分数', ascending=False)
        outlier_income_df = outliers_df[outliers_df['amount'] > 0]
        outlier_expense_df = outliers_df[outliers_df['amount'] < 0]
            
        outliers_head_df = outliers_df.head(10).copy()
        if 'transaction_date' in outliers_head_df.columns:
            outliers_head_df['transaction_date'] = outliers_head_df['transaction_date'].dt.strftime('%Y-%m-%d')
        outliers_list = outliers_head_df.to_dict('records')
            
        return {
            'outlier_count': len(outliers_df),
            'outlier_income_count': len(outlier_income_df),
            'outlier_expense_count': len(outlier_expense_df),
            'outlier_income_amount': outlier_income_df['amount'].sum() if not outlier_income_df.empty else 0,
            'outlier_expense_amount': outlier_expense_df['amount'].sum() if not outlier_expense_df.empty else 0,
            'outlier_percentage': len(outliers_df) / len(df) * 100 if not df.empty else 0,
            'outliers': outliers_list
        }

# 使用示例
if __name__ == "__main__":
    analyzer = TransactionAnalyzer()
    pass