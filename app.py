import os
import subprocess
import logging
import matplotlib
matplotlib.use('Agg', force=True)  # 强制使用非交互式Agg后端
os.environ['MPLBACKEND'] = 'Agg'  # 设置环境变量
from flask import Flask, request, render_template, redirect, url_for, flash, send_file, jsonify, session
from werkzeug.utils import secure_filename
import pandas as pd
import json
import traceback
import sys
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('ai_bookkeeping')

# 项目根目录
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

# 添加scripts目录到Python路径，以便导入模块
sys.path.append(os.path.join(ROOT_DIR, 'scripts'))

# 导入自定义模块
from scripts.transaction_analyzer import TransactionAnalyzer
from scripts.visualization_helper import VisualizationHelper
from scripts.bank_transaction_extractor import BankTransactionExtractor

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # 用于flash消息

# 配置上传文件夹和数据文件夹
UPLOAD_FOLDER = os.path.join(ROOT_DIR, 'uploads')
DATA_FOLDER = os.path.join(ROOT_DIR, 'data')
TRANSACTIONS_FOLDER = os.path.join(DATA_FOLDER, 'transactions')
SCRIPTS_FOLDER = os.path.join(ROOT_DIR, 'scripts')
ALLOWED_EXTENSIONS = {'xlsx', 'xls'}

