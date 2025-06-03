import os
import json
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # 设置非交互式后端
import numpy as np
from pathlib import Path
import logging
import sys
import io
import base64
from typing import Dict, List, Optional, Any, Union, Tuple

# 添加项目根目录到PYTHONPATH以解决导入问题
current_dir = os.path.dirname(os.path.abspath(__file__))
scripts_dir = os.path.dirname(current_dir)
root_dir = os.path.dirname(scripts_dir)
if root_dir not in sys.path:
    sys.path.append(root_dir)
if scripts_dir not in sys.path:
    sys.path.append(scripts_dir)

# 导入错误处理机制
from scripts.common.exceptions import (
    VisualizationError, ChartGenerationError, ConfigError
)
from scripts.common.error_handler import error_handler, safe_operation, log_error

# 导入配置管理器
from scripts.common.config import get_config_manager

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('visualization_helper')

class VisualizationHelper:
    """用于生成交易数据可视化的工具类"""
    
    def __init__(self, json_file: Optional[Union[str, Path]] = None, data: Optional[Dict[str, Any]] = None):
        """
        初始化可视化助手
        
        参数:
            json_file: 包含分析数据的JSON文件路径
            data: 直接提供的分析数据字典
        """
        # 获取配置管理器
        self.config_manager = get_config_manager()
        
        self.data = None
        if data is not None:
            self.data = data
        elif json_file is not None and isinstance(json_file, (str, Path)):
            self._load_data(json_file)
        
        # 从配置中获取图表风格
        theme = self.config_manager.get('visualization.theme', 'default')
        if theme == 'default':
            plt.style.use('seaborn-v0_8-pastel')
        else:
            try:
                plt.style.use(theme)
            except Exception:
                logger.warning(f"无法使用主题 {theme}，使用默认主题")
                plt.style.use('seaborn-v0_8-pastel')
        
        # 设置中文字体支持
        self._setup_chinese_font()
        
        # 从配置中获取图表保存目录
        charts_dir = self.config_manager.get('visualization.charts_dir', 'static/charts')
        
        # 确保路径是绝对路径
        if not os.path.isabs(charts_dir):
            self.charts_dir = os.path.join(root_dir, charts_dir)
        else:
            self.charts_dir = charts_dir
            
        os.makedirs(self.charts_dir, exist_ok=True)
        
        # 获取颜色配置
        self.colors = self.config_manager.get('visualization.colors', {
            'income': '#4CAF50',
            'expense': '#F44336',
            'net': '#2196F3',
            'transfer': '#FF9800'
        })
    
    @error_handler(fallback_value=None)
    def _setup_chinese_font(self) -> None:
        """设置中文字体支持"""
        # 从配置中获取字体信息
        default_font = self.config_manager.get('visualization.fonts.default', 'SimHei')
        fallback_fonts = self.config_manager.get('visualization.fonts.fallback', 
                                               ['Microsoft YaHei', 'SimSun', 'STSong', 'WenQuanYi Micro Hei'])
        
        # 所有可能的字体
        all_fonts = [default_font] + fallback_fonts
        font_found = False
        
        for font in all_fonts:
            try:
                matplotlib.rcParams['font.family'] = [font]
                matplotlib.rcParams['axes.unicode_minus'] = False  # 正确显示负号
                logger.info(f"Successfully set Chinese font: {font}")
                font_found = True
                break
            except Exception:
                continue
        
        if not font_found:
            logger.warning("Chinese font not found, chart Chinese characters may appear as blocks")
    
    @error_handler(fallback_value={}, expected_exceptions=ConfigError)
    def _load_data(self, json_file: Union[str, Path]) -> Dict[str, Any]:
        """从JSON文件加载数据
        
        Args:
            json_file: JSON文件路径
            
        Returns:
            dict: 加载的数据
        """
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
            logger.info(f"Successfully loaded analysis data: {json_file}")
            return self.data
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            raise ConfigError(f"JSON解析错误: {str(e)}", details={"file": str(json_file)})
        except FileNotFoundError:
            raise ConfigError(f"文件不存在: {json_file}", details={"file": str(json_file)})
        except Exception as e:
            raise ConfigError(f"加载数据失败: {str(e)}", details={"file": str(json_file)})
    
    @safe_operation("生成图表")
    def generate_all_charts(self) -> Dict[str, str]:
        """生成所有图表并返回它们的路径
        
        Returns:
            dict: 图表名称和路径的字典
        """
        if not self.data:
            raise VisualizationError("没有可用于可视化的数据")
        
        charts = {}
        
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
            
        logger.info(f"Successfully generated {len(charts)} charts")
        return charts
    
    @error_handler(fallback_value=None, expected_exceptions=ChartGenerationError)
    def generate_income_expense_chart(self) -> Optional[str]:
        """生成收入和支出趋势图
        
        Returns:
            str: 图表文件名，如果生成失败则返回None
        """
        if 'monthly_stats' not in self.data or not self.data['monthly_stats']:
            logger.warning("No monthly data available for plotting")
            return None
        
        monthly_stats = sorted(self.data['monthly_stats'], key=lambda x: x['month_label'])
        
        # 限制只显示最近12个月
        if len(monthly_stats) > 12:
            monthly_stats = monthly_stats[-12:]
        
        months = [m['month_label'] for m in monthly_stats]
        incomes = [m['income'] for m in monthly_stats]
        expenses = [m['expense'] for m in monthly_stats]
        nets = [m['net'] for m in monthly_stats]
        
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # 绘制条形图
        x = np.arange(len(months))
        width = 0.35
        ax.bar(x - width/2, incomes, width, label='income', color=self.colors.get('income', '#4CAF50'), alpha=0.7)
        ax.bar(x + width/2, [-e for e in expenses], width, label='expense', color=self.colors.get('expense', '#F44336'), alpha=0.7)
        
        # 绘制净额线
        ax.plot(x, nets, 'o-', label='net', color=self.colors.get('net', '#2196F3'), linewidth=2)
        
        # 设置坐标轴
        ax.set_ylabel('amount (yuan)')
        ax.set_title('monthly income and expense trend')
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
        
        try:
            plt.savefig(chart_path, dpi=100)
            plt.close()
            
            logger.info(f"income and expense trend chart saved to: {chart_path}")
            return os.path.basename(chart_path)
        except Exception as e:
            plt.close()
            raise ChartGenerationError(
                f"生成收入支出趋势图失败: {str(e)}", 
                details={"chart_type": "income_expense"}
            )
    
    @error_handler(fallback_value=None, expected_exceptions=ChartGenerationError)
    def generate_category_pie_chart(self) -> Optional[str]:
        """生成交易类别饼图
        
        Returns:
            str: 图表文件名，如果生成失败则返回None
        """
        # 获取分类数据
        category_data = self.get_category_data()
        if not category_data:
            return None
            
        categories = category_data['categories']
        values = category_data['values']
        
        # 从配置中获取饼图最大类别数
        max_categories = self.config_manager.get('visualization.max_categories_in_pie', 8)
        
        # 如果类别数量超过最大值，将多余的类别合并为"其他"
        if len(categories) > max_categories:
            # 保留前 max_categories-1 个类别，其余合并为"其他"
            other_value = sum(values[max_categories-1:])
            categories = categories[:max_categories-1] + ['其他']
            values = values[:max_categories-1] + [other_value]
        
        # 创建饼图
        fig, ax = plt.subplots(figsize=(10, 8))
        
        # 设置颜色和绘图参数
        colors = plt.cm.Spectral(np.linspace(0, 1, len(categories)))
        wedges, texts, autotexts = ax.pie(
            values, 
            labels=categories,
            autopct='%1.1f%%',
            startangle=90,
            colors=colors,
            wedgeprops={'edgecolor': 'w', 'linewidth': 1, 'antialiased': True}
        )
        
        # 设置标签样式
        for text in texts:
            text.set_fontsize(10)
        for autotext in autotexts:
            autotext.set_fontsize(8)
            autotext.set_color('white')
        
        # 添加图例
        ax.legend(
            wedges, 
            [f"{c} ({v:.0f})" for c, v in zip(categories, values)],
            title="Categories",
            loc="center left",
            bbox_to_anchor=(1, 0, 0.5, 1)
        )
        
        # 设置标题
        ax.set_title('Transaction Categories')
        
        # 保存图表
        plt.tight_layout()
        chart_path = os.path.join(self.charts_dir, 'category_pie.png')
        
        try:
            plt.savefig(chart_path, dpi=100)
            plt.close()
            
            logger.info(f"Category pie chart saved to: {chart_path}")
            return os.path.basename(chart_path)
        except Exception as e:
            plt.close()
            raise ChartGenerationError(
                f"生成类别饼图失败: {str(e)}", 
                details={"chart_type": "category_pie"}
            )
    
    def generate_recent_transactions_chart(self):
        """生成最近交易的柱状图"""
        try:
            if 'daily_stats' not in self.data or not self.data['daily_stats']:
                logger.warning("No daily data available for plotting")
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
            ax1.set_ylabel('transaction amount (yuan)', color='#333333')
            ax1.set_title('recent transaction trend')
            ax1.set_xticks(dates)
            ax1.set_xticklabels(dates, rotation=45)
            ax1.tick_params(axis='y', colors='#333333')
            ax1.grid(axis='y', linestyle='--', alpha=0.7)
            
            # 创建第二个坐标轴，显示交易笔数
            ax2 = ax1.twinx()
            ax2.plot(dates, counts, 'o-', color='#2196F3', linewidth=2, label='transaction count')
            ax2.set_ylabel('transaction count', color='#2196F3')
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
            ax1.legend(custom_lines, ['income', 'expense', 'transaction count'], loc='upper left')
            
            # 保存图表
            plt.tight_layout()
            chart_path = os.path.join(self.charts_dir, 'recent_transactions.png')
            plt.savefig(chart_path, dpi=100)
            plt.close()
            
            logger.info(f"最近交易图已保存至: {chart_path}")
            return os.path.basename(chart_path)
        
        except Exception as e:
            logger.error(f"Error generating recent transactions chart: {e}")
            return None
    
    def generate_weekday_chart(self):
        """生成按星期分析的图表"""
        try:
            if 'weekly_stats' not in self.data or not self.data['weekly_stats']:
                logger.warning("No weekly data available for plotting")
                return None
            
            weekly_stats = sorted(self.data['weekly_stats'], key=lambda x: x['weekday'])
            
            weekdays = [w['weekday_name'] for w in weekly_stats]
            amounts = [w['total'] for w in weekly_stats]
            counts = [w['count'] for w in weekly_stats]
            
            # 创建柱状图
            fig, ax1 = plt.subplots(figsize=(10, 6))
            
            # 金额柱状图
            x = np.arange(len(weekdays))
            bars = ax1.bar(x, amounts, alpha=0.7, width=0.6, color='#3F51B5')
            
            # 设置坐标轴
            ax1.set_ylabel('daily average transaction amount (yuan)', color='#333333')
            ax1.set_title('weekday analysis')
            ax1.set_xticks(x)
            ax1.set_xticklabels(weekdays)
            ax1.tick_params(axis='y', colors='#333333')
            ax1.grid(axis='y', linestyle='--', alpha=0.7)
            
            # 创建第二个坐标轴，显示交易笔数
            ax2 = ax1.twinx()
            ax2.plot(x, counts, 'o-', color='#FF9800', linewidth=2, label='daily average transaction count')
            ax2.set_ylabel('daily average transaction count', color='#FF9800')
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
            ax1.legend(custom_lines, ['daily average transaction amount', 'daily average transaction count'], loc='upper right')
            
            # 保存图表
            plt.tight_layout()
            chart_path = os.path.join(self.charts_dir, 'weekday_analysis.png')
            plt.savefig(chart_path, dpi=100)
            plt.close()
            
            logger.info(f"星期分析图已保存至: {chart_path}")
            return os.path.basename(chart_path)
        
        except Exception as e:
            logger.error(f"Error generating weekday analysis chart: {e}")
            return None
    
    def generate_merchant_chart(self):
        """生成商户分析图表"""
        try:
            if ('top_merchants' in self.data and 
                'by_amount' in self.data['top_merchants'] and 
                self.data['top_merchants']['by_amount']):
                
                merchants_by_amount = self.data['top_merchants']['by_amount']
                
                # 检查字段名称
                if 'merchant' in merchants_by_amount[0]:
                    merchant_key = 'merchant'
                elif 'counterparty' in merchants_by_amount[0]:
                    merchant_key = 'counterparty'
                elif '商户' in merchants_by_amount[0]:
                    merchant_key = '商户'
                elif '交易对象' in merchants_by_amount[0]:
                    merchant_key = '交易对象'
                else:
                    logger.warning(f"商户数据中找不到'merchant'、'counterparty'、'商户'或'交易对象'字段，尝试其他字段: {merchants_by_amount[0].keys()}")
                    # 尝试找到类似商户的字段
                    possible_keys = [k for k in merchants_by_amount[0].keys() if '商' in k or '户' in k or '对' in k]
                    if possible_keys:
                        merchant_key = possible_keys[0]
                        logger.info(f"Using alternative merchant field name: {merchant_key}")
                    else:
                        logger.warning("No suitable merchant field found")
                        return None
                
                # 检查金额字段
                if 'total' in merchants_by_amount[0]:
                    amount_key = 'total'
                elif 'amount' in merchants_by_amount[0]:
                    amount_key = 'amount'
                elif '金额' in merchants_by_amount[0]:
                    amount_key = '金额'
                elif '总额' in merchants_by_amount[0]:
                    amount_key = '总额'
                else:
                    logger.warning(f"商户数据中找不到'total'、'amount'、'金额'或'总额'字段，尝试其他字段: {merchants_by_amount[0].keys()}")
                    # 尝试找到类似金额的字段
                    possible_keys = [k for k in merchants_by_amount[0].keys() if '额' in k or '金' in k]
                    if possible_keys:
                        amount_key = possible_keys[0]
                        logger.info(f"Using alternative amount field name: {amount_key}")
                    else:
                        logger.warning("No suitable amount field found")
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
                    if 'count' in m:
                        counts.append(m['count'])
                    elif '笔数' in m:
                        counts.append(m['笔数'])
                    else:
                        counts.append(0)  # 如果没有笔数字段，设置为0
                
                # 创建水平条形图
                fig, ax = plt.subplots(figsize=(10, 8))
                
                # 商户条形图
                y = np.arange(len(merchants))
                bars = ax.barh(y, amounts, alpha=0.7, color='#009688')
                
                # 设置坐标轴
                ax.set_xlabel('transaction amount (yuan)')
                ax.set_title('merchant transaction analysis (Top 10)')
                ax.set_yticks(y)
                ax.set_yticklabels(merchants)
                ax.grid(axis='x', linestyle='--', alpha=0.7)
                
                # 添加数值标签
                for i, v in enumerate(amounts):
                    ax.text(v + max(amounts) * 0.01, i, f'{v:.0f}yuan', va='center')
                
                # 保存图表
                plt.tight_layout()
                chart_path = os.path.join(self.charts_dir, 'merchant_analysis.png')
                plt.savefig(chart_path, dpi=100)
                plt.close()
                
                logger.info(f"商户分析图已保存至: {chart_path}")
                return os.path.basename(chart_path)
            else:
                logger.warning("No merchant data available for plotting")
                return None
            
        except Exception as e:
            logger.error(f"Error generating merchant analysis chart: {e}")
            return None
    
    # 以下方法用于返回前端需要的图表数据
    def get_category_data(self):
        """获取类别分析的图表数据"""
        if 'category_stats' not in self.data or not self.data['category_stats']:
            return None
            
        category_stats = self.data['category_stats']
        
        # 检查键名
        if 'category' in category_stats[0]:
            key_name = 'category'
        elif '分类' in category_stats[0]:
            key_name = '分类'
        elif '类别' in category_stats[0]:
            key_name = '类别'
        else:
            logger.warning(f"类别数据中找不到'category'、'分类'或'类别'字段，尝试其他字段: {category_stats[0].keys()}")
            # 尝试找到类似类别的字段
            possible_keys = [k for k in category_stats[0].keys() if '类' in k or '分' in k]
            if possible_keys:
                key_name = possible_keys[0]
                logger.info(f"Using alternative field name: {key_name}")
            else:
                logger.warning("No suitable category field found")
                return None
        
        # 检查金额字段
        if 'total' in category_stats[0]:
            amount_key = 'total'
        elif 'amount' in category_stats[0]:
            amount_key = 'amount'
        elif '总额' in category_stats[0]:
            amount_key = '总额'
        elif '金额' in category_stats[0]:
            amount_key = '金额'
        else:
            logger.warning(f"类别数据中找不到'total'、'amount'、'总额'或'金额'字段，尝试其他字段: {category_stats[0].keys()}")
            # 尝试找到类似金额的字段
            possible_keys = [k for k in category_stats[0].keys() if '额' in k or '金' in k]
            if possible_keys:
                amount_key = possible_keys[0]
                logger.info(f"Using alternative amount field name: {amount_key}")
            else:
                logger.warning("No suitable amount field found")
                return None
                
        category_stats = sorted(category_stats, key=lambda x: abs(x[amount_key]), reverse=True)
        
        # 限制类别数量
        if len(category_stats) > 8:
            top_categories = category_stats[:7]
            other_amount = sum(c[amount_key] for c in category_stats[7:])
            other_count = sum(c.get('count', c.get('笔数', 0)) for c in category_stats[7:])
            
            top_categories.append({
                key_name: '其他',
                amount_key: other_amount,
                'count': other_count
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
        if 'merchant' in merchants_by_amount[0]:
            merchant_key = 'merchant'
        elif 'counterparty' in merchants_by_amount[0]:
            merchant_key = 'counterparty'
        elif '商户' in merchants_by_amount[0]:
            merchant_key = '商户'
        elif '交易对象' in merchants_by_amount[0]:
            merchant_key = '交易对象'
        else:
            logger.warning(f"Merchant data does not contain 'merchant', 'counterparty', or similar fields, trying other fields: {merchants_by_amount[0].keys()}")
            # 尝试找到类似商户的字段
            possible_keys = [k for k in merchants_by_amount[0].keys() if '商' in k or '户' in k or '对' in k]
            if possible_keys:
                merchant_key = possible_keys[0]
                logger.info(f"Using alternative merchant field name: {merchant_key}")
            else:
                logger.warning("No suitable merchant field found")
                return None
        
        # 检查金额字段
        if 'total' in merchants_by_amount[0]:
            amount_key = 'total'
        elif 'amount' in merchants_by_amount[0]:
            amount_key = 'amount'
        elif '金额' in merchants_by_amount[0]:
            amount_key = '金额'
        elif '总额' in merchants_by_amount[0]:
            amount_key = '总额'
        else:
            logger.warning(f"Merchant data does not contain 'total', 'amount', or similar fields, trying other fields: {merchants_by_amount[0].keys()}")
            # 尝试找到类似金额的字段
            possible_keys = [k for k in merchants_by_amount[0].keys() if '额' in k or '金' in k]
            if possible_keys:
                amount_key = possible_keys[0]
                logger.info(f"Using alternative amount field name: {amount_key}")
            else:
                logger.warning("No suitable amount field found")
                return None
        
        # 只取前10个商户
        if len(merchants_by_amount) > 10:
            merchants_by_amount = merchants_by_amount[:10]
        
        merchants = [m[merchant_key] for m in merchants_by_amount]
        amounts = [m[amount_key] for m in merchants_by_amount]
        
        # 获取交易笔数
        counts = []
        for m in merchants_by_amount:
            if 'count' in m:
                counts.append(m['count'])
            elif '笔数' in m:
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
        
        weekly_stats = sorted(self.data['weekly_stats'], key=lambda x: x['weekday'])
        
        weekdays = [w['weekday_name'] for w in weekly_stats]
        amounts = [w['total'] for w in weekly_stats]
        counts = [w['count'] for w in weekly_stats]
        
        return {
            'labels': weekdays,
            'values': amounts,  # 改为values以匹配前端代码
            'counts': counts
        }
    
    def get_monthly_data(self):
        """获取月度分析的图表数据"""
        if 'monthly_stats' not in self.data or not self.data['monthly_stats']:
            return None
        
        monthly_stats = sorted(self.data['monthly_stats'], key=lambda x: x['month_label'])
        
        # 限制只显示最近12个月
        if len(monthly_stats) > 12:
            monthly_stats = monthly_stats[-12:]
        
        months = [m['month_label'] for m in monthly_stats]
        incomes = [m['income'] for m in monthly_stats]
        expenses = [m['expense'] for m in monthly_stats]
        nets = [m['net'] for m in monthly_stats]
        
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
        
        yearly_stats = sorted(self.data['yearly_stats'], key=lambda x: x['year'])
        
        years = [y['year_label'] for y in yearly_stats]
        incomes = [y['income'] for y in yearly_stats]
        expenses = [y['expense'] for y in yearly_stats]
        nets = [y['net'] for y in yearly_stats]
        
        return {
            'labels': years,
            'income': incomes,
            'expense': expenses,
            'net': nets
        }

    def generate_weekday_chart(self, weekday_stats):
        """根据按星期统计的数据生成图表，并返回base64编码的图像
        
        Args:
            weekday_stats: 包含星期统计数据的DataFrame
            
        Returns:
            str: base64编码的图像字符串
        """
        try:
            if weekday_stats is None or weekday_stats.empty:
                logger.warning("无法生成星期分析图表，数据为空")
                return None
            
            # 确保按星期顺序排序
            weekday_stats = weekday_stats.sort_values('weekday')
            
            weekdays = weekday_stats['weekday_name'].tolist()
            amounts = weekday_stats['total'].tolist()
            counts = weekday_stats['count'].tolist()
            
            # 创建柱状图
            fig, ax1 = plt.subplots(figsize=(10, 6))
            
            # 金额柱状图
            x = np.arange(len(weekdays))
            bars = ax1.bar(x, amounts, alpha=0.7, width=0.6, color='#3F51B5')
            
            # 设置坐标轴
            ax1.set_ylabel('日均交易金额 (元)', color='#333333')
            ax1.set_title('星期消费分析')
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
            
            # 保存为内存中的图像并转为base64
            buf = io.BytesIO()
            plt.tight_layout()
            plt.savefig(buf, format='png', dpi=100)
            plt.close()
            
            # 将图像转换为base64字符串
            buf.seek(0)
            img_str = base64.b64encode(buf.read()).decode('utf-8')
            
            logger.info("星期分析图表生成成功")
            return img_str
            
        except Exception as e:
            logger.error(f"生成星期分析图表时出错: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None
    
    def generate_daily_spending_chart(self, daily_stats):
        """根据日消费统计数据生成图表，并返回base64编码的图像
        
        Args:
            daily_stats: 包含日统计数据的DataFrame
            
        Returns:
            str: base64编码的图像字符串
        """
        try:
            if daily_stats is None or daily_stats.empty:
                logger.warning("无法生成日消费趋势图，数据为空")
                return None
            
            # 确保按日期排序
            daily_stats = daily_stats.sort_values('date')
            
            # 只取最近30天的数据
            if len(daily_stats) > 30:
                daily_stats = daily_stats.tail(30)
            
            dates = daily_stats['date'].tolist()
            amounts = daily_stats['total'].tolist()
            counts = daily_stats['count'].tolist()
            
            # 创建柱状图
            fig, ax1 = plt.subplots(figsize=(12, 6))
            
            # 金额柱状图
            bars = ax1.bar(dates, amounts, alpha=0.6, color='#4CAF50')
            
            # 设置坐标轴
            ax1.set_ylabel('交易金额 (元)', color='#333333')
            ax1.set_title('日消费趋势')
            plt.xticks(rotation=45)
            ax1.tick_params(axis='y', colors='#333333')
            ax1.grid(axis='y', linestyle='--', alpha=0.7)
            
            # 创建第二个坐标轴，显示交易笔数
            ax2 = ax1.twinx()
            ax2.plot(dates, counts, 'o-', color='#2196F3', linewidth=2, label='交易笔数')
            ax2.set_ylabel('交易笔数', color='#2196F3')
            ax2.tick_params(axis='y', colors='#2196F3')
            
            # 添加图例
            from matplotlib.lines import Line2D
            custom_lines = [
                Line2D([0], [0], color='#4CAF50', lw=0, marker='s', markersize=10, alpha=0.6),
                Line2D([0], [0], color='#2196F3', lw=2, marker='o', markersize=5)
            ]
            ax1.legend(custom_lines, ['支出金额', '交易笔数'], loc='upper left')
            
            # 保存为内存中的图像并转为base64
            buf = io.BytesIO()
            plt.tight_layout()
            plt.savefig(buf, format='png', dpi=100)
            plt.close()
            
            # 将图像转换为base64字符串
            buf.seek(0)
            img_str = base64.b64encode(buf.read()).decode('utf-8')
            
            logger.info("日消费趋势图生成成功")
            return img_str
            
        except Exception as e:
            logger.error(f"生成日消费趋势图时出错: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None 