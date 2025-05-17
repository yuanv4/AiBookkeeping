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
        self.df = None
        self.cached_transactions = {}  # 用于缓存最近的查询结果
    
    def load_data(self, start_date=None, end_date=None, account_id=None):
        """从数据库加载交易数据
        
        Args:
            start_date: 开始日期，格式：YYYY-MM-DD
            end_date: 结束日期，格式：YYYY-MM-DD
            account_id: 账户ID，如果为None则加载所有账户数据
            
        Returns:
            bool: 是否成功加载数据
        """
        try:
            logger.info(f"开始从数据库加载交易数据: start_date={start_date}, end_date={end_date}, account_id={account_id}")
            
            # 从数据库获取交易数据
            transactions = self.db_manager.get_transactions(
                account_id=account_id,
                start_date=start_date,
                end_date=end_date,
                limit=100000  # 设置一个合理的限制
            )
            
            if not transactions:
                logger.warning("未找到交易数据")
                return False
            
            # 转换为DataFrame
            self.df = pd.DataFrame(transactions)
            
            # 重置索引并移除重复数据（如果存在）
            self.df = self.df.reset_index(drop=True)
            
            # 确保交易日期是日期类型
            self.df['transaction_date'] = pd.to_datetime(self.df['transaction_date'])
            
            # 从日期字段提取年月日星期
            self.df['year'] = self.df['transaction_date'].dt.year
            self.df['month'] = self.df['transaction_date'].dt.month
            self.df['day'] = self.df['transaction_date'].dt.day
            self.df['weekday'] = self.df['transaction_date'].dt.dayofweek
            
            # 添加分类
            self.categorize_transactions()
            
            logger.info(f"成功从数据库加载 {len(self.df)} 条交易记录")
            return True
            
        except Exception as e:
            logger.error(f"从数据库加载数据失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
    
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
            # 生成缓存键
            cache_key = f"{start_date}_{end_date}_{account_id}_{limit}"
            
            # 检查缓存
            if cache_key in self.cached_transactions:
                logger.info(f"从缓存获取交易数据: {cache_key}")
                df = self.cached_transactions[cache_key]
                logger.info(f"缓存命中，返回{len(df)}条交易记录")
                return df
                
            logger.info(f"直接从数据库获取交易数据: start_date={start_date}, end_date={end_date}, account_id={account_id}")
            
            # 从数据库获取交易数据
            transactions = self.db_manager.get_transactions(
                account_id=account_id,
                start_date=start_date,
                end_date=end_date,
                limit=limit
            )
            
            if not transactions:
                logger.warning("从数据库查询未找到交易数据")
                return None
            
            logger.info(f"从数据库获取到{len(transactions)}条交易数据")
            
            # 转换为DataFrame
            df = pd.DataFrame(transactions)
            logger.info(f"成功转换为DataFrame，列：{df.columns.tolist()}")
            
            # 重置索引并移除重复数据（如果存在）
            df = df.reset_index(drop=True)
            
            # 确保交易日期是日期类型
            if 'transaction_date' in df.columns:
                logger.info("转换交易日期为日期类型")
                df['transaction_date'] = pd.to_datetime(df['transaction_date'])
                
                # 从日期字段提取年月日星期
                logger.info("从交易日期提取年月日星期")
                df['year'] = df['transaction_date'].dt.year
                df['month'] = df['transaction_date'].dt.month
                df['day'] = df['transaction_date'].dt.day
                df['weekday'] = df['transaction_date'].dt.dayofweek
            else:
                logger.error("数据中不存在transaction_date列！")
            
            # 添加分类
            logger.info("添加交易分类")
            self._categorize_transactions_df(df)
            
            # 输出一些数据样本
            logger.info(f"数据样本：\n{df.head(3)}")
            logger.info(f"交易日期取值范围: {df['transaction_date'].min()} 至 {df['transaction_date'].max()}")
            
            # 存入缓存
            self.cached_transactions[cache_key] = df
            
            # 如果缓存过大，清理最早的条目
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
        """对指定的DataFrame中的交易进行分类
        
        Args:
            df: 包含交易数据的DataFrame
        """
        # 创建分类函数
        def get_category(row):
            # 收入类别
            if row['amount'] > 0:
                if '工资' in str(row.get('transaction_type', '')) or '工资' in str(row.get('counterparty', '')):
                    return '工资'
                elif '退款' in str(row.get('transaction_type', '')):
                    return '退款'
                elif '结息' in str(row.get('transaction_type', '')):
                    return '利息'
                else:
                    return '其他收入'
            # 支出类别
            else:
                # 转账类
                if '转账' in str(row.get('transaction_type', '')) or '转账' in str(row.get('counterparty', '')) or '汇款' in str(row.get('transaction_type', '')):
                    return '转账'
                    
                # 其他支出类别
                transaction_info = f"{row.get('transaction_type', '')} {row.get('counterparty', '')}"
                for category, keywords in self.categories.items():
                    for keyword in keywords:
                        if keyword in transaction_info:
                            return category
                
                # 如果没有匹配到任何类别，返回"其他"
                return '其他'
        
        # 应用分类函数
        df['category'] = df.apply(get_category, axis=1)
        
    def categorize_transactions(self):
        """根据交易描述对交易进行分类"""
        if self.df is not None:
            self._categorize_transactions_df(self.df)
            
    def get_summary_direct(self, start_date=None, end_date=None, account_id=None):
        """直接从数据库获取交易数据的总体摘要，不依赖于预先加载的数据
        
        Args:
            start_date: 开始日期，格式：YYYY-MM-DD
            end_date: 结束日期，格式：YYYY-MM-DD
            account_id: 账户ID，如果为None则加载所有账户数据
            
        Returns:
            dict: 包含摘要数据的字典
        """
        df = self.get_transactions_direct(start_date, end_date, account_id)
        if df is None or len(df) == 0:
            logger.warning("无法获取摘要，数据为空")
            return None
        
        try:
            start_date = df['transaction_date'].min()
            end_date = df['transaction_date'].max()
            total_income = df[df['amount'] > 0]['amount'].sum()
            total_expense = abs(df[df['amount'] < 0]['amount'].sum())
            
            # 确保start_date和end_date是datetime对象
            if not isinstance(start_date, datetime):
                start_date = pd.to_datetime(start_date)
            if not isinstance(end_date, datetime):
                end_date = pd.to_datetime(end_date)
            
            days_count = (end_date - start_date).days
            avg_daily_expense = total_expense / days_count if days_count > 0 else 0
            
            # 计算转账相关统计
            transfer_df = df[df['category'] == '转账']
            transfer_amount = abs(transfer_df[transfer_df['amount'] < 0]['amount'].sum())
            transfer_count = len(transfer_df[transfer_df['amount'] < 0])
            
            # 获取账户余额信息
            latest_balance = 0
            try:
                balance_summary = self.db_manager.get_balance_summary()
                latest_balance = sum(float(account.get('latest_balance', 0) or 0) for account in balance_summary)
            except Exception as e:
                logger.error(f"获取账户余额时出错: {e}")
            
            # 计算还能支撑多少天
            remaining_funds = latest_balance
            days_coverage = remaining_funds / avg_daily_expense if avg_daily_expense > 0 else 0
            
            return {
                'start_date': start_date.strftime('%Y-%m-%d') if not pd.isna(start_date) else '',
                'end_date': end_date.strftime('%Y-%m-%d') if not pd.isna(end_date) else '',
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
            return {}
    
    def get_monthly_stats(self):
        """获取月度统计数据"""
        if self.df is None or len(self.df) == 0:
            logger.warning("无法获取月度统计，数据为空")
            return None
        
        logger.info("开始获取月度统计数据")
        try:
            # 检查年月列是否存在
            if 'year' not in self.df.columns or 'month' not in self.df.columns:
                logger.error("数据中缺少'year'或'month'列")
                # 如果缺少这些列，尝试从交易日期重新生成
                logger.info("尝试从交易日期重新生成年月列")
                self.df['year'] = self.df['transaction_date'].dt.year
                self.df['month'] = self.df['transaction_date'].dt.month
            
            # 记录分组前的年月数据样本
            year_samples = self.df['year'].head(10).tolist()
            month_samples = self.df['month'].head(10).tolist()
            logger.info(f"year列样本数据: {year_samples}")
            logger.info(f"month列样本数据: {month_samples}")
            
            # 按年月分组
            logger.info("开始按年月分组数据")
            monthly_data = self.df.groupby(['year', 'month']).agg({
                'amount': [
                    ('income', lambda x: x[x > 0].sum()),
                    ('expense', lambda x: abs(x[x < 0].sum())),
                    ('net', 'sum')
                ]
            })
            
            # 重置索引，并展平多级列
            monthly_data = monthly_data.reset_index()
            monthly_data.columns = ['year', 'month', 'income', 'expense', 'net']
            
            # 添加月份标签
            monthly_data['month_label'] = monthly_data.apply(lambda row: f"{int(row['year'])}-{int(row['month']):02d}", axis=1)
            
            # 排序
            monthly_data = monthly_data.sort_values(['year', 'month'])
            
            logger.info(f"月度统计数据生成成功，行数: {len(monthly_data)}")
            return monthly_data
        except Exception as e:
            logger.error(f"获取月度统计数据时出错: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return pd.DataFrame()  # 返回空DataFrame而不是None，避免后续处理错误
    
    def get_yearly_stats(self):
        """获取年度统计数据"""
        if self.df is None or len(self.df) == 0:
            logger.warning("无法获取年度统计，数据为空")
            return None
        
        logger.info("开始获取年度统计数据")
        try:
            # 检查年列是否存在
            if 'year' not in self.df.columns:
                logger.error("数据中缺少'year'列")
                # 如果缺少年列，尝试从交易日期重新生成
                logger.info("尝试从交易日期重新生成年列")
                self.df['year'] = self.df['transaction_date'].dt.year
            
            # 记录分组前的年数据样本
            year_samples = self.df['year'].head(10).tolist()
            logger.info(f"year列样本数据: {year_samples}")
            
            # 按年分组
            logger.info("开始按年分组数据")
            yearly_data = self.df.groupby(['year']).agg({
                'amount': [
                    ('income', lambda x: x[x > 0].sum()),
                    ('expense', lambda x: abs(x[x < 0].sum())),
                    ('net', 'sum')
                ]
            })
            
            # 重置索引，并展平多级列
            yearly_data = yearly_data.reset_index()
            yearly_data.columns = ['year', 'income', 'expense', 'net']
            
            # 添加年份标签为字符串类型
            yearly_data['year_label'] = yearly_data['year'].astype(str)
            
            # 排序
            yearly_data = yearly_data.sort_values(['year'])
            
            logger.info(f"年度统计数据生成成功，行数: {len(yearly_data)}")
            return yearly_data
        except Exception as e:
            logger.error(f"获取年度统计数据时出错: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return pd.DataFrame()  # 返回空DataFrame而不是None，避免后续处理错误
    
    def get_category_stats(self):
        """获取分类统计数据"""
        if self.df is None or len(self.df) == 0:
            return None
        
        # 支出类别统计
        expense_df = self.df[self.df['amount'] < 0]
        category_stats = expense_df.groupby('category').agg({
            'amount': [
                ('total', lambda x: abs(x.sum())),
                ('count', 'count'),
                ('average', lambda x: abs(x.mean()))
            ]
        })
        
        # 重置索引，并展平多级列
        category_stats = category_stats.reset_index()
        category_stats.columns = ['category', 'total', 'count', 'average']
        
        # 计算占比
        total_expense = category_stats['total'].sum()
        category_stats['percentage'] = category_stats['total'] / total_expense * 100
        
        # 排序
        category_stats = category_stats.sort_values('total', ascending=False)
        
        return category_stats
    
    def get_weekly_stats(self):
        """获取按星期统计的消费数据"""
        if self.df is None or len(self.df) == 0:
            return None
        
        # 只考虑支出
        expense_df = self.df[self.df['amount'] < 0]
        
        # 按星期分组
        weekday_stats = expense_df.groupby('weekday').agg({
            'amount': [
                ('total', lambda x: abs(x.sum())),
                ('count', 'count'),
                ('average', lambda x: abs(x.mean()))
            ]
        })
        
        # 重置索引，并展平多级列
        weekday_stats = weekday_stats.reset_index()
        weekday_stats.columns = ['weekday', 'total', 'count', 'average']
        
        # 添加星期标签
        weekday_names = {
            0: '周一',
            1: '周二',
            2: '周三',
            3: '周四',
            4: '周五',
            5: '周六',
            6: '周日'
        }
        weekday_stats['weekday_name'] = weekday_stats['weekday'].map(weekday_names)
        
        # 排序
        weekday_stats = weekday_stats.sort_values('weekday')
        
        return weekday_stats
    
    def get_daily_stats(self):
        """获取日消费统计数据"""
        if self.df is None or len(self.df) == 0:
            return None
        
        # 只考虑支出
        expense_df = self.df[self.df['amount'] < 0]
        
        # 按日期分组
        daily_stats = expense_df.groupby('transaction_date').agg({
            'amount': [
                ('total', lambda x: abs(x.sum())),
                ('count', 'count')
            ]
        })
        
        # 重置索引，并展平多级列
        daily_stats = daily_stats.reset_index()
        daily_stats.columns = ['date', 'total', 'count']
        
        # 将日期转为字符串，解决JSON序列化问题
        daily_stats['date'] = daily_stats['date'].dt.strftime('%Y-%m-%d')
        
        # 排序
        daily_stats = daily_stats.sort_values('date')
        
        return daily_stats
    
    def get_top_merchants(self, n=10):
        """获取交易次数最多的商户"""
        if self.df is None or len(self.df) == 0:
            return None
        
        # 只考虑支出
        expense_df = self.df[self.df['amount'] < 0]
        
        # 按商户分组
        merchant_stats = expense_df.groupby('counterparty').agg({
            'amount': [
                ('total', lambda x: abs(x.sum())),
                ('count', 'count'),
                ('average', lambda x: abs(x.mean()))
            ]
        })
        
        # 重置索引，并展平多级列
        merchant_stats = merchant_stats.reset_index()
        merchant_stats.columns = ['merchant', 'total', 'count', 'average']
        
        # 排序并取前N个
        top_by_count = merchant_stats.sort_values('count', ascending=False).head(n)
        top_by_amount = merchant_stats.sort_values('total', ascending=False).head(n)
        
        return {
            'by_count': top_by_count,
            'by_amount': top_by_amount
        }
    
    def analyze_transaction_data(self):
        """完整分析交易数据并返回所有统计数据"""
        if self.df is None or len(self.df) == 0:
            logger.warning("无法分析交易数据，数据为空")
            return None
        
        logger.info("开始完整分析交易数据")
        try:
            monthly_stats = self.get_monthly_stats()
            if monthly_stats is None or monthly_stats.empty:
                logger.error("获取月度统计数据失败")
                monthly_stats = pd.DataFrame(columns=['year', 'month', 'income', 'expense', 'net', 'month_label'])
            
            yearly_stats = self.get_yearly_stats()
            if yearly_stats is None or yearly_stats.empty:
                logger.error("获取年度统计数据失败")
                yearly_stats = pd.DataFrame(columns=['year', 'income', 'expense', 'net', 'year_label'])
            
            category_stats = self.get_category_stats()
            if category_stats is None:
                logger.error("获取分类统计数据失败")
                category_stats = pd.DataFrame()
            
            weekly_stats = self.get_weekly_stats()
            if weekly_stats is None:
                logger.error("获取周统计数据失败")
                weekly_stats = pd.DataFrame()
                
            daily_stats = self.get_daily_stats()
            if daily_stats is None:
                logger.error("获取日统计数据失败")
                daily_stats = pd.DataFrame()
                
            top_merchants = self.get_top_merchants()
            if top_merchants is None:
                logger.error("获取热门商户数据失败")
                top_merchants = {'by_count': pd.DataFrame(), 'by_amount': pd.DataFrame()}
            
            summary = self.get_summary_direct()
            if summary is None:
                logger.error("获取摘要数据失败")
                summary = {}
            
            # 添加原始交易数据
            logger.info("添加原始交易数据到分析结果")
            # 确保交易日期是字符串格式
            transaction_df = self.df.copy()
            if 'transaction_date' in transaction_df.columns:
                transaction_df['transaction_date'] = transaction_df['transaction_date'].dt.strftime('%Y-%m-%d')
            
            # 转换DataFrame为字典列表
            try:
                transactions = transaction_df.to_dict('records')
                logger.info(f"成功转换{len(transactions)}条交易记录")
            except Exception as e:
                logger.error(f"转换交易记录时出错: {e}")
                transactions = []
            
            results = {
                'summary': summary,
                'monthly_stats': monthly_stats.to_dict('records') if not monthly_stats.empty else [],
                'yearly_stats': yearly_stats.to_dict('records') if not yearly_stats.empty else [],
                'category_stats': category_stats.to_dict('records') if not category_stats.empty else [],
                'weekly_stats': weekly_stats.to_dict('records') if not weekly_stats.empty else [],
                'daily_stats': daily_stats.to_dict('records') if not daily_stats.empty else [],
                'top_merchants': {
                    'by_count': top_merchants['by_count'].to_dict('records') if 'by_count' in top_merchants and not top_merchants['by_count'].empty else [],
                    'by_amount': top_merchants['by_amount'].to_dict('records') if 'by_amount' in top_merchants and not top_merchants['by_amount'].empty else []
                },
                # 添加交易记录到分析数据中
                'transactions': transactions
            }
            
            logger.info("交易数据分析完成")
            return results
        except Exception as e:
            logger.error(f"分析交易数据时出错: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {}
    
    def generate_json_data(self, output_file=None):
        """生成JSON格式的分析数据"""
        if self.df is None or len(self.df) == 0:
            return False
        
        try:
            # 获取所有分析数据
            analysis_data = self.analyze_transaction_data()
            if analysis_data:
                logger.info("分析数据准备完成，开始生成JSON")
                
                # JSON序列化函数，处理不可直接序列化的类型
                def json_serializable(obj):
                    if isinstance(obj, (pd.Timestamp, datetime.datetime, datetime.date)):
                        return obj.strftime('%Y-%m-%d')
                    if isinstance(obj, np.int64):
                        return int(obj)
                    if isinstance(obj, np.float64):
                        return float(obj)
                    if callable(obj):
                        return str(obj)
                    raise TypeError(f"无法序列化对象类型: {type(obj)}")
                
                # 处理字典中的不可序列化值
                def process_dict(d):
                    if not isinstance(d, dict):
                        return d
                    
                    result = {}
                    for k, v in d.items():
                        if isinstance(v, dict):
                            result[k] = process_dict(v)
                        elif isinstance(v, list):
                            result[k] = [process_item(item) for item in v]
                        else:
                            try:
                                # 测试是否可序列化
                                json.dumps(v)
                                result[k] = v
                            except TypeError:
                                result[k] = json_serializable(v)
                    return result
                
                # 处理单个项目
                def process_item(item):
                    if isinstance(item, dict):
                        return process_dict(item)
                    
                    try:
                        # 测试是否可序列化
                        json.dumps(item)
                        return item
                    except TypeError:
                        return json_serializable(item)
                
                # 检查yearly_stats是否为空，如果为空则从monthly_stats创建
                if 'yearly_stats' not in analysis_data or not analysis_data['yearly_stats']:
                    logger.info("年度统计数据为空，从月度数据生成年度数据")
                    if 'monthly_stats' in analysis_data and analysis_data['monthly_stats']:
                        # 从月度数据创建年度数据
                        monthly_stats = pd.DataFrame(analysis_data['monthly_stats'])
                        yearly_data = monthly_stats.groupby('year').agg({
                            'income': 'sum',
                            'expense': 'sum',
                            'net': 'sum'
                        }).reset_index()
                        yearly_data['year_label'] = yearly_data['year'].astype(str)
                        analysis_data['yearly_stats'] = yearly_data.to_dict('records')
                        logger.info(f"成功从月度数据生成了{len(yearly_data)}条年度数据")
                
                # 序列化处理
                processed_data = process_dict(analysis_data)
                
                # 检查是否有输出文件路径
                if output_file:
                    # 使用UTF-8编码，确保中文正确显示
                    try:
                        logger.info("使用UTF-8编码保存JSON文件")
                        with open(output_file, 'w', encoding='utf-8') as f:
                            json.dump(processed_data, f, ensure_ascii=False, indent=2)
                        logger.info(f"分析数据已保存到: {output_file}")
                    except Exception as e:
                        logger.error(f"保存JSON文件时出错: {e}")
                        import traceback
                        logger.error(traceback.format_exc())
                        return False
                
                return processed_data
            else:
                logger.error("获取分析数据失败")
                return False
        except Exception as e:
            logger.error(f"生成JSON数据时出错: {e}")
            import traceback
            logger.error(traceback.format_exc())
            
            # 尝试找出无法序列化的对象
            self._debug_find_non_serializable(analysis_data)
            
            return False
        
    def _debug_find_non_serializable(self, data, path="root"):
        """递归查找不可序列化的对象"""
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

    def get_transaction_count(self):
        """获取当前加载的交易数据条数"""
        if self.df is None:
            return 0
        return len(self.df)

    def separate_core_transactions(self, percentile_threshold=95, strategy='percentile', min_transaction_count=10, fixed_threshold=None, recurring_only=False):
        """
        将交易分为核心交易和非常规交易
        
        Args:
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
        if self.df.empty:
            return pd.DataFrame(), pd.DataFrame()
            
        # 确保交易数据足够
        if len(self.df) < min_transaction_count:
            logger.warning(f"交易数量({len(self.df)})不足，无法可靠地识别核心交易，返回所有交易作为核心交易")
            return self.df.copy(), pd.DataFrame()
        
        # 预处理：分离收入和支出数据
        income_df = self.df[self.df['amount'] > 0]
        expense_df = self.df[self.df['amount'] < 0]
        
        # 如果收入或支出数据不足，则将所有该类型交易作为核心交易
        if len(income_df) < min_transaction_count / 2:
            logger.info(f"收入交易数量({len(income_df)})不足，将所有收入视为核心收入")
            income_is_core = pd.Series(True, index=income_df.index)
        else:
            income_is_core = self._identify_core_transactions(income_df, is_income=True, 
                                                           percentile_threshold=percentile_threshold,
                                                           strategy=strategy, 
                                                           fixed_threshold=fixed_threshold[0] if fixed_threshold else None,
                                                           recurring_only=recurring_only)
            
        if len(expense_df) < min_transaction_count / 2:
            logger.info(f"支出交易数量({len(expense_df)})不足，将所有支出视为核心支出")
            expense_is_core = pd.Series(True, index=expense_df.index)
        else:
            expense_is_core = self._identify_core_transactions(expense_df, is_income=False, 
                                                            percentile_threshold=percentile_threshold,
                                                            strategy=strategy,
                                                            fixed_threshold=fixed_threshold[1] if fixed_threshold else None,
                                                            recurring_only=recurring_only)
        
        # 合并结果
        is_core = pd.Series(False, index=self.df.index)
        is_core.loc[income_is_core.index] = income_is_core
        is_core.loc[expense_is_core.index] = expense_is_core
        
        # 返回核心交易和非核心交易
        core_transactions = self.df[is_core]
        non_core_transactions = self.df[~is_core]
        
        logger.info(f"核心交易识别完成: 总交易={len(self.df)}, 核心交易={len(core_transactions)}, 非核心交易={len(non_core_transactions)}")
        logger.info(f"使用策略: {strategy}, 百分位阈值: {percentile_threshold}, 仅重复交易: {recurring_only}")
        
        return core_transactions, non_core_transactions
    
    def _identify_core_transactions(self, df, is_income=True, percentile_threshold=95, strategy='percentile', 
                                   fixed_threshold=None, recurring_only=False):
        """
        识别核心交易
        
        Args:
            df: 交易DataFrame
            is_income: 是否为收入交易
            percentile_threshold: 百分位阈值
            strategy: 识别策略
            fixed_threshold: 固定金额阈值
            recurring_only: 是否仅将重复出现的交易视为核心交易
            
        Returns:
            Series: 布尔Series，True表示为核心交易
        """
        if df.empty:
            return pd.Series(dtype=bool)
            
        amounts = df['amount'].abs()
        
        # 预处理：如果recurring_only=True，识别重复出现的交易
        if recurring_only:
            # 根据交易对象和交易描述识别重复交易
            if 'counterparty' in df.columns and 'description' in df.columns:
                # 获取重复出现的交易对象
                repeat_counter = df['counterparty'].value_counts()
                repeat_merchants = set(repeat_counter[repeat_counter > 1].index)
                
                # 标记重复交易
                is_recurring = df['counterparty'].isin(repeat_merchants)
                
                # 对于没有交易对象但有相似描述的交易，也视为重复交易
                if 'description' in df.columns:
                    # 简化描述（移除日期、金额等变化部分）
                    simplified_desc = df['description'].str.replace(r'\d+', '').str.replace(r'[.-]', '')
                    repeat_desc = simplified_desc.value_counts()
                    repeat_descriptions = set(repeat_desc[repeat_desc > 1].index)
                    is_recurring = is_recurring | simplified_desc.isin(repeat_descriptions)
            else:
                # 没有足够信息识别重复交易，忽略recurring_only要求
                logger.warning("缺少交易对象或交易描述字段，无法可靠识别重复交易，忽略recurring_only要求")
                is_recurring = pd.Series(True, index=df.index)
        else:
            # 不要求仅重复交易作为核心交易
            is_recurring = pd.Series(True, index=df.index)
        
        # 根据不同策略识别核心交易
        if strategy == 'percentile':
            # 基于百分位数识别
            if is_income:
                # 收入: 小于95%分位数的为核心收入
                threshold = amounts.quantile(percentile_threshold/100)
                is_core = (amounts <= threshold) & is_recurring
                logger.debug(f"收入百分位阈值: {threshold}, 交易数量: {len(df)}, 核心交易: {is_core.sum()}")
            else:
                # 支出: 小于95%分位数的为核心支出 (注意：这里修改了计算方式，使用直接的percentile_threshold/100)
                # 由于支出的绝对金额越大，说明消费越大，我们希望排除大额消费，所以直接用percentile_threshold/100
                threshold = amounts.quantile(percentile_threshold/100)
                is_core = (amounts <= threshold) & is_recurring
                logger.debug(f"支出百分位阈值: {threshold}, 交易数量: {len(df)}, 核心交易: {is_core.sum()}")
                
        elif strategy == 'fixed':
            # 使用固定阈值
            if fixed_threshold is None:
                logger.warning("未指定固定金额阈值，使用合理的默认值")
                fixed_threshold = 10000 if is_income else 5000
                
            is_core = (amounts <= fixed_threshold) & is_recurring
            logger.debug(f"{'收入' if is_income else '支出'}固定阈值: {fixed_threshold}, 交易数量: {len(df)}, 核心交易: {is_core.sum()}")
            
        elif strategy == 'iqr':
            # 基于四分位距(IQR)方法识别异常值
            Q1 = amounts.quantile(0.25)
            Q3 = amounts.quantile(0.75)
            IQR = Q3 - Q1
            upper_bound = Q3 + 1.5 * IQR
            
            is_core = (amounts <= upper_bound) & is_recurring
            logger.debug(f"{'收入' if is_income else '支出'}IQR上界: {upper_bound}, 交易数量: {len(df)}, 核心交易: {is_core.sum()}")
            
        elif strategy == 'zmm':
            # 基于z-score和中位数偏差的混合方法
            median = amounts.median()
            # 计算与中位数的偏差而不是与均值的偏差（更稳健）
            deviations = abs(amounts - median)
            # 使用中位数绝对偏差(MAD)
            mad = deviations.median()
            # 基于MAD计算稳健z分数（类似于z-score但对异常值不敏感）
            robust_z = 0.6745 * deviations / mad if mad > 0 else deviations
            
            is_core = (robust_z <= 3.5) & is_recurring  # 3.5是一个常用的稳健z分数阈值
            logger.debug(f"{'收入' if is_income else '支出'}中位数: {median}, MAD: {mad}, 交易数量: {len(df)}, 核心交易: {is_core.sum()}")
            
        elif strategy == 'combo':
            # 组合多种方法，更保守的方法（只有当多种方法都认为是核心交易时才视为核心）
            # 百分位数方法
            if is_income:
                p_threshold = amounts.quantile(percentile_threshold/100)
                is_core_p = amounts <= p_threshold
            else:
                # 修正支出的百分位数计算方式
                p_threshold = amounts.quantile(percentile_threshold/100)
                is_core_p = amounts <= p_threshold
                
            # IQR方法
            Q1 = amounts.quantile(0.25)
            Q3 = amounts.quantile(0.75)
            IQR = Q3 - Q1
            upper_bound = Q3 + 1.5 * IQR
            is_core_iqr = amounts <= upper_bound
            
            # 组合结果（交集）
            is_core = (is_core_p & is_core_iqr) & is_recurring
            logger.debug(f"{'收入' if is_income else '支出'}组合策略 - 百分位阈值: {p_threshold}, IQR上界: {upper_bound}, 交易数量: {len(df)}, 核心交易: {is_core.sum()}")
            
        else:
            # 默认回退到百分位数方法
            logger.warning(f"未知策略: {strategy}, 使用默认的百分位数方法")
            if is_income:
                threshold = amounts.quantile(percentile_threshold/100)
                is_core = (amounts <= threshold) & is_recurring
            else:
                # 修正默认回退的支出百分位数计算
                threshold = amounts.quantile(percentile_threshold/100)
                is_core = (amounts <= threshold) & is_recurring
        
        return is_core
    
    def get_core_transaction_stats(self, percentile_threshold=95, strategy='percentile', 
                                  fixed_threshold=None, recurring_only=False):
        """
        获取核心交易的统计数据
        
        Args:
            percentile_threshold: 金额百分位阈值，用于识别非常规交易
            strategy: 识别核心交易的策略
            fixed_threshold: 固定金额阈值，仅当strategy='fixed'时使用
            recurring_only: 是否仅将重复出现的交易视为核心交易
            
        Returns:
            dict: 核心交易的统计信息
        """
        core_trans, non_core_trans = self.separate_core_transactions(
            percentile_threshold=percentile_threshold,
            strategy=strategy,
            fixed_threshold=fixed_threshold,
            recurring_only=recurring_only
        )
        
        if core_trans.empty:
            return {
                'core_income': 0,
                'core_expense': 0,
                'core_net': 0,
                'core_transaction_count': 0,
                'core_percentage': 0,
                'core_income_count': 0,
                'core_expense_count': 0
            }
            
        core_income_df = core_trans[core_trans['amount'] > 0]
        core_expense_df = core_trans[core_trans['amount'] < 0]
        
        core_income = core_income_df['amount'].sum()
        core_expense = core_expense_df['amount'].sum()
        core_net = core_income + core_expense
        
        return {
            'core_income': core_income,
            'core_expense': core_expense,
            'core_net': core_net,
            'core_transaction_count': len(core_trans),
            'core_percentage': len(core_trans) / len(self.df) * 100 if not self.df.empty else 0,
            'core_income_count': len(core_income_df),
            'core_expense_count': len(core_expense_df),
            'core_transactions': core_trans.to_dict('records') if not core_trans.empty else []
        }

    def detect_outlier_transactions(self, method='iqr', threshold=1.5):
        """
        检测异常的交易记录
        
        Args:
            method: 检测方法，'iqr'(四分位距法) 或 'zscore'(Z分数法)
            threshold: IQR法的倍数阈值或Z分数法的标准差阈值
            
        Returns:
            DataFrame: 含异常标记的交易数据
        """
        if self.df.empty:
            return pd.DataFrame()
            
        # 创建结果DataFrame的副本，添加异常标记列
        result_df = self.df.copy()
        result_df['是否异常'] = False
        result_df['异常类型'] = ''
        result_df['异常分数'] = 0.0
        
        # 分别处理收入和支出
        for trans_type, condition in [('收入', self.df['amount'] > 0), ('支出', self.df['amount'] < 0)]:
            type_df = self.df[condition]
            if type_df.empty:
                continue
                
            amounts = type_df['amount'].abs()  # 取绝对值进行计算
            
            if method == 'iqr':
                # 四分位距法 (IQR)
                Q1 = amounts.quantile(0.25)
                Q3 = amounts.quantile(0.75)
                IQR = Q3 - Q1
                lower_bound = Q1 - threshold * IQR
                upper_bound = Q3 + threshold * IQR
                
                # 标记异常值
                outliers = type_df[
                    (amounts < lower_bound) | (amounts > upper_bound)
                ]
                
                # 计算异常分数 (与上界的距离，按IQR归一化)
                for idx in outliers.index:
                    amount = amounts.loc[idx]
                    if amount > upper_bound:
                        result_df.loc[idx, '异常分数'] = (amount - upper_bound) / IQR
                        result_df.loc[idx, '异常类型'] = f'异常{trans_type}'
                        result_df.loc[idx, '是否异常'] = True
                        
            elif method == 'zscore':
                # Z分数法
                mean = amounts.mean()
                std = amounts.std()
                
                if std == 0:  # 避免除以零
                    continue
                    
                # 计算Z分数
                z_scores = (amounts - mean) / std
                
                # 标记异常值
                outliers = type_df[abs(z_scores) > threshold]
                
                # 记录异常分数
                for idx in outliers.index:
                    result_df.loc[idx, '异常分数'] = abs(z_scores.loc[idx])
                    result_df.loc[idx, '异常类型'] = f'异常{trans_type}'
                    result_df.loc[idx, '是否异常'] = True
        
        return result_df
    
    def get_outlier_stats(self, method='iqr', threshold=1.5):
        """
        获取异常交易的统计信息
        
        Args:
            method: 检测方法，'iqr'或'zscore'
            threshold: 阈值
            
        Returns:
            dict: 异常交易的统计信息
        """
        result_df = self.detect_outlier_transactions(method, threshold)
        
        if result_df.empty:
            return {
                'outlier_count': 0,
                'outlier_income_count': 0, 
                'outlier_expense_count': 0,
                'outlier_income_amount': 0,
                'outlier_expense_amount': 0,
                'outlier_percentage': 0,
                'outliers': []
            }
            
        # 提取异常交易
        outliers = result_df[result_df['是否异常']]
        
        # 按异常分数排序
        outliers = outliers.sort_values('异常分数', ascending=False)
        
        # 统计异常收入和支出
        outlier_income = outliers[outliers['amount'] > 0]
        outlier_expense = outliers[outliers['amount'] < 0]
        
        # 构建返回的统计信息
        stats = {
            'outlier_count': len(outliers),
            'outlier_income_count': len(outlier_income),
            'outlier_expense_count': len(outlier_expense),
            'outlier_income_amount': outlier_income['amount'].sum() if not outlier_income.empty else 0,
            'outlier_expense_amount': outlier_expense['amount'].sum() if not outlier_expense.empty else 0,
            'outlier_percentage': len(outliers) / len(self.df) * 100 if not self.df.empty else 0,
            'outliers': outliers.head(10).to_dict('records')  # 取前10条异常交易
        }
        
        return stats

    def get_summary(self):
        """获取交易数据的总体摘要"""
        if self.df is None or len(self.df) == 0:
            logger.warning("无法获取摘要，数据为空")
            return None
        
        try:
            start_date = self.df['transaction_date'].min()
            end_date = self.df['transaction_date'].max()
            total_income = self.df[self.df['amount'] > 0]['amount'].sum()
            total_expense = abs(self.df[self.df['amount'] < 0]['amount'].sum())
            
            # 确保start_date和end_date是datetime对象
            if not isinstance(start_date, datetime):
                start_date = pd.to_datetime(start_date)
            if not isinstance(end_date, datetime):
                end_date = pd.to_datetime(end_date)
            
            days_count = (end_date - start_date).days
            avg_daily_expense = total_expense / days_count if days_count > 0 else 0
            
            # 计算转账相关统计（仍然计算但不用于前端过滤）
            transfer_df = self.df[self.df['category'] == '转账']
            transfer_amount = abs(transfer_df[transfer_df['amount'] < 0]['amount'].sum())
            transfer_count = len(transfer_df[transfer_df['amount'] < 0])
            
            # 计算数据 - 获取账户余额信息（需要通过db_manager）
            latest_balance = 0
            try:
                balance_summary = self.db_manager.get_balance_summary()
                latest_balance = sum(float(account.get('latest_balance', 0) or 0) for account in balance_summary)
            except Exception as e:
                logger.error(f"获取账户余额时出错: {e}")
            
            # 计算还能支撑多少天
            remaining_funds = latest_balance
            days_coverage = remaining_funds / avg_daily_expense if avg_daily_expense > 0 else 0
            
            return {
                'start_date': start_date.strftime('%Y-%m-%d') if not pd.isna(start_date) else '',
                'end_date': end_date.strftime('%Y-%m-%d') if not pd.isna(end_date) else '',
                'total_income': float(total_income) if not pd.isna(total_income) else 0,
                'total_expense': float(total_expense) if not pd.isna(total_expense) else 0,
                'net_amount': float(total_income - total_expense) if not (pd.isna(total_income) or pd.isna(total_expense)) else 0,
                'daily_avg_expense': float(avg_daily_expense) if not pd.isna(avg_daily_expense) else 0,
                'transaction_count': int(len(self.df)),
                'income_count': int(len(self.df[self.df['amount'] > 0])),
                'expense_count': int(len(self.df[self.df['amount'] < 0])),
                'transfer_amount': float(transfer_amount) if not pd.isna(transfer_amount) else 0,
                'transfer_count': int(transfer_count),
                'remaining_funds': float(remaining_funds),
                'days_coverage': float(days_coverage)
            }
        except Exception as e:
            logger.error(f"获取摘要数据时出错: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {}
    
    def get_monthly_stats_direct(self, start_date=None, end_date=None, account_id=None):
        """直接从数据库获取月度统计数据
        
        Args:
            start_date: 开始日期，格式：YYYY-MM-DD
            end_date: 结束日期，格式：YYYY-MM-DD
            account_id: 账户ID，如果为None则加载所有账户数据
            
        Returns:
            DataFrame: 月度统计数据
        """
        df = self.get_transactions_direct(start_date, end_date, account_id)
        if df is None or len(df) == 0:
            logger.warning("无法获取月度统计，数据为空")
            return pd.DataFrame()
        
        logger.info("开始获取月度统计数据")
        try:
            # 按年月分组
            logger.info("开始按年月分组数据")
            monthly_data = df.groupby(['year', 'month']).agg({
                'amount': [
                    ('income', lambda x: x[x > 0].sum()),
                    ('expense', lambda x: abs(x[x < 0].sum())),
                    ('net', 'sum')
                ]
            })
            
            # 重置索引，并展平多级列
            monthly_data = monthly_data.reset_index()
            monthly_data.columns = ['year', 'month', 'income', 'expense', 'net']
            
            # 添加月份标签
            monthly_data['month_label'] = monthly_data.apply(lambda row: f"{int(row['year'])}-{int(row['month']):02d}", axis=1)
            
            # 排序
            monthly_data = monthly_data.sort_values(['year', 'month'])
            
            logger.info(f"月度统计数据生成成功，行数: {len(monthly_data)}")
            return monthly_data
        except Exception as e:
            logger.error(f"获取月度统计数据时出错: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return pd.DataFrame()  # 返回空DataFrame而不是None，避免后续处理错误
    
    def get_yearly_stats_direct(self, start_date=None, end_date=None, account_id=None):
        """直接从数据库获取年度统计数据
        
        Args:
            start_date: 开始日期，格式：YYYY-MM-DD
            end_date: 结束日期，格式：YYYY-MM-DD
            account_id: 账户ID，如果为None则加载所有账户数据
            
        Returns:
            DataFrame: 年度统计数据
        """
        df = self.get_transactions_direct(start_date, end_date, account_id)
        if df is None or len(df) == 0:
            logger.warning("无法获取年度统计，数据为空")
            return pd.DataFrame()
        
        logger.info("开始获取年度统计数据")
        try:
            # 按年分组
            logger.info("开始按年分组数据")
            yearly_data = df.groupby(['year']).agg({
                'amount': [
                    ('income', lambda x: x[x > 0].sum()),
                    ('expense', lambda x: abs(x[x < 0].sum())),
                    ('net', 'sum')
                ]
            })
            
            # 重置索引，并展平多级列
            yearly_data = yearly_data.reset_index()
            yearly_data.columns = ['year', 'income', 'expense', 'net']
            
            # 添加年份标签为字符串类型
            yearly_data['year_label'] = yearly_data['year'].astype(str)
            
            # 排序
            yearly_data = yearly_data.sort_values(['year'])
            
            logger.info(f"年度统计数据生成成功，行数: {len(yearly_data)}")
            return yearly_data
        except Exception as e:
            logger.error(f"获取年度统计数据时出错: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return pd.DataFrame()  # 返回空DataFrame而不是None，避免后续处理错误
    
    def get_category_stats_direct(self, start_date=None, end_date=None, account_id=None):
        """直接从数据库获取分类统计数据
        
        Args:
            start_date: 开始日期，格式：YYYY-MM-DD
            end_date: 结束日期，格式：YYYY-MM-DD
            account_id: 账户ID，如果为None则加载所有账户数据
            
        Returns:
            DataFrame: 分类统计数据
        """
        df = self.get_transactions_direct(start_date, end_date, account_id)
        if df is None or len(df) == 0:
            logger.warning("无法获取分类统计，数据为空")
            return pd.DataFrame()
        
        try:
            # 支出类别统计
            expense_df = df[df['amount'] < 0]
            category_stats = expense_df.groupby('category').agg({
                'amount': [
                    ('total', lambda x: abs(x.sum())),
                    ('count', 'count'),
                    ('average', lambda x: abs(x.mean()))
                ]
            })
            
            # 重置索引，并展平多级列
            category_stats = category_stats.reset_index()
            category_stats.columns = ['category', 'total', 'count', 'average']
            
            # 计算占比
            total_expense = category_stats['total'].sum()
            category_stats['percentage'] = category_stats['total'] / total_expense * 100
            
            # 排序
            category_stats = category_stats.sort_values('total', ascending=False)
            
            return category_stats
        except Exception as e:
            logger.error(f"获取分类统计数据时出错: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return pd.DataFrame()
            
    def get_weekly_stats_direct(self, start_date=None, end_date=None, account_id=None):
        """直接从数据库获取按星期统计的消费数据
        
        Args:
            start_date: 开始日期，格式：YYYY-MM-DD
            end_date: 结束日期，格式：YYYY-MM-DD
            account_id: 账户ID，如果为None则加载所有账户数据
            
        Returns:
            DataFrame: 周度统计数据
        """
        logger.info(f"开始获取周度统计数据: start_date={start_date}, end_date={end_date}, account_id={account_id}")
        
        df = self.get_transactions_direct(start_date, end_date, account_id)
        if df is None:
            logger.warning("无法获取周度统计，数据为None")
            return pd.DataFrame()
            
        if len(df) == 0:
            logger.warning("无法获取周度统计，数据为空")
            return pd.DataFrame()
        
        logger.info(f"成功获取{len(df)}条交易数据进行周度统计")
        logger.info(f"数据列: {df.columns.tolist()}")
            
        try:
            # 只考虑支出
            expense_df = df[df['amount'] < 0]
            logger.info(f"支出交易数量: {len(expense_df)}")
            
            if expense_df.empty:
                logger.warning("没有支出交易数据，无法进行周度统计")
                return pd.DataFrame()
            
            if 'weekday' not in df.columns:
                logger.warning("交易数据中缺少weekday列，尝试添加")
                if 'transaction_date' in df.columns:
                    df['weekday'] = pd.to_datetime(df['transaction_date']).dt.dayofweek
                    expense_df = df[df['amount'] < 0]
                else:
                    logger.error("交易数据中缺少transaction_date列，无法进行周度统计")
                    return pd.DataFrame()
            
            # 按星期分组
            logger.info("开始按星期分组统计数据")
            weekday_stats = expense_df.groupby('weekday').agg({
                'amount': [
                    ('total', lambda x: abs(x.sum())),
                    ('count', 'count'),
                    ('average', lambda x: abs(x.mean()))
                ]
            })
            
            # 重置索引，并展平多级列
            weekday_stats = weekday_stats.reset_index()
            weekday_stats.columns = ['weekday', 'total', 'count', 'average']
            
            logger.info(f"星期分组统计结果: {len(weekday_stats)}行")
            if not weekday_stats.empty:
                logger.info(f"星期统计样本: {weekday_stats.head().to_dict('records')}")
            
            # 添加星期标签
            weekday_names = {
                0: '周一',
                1: '周二',
                2: '周三',
                3: '周四',
                4: '周五',
                5: '周六',
                6: '周日'
            }
            weekday_stats['weekday_name'] = weekday_stats['weekday'].map(weekday_names)
            
            # 排序
            weekday_stats = weekday_stats.sort_values('weekday')
            
            logger.info(f"周度统计数据生成成功: {len(weekday_stats)}行")
            return weekday_stats
        except Exception as e:
            logger.error(f"获取周度统计数据时出错: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return pd.DataFrame()
            
    def get_daily_stats_direct(self, start_date=None, end_date=None, account_id=None):
        """直接从数据库获取日消费统计数据
        
        Args:
            start_date: 开始日期，格式：YYYY-MM-DD
            end_date: 结束日期，格式：YYYY-MM-DD
            account_id: 账户ID，如果为None则加载所有账户数据
            
        Returns:
            DataFrame: 日度统计数据
        """
        df = self.get_transactions_direct(start_date, end_date, account_id)
        if df is None or len(df) == 0:
            logger.warning("无法获取日度统计，数据为空")
            return pd.DataFrame()
        
        try:
            # 只考虑支出
            expense_df = df[df['amount'] < 0]
            
            # 按日期分组
            daily_stats = expense_df.groupby('transaction_date').agg({
                'amount': [
                    ('total', lambda x: abs(x.sum())),
                    ('count', 'count')
                ]
            })
            
            # 重置索引，并展平多级列
            daily_stats = daily_stats.reset_index()
            daily_stats.columns = ['date', 'total', 'count']
            
            # 将日期转为字符串，解决JSON序列化问题
            daily_stats['date'] = daily_stats['date'].dt.strftime('%Y-%m-%d')
            
            # 排序
            daily_stats = daily_stats.sort_values('date')
            
            return daily_stats
        except Exception as e:
            logger.error(f"获取日度统计数据时出错: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return pd.DataFrame()
    
    def get_top_merchants_direct(self, start_date=None, end_date=None, account_id=None, n=10):
        """直接从数据库获取交易次数最多的商户
        
        Args:
            start_date: 开始日期，格式：YYYY-MM-DD
            end_date: 结束日期，格式：YYYY-MM-DD
            account_id: 账户ID，如果为None则加载所有账户数据
            n: 返回的商户数量
            
        Returns:
            dict: 包含按交易次数和金额排序的商户数据
        """
        df = self.get_transactions_direct(start_date, end_date, account_id)
        if df is None or len(df) == 0:
            logger.warning("无法获取热门商户，数据为空")
            return {'by_count': pd.DataFrame(), 'by_amount': pd.DataFrame()}
        
        try:
            # 只考虑支出
            expense_df = df[df['amount'] < 0]
            
            # 按商户分组
            merchant_stats = expense_df.groupby('counterparty').agg({
                'amount': [
                    ('total', lambda x: abs(x.sum())),
                    ('count', 'count'),
                    ('average', lambda x: abs(x.mean()))
                ]
            })
            
            # 重置索引，并展平多级列
            merchant_stats = merchant_stats.reset_index()
            merchant_stats.columns = ['merchant', 'total', 'count', 'average']
            
            # 排序并取前N个
            top_by_count = merchant_stats.sort_values('count', ascending=False).head(n)
            top_by_amount = merchant_stats.sort_values('total', ascending=False).head(n)
            
            return {
                'by_count': top_by_count,
                'by_amount': top_by_amount
            }
        except Exception as e:
            logger.error(f"获取热门商户数据时出错: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {'by_count': pd.DataFrame(), 'by_amount': pd.DataFrame()}

    def analyze_transaction_data_direct(self, start_date=None, end_date=None, account_id=None):
        """直接从数据库获取并分析交易数据，返回完整的分析结果
        
        Args:
            start_date: 开始日期，格式：YYYY-MM-DD
            end_date: 结束日期，格式：YYYY-MM-DD
            account_id: 账户ID，如果为None则加载所有账户数据
            
        Returns:
            dict: 包含所有分析结果的字典
        """
        logger.info(f"开始直接分析交易数据: start_date={start_date}, end_date={end_date}, account_id={account_id}")
        
        # 获取交易数据，用于提取原始交易记录
        df = self.get_transactions_direct(start_date, end_date, account_id)
        if df is None or df.empty:
            logger.warning("无法获取交易数据，返回空结果")
            return {}
            
        try:
            # 获取各种统计数据
            summary = self.get_summary_direct(start_date, end_date, account_id)
            if summary is None:
                logger.error("获取摘要数据失败")
                summary = {}
                
            monthly_stats = self.get_monthly_stats_direct(start_date, end_date, account_id)
            if monthly_stats.empty:
                logger.error("获取月度统计数据失败")
                monthly_stats = pd.DataFrame(columns=['year', 'month', 'income', 'expense', 'net', 'month_label'])
                
            yearly_stats = self.get_yearly_stats_direct(start_date, end_date, account_id)
            if yearly_stats.empty:
                logger.error("获取年度统计数据失败")
                yearly_stats = pd.DataFrame(columns=['year', 'income', 'expense', 'net', 'year_label'])
                
            category_stats = self.get_category_stats_direct(start_date, end_date, account_id)
            if category_stats.empty:
                logger.error("获取分类统计数据失败")
                category_stats = pd.DataFrame()
                
            weekly_stats = self.get_weekly_stats_direct(start_date, end_date, account_id)
            if weekly_stats.empty:
                logger.error("获取周度统计数据失败")
                weekly_stats = pd.DataFrame()
                
            daily_stats = self.get_daily_stats_direct(start_date, end_date, account_id)
            if daily_stats.empty:
                logger.error("获取日度统计数据失败")
                daily_stats = pd.DataFrame()
                
            top_merchants = self.get_top_merchants_direct(start_date, end_date, account_id)
            if 'by_count' not in top_merchants or top_merchants['by_count'].empty:
                logger.error("获取热门商户数据失败")
                top_merchants = {'by_count': pd.DataFrame(), 'by_amount': pd.DataFrame()}
                
            # 准备原始交易数据
            transactions = []
            if not df.empty:
                # 确保交易日期是字符串格式
                transaction_df = df.copy()
                if 'transaction_date' in transaction_df.columns:
                    transaction_df['transaction_date'] = transaction_df['transaction_date'].dt.strftime('%Y-%m-%d')
                
                # 转换为字典列表
                try:
                    transactions = transaction_df.to_dict('records')
                    logger.info(f"成功转换 {len(transactions)} 条交易记录")
                except Exception as e:
                    logger.error(f"转换交易记录时出错: {e}")
                    transactions = []
            
            # 组织返回结果
            results = {
                'summary': summary,
                'monthly_stats': monthly_stats.to_dict('records') if not monthly_stats.empty else [],
                'yearly_stats': yearly_stats.to_dict('records') if not yearly_stats.empty else [],
                'category_stats': category_stats.to_dict('records') if not category_stats.empty else [],
                'weekly_stats': weekly_stats.to_dict('records') if not weekly_stats.empty else [],
                'daily_stats': daily_stats.to_dict('records') if not daily_stats.empty else [],
                'top_merchants': {
                    'by_count': top_merchants['by_count'].to_dict('records') if 'by_count' in top_merchants and not top_merchants['by_count'].empty else [],
                    'by_amount': top_merchants['by_amount'].to_dict('records') if 'by_amount' in top_merchants and not top_merchants['by_amount'].empty else []
                },
                'transactions': transactions
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
        """直接从数据库获取核心交易的统计数据
        
        Args:
            start_date: 开始日期，格式：YYYY-MM-DD
            end_date: 结束日期，格式：YYYY-MM-DD
            account_id: 账户ID，如果为None则加载所有账户数据
            percentile_threshold: 金额百分位阈值，用于识别非常规交易
            strategy: 识别核心交易的策略
            fixed_threshold: 固定金额阈值，仅当strategy='fixed'时使用
            recurring_only: 是否仅将重复出现的交易视为核心交易
            
        Returns:
            dict: 核心交易的统计信息
        """
        # 获取交易数据
        df = self.get_transactions_direct(start_date, end_date, account_id)
        if df is None or df.empty:
            logger.warning("无法获取交易数据，返回空结果")
            return {
                'core_income': 0,
                'core_expense': 0,
                'core_net': 0,
                'core_transaction_count': 0,
                'core_percentage': 0,
                'core_income_count': 0,
                'core_expense_count': 0
            }
            
        # 临时设置实例的df属性
        temp_df = self.df
        self.df = df
        
        try:
            # 调用现有方法识别核心交易
            core_trans, non_core_trans = self.separate_core_transactions(
                percentile_threshold=percentile_threshold,
                strategy=strategy,
                fixed_threshold=fixed_threshold,
                recurring_only=recurring_only
            )
            
            # 计算统计数据
            if core_trans.empty:
                result = {
                    'core_income': 0,
                    'core_expense': 0,
                    'core_net': 0,
                    'core_transaction_count': 0,
                    'core_percentage': 0,
                    'core_income_count': 0,
                    'core_expense_count': 0
                }
            else:
                core_income_df = core_trans[core_trans['amount'] > 0]
                core_expense_df = core_trans[core_trans['amount'] < 0]
                
                core_income = core_income_df['amount'].sum()
                core_expense = core_expense_df['amount'].sum()
                core_net = core_income + core_expense
                
                # 转换交易日期格式
                if not core_trans.empty:
                    core_trans_copy = core_trans.copy()
                    if 'transaction_date' in core_trans_copy.columns:
                        core_trans_copy['transaction_date'] = core_trans_copy['transaction_date'].dt.strftime('%Y-%m-%d')
                    core_transactions = core_trans_copy.to_dict('records')
                else:
                    core_transactions = []
                
                result = {
                    'core_income': core_income,
                    'core_expense': core_expense,
                    'core_net': core_net,
                    'core_transaction_count': len(core_trans),
                    'core_percentage': len(core_trans) / len(df) * 100 if not df.empty else 0,
                    'core_income_count': len(core_income_df),
                    'core_expense_count': len(core_expense_df),
                    'core_transactions': core_transactions
                }
        finally:
            # 恢复原始df
            self.df = temp_df
            
        return result
        
    def get_outlier_stats_direct(self, start_date=None, end_date=None, account_id=None, 
                                method='iqr', threshold=1.5):
        """直接从数据库获取异常交易的统计信息
        
        Args:
            start_date: 开始日期，格式：YYYY-MM-DD
            end_date: 结束日期，格式：YYYY-MM-DD
            account_id: 账户ID，如果为None则加载所有账户数据
            method: 检测方法，'iqr'或'zscore'
            threshold: 阈值
            
        Returns:
            dict: 异常交易的统计信息
        """
        # 获取交易数据
        df = self.get_transactions_direct(start_date, end_date, account_id)
        if df is None or df.empty:
            logger.warning("无法获取交易数据，返回空结果")
            return {
                'outlier_count': 0,
                'outlier_income_count': 0, 
                'outlier_expense_count': 0,
                'outlier_income_amount': 0,
                'outlier_expense_amount': 0,
                'outlier_percentage': 0,
                'outliers': []
            }
            
        # 临时设置实例的df属性
        temp_df = self.df
        self.df = df
        
        try:
            # 检测异常交易
            result_df = self.detect_outlier_transactions(method, threshold)
            
            if result_df.empty:
                return {
                    'outlier_count': 0,
                    'outlier_income_count': 0, 
                    'outlier_expense_count': 0,
                    'outlier_income_amount': 0,
                    'outlier_expense_amount': 0,
                    'outlier_percentage': 0,
                    'outliers': []
                }
                
            # 提取异常交易
            outliers = result_df[result_df['是否异常']]
            
            # 按异常分数排序
            outliers = outliers.sort_values('异常分数', ascending=False)
            
            # 统计异常收入和支出
            outlier_income = outliers[outliers['amount'] > 0]
            outlier_expense = outliers[outliers['amount'] < 0]
            
            # 转换日期格式
            outliers_head = outliers.head(10).copy()
            if 'transaction_date' in outliers_head.columns:
                outliers_head['transaction_date'] = outliers_head['transaction_date'].dt.strftime('%Y-%m-%d')
            
            # 构建返回的统计信息
            stats = {
                'outlier_count': len(outliers),
                'outlier_income_count': len(outlier_income),
                'outlier_expense_count': len(outlier_expense),
                'outlier_income_amount': outlier_income['amount'].sum() if not outlier_income.empty else 0,
                'outlier_expense_amount': outlier_expense['amount'].sum() if not outlier_expense.empty else 0,
                'outlier_percentage': len(outliers) / len(df) * 100 if not df.empty else 0,
                'outliers': outliers_head.to_dict('records')  # 取前10条异常交易
            }
            
            return stats
        finally:
            # 恢复原始df
            self.df = temp_df

# 使用示例
if __name__ == "__main__":
    # 创建分析器实例
    analyzer = TransactionAnalyzer()
    
    # 从数据库加载最近一年的数据
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
    
    # 直接从数据库分析，无需先加载数据
    analysis_results = analyzer.analyze_transaction_data_direct(start_date=start_date, end_date=end_date)
    
    # 生成输出文件路径
    output_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'analysis_data.json')
    
    # 将结果保存到JSON文件
    if analysis_results:
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                # 使用自定义的json序列化函数处理不可直接序列化的类型
                def json_serializable(obj):
                    if isinstance(obj, (pd.Timestamp, datetime, datetime.date)):
                        return obj.strftime('%Y-%m-%d')
                    if isinstance(obj, np.int64):
                        return int(obj)
                    if isinstance(obj, np.float64):
                        return float(obj)
                    if callable(obj):
                        return str(obj)
                    raise TypeError(f"无法序列化对象类型: {type(obj)}")
                
                json.dump(analysis_results, f, ensure_ascii=False, indent=2, default=json_serializable)
            print(f"分析数据已保存到 {output_file}")
        except Exception as e:
            print(f"保存分析数据失败: {e}")
    else:
        print("生成分析数据失败") 