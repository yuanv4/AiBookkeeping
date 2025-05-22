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
        if db_manager is None:
            # 如果没有提供db_manager，则创建一个默认的实例
            # 这假设 DBManager 可以无参数初始化，或者有一个标准的数据库路径配置
            # from scripts.db.db_manager import DBManager # 放在这里避免循环导入
            # self.db_manager = DBManager() # 实际项目中可能需要更复杂的依赖注入
            # 为了简化，我们假设 db_manager 总是被传入
            raise ValueError("DBManager instance must be provided to TransactionAnalyzer")
        self.db_manager = db_manager
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
        
        self.cached_transactions = {}  # 用于缓存最近的查询结果
    
    def get_transactions_direct(self, start_date=None, end_date=None, account_number=None, currency=None, account_name=None):
        """直接从数据库获取交易数据并转换为DataFrame (重构后)

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
        transactions = self.db_manager.get_transactions(
            account_number_filter=account_number, 
            start_date=start_date,
            end_date=end_date,
            currency_filter=currency, # 新增
            account_name_filter=account_name, # 新增
            limit=1000000,  # 获取足够多的数据进行分析
            offset=0
        )
        
        if not transactions:
            self.logger.warning("No transactions found for direct fetching.")
            return pd.DataFrame() 
        
        df = pd.DataFrame(transactions)
        
        # 标准化日期列，确保后续分析的日期类型正确
        if 'transaction_date' in df.columns:
            try:
                df['transaction_date'] = pd.to_datetime(df['transaction_date'], errors='coerce')
                # 移除转换后仍为NaT的行，这些通常是无效日期
                df.dropna(subset=['transaction_date'], inplace=True)
            except Exception as e:
                self.logger.error(f"Error converting transaction_date to datetime: {e}")
                return pd.DataFrame() # 返回空DataFrame以避免后续错误
        else:
            self.logger.warning("transaction_date column not found in fetched data.")
            return pd.DataFrame()
            
        self.logger.info(f"Successfully fetched and processed {len(df)} transactions directly.")
        return df

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
        
    def get_summary_direct(self, start_date=None, end_date=None, account_number=None, currency=None, account_name=None):
        """获取交易摘要统计 (重构后)
        Args:
            start_date: 开始日期
            end_date: 结束日期
            account_number: 账号 (用于过滤)
            currency: 币种 (用于过滤)
            account_name: 户名 (用于过滤)
        """
        df = self.get_transactions_direct(start_date, end_date, account_number, currency, account_name)
        if df is None or df.empty:
            self.logger.warning("无法获取摘要，数据为空")
            # 返回一个包含默认零值的结构，以避免调用方出错
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
                'latest_balance_sum': 0, # 注意：latest_balance 的准确计算可能需要专门的逻辑
                'remaining_funds_coverage_days': 0
            }
        
        try:
            summary = {}
            summary['start_date'] = df['transaction_date'].min()
            summary['end_date'] = df['transaction_date'].max()
            summary['total_transactions'] = len(df)
            
            summary['total_income'] = df[df['amount'] > 0]['amount'].sum()
            summary['total_expense'] = abs(df[df['amount'] < 0]['amount'].sum())
            summary['net_flow'] = summary['total_income'] - summary['total_expense']
            
            if pd.notna(summary['start_date']) and pd.notna(summary['end_date']):
                # 确保日期是 datetime 对象
                start_date_val = pd.to_datetime(summary['start_date'])
                end_date_val = pd.to_datetime(summary['end_date'])
                summary['days_count'] = (end_date_val - start_date_val).days + 1 # 加1天以包含首尾
            else:
                summary['days_count'] = 0
                
            summary['avg_daily_expense'] = summary['total_expense'] / summary['days_count'] if summary['days_count'] > 0 else 0
            
            # 修改转账逻辑：基于 transaction_type 列
            # 假设 '转账' 是一个可能的 transaction_type 值
            # 我们主要关心转出的部分作为支出影响现金流
            transfer_df_out = df[(df['transaction_type'].astype(str).str.contains('转账', case=False, na=False)) & (df['amount'] < 0)]
            summary['transfer_amount_out'] = abs(transfer_df_out['amount'].sum())
            summary['transfer_count_out'] = len(transfer_df_out)
            
            # 最新总余额的获取方式需要重新评估
            # 原来的 get_balance_summary() 可能依赖旧的表结构或产生多个账户的余额
            # 如果是单账户分析，可以取该账户的最新一条记录的 balance
            # 如果是多账户分析，则需要不同的逻辑
            # 此处简化：如果分析是针对特定 account_number，尝试获取该账户的最新余额
            # 否则，latest_balance_sum 可能不准确或需要从 self.db_manager.get_accounts() 等聚合
            latest_balance_sum = 0
            if account_number and not df.empty:
                # 按日期和ID（如果有多条同日记录）排序，获取最新的一条
                latest_transaction_for_account = df[df['account_number'] == account_number].sort_values(by=['transaction_date', 'id'], ascending=[False, False]).head(1)
                if not latest_transaction_for_account.empty and pd.notna(latest_transaction_for_account['balance'].iloc[0]):
                    latest_balance_sum = latest_transaction_for_account['balance'].iloc[0]
            elif not df.empty: # 如果没有指定账户，但df不为空，这是一个模糊的情况
                # 可以尝试聚合所有账户的最新余额，但这需要更复杂的逻辑，比如查询 accounts 表
                # 或者取所有交易中最新的那条记录的余额（但这不代表总余额）
                # 暂时设为0，提示这部分需要细化
                self.logger.warning("Latest balance sum calculation is simplified for multi-account summary.")
                # Potentially use: self.db_manager.get_balance_summary() if it's adapted
                # For now, keeping it simple and possibly inaccurate for multi-account without filter.
                # A more robust way for a specific account is done above.
                # If we need total sum of all accounts, it should be fetched differently, e.g. from accounts table state.
                # Let's assume for now, if no account_number, this means sum of balances from the LATEST transaction of EACH account in the df.
                # This is still an approximation.
                if 'balance' in df.columns:
                     # Get the last transaction for each account in the current df and sum their balances
                    latest_balances_per_account = df.sort_values('transaction_date').groupby('account_number').last()['balance']
                    latest_balance_sum = latest_balances_per_account.sum()
                

            summary['latest_balance_sum'] = latest_balance_sum
            summary['remaining_funds_coverage_days'] = latest_balance_sum / summary['avg_daily_expense'] if summary['avg_daily_expense'] > 0 else float('inf') if latest_balance_sum > 0 else 0

            # 确保所有数值都是 Python 原生类型，以便 JSON 序列化
            for key, value in summary.items():
                if isinstance(value, (np.generic, pd.Timestamp)):
                    if pd.isna(value):
                        summary[key] = None  # Convert NaT or NaN to None
                    elif isinstance(value, pd.Timestamp):
                        summary[key] = value.strftime('%Y-%m-%d') # Format date
                    else:
                        summary[key] = value.item() # Convert numpy types (int64, float64) to python types

            return summary

        except Exception as e:
            self.logger.error(f"计算交易摘要时出错: {e}", exc_info=True)
            # Fallback to default structure on error
            return {
                'start_date': None, 'end_date': None, 'total_transactions': 0,
                'total_income': 0, 'total_expense': 0, 'net_flow': 0,
                'avg_daily_expense': 0, 'days_count': 0,
                'transfer_amount_out': 0, 'transfer_count_out': 0,
                'latest_balance_sum': 0,
                'remaining_funds_coverage_days': 0
            }
    
    def get_monthly_stats_direct(self, start_date=None, end_date=None, account_number=None, currency=None, account_name=None):
        df = self.get_transactions_direct(start_date, end_date, account_number, currency, account_name)
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
    
    def get_yearly_stats_direct(self, start_date=None, end_date=None, account_number=None, currency=None, account_name=None):
        df = self.get_transactions_direct(start_date, end_date, account_number, currency, account_name)
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
    
    def get_category_stats_direct(self, start_date=None, end_date=None, account_number=None, currency=None, account_name=None):
        """ 获取按交易类型统计的支出数据 (原category列已移除) """
        df = self.get_transactions_direct(start_date, end_date, account_number, currency, account_name)
        if df is None or df.empty:
            logger.warning("无法获取交易类型统计，数据为空")
            return pd.DataFrame(columns=['transaction_type', 'total', 'count', 'average', 'percentage'])
        try:
            expense_df = df[df['amount'] < 0].copy()
            if expense_df.empty: 
                return pd.DataFrame(columns=['transaction_type', 'total', 'count', 'average', 'percentage'])

            if 'transaction_type' not in expense_df.columns or expense_df['transaction_type'].isnull().all():
                logger.warning("支出数据中缺少有效的 'transaction_type' 列，无法按类型统计。")
                return pd.DataFrame(columns=['transaction_type', 'total', 'count', 'average', 'percentage'])

            # 按 transaction_type 分组
            expense_df.loc[:, 'transaction_type'] = expense_df['transaction_type'].fillna('未知类型')
            category_stats = expense_df.groupby('transaction_type').agg(
                total=('amount', lambda x: abs(x.sum())),
                count=('amount', 'count'),
                average=('amount', lambda x: abs(x.mean()))
            ).reset_index()
            
            total_expense = category_stats['total'].sum()
            category_stats['percentage'] = (category_stats['total'] / total_expense * 100) if total_expense > 0 else 0
            category_stats = category_stats.sort_values('total', ascending=False)
            
            # 确保列名符合预期，即使源列名是 transaction_type
            # category_stats.rename(columns={'transaction_type': 'category'}, inplace=True) 
            # 保持为 transaction_type, 前端将需要适配

            return category_stats
        except Exception as e:
            logger.error(f"获取交易类型统计数据时出错: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return pd.DataFrame(columns=['transaction_type', 'total', 'count', 'average', 'percentage'])
            
    def get_weekly_stats_direct(self, start_date=None, end_date=None, account_number=None, currency=None, account_name=None):
        df = self.get_transactions_direct(start_date, end_date, account_number, currency, account_name)
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
            
    def get_daily_stats_direct(self, start_date=None, end_date=None, account_number=None, currency=None, account_name=None):
        df = self.get_transactions_direct(start_date, end_date, account_number, currency, account_name)
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
    
    def get_top_merchants_direct(self, start_date=None, end_date=None, account_number=None, currency=None, account_name=None, n=10):
        df = self.get_transactions_direct(start_date, end_date, account_number, currency, account_name)
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
            # recurring_only 逻辑不再依赖 category，需要基于其他字段，如 counterparty 和 transaction_type
            self.logger.warning("'recurring_only' 功能受影响，因 'category' 列已移除。当前实现可能不准确。")
            if 'counterparty' in df.columns and 'transaction_type' in df.columns:
                # 简单的启发式：同一对手方和同一交易类型出现多次视为经常性
                # 更复杂的可能需要分析频率、金额稳定性等
                df_copy = df.copy()
                df_copy['recurring_key'] = df_copy['counterparty'].fillna('') + "_" + df_copy['transaction_type'].fillna('')
                key_counts = df_copy['recurring_key'].value_counts()
                recurring_keys = key_counts[key_counts > 1].index
                is_recurring = df_copy['recurring_key'].isin(recurring_keys)
            elif 'counterparty' in df.columns: # 备选：仅基于对手方
                repeat_counter = df['counterparty'].value_counts()
                repeat_merchants = set(repeat_counter[repeat_counter > 1].index)
                is_recurring = df['counterparty'].isin(repeat_merchants)
            else:
                self.logger.warning("缺少 'counterparty' 或 'transaction_type'，无法应用 'recurring_only' 筛选。")
                is_recurring = pd.Series(True, index=df.index) # 默认全部通过
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
    
    def analyze_transaction_data_direct(self, start_date=None, end_date=None, account_number=None, currency=None, account_name=None):
        logger.info(f"开始直接分析交易数据: start_date={start_date}, end_date={end_date}, account_number={account_number}, currency={currency}, account_name={account_name}")
        df = self.get_transactions_direct(start_date, end_date, account_number, currency, account_name)
        if df is None or df.empty:
            logger.warning("无法获取交易数据，返回空结果")
            return {}
        try:
            summary = self.get_summary_direct(start_date, end_date, account_number, currency, account_name)
            monthly_stats_df = self.get_monthly_stats_direct(start_date, end_date, account_number, currency, account_name)
            yearly_stats_df = self.get_yearly_stats_direct(start_date, end_date, account_number, currency, account_name)
            # category_stats_df 现在是按 transaction_type 统计
            type_stats_df = self.get_category_stats_direct(start_date, end_date, account_number, currency, account_name) 
            weekly_stats_df = self.get_weekly_stats_direct(start_date, end_date, account_number, currency, account_name)
            daily_stats_df = self.get_daily_stats_direct(start_date, end_date, account_number, currency, account_name)
            top_merchants_dict = self.get_top_merchants_direct(start_date, end_date, account_number, currency, account_name)
            
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
                'category_stats': type_stats_df.to_dict('records') if not type_stats_df.empty else [], # 更名为 type_stats 或保持 category_stats 并告知前端变化
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
            
    def get_core_transaction_stats_direct(self, start_date=None, end_date=None, account_number=None, currency=None, account_name=None,
                                         percentile_threshold=95, strategy='percentile', 
                                         fixed_threshold=None, recurring_only=False):
        """获取核心交易统计 (重构后，category列不再可用)
        Args:
            start_date, end_date, account_number, currency, account_name: 筛选参数
            percentile_threshold, strategy, fixed_threshold, recurring_only: 核心交易识别参数
        """
        df = self.get_transactions_direct(start_date, end_date, account_number, currency, account_name)

        if df is None or df.empty:
            self.logger.warning("无法获取核心交易统计，数据为空")
            return {
                'core_income': 0, 'core_expense': 0, 'core_net': 0,
                'core_transaction_count': 0, 'core_percentage': 0,
                'core_income_count': 0, 'core_expense_count': 0,
                'core_transactions': []
            }
        
        # 移除对 recurring_transactions_df 的依赖，因为 category 列没了
        # 如果 recurring_only 为 True，需要新的逻辑来识别经常性交易 (可能基于counterparty, amount, frequency)
        # 目前简化：如果 recurring_only 为 True 但无新逻辑，则返回空或警告
        if recurring_only:
            self.logger.warning("recurring_only=True 无法按旧方式执行，因为category列已移除。需要新逻辑识别经常性交易。")
            # For now, let's assume it means no transactions if no specific logic for recurring is added here based on other fields.
            # Or, we could filter by transactions that appear multiple times with same counterparty and similar amount.
            # This is a placeholder for more complex recurring transaction detection.
            # df = df[df.duplicated(subset=['counterparty', 'amount'], keep=False)] # A very simple heuristic
            pass # Current pass-through, meaning recurring_only won't filter if not implemented further

        # 核心交易识别不再依赖 _identify_core_transactions, 直接在下面应用策略
        # 因为 _identify_core_transactions 的 recurring_only 逻辑被简化了
        # 我们在这里直接应用金额阈值，如果 recurring_only 为 True，则附加其（简化的）筛选

        amounts = df['amount'].abs()
        is_core_by_amount = pd.Series(False, index=df.index)

        if strategy == 'percentile':
            threshold = amounts.quantile(percentile_threshold / 100.0) if not amounts.empty else 0
            is_core_by_amount = amounts <= threshold
        elif strategy == 'fixed':
            if fixed_threshold is None:
                self.logger.error("固定阈值策略需要提供 fixed_threshold 参数")
                # Fallback to a default or return empty, for now, let's use a high threshold (effectively no filtering by amount)
                is_core_by_amount = pd.Series(True, index=df.index) 
            else:
                is_core_by_amount = amounts <= fixed_threshold
        else:
            self.logger.error(f"未知核心交易策略: {strategy}")
            is_core_by_amount = pd.Series(True, index=df.index) # Default to all if strategy is unknown

        if recurring_only:
            self.logger.warning("'recurring_only' 功能受影响，因 'category' 列已移除。当前实现可能不准确。")
            if 'counterparty' in df.columns and 'transaction_type' in df.columns:
                df_copy = df.copy()
                df_copy['recurring_key'] = df_copy['counterparty'].fillna('') + "_" + df_copy['transaction_type'].fillna('')
                key_counts = df_copy['recurring_key'].value_counts()
                recurring_keys = key_counts[key_counts > 1].index
                is_recurring_filter = df_copy['recurring_key'].isin(recurring_keys)
                core_trans = df[is_core_by_amount & is_recurring_filter]
            else:
                self.logger.warning("缺少 'counterparty' 或 'transaction_type'，无法应用 'recurring_only' 筛选。核心交易将仅基于金额。")
                core_trans = df[is_core_by_amount]
        else:
            core_trans = df[is_core_by_amount]
        
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
            core_expense = core_expense_df['amount'].sum() # 支出为负数，直接求和
            
            core_trans_copy = core_trans.copy() # 操作副本以避免 SettingWithCopyWarning
            if 'transaction_date' in core_trans_copy.columns:
                # 确保日期列是字符串格式，以便JSON序列化
                core_trans_copy.loc[:, 'transaction_date'] = pd.to_datetime(core_trans_copy['transaction_date']).dt.strftime('%Y-%m-%d')
            
            # 将DataFrame转换为字典列表，确保所有值都是JSON可序列化的
            core_transactions_list = []
            for record in core_trans_copy.to_dict('records'):
                for key, value in record.items():
                    if isinstance(value, (np.generic, pd.Timestamp)):
                        if pd.isna(value):
                            record[key] = None
                        elif isinstance(value, pd.Timestamp):
                            record[key] = value.strftime('%Y-%m-%d')
                        else:
                            record[key] = value.item()
                core_transactions_list.append(record)
            
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

    def get_outlier_stats_direct(self, start_date=None, end_date=None, account_number=None, currency=None, account_name=None,
                                method='iqr', threshold=1.5):
        df = self.get_transactions_direct(start_date, end_date, account_number, currency, account_name)
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

    def get_expense_distribution_direct(self, start_date=None, end_date=None, account_number=None, currency=None, account_name=None, use_transaction_type=True):
        """获取支出分布 (重构后，category列不再可用)
           现在将基于 transaction_type 进行分布统计 (如果 use_transaction_type 为 True)
        Args:
            start_date, end_date, account_number, currency, account_name: 筛选参数
            use_transaction_type: 是否按交易类型分组
        """
        df = self.get_transactions_direct(start_date, end_date, account_number, currency, account_name)
        expense_df = df[df['amount'] < 0].copy() # 只关注支出，并使用 .copy() 避免警告

        if expense_df.empty:
            self.logger.warning("没有支出数据可供分析分布")
            return pd.DataFrame(columns=['group', 'total_amount', 'percentage']).to_dict('records')

        if use_transaction_type and 'transaction_type' in expense_df.columns:
            group_by_col = 'transaction_type'
            expense_df.loc[:, 'group'] = expense_df[group_by_col].fillna('未知类型')
        else:
            # 如果不使用 transaction_type，或者该列不存在，则无法进行有意义的支出分布
            # 除非有其他可用于分组的列。这里可以返回一个简单的总支出，或警告。
            self.logger.warning("无法按类型进行支出分布，将返回总支出或空结果。")
            # 示例：返回总支出作为一个组
            # total_expense = abs(expense_df['amount'].sum())
            # return [{'group': '总支出', 'total_amount': total_expense.item() if pd.notna(total_expense) else 0, 'percentage': 100.0}]
            # 或者，如果没有合适的列分组，返回空
            return pd.DataFrame(columns=['group', 'total_amount', 'percentage']).to_dict('records')

        # 计算每个组的总金额
        distribution = expense_df.groupby('group')['amount'].sum().abs().reset_index(name='total_amount')
        total_overall_expense = distribution['total_amount'].sum()
        
        if total_overall_expense == 0:
            distribution['percentage'] = 0.0
        else:
            distribution['percentage'] = (distribution['total_amount'] / total_overall_expense * 100).round(2)
        
        distribution.sort_values('total_amount', ascending=False, inplace=True)
        
        # 确保数值是Python原生类型
        results = []
        for record in distribution.to_dict('records'):
            for key, value in record.items():
                if isinstance(value, np.generic):
                    record[key] = value.item()
            results.append(record)
        return results

    def get_income_sources_direct(self, start_date=None, end_date=None, account_number=None, currency=None, account_name=None, use_transaction_type=True):
        """获取收入来源分布 (重构后，category列不再可用)
           现在将基于 transaction_type 进行分布统计
        Args:
            start_date, end_date, account_number, currency, account_name: 筛选参数
            use_transaction_type: 是否按交易类型分组
        """
        df = self.get_transactions_direct(start_date, end_date, account_number, currency, account_name)
        income_df = df[df['amount'] > 0].copy()

        if income_df.empty:
            self.logger.warning("没有收入数据可供分析来源")
            return pd.DataFrame(columns=['group', 'total_amount', 'percentage']).to_dict('records')

        if use_transaction_type and 'transaction_type' in income_df.columns:
            group_by_col = 'transaction_type'
            income_df.loc[:, 'group'] = income_df[group_by_col].fillna('未知类型')
        else:
            self.logger.warning("无法按类型进行收入来源分析，将返回空结果。")
            return pd.DataFrame(columns=['group', 'total_amount', 'percentage']).to_dict('records')

        distribution = income_df.groupby('group')['amount'].sum().reset_index(name='total_amount')
        total_overall_income = distribution['total_amount'].sum()

        if total_overall_income == 0:
            distribution['percentage'] = 0.0
        else:
            distribution['percentage'] = (distribution['total_amount'] / total_overall_income * 100).round(2)
            
        distribution.sort_values('total_amount', ascending=False, inplace=True)
        
        results = []
        for record in distribution.to_dict('records'):
            for key, value in record.items():
                if isinstance(value, np.generic):
                    record[key] = value.item()
            results.append(record)
        return results

    # 辅助方法，确保在类实例化时logger可用
    @property
    def logger(self):
        return logging.getLogger(self.__class__.__name__)

# 使用示例
if __name__ == "__main__":
    analyzer = TransactionAnalyzer()
    pass