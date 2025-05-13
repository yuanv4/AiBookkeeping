import os
import json
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # 设置非交互式后端
import numpy as np
from pathlib import Path
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('visualization_helper')

class VisualizationHelper:
    """用于生成交易数据可视化的工具类"""
    
    def __init__(self, json_file=None, data=None):
        """
        初始化可视化助手
        
        参数:
            json_file: 包含分析数据的JSON文件路径
            data: 直接提供的分析数据字典
        """
        self.data = None
        if data is not None:
            self.data = data
        elif json_file is not None and isinstance(json_file, (str, Path)):
            self._load_data(json_file)
        
        # 设置图表风格
        plt.style.use('seaborn-v0_8-pastel')
        
        # 设置中文字体支持
        self._setup_chinese_font()
        
        # 图表保存目录
        self.charts_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'static', 'charts')
        os.makedirs(self.charts_dir, exist_ok=True)
    
    def _setup_chinese_font(self):
        """设置中文字体支持"""
        try:
            # 尝试使用系统字体
            font_list = ['Microsoft YaHei', 'SimHei', 'SimSun', 'STSong', 'WenQuanYi Micro Hei']
            font_found = False
            
            for font in font_list:
                try:
                    matplotlib.rcParams['font.family'] = [font]
                    matplotlib.rcParams['axes.unicode_minus'] = False  # 正确显示负号
                    logger.info(f"成功设置中文字体: {font}")
                    font_found = True
                    break
                except:
                    continue
            
            if not font_found:
                logger.warning("未找到中文字体，图表中文可能显示为方块")
        except Exception as e:
            logger.error(f"设置中文字体时出错: {e}")
    
    def _load_data(self, json_file):
        """从JSON文件加载数据"""
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
            logger.info(f"成功加载分析数据: {json_file}")
        except Exception as e:
            logger.error(f"加载数据失败: {e}")
            self.data = {}
    
    def generate_all_charts(self):
        """生成所有图表并返回它们的路径"""
        if not self.data:
            logger.error("没有数据可供可视化")
            return {}
        
        charts = {}
        
        try:
            # 收支趋势图
            income_expense_chart = self.generate_income_expense_chart()
            if income_expense_chart:
                charts['income_expense'] = income_expense_chart
            
            # 类别饼图
            category_chart = self.generate_category_pie_chart()
            if category_chart:
                charts['category'] = category_chart
            
            # 最近交易柱状图
            recent_transactions_chart = self.generate_recent_transactions_chart()
            if recent_transactions_chart:
                charts['recent'] = recent_transactions_chart
                
            # 星期分析图
            weekday_chart = self.generate_weekday_chart()
            if weekday_chart:
                charts['weekday'] = weekday_chart
                
            # 商户分析图
            merchant_chart = self.generate_merchant_chart()
            if merchant_chart:
                charts['merchant'] = merchant_chart
                
            logger.info(f"成功生成 {len(charts)} 个图表")
            return charts
            
        except Exception as e:
            logger.error(f"生成图表时出错: {e}")
            return {}
    
    def generate_income_expense_chart(self):
        """生成收入和支出趋势图"""
        try:
            if 'monthly_stats' not in self.data or not self.data['monthly_stats']:
                logger.warning("没有月度数据可供绘图")
                return None
            
            monthly_stats = sorted(self.data['monthly_stats'], key=lambda x: x['月份'])
            
            # 限制只显示最近12个月
            if len(monthly_stats) > 12:
                monthly_stats = monthly_stats[-12:]
            
            months = [m['月份'] for m in monthly_stats]
            incomes = [m['收入'] for m in monthly_stats]
            expenses = [m['支出'] for m in monthly_stats]
            nets = [m['净额'] for m in monthly_stats]
            
            fig, ax = plt.subplots(figsize=(10, 6))
            
            # 绘制条形图
            x = np.arange(len(months))
            width = 0.35
            ax.bar(x - width/2, incomes, width, label='收入', color='#4CAF50', alpha=0.7)
            ax.bar(x + width/2, [-e for e in expenses], width, label='支出', color='#F44336', alpha=0.7)
            
            # 绘制净额线
            ax.plot(x, nets, 'o-', label='净额', color='#2196F3', linewidth=2)
            
            # 设置坐标轴
            ax.set_ylabel('金额 (元)')
            ax.set_title('月度收支趋势')
            ax.set_xticks(x)
            ax.set_xticklabels(months, rotation=45)
            ax.legend()
            ax.grid(axis='y', linestyle='--', alpha=0.7)
            
            # 添加数值标签
            for i, v in enumerate(incomes):
                ax.text(i - width/2, v + max(incomes)*0.02, f'{v:.0f}', ha='center', va='bottom', fontsize=8)
            for i, v in enumerate(expenses):
                ax.text(i + width/2, -v - max(expenses)*0.02, f'{v:.0f}', ha='center', va='top', fontsize=8)
            
            # 保存图表
            plt.tight_layout()
            chart_path = os.path.join(self.charts_dir, 'income_expense.png')
            plt.savefig(chart_path, dpi=100)
            plt.close()
            
            logger.info(f"收支趋势图已保存至: {chart_path}")
            return os.path.basename(chart_path)
        
        except Exception as e:
            logger.error(f"生成收支趋势图时出错: {e}")
            return None
    
    def generate_category_pie_chart(self):
        """生成交易类别饼图"""
        try:
            # 检查category_stats或原始字段是否存在
            if 'category_stats' in self.data and self.data['category_stats']:
                category_stats = self.data['category_stats']
                # 检查键名是否为'分类'或'类别'
                if '分类' in category_stats[0]:
                    key_name = '分类'
                elif '类别' in category_stats[0]:
                    key_name = '类别'
                else:
                    logger.warning(f"类别数据中找不到'分类'或'类别'字段，尝试其他字段: {category_stats[0].keys()}")
                    # 尝试找到类似类别的字段
                    possible_keys = [k for k in category_stats[0].keys() if '类' in k or '分' in k]
                    if possible_keys:
                        key_name = possible_keys[0]
                        logger.info(f"使用替代字段名: {key_name}")
                    else:
                        logger.warning("没有找到合适的类别字段")
                        return None
                
                # 检查金额字段
                if '总额' in category_stats[0]:
                    amount_key = '总额'
                elif '金额' in category_stats[0]:
                    amount_key = '金额'
                else:
                    logger.warning(f"类别数据中找不到'总额'或'金额'字段，尝试其他字段: {category_stats[0].keys()}")
                    # 尝试找到类似金额的字段
                    possible_keys = [k for k in category_stats[0].keys() if '额' in k or '金' in k]
                    if possible_keys:
                        amount_key = possible_keys[0]
                        logger.info(f"使用替代金额字段名: {amount_key}")
                    else:
                        logger.warning("没有找到合适的金额字段")
                        return None
                
                # 排序并限制类别数量，避免过多
                category_stats = sorted(category_stats, key=lambda x: abs(x[amount_key]), reverse=True)
                
                if len(category_stats) > 8:
                    # 保留前7个类别，其余归为"其他"
                    top_categories = category_stats[:7]
                    other_amount = sum(c[amount_key] for c in category_stats[7:])
                    other_count = sum(c.get('笔数', 0) for c in category_stats[7:])
                    
                    top_categories.append({
                        key_name: '其他',
                        amount_key: other_amount,
                        '笔数': other_count
                    })
                    category_stats = top_categories
                
                labels = [c[key_name] for c in category_stats]
                amounts = [abs(c[amount_key]) for c in category_stats]  # 使用绝对值以便显示
                
                # 创建饼图
                fig, ax = plt.subplots(figsize=(8, 8))
                wedges, texts, autotexts = ax.pie(
                    amounts, 
                    labels=None,  # 不在饼图上直接显示标签
                    autopct='%1.1f%%',
                    startangle=90,
                    shadow=False,
                    colors=plt.cm.tab10.colors
                )
                
                # 让饼图中心空心
                circle = plt.Circle((0, 0), 0.4, fc='white')
                fig.gca().add_artist(circle)
                
                # 设置标题和图例
                ax.set_title('交易类别分布')
                ax.legend(wedges, [f'{l} ({a:.0f}元)' for l, a in zip(labels, amounts)], 
                        loc='center left', bbox_to_anchor=(1, 0.5))
                
                # 设置自动文本的样式
                for autotext in autotexts:
                    autotext.set_fontsize(10)
                    autotext.set_weight('bold')
                
                # 保存图表
                plt.tight_layout()
                chart_path = os.path.join(self.charts_dir, 'category_pie.png')
                plt.savefig(chart_path, dpi=100, bbox_inches='tight')
                plt.close()
                
                logger.info(f"类别饼图已保存至: {chart_path}")
                return os.path.basename(chart_path)
            else:
                logger.warning("没有类别数据可供绘图")
                return None
            
        except Exception as e:
            logger.error(f"生成类别饼图时出错: {e}")
            return None
    
    def generate_recent_transactions_chart(self):
        """生成最近交易的柱状图"""
        try:
            if 'daily_stats' not in self.data or not self.data['daily_stats']:
                logger.warning("没有每日数据可供绘图")
                return None
            
            daily_stats = sorted(self.data['daily_stats'], key=lambda x: x['日期'])
            
            # 只取最近15天的数据
            if len(daily_stats) > 15:
                daily_stats = daily_stats[-15:]
            
            dates = [d['日期'] for d in daily_stats]
            amounts = [d['总额'] for d in daily_stats]
            counts = [d['笔数'] for d in daily_stats]
            
            # 创建柱状图
            fig, ax1 = plt.subplots(figsize=(10, 6))
            
            # 金额柱状图
            bars = ax1.bar(dates, amounts, alpha=0.6, color=[
                '#4CAF50' if a > 0 else '#F44336' for a in amounts
            ])
            
            # 设置坐标轴
            ax1.set_ylabel('交易金额 (元)', color='#333333')
            ax1.set_title('最近交易趋势')
            ax1.set_xticks(dates)
            ax1.set_xticklabels(dates, rotation=45)
            ax1.tick_params(axis='y', colors='#333333')
            ax1.grid(axis='y', linestyle='--', alpha=0.7)
            
            # 创建第二个坐标轴，显示交易笔数
            ax2 = ax1.twinx()
            ax2.plot(dates, counts, 'o-', color='#2196F3', linewidth=2, label='交易笔数')
            ax2.set_ylabel('交易笔数', color='#2196F3')
            ax2.tick_params(axis='y', colors='#2196F3')
            
            # 添加数值标签
            for i, (v, c) in enumerate(zip(amounts, counts)):
                ax1.text(i, v + (max(amounts) - min(amounts)) * 0.03 * (1 if v >= 0 else -1), 
                         f'{v:.0f}', ha='center', va='bottom' if v >= 0 else 'top', fontsize=8)
                ax2.text(i, c + 0.3, f'{c}', ha='center', va='bottom', fontsize=8, color='#2196F3')
            
            # 添加图例
            from matplotlib.lines import Line2D
            custom_lines = [
                Line2D([0], [0], color='#4CAF50', lw=0, marker='s', markersize=10, alpha=0.6),
                Line2D([0], [0], color='#F44336', lw=0, marker='s', markersize=10, alpha=0.6),
                Line2D([0], [0], color='#2196F3', lw=2, marker='o', markersize=5)
            ]
            ax1.legend(custom_lines, ['收入', '支出', '交易笔数'], loc='upper left')
            
            # 保存图表
            plt.tight_layout()
            chart_path = os.path.join(self.charts_dir, 'recent_transactions.png')
            plt.savefig(chart_path, dpi=100)
            plt.close()
            
            logger.info(f"最近交易图已保存至: {chart_path}")
            return os.path.basename(chart_path)
        
        except Exception as e:
            logger.error(f"生成最近交易图时出错: {e}")
            return None
    
    def generate_weekday_chart(self):
        """生成按星期分析的图表"""
        try:
            if 'weekly_stats' not in self.data or not self.data['weekly_stats']:
                logger.warning("没有星期数据可供绘图")
                return None
            
            weekly_stats = sorted(self.data['weekly_stats'], key=lambda x: x['星期'])
            
            weekdays = [w['星期名'] for w in weekly_stats]
            amounts = [w['总额'] for w in weekly_stats]
            counts = [w['笔数'] for w in weekly_stats]
            
            # 创建柱状图
            fig, ax1 = plt.subplots(figsize=(10, 6))
            
            # 金额柱状图
            x = np.arange(len(weekdays))
            bars = ax1.bar(x, amounts, alpha=0.7, width=0.6, color='#3F51B5')
            
            # 设置坐标轴
            ax1.set_ylabel('日均交易金额 (元)', color='#333333')
            ax1.set_title('按星期分析')
            ax1.set_xticks(x)
            ax1.set_xticklabels(weekdays)
            ax1.tick_params(axis='y', colors='#333333')
            ax1.grid(axis='y', linestyle='--', alpha=0.7)
            
            # 创建第二个坐标轴，显示交易笔数
            ax2 = ax1.twinx()
            ax2.plot(x, counts, 'o-', color='#FF9800', linewidth=2, label='日均交易笔数')
            ax2.set_ylabel('日均交易笔数', color='#FF9800')
            ax2.tick_params(axis='y', colors='#FF9800')
            
            # 添加数值标签
            for i, (v, c) in enumerate(zip(amounts, counts)):
                ax1.text(i, v + max(amounts) * 0.03, f'{v:.0f}', ha='center', va='bottom', fontsize=9)
                ax2.text(i, c + max(counts) * 0.03, f'{c:.1f}', ha='center', va='bottom', fontsize=9, color='#FF9800')
            
            # 添加图例
            from matplotlib.lines import Line2D
            custom_lines = [
                Line2D([0], [0], color='#3F51B5', lw=0, marker='s', markersize=10, alpha=0.7),
                Line2D([0], [0], color='#FF9800', lw=2, marker='o', markersize=5)
            ]
            ax1.legend(custom_lines, ['日均交易金额', '日均交易笔数'], loc='upper right')
            
            # 保存图表
            plt.tight_layout()
            chart_path = os.path.join(self.charts_dir, 'weekday_analysis.png')
            plt.savefig(chart_path, dpi=100)
            plt.close()
            
            logger.info(f"星期分析图已保存至: {chart_path}")
            return os.path.basename(chart_path)
        
        except Exception as e:
            logger.error(f"生成星期分析图时出错: {e}")
            return None
    
    def generate_merchant_chart(self):
        """生成商户分析图表"""
        try:
            if ('top_merchants' in self.data and 
                'by_amount' in self.data['top_merchants'] and 
                self.data['top_merchants']['by_amount']):
                
                merchants_by_amount = self.data['top_merchants']['by_amount']
                
                # 检查字段名称
                if '商户' in merchants_by_amount[0]:
                    merchant_key = '商户'
                elif '交易对象' in merchants_by_amount[0]:
                    merchant_key = '交易对象'
                else:
                    logger.warning(f"商户数据中找不到'商户'或'交易对象'字段，尝试其他字段: {merchants_by_amount[0].keys()}")
                    # 尝试找到类似商户的字段
                    possible_keys = [k for k in merchants_by_amount[0].keys() if '商' in k or '户' in k or '对' in k]
                    if possible_keys:
                        merchant_key = possible_keys[0]
                        logger.info(f"使用替代商户字段名: {merchant_key}")
                    else:
                        logger.warning("没有找到合适的商户字段")
                        return None
                
                # 检查金额字段
                if '金额' in merchants_by_amount[0]:
                    amount_key = '金额'
                elif '总额' in merchants_by_amount[0]:
                    amount_key = '总额'
                else:
                    logger.warning(f"商户数据中找不到'金额'或'总额'字段，尝试其他字段: {merchants_by_amount[0].keys()}")
                    # 尝试找到类似金额的字段
                    possible_keys = [k for k in merchants_by_amount[0].keys() if '额' in k or '金' in k]
                    if possible_keys:
                        amount_key = possible_keys[0]
                        logger.info(f"使用替代金额字段名: {amount_key}")
                    else:
                        logger.warning("没有找到合适的金额字段")
                        return None
                
                # 只取前10个商户
                if len(merchants_by_amount) > 10:
                    merchants_by_amount = merchants_by_amount[:10]
                
                # 翻转列表，使图表从上到下按由大到小排序
                merchants_by_amount = list(reversed(merchants_by_amount))
                
                merchants = [m[merchant_key] for m in merchants_by_amount]
                amounts = [m[amount_key] for m in merchants_by_amount]
                
                # 获取交易笔数
                counts = []
                for m in merchants_by_amount:
                    if '笔数' in m:
                        counts.append(m['笔数'])
                    else:
                        counts.append(0)  # 如果没有笔数字段，设置为0
                
                # 创建水平条形图
                fig, ax = plt.subplots(figsize=(10, 8))
                
                # 商户条形图
                y = np.arange(len(merchants))
                bars = ax.barh(y, amounts, alpha=0.7, color='#009688')
                
                # 设置坐标轴
                ax.set_xlabel('消费金额 (元)')
                ax.set_title('商户消费分析 (Top 10)')
                ax.set_yticks(y)
                ax.set_yticklabels(merchants)
                ax.grid(axis='x', linestyle='--', alpha=0.7)
                
                # 添加数值标签
                for i, v in enumerate(amounts):
                    ax.text(v + max(amounts) * 0.01, i, f'{v:.0f}元', va='center')
                
                # 保存图表
                plt.tight_layout()
                chart_path = os.path.join(self.charts_dir, 'merchant_analysis.png')
                plt.savefig(chart_path, dpi=100)
                plt.close()
                
                logger.info(f"商户分析图已保存至: {chart_path}")
                return os.path.basename(chart_path)
            else:
                logger.warning("没有商户数据可供绘图")
                return None
            
        except Exception as e:
            logger.error(f"生成商户分析图时出错: {e}")
            return None
    
    # 以下方法用于返回前端需要的图表数据
    def get_category_data(self):
        """获取类别分析的图表数据"""
        if 'category_stats' not in self.data or not self.data['category_stats']:
            return None
            
        category_stats = self.data['category_stats']
        
        # 检查键名是否为'分类'或'类别'
        if '分类' in category_stats[0]:
            key_name = '分类'
        elif '类别' in category_stats[0]:
            key_name = '类别'
        else:
            logger.warning(f"类别数据中找不到'分类'或'类别'字段，尝试其他字段: {category_stats[0].keys()}")
            # 尝试找到类似类别的字段
            possible_keys = [k for k in category_stats[0].keys() if '类' in k or '分' in k]
            if possible_keys:
                key_name = possible_keys[0]
                logger.info(f"使用替代字段名: {key_name}")
            else:
                logger.warning("没有找到合适的类别字段")
                return None
        
        # 检查金额字段
        if '总额' in category_stats[0]:
            amount_key = '总额'
        elif '金额' in category_stats[0]:
            amount_key = '金额'
        else:
            logger.warning(f"类别数据中找不到'总额'或'金额'字段，尝试其他字段: {category_stats[0].keys()}")
            # 尝试找到类似金额的字段
            possible_keys = [k for k in category_stats[0].keys() if '额' in k or '金' in k]
            if possible_keys:
                amount_key = possible_keys[0]
                logger.info(f"使用替代金额字段名: {amount_key}")
            else:
                logger.warning("没有找到合适的金额字段")
                return None
                
        category_stats = sorted(category_stats, key=lambda x: abs(x[amount_key]), reverse=True)
        
        # 限制类别数量
        if len(category_stats) > 8:
            top_categories = category_stats[:7]
            other_amount = sum(c[amount_key] for c in category_stats[7:])
            other_count = sum(c.get('笔数', 0) for c in category_stats[7:])
            
            top_categories.append({
                key_name: '其他',
                amount_key: other_amount,
                '笔数': other_count
            })
            category_stats = top_categories
        
        labels = [c[key_name] for c in category_stats]
        amounts = [abs(c[amount_key]) for c in category_stats]
        
        return {
            'labels': labels,
            'values': amounts  # 改为values以匹配前端代码
        }
    
    def get_merchant_data(self):
        """获取商户分析的图表数据"""
        if ('top_merchants' not in self.data or 
            'by_amount' not in self.data['top_merchants'] or 
            not self.data['top_merchants']['by_amount']):
            return None
        
        merchants_by_amount = self.data['top_merchants']['by_amount']
        
        # 检查字段名称
        if '商户' in merchants_by_amount[0]:
            merchant_key = '商户'
        elif '交易对象' in merchants_by_amount[0]:
            merchant_key = '交易对象'
        else:
            logger.warning(f"商户数据中找不到'商户'或'交易对象'字段，尝试其他字段: {merchants_by_amount[0].keys()}")
            # 尝试找到类似商户的字段
            possible_keys = [k for k in merchants_by_amount[0].keys() if '商' in k or '户' in k or '对' in k]
            if possible_keys:
                merchant_key = possible_keys[0]
                logger.info(f"使用替代商户字段名: {merchant_key}")
            else:
                logger.warning("没有找到合适的商户字段")
                return None
        
        # 检查金额字段
        if '金额' in merchants_by_amount[0]:
            amount_key = '金额'
        elif '总额' in merchants_by_amount[0]:
            amount_key = '总额'
        else:
            logger.warning(f"商户数据中找不到'金额'或'总额'字段，尝试其他字段: {merchants_by_amount[0].keys()}")
            # 尝试找到类似金额的字段
            possible_keys = [k for k in merchants_by_amount[0].keys() if '额' in k or '金' in k]
            if possible_keys:
                amount_key = possible_keys[0]
                logger.info(f"使用替代金额字段名: {amount_key}")
            else:
                logger.warning("没有找到合适的金额字段")
                return None
        
        # 只取前10个商户
        if len(merchants_by_amount) > 10:
            merchants_by_amount = merchants_by_amount[:10]
        
        merchants = [m[merchant_key] for m in merchants_by_amount]
        amounts = [m[amount_key] for m in merchants_by_amount]
        
        # 获取交易笔数
        counts = []
        for m in merchants_by_amount:
            if '笔数' in m:
                counts.append(m['笔数'])
            else:
                counts.append(0)  # 如果没有笔数字段，设置为0
        
        return {
            'labels': merchants,
            'values': amounts,
            'counts': counts
        }
    
    def get_weekday_data(self):
        """获取星期分析的图表数据"""
        if 'weekly_stats' not in self.data or not self.data['weekly_stats']:
            return None
        
        weekly_stats = sorted(self.data['weekly_stats'], key=lambda x: x['星期'])
        
        weekdays = [w['星期名'] for w in weekly_stats]
        amounts = [w['总额'] for w in weekly_stats]
        counts = [w['笔数'] for w in weekly_stats]
        
        return {
            'labels': weekdays,
            'values': amounts,  # 改为values以匹配前端代码
            'counts': counts
        }
    
    def get_monthly_data(self):
        """获取月度分析的图表数据"""
        if 'monthly_stats' not in self.data or not self.data['monthly_stats']:
            return None
        
        monthly_stats = sorted(self.data['monthly_stats'], key=lambda x: x['月份'])
        
        # 限制只显示最近12个月
        if len(monthly_stats) > 12:
            monthly_stats = monthly_stats[-12:]
        
        months = [m['月份'] for m in monthly_stats]
        incomes = [m['收入'] for m in monthly_stats]
        expenses = [m['支出'] for m in monthly_stats]
        nets = [m['净额'] for m in monthly_stats]
        
        return {
            'labels': months,
            'income': incomes,
            'expense': expenses,
            'net': nets
        }
    
    def get_yearly_data(self):
        """获取年度分析的图表数据"""
        if 'yearly_stats' not in self.data or not self.data['yearly_stats']:
            return None
        
        yearly_stats = sorted(self.data['yearly_stats'], key=lambda x: x['年份'])
        
        years = [y['年份'] for y in yearly_stats]
        incomes = [y['收入'] for y in yearly_stats]
        expenses = [y['支出'] for y in yearly_stats]
        nets = [y['净额'] for y in yearly_stats]
        
        return {
            'labels': years,
            'income': incomes,
            'expense': expenses,
            'net': nets
        } 