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
from scripts.db_manager import DBManager

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
            
            # 重命名列以匹配原有代码
            column_mapping = {
                'transaction_date': '交易日期',
                'amount': '交易金额',
                'counterparty': '交易对象',
                'description': '交易描述',
                'category': '交易分类',
                'transaction_type': '交易类型',
                'account_number': '账号',
                'bank_name': '银行'
            }
            self.df = self.df.rename(columns=column_mapping)
            
            # 确保交易日期是日期类型
            self.df['交易日期'] = pd.to_datetime(self.df['交易日期'])
            
            # 从日期字段提取年月日星期
            self.df['年'] = self.df['交易日期'].dt.year
            self.df['月'] = self.df['交易日期'].dt.month
            self.df['日'] = self.df['交易日期'].dt.day
            self.df['星期'] = self.df['交易日期'].dt.dayofweek
            
            # 添加分类
            self.categorize_transactions()
            
            logger.info(f"成功从数据库加载 {len(self.df)} 条交易记录")
            return True
            
        except Exception as e:
            logger.error(f"从数据库加载数据失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
    
    def categorize_transactions(self):
        """根据交易描述对交易进行分类"""
        # 创建分类函数
        def get_category(row):
            # 收入类别
            if row['交易金额'] > 0:
                if '工资' in row['交易类型'] or '工资' in str(row['交易对象']):
                    return '工资'
                elif '退款' in row['交易类型']:
                    return '退款'
                elif '结息' in row['交易类型']:
                    return '利息'
                else:
                    return '其他收入'
            # 支出类别
            else:
                # 转账类
                if '转账' in row['交易类型'] or '转账' in str(row['交易对象']) or '汇款' in row['交易类型']:
                    return '转账'
                    
                # 其他支出类别
                transaction_info = f"{row['交易类型']} {row['交易对象']}"
                for category, keywords in self.categories.items():
                    for keyword in keywords:
                        if keyword in transaction_info:
                            return category
                
                # 如果没有匹配到任何类别，返回"其他"
                return '其他'
        
        # 应用分类函数
        self.df['交易分类'] = self.df.apply(get_category, axis=1)
    
    def get_summary(self):
        """获取交易数据的总体摘要"""
        if self.df is None or len(self.df) == 0:
            logger.warning("无法获取摘要，数据为空")
            return None
        
        try:
            start_date = self.df['交易日期'].min()
            end_date = self.df['交易日期'].max()
            total_income = self.df[self.df['交易金额'] > 0]['交易金额'].sum()
            total_expense = abs(self.df[self.df['交易金额'] < 0]['交易金额'].sum())
            
            # 确保start_date和end_date是datetime对象
            if not isinstance(start_date, datetime):
                start_date = pd.to_datetime(start_date)
            if not isinstance(end_date, datetime):
                end_date = pd.to_datetime(end_date)
            
            avg_daily_expense = total_expense / (end_date - start_date).days if (end_date - start_date).days > 0 else 0
            
            # 计算转账相关统计（仍然计算但不用于前端过滤）
            transfer_df = self.df[self.df['交易分类'] == '转账']
            transfer_amount = abs(transfer_df[transfer_df['交易金额'] < 0]['交易金额'].sum())
            transfer_count = len(transfer_df[transfer_df['交易金额'] < 0])
            
            return {
                '起始日期': start_date.strftime('%Y-%m-%d') if not pd.isna(start_date) else '',
                '结束日期': end_date.strftime('%Y-%m-%d') if not pd.isna(end_date) else '',
                '总收入': float(total_income) if not pd.isna(total_income) else 0,
                '总支出': float(total_expense) if not pd.isna(total_expense) else 0,
                '净收支': float(total_income - total_expense) if not (pd.isna(total_income) or pd.isna(total_expense)) else 0,
                '日均支出': float(avg_daily_expense) if not pd.isna(avg_daily_expense) else 0,
                '交易笔数': int(len(self.df)),
                '收入笔数': int(len(self.df[self.df['交易金额'] > 0])),
                '支出笔数': int(len(self.df[self.df['交易金额'] < 0])),
                '转账总额': float(transfer_amount) if not pd.isna(transfer_amount) else 0,
                '转账笔数': int(transfer_count)
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
            if '年' not in self.df.columns or '月' not in self.df.columns:
                logger.error("数据中缺少'年'或'月'列")
                # 如果缺少这些列，尝试从交易日期重新生成
                logger.info("尝试从交易日期重新生成年月列")
                self.df['年'] = self.df['交易日期'].dt.year
                self.df['月'] = self.df['交易日期'].dt.month
            
            # 记录分组前的年月数据样本
            year_samples = self.df['年'].head(10).tolist()
            month_samples = self.df['月'].head(10).tolist()
            logger.info(f"年列样本数据: {year_samples}")
            logger.info(f"月列样本数据: {month_samples}")
            
            # 按年月分组
            logger.info("开始按年月分组数据")
            monthly_data = self.df.groupby(['年', '月']).agg({
                '交易金额': [
                    ('收入', lambda x: x[x > 0].sum()),
                    ('支出', lambda x: abs(x[x < 0].sum())),
                    ('净额', 'sum')
                ]
            })
            
            # 重置索引，并展平多级列
            monthly_data = monthly_data.reset_index()
            monthly_data.columns = ['年', '月', '收入', '支出', '净额']
            
            # 添加月份标签
            monthly_data['月份'] = monthly_data.apply(lambda row: f"{int(row['年'])}-{int(row['月']):02d}", axis=1)
            
            # 排序
            monthly_data = monthly_data.sort_values(['年', '月'])
            
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
            if '年' not in self.df.columns:
                logger.error("数据中缺少'年'列")
                # 如果缺少年列，尝试从交易日期重新生成
                logger.info("尝试从交易日期重新生成年列")
                self.df['年'] = self.df['交易日期'].dt.year
            
            # 记录分组前的年数据样本
            year_samples = self.df['年'].head(10).tolist()
            logger.info(f"年列样本数据: {year_samples}")
            
            # 按年分组
            logger.info("开始按年分组数据")
            yearly_data = self.df.groupby(['年']).agg({
                '交易金额': [
                    ('收入', lambda x: x[x > 0].sum()),
                    ('支出', lambda x: abs(x[x < 0].sum())),
                    ('净额', 'sum')
                ]
            })
            
            # 重置索引，并展平多级列
            yearly_data = yearly_data.reset_index()
            yearly_data.columns = ['年', '收入', '支出', '净额']
            
            # 添加年份标签为字符串类型
            yearly_data['年份'] = yearly_data['年'].astype(str)
            
            # 排序
            yearly_data = yearly_data.sort_values(['年'])
            
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
        expense_df = self.df[self.df['交易金额'] < 0]
        category_stats = expense_df.groupby('交易分类').agg({
            '交易金额': [
                ('总额', lambda x: abs(x.sum())),
                ('笔数', 'count'),
                ('平均值', lambda x: abs(x.mean()))
            ]
        })
        
        # 重置索引，并展平多级列
        category_stats = category_stats.reset_index()
        category_stats.columns = ['分类', '总额', '笔数', '平均值']
        
        # 计算占比
        total_expense = category_stats['总额'].sum()
        category_stats['占比'] = category_stats['总额'] / total_expense * 100
        
        # 排序
        category_stats = category_stats.sort_values('总额', ascending=False)
        
        return category_stats
    
    def get_weekly_stats(self):
        """获取按星期统计的消费数据"""
        if self.df is None or len(self.df) == 0:
            return None
        
        # 只考虑支出
        expense_df = self.df[self.df['交易金额'] < 0]
        
        # 按星期分组
        weekday_stats = expense_df.groupby('星期').agg({
            '交易金额': [
                ('总额', lambda x: abs(x.sum())),
                ('笔数', 'count'),
                ('平均值', lambda x: abs(x.mean()))
            ]
        })
        
        # 重置索引，并展平多级列
        weekday_stats = weekday_stats.reset_index()
        weekday_stats.columns = ['星期', '总额', '笔数', '平均值']
        
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
        weekday_stats['星期名'] = weekday_stats['星期'].map(weekday_names)
        
        # 排序
        weekday_stats = weekday_stats.sort_values('星期')
        
        return weekday_stats
    
    def get_daily_stats(self):
        """获取日消费统计数据"""
        if self.df is None or len(self.df) == 0:
            return None
        
        # 只考虑支出
        expense_df = self.df[self.df['交易金额'] < 0]
        
        # 按日期分组
        daily_stats = expense_df.groupby('交易日期').agg({
            '交易金额': [
                ('总额', lambda x: abs(x.sum())),
                ('笔数', 'count')
            ]
        })
        
        # 重置索引，并展平多级列
        daily_stats = daily_stats.reset_index()
        daily_stats.columns = ['日期', '总额', '笔数']
        
        # 将日期转为字符串，解决JSON序列化问题
        daily_stats['日期'] = daily_stats['日期'].dt.strftime('%Y-%m-%d')
        
        # 排序
        daily_stats = daily_stats.sort_values('日期')
        
        return daily_stats
    
    def get_top_merchants(self, n=10):
        """获取交易次数最多的商户"""
        if self.df is None or len(self.df) == 0:
            return None
        
        # 只考虑支出
        expense_df = self.df[self.df['交易金额'] < 0]
        
        # 按商户分组
        merchant_stats = expense_df.groupby('交易对象').agg({
            '交易金额': [
                ('总额', lambda x: abs(x.sum())),
                ('笔数', 'count'),
                ('平均值', lambda x: abs(x.mean()))
            ]
        })
        
        # 重置索引，并展平多级列
        merchant_stats = merchant_stats.reset_index()
        merchant_stats.columns = ['商户', '总额', '笔数', '平均值']
        
        # 排序并取前N个
        top_by_count = merchant_stats.sort_values('笔数', ascending=False).head(n)
        top_by_amount = merchant_stats.sort_values('总额', ascending=False).head(n)
        
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
                monthly_stats = pd.DataFrame(columns=['年', '月', '收入', '支出', '净额', '月份'])
            
            yearly_stats = self.get_yearly_stats()
            if yearly_stats is None or yearly_stats.empty:
                logger.error("获取年度统计数据失败")
                yearly_stats = pd.DataFrame(columns=['年', '收入', '支出', '净额', '年份'])
            
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
            
            summary = self.get_summary()
            if summary is None:
                logger.error("获取摘要数据失败")
                summary = {}
            
            # 添加原始交易数据
            logger.info("添加原始交易数据到分析结果")
            # 确保交易日期是字符串格式
            transaction_df = self.df.copy()
            if '交易日期' in transaction_df.columns:
                transaction_df['交易日期'] = transaction_df['交易日期'].dt.strftime('%Y-%m-%d')
            
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
                        yearly_data = monthly_stats.groupby('年').agg({
                            '收入': 'sum',
                            '支出': 'sum',
                            '净额': 'sum'
                        }).reset_index()
                        yearly_data['年份'] = yearly_data['年'].astype(str)
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
        income_df = self.df[self.df['交易金额'] > 0]
        expense_df = self.df[self.df['交易金额'] < 0]
        
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
            
        amounts = df['交易金额'].abs()
        
        # 预处理：如果recurring_only=True，识别重复出现的交易
        if recurring_only:
            # 根据交易对象和交易描述识别重复交易
            if '交易对象' in df.columns and '交易描述' in df.columns:
                # 获取重复出现的交易对象
                repeat_counter = df['交易对象'].value_counts()
                repeat_merchants = set(repeat_counter[repeat_counter > 1].index)
                
                # 标记重复交易
                is_recurring = df['交易对象'].isin(repeat_merchants)
                
                # 对于没有交易对象但有相似描述的交易，也视为重复交易
                if '交易描述' in df.columns:
                    # 简化描述（移除日期、金额等变化部分）
                    simplified_desc = df['交易描述'].str.replace(r'\d+', '').str.replace(r'[.-]', '')
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
            
        core_income_df = core_trans[core_trans['交易金额'] > 0]
        core_expense_df = core_trans[core_trans['交易金额'] < 0]
        
        core_income = core_income_df['交易金额'].sum()
        core_expense = core_expense_df['交易金额'].sum()
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
        for trans_type, condition in [('收入', self.df['交易金额'] > 0), ('支出', self.df['交易金额'] < 0)]:
            type_df = self.df[condition]
            if type_df.empty:
                continue
                
            amounts = type_df['交易金额'].abs()  # 取绝对值进行计算
            
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
        outlier_income = outliers[outliers['交易金额'] > 0]
        outlier_expense = outliers[outliers['交易金额'] < 0]
        
        # 构建返回的统计信息
        stats = {
            'outlier_count': len(outliers),
            'outlier_income_count': len(outlier_income),
            'outlier_expense_count': len(outlier_expense),
            'outlier_income_amount': outlier_income['交易金额'].sum() if not outlier_income.empty else 0,
            'outlier_expense_amount': outlier_expense['交易金额'].sum() if not outlier_expense.empty else 0,
            'outlier_percentage': len(outliers) / len(self.df) * 100 if not self.df.empty else 0,
            'outliers': outliers.head(10).to_dict('records')  # 取前10条异常交易
        }
        
        return stats

# 使用示例
if __name__ == "__main__":
    # 创建分析器实例
    analyzer = TransactionAnalyzer()
    
    # 从数据库加载最近一年的数据
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
    
    if analyzer.load_data(start_date=start_date, end_date=end_date):
        # 生成输出文件路径
        output_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'analysis_data.json')
        # 生成分析数据
        if analyzer.generate_json_data(output_file):
            print(f"分析数据已保存到 {output_file}")
        else:
            print("生成分析数据失败")
    else:
        print("加载交易数据失败") 