# 确保上传文件夹和数据文件夹存在
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(DATA_FOLDER, exist_ok=True)
os.makedirs(TRANSACTIONS_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 限制上传文件大小为16MB

# 验证文件扩展名是否合法
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/', methods=['GET'])
def index():
    """首页"""
    return redirect(url_for('dashboard'))

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    """文件上传页面"""
    if request.method == 'POST':
        # 检查是否有文件部分
        if 'file' not in request.files:
            flash('没有选择文件')
            return redirect(url_for('dashboard'))
        
        files = request.files.getlist('file')
        
        # 如果用户没有选择文件，浏览器也可能提交一个空的文件部分
        if not files or files[0].filename == '':
            flash('没有选择文件')
            return redirect(url_for('dashboard'))
        
        # 检查所有文件扩展名是否合法
        for file in files:
            if not allowed_file(file.filename):
                flash(f'不支持的文件类型: {file.filename}，请上传xlsx或xls文件')
                return redirect(url_for('dashboard'))
        
        # 保存所有合法文件并检查是否重复
        filenames = []
        duplicate_files = []
        
        for file in files:
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            
            # 检查文件名是否已存在
            if os.path.exists(file_path):
                # 检查文件内容是否相同(通过文件大小快速判断)
                file.seek(0, os.SEEK_END)
                file_size = file.tell()
                file.seek(0)
                
                existing_size = os.path.getsize(file_path)
                if file_size == existing_size:
                    duplicate_files.append(filename)
                    continue
            
            # 保存新文件
            file.save(file_path)
            filenames.append(filename)
        
        # 如果所有文件都是重复的，则提示用户并返回
        if not filenames and duplicate_files:
            flash(f'所选文件已存在并且内容相同，跳过上传: {", ".join(duplicate_files)}')
            return redirect(url_for('dashboard'))
        
        # 如果有部分文件重复，提示用户
        if duplicate_files:
            flash(f'以下文件已存在并且内容相同，跳过上传: {", ".join(duplicate_files)}')
        
        # 运行交易数据自动检测和提取过程
        try:
            if not filenames:
                # 如果没有新文件被保存(都是重复的)，直接返回仪表板
                return redirect(url_for('dashboard'))
                
            logger.info("开始自动检测银行类型并处理交易数据")
            flash('开始处理文件，请稍候...')
            
            # 调用自动检测和处理函数
            upload_dir = Path(UPLOAD_FOLDER)
            data_dir = Path(TRANSACTIONS_FOLDER)
            
            # 使用自动检测功能处理文件
            processed_files = BankTransactionExtractor.auto_detect_bank_and_process(upload_dir, data_dir)
            
            if processed_files:
                # 构建处理结果消息
                result_message = "处理完成。\n"
                result_message += f"成功处理 {len(processed_files)} 个文件，共提取 "
                total_records = sum(file_info['record_count'] for file_info in processed_files)
                result_message += f"{total_records} 条交易记录。\n"
                
                # 按银行分组统计
                bank_summary = {}
                for file_info in processed_files:
                    bank = file_info['bank']
                    if bank not in bank_summary:
                        bank_summary[bank] = {'files': 0, 'records': 0}
                    bank_summary[bank]['files'] += 1
                    bank_summary[bank]['records'] += file_info['record_count']
                
                result_message += "按银行分组统计：\n"
                for bank, stats in bank_summary.items():
                    result_message += f"- {bank}: {stats['files']} 个文件, {stats['records']} 条记录\n"
                
                flash(f'文件上传成功: {", ".join(filenames)}')
                flash(result_message)
                
                # 分析数据
                generate_analysis_data()
                return redirect(url_for('dashboard'))
            else:
                flash('处理完成，但未能成功提取任何交易记录。请确保文件格式正确。')
                return redirect(url_for('dashboard'))
                
        except Exception as e:
            error_message = str(e)
            logger.error(f"处理文件时出错: {error_message}")
            logger.error(traceback.format_exc())
            flash(f'处理文件时出错: {error_message}')
            return redirect(url_for('dashboard'))
        
    # GET请求，显示上传页面
    return render_template('upload.html')

def generate_analysis_data():
    """生成分析数据"""
    # 使用transactions目录中的所有CSV文件
    transactions_dir = TRANSACTIONS_FOLDER
    if not os.path.exists(transactions_dir):
        logger.error(f"找不到交易数据目录: {transactions_dir}")
        return False
    
    # 检查是否有CSV文件
    csv_files = [f for f in os.listdir(transactions_dir) if f.endswith('.csv')]
    if not csv_files:
        logger.error(f"在目录 {transactions_dir} 中找不到CSV文件")
        return False

    try:
        # 使用交易分析器的多文件加载功能
        logger.info(f"开始加载并分析目录中的所有CSV文件: {transactions_dir}")
        analyzer = TransactionAnalyzer()
        
        # 加载所有交易CSV文件
        if analyzer.load_multiple_data(transactions_dir):
            # 检查是否已有现有的分析数据文件，如果有，比较看是否有变化
            json_file = os.path.join(DATA_FOLDER, 'analysis_data.json')
            existing_transaction_count = 0
            
            if os.path.exists(json_file):
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        existing_data = json.load(f)
                        if 'summary' in existing_data and '交易笔数' in existing_data['summary']:
                            existing_transaction_count = existing_data['summary']['交易笔数']
                            logger.info(f"现有分析数据包含 {existing_transaction_count} 条交易记录")
                except Exception as e:
                    logger.error(f"读取现有分析数据文件时出错: {e}")
                    # 如果文件损坏，继续生成新的分析数据
            
            # 获取新加载的交易数据计数
            current_transaction_count = analyzer.get_transaction_count()
            logger.info(f"当前加载的交易数据包含 {current_transaction_count} 条记录")
            
            # 如果交易数量相同，可能数据没有变化
            if existing_transaction_count > 0 and current_transaction_count == existing_transaction_count:
                logger.info("交易数量没有变化，保持现有分析数据不变")
                return True
            
            # 生成分析数据
            result = analyzer.generate_json_data(json_file)
            
            if result:
                logger.info(f"分析数据已保存到: {json_file}")
                return True
            else:
                logger.error("生成JSON数据失败")
                return False
        else:
            logger.error("加载多个CSV文件失败")
            return False
    except Exception as e:
        logger.error(f"生成分析数据时出错: {str(e)}")
        logger.error(traceback.format_exc())
        return False

@app.route('/dashboard')
def dashboard():
    """仪表盘页面，显示总体财务概况"""
    # 检查是否有分析数据
    json_file = os.path.join(DATA_FOLDER, 'analysis_data.json')
    
    if not os.path.exists(json_file):
        flash('没有找到分析数据。请先上传并处理银行交易明细文件。')
        return redirect(url_for('upload_file'))
    
    try:
        # 加载分析数据
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 加载交易数据并获取分析
        analyzer = TransactionAnalyzer()
        if analyzer.load_multiple_data(TRANSACTIONS_FOLDER):
            # 确保summary数据存在
            if 'summary' in data:
                # 从summary中获取总收入和总支出数据
                data['income'] = data['summary'].get('总收入', 0)
                data['expense'] = data['summary'].get('总支出', 0) * -1  # 确保支出为负数
                logger.info(f"仪表盘 - 从summary获取数据: 总收入={data['income']}, 总支出={data['expense']}")
            else:
                data['income'] = 0
                data['expense'] = 0
                logger.warning("仪表盘 - 找不到summary数据，使用默认值")
            
            # 获取异常交易统计数据，使用IQR方法
            outlier_stats = analyzer.get_outlier_stats(method='iqr', threshold=1.5)
            
            # 将异常交易数据添加到data字典中
            data.update(outlier_stats)
            
            # 添加平均交易金额和月数统计
            summary = data.get('summary', {})
            if summary.get('交易笔数', 0) > 0:
                total_amount = summary.get('总收入', 0) + summary.get('总支出', 0)
                data['avg_transaction'] = abs(total_amount / summary.get('交易笔数', 1))
            else:
                data['avg_transaction'] = 0
                
            # 计算交易记录涵盖的月数
            if 'monthly_stats' in data and data['monthly_stats']:
                data['months_count'] = len(data['monthly_stats'])
            else:
                # 从交易日期范围估算
                if '起始日期' in summary and '结束日期' in summary:
                    try:
                        from datetime import datetime
                        start_date = datetime.strptime(summary['起始日期'], '%Y-%m-%d')
                        end_date = datetime.strptime(summary['结束日期'], '%Y-%m-%d')
                        diff_months = (end_date.year - start_date.year) * 12 + end_date.month - start_date.month + 1
                        data['months_count'] = max(1, diff_months)
                    except Exception as e:
                        logger.error(f"计算月数出错: {str(e)}")
                        data['months_count'] = 1
                else:
                    data['months_count'] = 1
                    
            # 计算最高和最低余额
            if 'transactions' in data and data['transactions']:
                balances = []
                for transaction in data['transactions']:
                    if '账户余额' in transaction and transaction['账户余额'] is not None:
                        balances.append(transaction['账户余额'])
                        
                if balances:
                    data['max_balance'] = max(balances)
                    data['min_balance'] = min(balances)
                else:
                    # 每个交易记录必须有账户余额
                    logger.warning("没有找到任何账户余额数据")
                    data['max_balance'] = 0
                    data['min_balance'] = 0
            else:
                # 没有交易记录
                logger.warning("没有找到任何交易记录")
                data['max_balance'] = 0
                data['min_balance'] = 0
        
        # 获取摘要数据
        summary = data['summary'] if 'summary' in data else {}
        
        # 添加账户余额字段到summary中，处理多张卡的情况
        total_balance = 0
        
        if 'transactions' in data and data['transactions'] and len(data['transactions']) > 0:
            # 按账号分组，找出每个账号的最新交易记录
            account_groups = {}
            for transaction in data['transactions']:
                account_number = transaction.get('账号', '')
                if not account_number:
                    continue
                    
                # 获取交易日期
                trans_date = transaction.get('交易日期', '')
                if not trans_date:
                    continue
                    
                # 如果这个账号还没有记录，或者这个交易比已有记录更新，则更新
                if account_number not in account_groups or trans_date > account_groups[account_number].get('交易日期', ''):
                    account_groups[account_number] = transaction
            
            # 计算所有账号的余额总和
            account_balances = []
            for account_number, latest_trans in account_groups.items():
                if '账户余额' in latest_trans:
                    balance = latest_trans['账户余额']
                    total_balance += balance
                    # 记录账户余额信息，用于显示
                    account_balances.append({
                        '账号': account_number,
                        '余额': balance,
                        '银行': latest_trans.get('银行', '未知银行')
                    })
            
            # 保存账户余额列表到summary中
            summary['账户余额列表'] = sorted(account_balances, key=lambda x: x['余额'], reverse=True)
            summary['账户余额'] = total_balance
            logger.info(f"计算得到{len(account_balances)}个账户，总余额为{total_balance}")
        else:
            summary['账户余额'] = 0
            summary['账户余额列表'] = []
            logger.warning("没有交易数据，使用0作为账户余额默认值")
        
        # 构建可视化助手
        viz_helper = VisualizationHelper(data=data)
            
        # 生成图表
        logger.info("开始生成图表")
        charts = viz_helper.generate_all_charts()
        
        # 为前端图表数据准备相应的数据结构
        chart_data = {}
        
        # 添加年度数据
        yearly_data = viz_helper.get_yearly_data()
        if yearly_data:
            chart_data['yearly_data'] = yearly_data
            logger.info("年度图表数据生成成功")
        else:
            logger.warning("未能生成年度图表数据")
            
        # 添加类别数据
        category_data = viz_helper.get_category_data()
        if category_data:
            chart_data['category_data'] = category_data
            logger.info("类别图表数据生成成功")
        else:
            logger.warning("未能生成类别图表数据")
            
        # 添加星期数据
        weekday_data = viz_helper.get_weekday_data()
        if weekday_data:
            chart_data['weekday_data'] = weekday_data
            logger.info("星期图表数据生成成功")
        else:
            logger.warning("未能生成星期图表数据")
            
        # 添加商户数据
        merchant_data = viz_helper.get_merchant_data()
        if merchant_data:
            chart_data['merchant_data'] = merchant_data
            logger.info("商户图表数据生成成功")
        else:
            logger.warning("未能生成商户图表数据")
        
        logger.info(f"图表数据生成完成，包含 {len(chart_data)} 个图表数据集")
        
        # 获取最近交易记录
        recent_transactions = []
        if 'transactions' in data:
            # 按照交易日期排序，确保最新的交易显示在前面
            sorted_transactions = sorted(data['transactions'], 
                                        key=lambda x: x.get('交易日期', ''), 
                                        reverse=True)  # 降序排列，最新的在前面
            recent_transactions = sorted_transactions[:10]  # 获取最新的10条交易
            logger.info(f"获取最近交易记录 - 已按日期排序，取前10条，最新日期: {recent_transactions[0].get('交易日期', '') if recent_transactions else '无'}")
        
        # 获取类别统计
        category_stats = []
        if 'category_stats' in data:
            category_stats = data['category_stats']
            
        return render_template('dashboard.html', 
                              charts=chart_data, 
                              recent_transactions=recent_transactions,
                              category_stats=category_stats,
                              summary=summary,
                              data=data,
                              abs=abs,
                              min=min)
    
    except Exception as e:
        logger.error(f"生成仪表盘页面时出错: {str(e)}")
        logger.error(traceback.format_exc())
        return render_template('error.html', error=f"生成仪表盘页面时出错: {str(e)}")

@app.route('/transactions')
def transactions():
    """交易记录页面"""
    # 只检查分析数据文件是否存在
    json_file = os.path.join(DATA_FOLDER, 'analysis_data.json')
    
    if not os.path.exists(json_file):
        flash('找不到交易数据，请先上传文件')
        return render_template('transactions.html', 
                              transactions_data=[],
                              banks=[],
                              accounts=[])
    
    try:
        # 加载分析数据
        logger.info(f"加载交易记录数据: {json_file}")
        with open(json_file, 'r', encoding='utf-8') as f:
            analysis_data = json.load(f)
        
        # 创建一个新的交易数据列表，确保格式一致性
        transactions_data = []
        
        # 检查分析数据中是否包含transactions字段
        if 'transactions' in analysis_data and analysis_data['transactions']:
            raw_transactions = analysis_data['transactions']
            logger.info(f"从分析数据中找到{len(raw_transactions)}条原始交易记录")
            
            # 处理每条交易记录，确保必要的字段存在
            for i, trans in enumerate(raw_transactions):
                # 创建一个标准格式的交易记录
                processed_trans = {
                    '交易日期': trans.get('交易日期', ''),
                    '交易金额': trans.get('交易金额', 0),
                    '交易类型': trans.get('交易类型', '未知'),
                    '交易对象': trans.get('交易对象', ''),
                    '账户余额': trans.get('账户余额', 0),
                    '账号': trans.get('账号', ''),
                    '银行': trans.get('银行', '未知银行')
                }
                transactions_data.append(processed_trans)
            
            # 输出一些示例数据以帮助调试
            logger.info(f"处理后的交易记录数量: {len(transactions_data)}")
            if transactions_data:
                logger.info(f"示例交易记录: {json.dumps(transactions_data[0], ensure_ascii=False)}")
        else:
            logger.warning("分析数据中未找到交易记录或transactions字段为空")
        
        # 如果仍然没有交易数据，生成示例数据
        if not transactions_data:
            logger.info("生成示例交易数据")
            # 生成一些示例交易数据
            for i in range(10):
                transactions_data.append({
                    '交易日期': f"2023-{(i%12)+1:02d}-{(i%28)+1:02d}",
                    '交易金额': 100.00 if i % 2 == 0 else -200.00,
                    '交易类型': '收入' if i % 2 == 0 else '支出',
                    '交易对象': f'示例商户{i+1}',
                    '账户余额': 1000.00 - i * 50,
                    '账号': '123456789012',
                    '银行': '示例银行'
                })
            flash('显示的是示例交易数据，请重新上传交易数据文件以查看实际交易记录', 'warning')
        
        # 获取分类和日期范围供筛选使用
        categories = set()
        min_date = None
        max_date = None
        
        for trans in transactions_data:
            if '交易类型' in trans and trans['交易类型']:
                categories.add(trans['交易类型'])
            
            if '交易日期' in trans and trans['交易日期']:
                date = trans['交易日期']
                if min_date is None or date < min_date:
                    min_date = date
                if max_date is None or date > max_date:
                    max_date = date
        
        categories = sorted(list(categories))
        logger.info(f"筛选信息: 交易类型数量:{len(categories)}, 日期范围:{min_date}至{max_date}")
        
        # 将交易数据直接转换为JSON字符串，避免模板引擎的处理问题
        transactions_json = json.dumps(transactions_data, ensure_ascii=False)
        logger.info(f"生成的JSON数据长度: {len(transactions_json)}")
        
        return render_template('transactions.html', 
                              transactions=transactions_data,
                              transactions_json=transactions_json,
                              categories=categories,
                              min_date=min_date,
                              max_date=max_date)
    except Exception as e:
        logger.error(f"加载交易记录时出错: {e}")
        logger.error(traceback.format_exc())
        flash(f'加载数据时出错: {str(e)}', 'danger')
        return render_template('error.html', error=str(e), traceback=traceback.format_exc())

@app.route('/monthly')
def monthly_analysis():
    """月度收支分析页面"""
    # 只检查分析数据文件是否存在
    json_file = os.path.join(DATA_FOLDER, 'analysis_data.json')
    
    if not os.path.exists(json_file):
        flash('找不到交易数据，请先上传文件')
        return render_template('monthly.html', 
                              monthly_stats=[], 
                              monthly_data=None,
                              year_filter=None,
                              page_title="月度分析")
    
    try:
        # 加载分析数据
        with open(json_file, 'r', encoding='utf-8') as f:
            analysis_data = json.load(f)
        
        # 获取URL中的年份参数
        year_filter = request.args.get('year')
        
        # 获取月度统计数据
        monthly_stats = []
        if 'monthly_stats' in analysis_data:
            monthly_stats = sorted(analysis_data['monthly_stats'], key=lambda x: x['月份'])
            
            # 如果有年份过滤器，只显示该年份的月份数据
            if year_filter:
                monthly_stats = [month for month in monthly_stats if month['月份'].startswith(str(year_filter))]
        
        # 准备月度图表数据
        monthly_data = None
        if monthly_stats:  # 使用过滤后的monthly_stats
            # 手动构建图表数据
            labels = [month['月份'] for month in monthly_stats]
            income = [month['收入'] for month in monthly_stats]
            expense = [month['支出'] for month in monthly_stats]
            net = [month['净额'] for month in monthly_stats]
            
            monthly_data = {
                'labels': labels,
                'income': income,
                'expense': expense,
                'net': net
            }
        
        page_title = f"{year_filter}年月度分析" if year_filter else "月度分析"
        
        return render_template('monthly.html', 
                              monthly_stats=monthly_stats, 
                              monthly_data=monthly_data,
                              year_filter=year_filter,
                              page_title=page_title)
    
    except Exception as e:
        logger.error("生成月度分析页面时出错: %s", str(e))
        logger.error(traceback.format_exc())
        return render_template('error.html', error=f"生成月度分析页面时出错: {str(e)}")

@app.route('/yearly')
def yearly_analysis():
    """年度收支分析页面"""
    # 只检查分析数据文件是否存在
    json_file = os.path.join(DATA_FOLDER, 'analysis_data.json')
    
    if not os.path.exists(json_file):
        flash('找不到交易数据，请先上传文件')
        return render_template('yearly.html', yearly_stats=[], yearly_data=None)
    
    try:
        # 加载分析数据
        with open(json_file, 'r', encoding='utf-8') as f:
            analysis_data = json.load(f)
        
        # 获取年度统计数据
        yearly_stats = []
        if 'yearly_stats' in analysis_data:
            yearly_stats = sorted(analysis_data['yearly_stats'], key=lambda x: x['年份'])
        
        # 准备年度图表数据
        yearly_data = None
        if 'yearly_stats' in analysis_data and analysis_data['yearly_stats']:
            viz_helper = VisualizationHelper(data=analysis_data)
            yearly_data = viz_helper.get_yearly_data()
        
        return render_template('yearly.html', yearly_stats=yearly_stats, yearly_data=yearly_data)
    
    except Exception as e:
        logger.error("生成年度分析页面时出错: %s", str(e))
        logger.error(traceback.format_exc())
        return render_template('error.html', error=f"生成年度分析页面时出错: {str(e)}")

@app.route('/category')
def category_analysis():
    """类别支出分析页面"""
    # 只检查分析数据文件是否存在
    json_file = os.path.join(DATA_FOLDER, 'analysis_data.json')
    
    if not os.path.exists(json_file):
        flash('找不到交易数据，请先上传文件')
        return render_template('category.html', 
                              category_stats=[], 
                              category_data=None)
    
    try:
        # 加载分析数据
        with open(json_file, 'r', encoding='utf-8') as f:
            analysis_data = json.load(f)
        
        # 获取类别统计数据
        category_stats = []
        if 'category_stats' in analysis_data:
            category_stats = sorted(analysis_data['category_stats'], key=lambda x: x['总额'], reverse=True)
        
        # 准备类别图表数据
        category_data = None
        if 'category_stats' in analysis_data and analysis_data['category_stats']:
            viz_helper = VisualizationHelper(data=analysis_data)
            category_data = viz_helper.get_category_data()
            
        # 获取URL参数中的类别过滤器
        category_filter = request.args.get('category')
        if category_filter:
            # 过滤交易数据以获取特定类别的交易
            transactions = []
            if 'transactions' in analysis_data:
                transactions = [t for t in analysis_data['transactions'] if t.get('交易分类') == category_filter]
            return render_template('category.html', 
                                  category_stats=category_stats, 
                                  category_data=category_data,
                                  category_filter=category_filter,
                                  filtered_transactions=transactions)
        
        return render_template('category.html', 
                               category_stats=category_stats, 
                               category_data=category_data)
    
    except Exception as e:
        logger.error("生成类别分析页面时出错: %s", str(e))
        logger.error(traceback.format_exc())
        return render_template('error.html', error=f"生成类别分析页面时出错: {str(e)}")

@app.route('/time')
def time_analysis():
    """时间分析页面（按星期/日分析）"""
    # 只检查分析数据文件是否存在
    json_file = os.path.join(DATA_FOLDER, 'analysis_data.json')
    
    if not os.path.exists(json_file):
        flash('找不到交易数据，请先上传文件')
        return render_template('time.html', 
                              weekly_stats=[], 
                              daily_stats=[],
                              weekday_data=None,
                              daily_data=None)
    
    try:
        # 加载分析数据
        with open(json_file, 'r', encoding='utf-8') as f:
            analysis_data = json.load(f)
        
        # 获取星期统计数据
        weekly_stats = []
        if 'weekly_stats' in analysis_data:
            weekly_stats = sorted(analysis_data['weekly_stats'], key=lambda x: x['星期'])
            
        # 获取每日统计数据
        daily_stats = []
        if 'daily_stats' in analysis_data:
            daily_stats = sorted(analysis_data['daily_stats'], key=lambda x: x['日期'], reverse=True)
        
        # 准备星期图表数据
        weekday_data = None
        if 'weekly_stats' in analysis_data and analysis_data['weekly_stats']:
            viz_helper = VisualizationHelper(data=analysis_data)
            weekday_data = viz_helper.get_weekday_data()
            
        # 准备每日图表数据
        daily_data = None
        if 'daily_stats' in analysis_data and analysis_data['daily_stats']:
            # 创建每日数据的格式化结构
            daily_amounts = [d.get('总额', 0) for d in daily_stats[:90]]  # 最近90天
            daily_counts = [d.get('笔数', 0) for d in daily_stats[:90]]
            daily_dates = [d.get('日期', '') for d in daily_stats[:90]]
            daily_data = {
                'labels': daily_dates,
                'amounts': daily_amounts,
                'counts': daily_counts
            }
        
        # 获取URL参数中的过滤器
        day_filter = request.args.get('day')
        if day_filter:
            # 过滤交易数据以获取特定星期的交易
            try:
                day_index = int(day_filter)
                day_name = weekly_stats[day_index]['星期名'] if 0 <= day_index < len(weekly_stats) else None
                if day_name:
                    transactions = []
                    if 'transactions' in analysis_data:
                        # 找出所有属于该星期的交易
                        import datetime
                        transactions = [t for t in analysis_data['transactions'] 
                                      if datetime.datetime.strptime(t.get('交易日期', ''), '%Y-%m-%d').weekday() == day_index]
                    
                    return render_template('time.html', 
                                         weekly_stats=weekly_stats,
                                         daily_stats=daily_stats[:30],  # 显示最近30天
                                         weekday_data=weekday_data,
                                         daily_data=daily_data,
                                         day_filter=day_name,
                                         filtered_transactions=transactions)
            except (ValueError, IndexError) as e:
                logger.error(f"处理星期过滤器时出错: {e}")
        
        return render_template('time.html', 
                               weekly_stats=weekly_stats, 
                               daily_stats=daily_stats[:30],  # 显示最近30天
                               weekday_data=weekday_data,
                               daily_data=daily_data)
    
    except Exception as e:
        logger.error("生成时间分析页面时出错: %s", str(e))
        logger.error(traceback.format_exc())
        return render_template('error.html', error=f"生成时间分析页面时出错: {str(e)}")

@app.route('/merchant')
def merchant_analysis():
    """商户分析页面"""
    # 只检查分析数据文件是否存在
    json_file = os.path.join(DATA_FOLDER, 'analysis_data.json')
    
    if not os.path.exists(json_file):
        flash('找不到交易数据，请先上传文件')
        return render_template('merchant.html', 
                              top_merchants={'by_amount': [], 'by_count': []},
                              merchant_data=None)
    
    try:
        # 加载分析数据
        with open(json_file, 'r', encoding='utf-8') as f:
            analysis_data = json.load(f)
        
        # 获取商户统计数据
        merchant_stats = []
        if 'top_merchants' in analysis_data and 'by_amount' in analysis_data['top_merchants']:
            merchant_stats = analysis_data['top_merchants']['by_amount']
        
        merchant_count_stats = []
        if 'top_merchants' in analysis_data and 'by_count' in analysis_data['top_merchants']:
            merchant_count_stats = analysis_data['top_merchants']['by_count']
        
        # 创建top_merchants字典以匹配模板中的变量名
        top_merchants = {
            'by_amount': merchant_stats,
            'by_count': merchant_count_stats
        }
        
        # 准备商户图表数据
        merchant_data = None
        if 'top_merchants' in analysis_data and 'by_amount' in analysis_data['top_merchants']:
            viz_helper = VisualizationHelper(data=analysis_data)
            try:
                merchant_data = viz_helper.get_merchant_data()
                # 确保所有值都是基本类型，可以被JSON序列化
                if merchant_data and isinstance(merchant_data, dict):
                    for key in list(merchant_data.keys()):
                        if not isinstance(merchant_data[key], (list, str, int, float, bool, type(None))):
                            # 尝试转换为列表
                            try:
                                merchant_data[key] = list(map(float, merchant_data[key]))
                            except (TypeError, ValueError) as e:
                                logger.error(f"无法将{key}转换为列表: {e}")
                                # 如果转换失败，删除这个键
                                del merchant_data[key]
                        
                        # 检查列表中的每个元素
                        if isinstance(merchant_data[key], list):
                            for i, item in enumerate(merchant_data[key]):
                                if callable(item) or not isinstance(item, (str, int, float, bool, type(None))):
                                    logger.error(f"发现不可序列化的值: {key}[{i}] = {type(item)}")
                                    # 将不可序列化的值替换为字符串
                                    merchant_data[key][i] = str(item)
                
                # 尝试序列化一次，看是否会出错
                try:
                    json.dumps(merchant_data)
                except TypeError as e:
                    logger.error(f"JSON序列化失败: {e}")
                    # 遍历字典，找出不可序列化的值
                    for key, value in list(merchant_data.items()):
                        try:
                            json.dumps({key: value})
                        except TypeError:
                            logger.error(f"键'{key}'包含不可序列化的值")
                            # 尝试移除问题键
                            del merchant_data[key]
            except Exception as e:
                logger.error(f"处理商户图表数据时出错: {e}")
                logger.error(traceback.format_exc())
                merchant_data = None
        
        # 获取URL参数中的商户过滤器
        merchant_filter = request.args.get('merchant')
        if merchant_filter:
            # 过滤交易数据以获取特定商户的交易
            transactions = []
            if 'transactions' in analysis_data:
                transactions = [t for t in analysis_data['transactions'] if t.get('交易对方') == merchant_filter]
            
            return render_template('merchant.html', 
                                  top_merchants=top_merchants,
                                  merchant_data=merchant_data,
                                  merchant_filter=merchant_filter,
                                  filtered_transactions=transactions)
        
        return render_template('merchant.html', 
                               top_merchants=top_merchants,
                               merchant_data=merchant_data)
    
    except Exception as e:
        logger.error("生成商户分析页面时出错: %s", str(e))
        logger.error(traceback.format_exc())
        return render_template('error.html', error=f"生成商户分析页面时出错: {str(e)}")

@app.route('/download')
def download_result():
    """下载结果页面"""
    return render_template('download.html')

@app.route('/get_csv')
def get_csv():
    """提供CSV文件下载"""
    output_csv = os.path.join(DATA_FOLDER, 'bank_transactions.csv')
    return send_file(output_csv,
                     mimetype='text/csv',
                     as_attachment=True)

@app.route('/api/data')
def api_data():
    """提供JSON格式的分析数据"""
    json_file = os.path.join(DATA_FOLDER, 'analysis_data.json')
    
    if not os.path.exists(json_file):
        if not generate_analysis_data():
            return jsonify({'error': '找不到交易数据'}), 404
    
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    return jsonify(data)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000) 