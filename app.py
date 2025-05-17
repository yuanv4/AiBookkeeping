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
import shutil
from pathlib import Path
from datetime import datetime, timedelta

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
sys.path.append(ROOT_DIR)

# 导入自定义模块 - 更新为新的模块结构
from scripts.analyzers.transaction_analyzer import TransactionAnalyzer
from scripts.visualization.visualization_helper import VisualizationHelper
from scripts.extractors.factory.extractor_factory import get_extractor_factory
from scripts.db.db_manager import DBManager

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # 用于flash消息
app.config['TEMPLATES_AUTO_RELOAD'] = True  # 禁用模板缓存，强制每次刷新重新加载模板

# 配置上传文件夹和数据文件夹
UPLOAD_FOLDER = os.path.join(ROOT_DIR, 'uploads')
DATA_FOLDER = os.path.join(ROOT_DIR, 'data')
SCRIPTS_FOLDER = os.path.join(ROOT_DIR, 'scripts')
PROCESSED_FOLDER = os.path.join(ROOT_DIR, 'processed_files')  # 添加已处理文件存档目录
ALLOWED_EXTENSIONS = {'xlsx', 'xls'}

# 确保上传文件夹和数据文件夹存在
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(DATA_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)  # 确保存档目录存在

# 初始化数据库管理器
db_manager = DBManager()
# 初始化提取器工厂
extractor_factory = get_extractor_factory()

# 在应用启动时准备数据库
def init_database():
    """初始化或加载数据库"""
    try:
        logger.info("应用启动: 初始化数据库")
        
        # 检查uploads目录中是否有新文件
        upload_dir = Path(UPLOAD_FOLDER)
        if upload_dir.exists():
            excel_files = list(upload_dir.glob('*.xlsx')) + list(upload_dir.glob('*.xls'))
            if excel_files:
                logger.info(f"发现 {len(excel_files)} 个Excel文件，开始自动处理")
                
                # 使用提取器工厂自动处理文件
                processed_files = extractor_factory.auto_detect_and_process(upload_dir)
                
                if processed_files:
                    logger.info(f"成功处理 {len(processed_files)} 个文件")
                    # 处理完成后移动已处理的文件到存档目录
                    for file_info in processed_files:
                        try:
                            file_name = file_info['file']
                            source_path = os.path.join(UPLOAD_FOLDER, file_name)
                            # 添加时间戳前缀，避免文件名冲突
                            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                            dest_path = os.path.join(PROCESSED_FOLDER, f"{timestamp}_{file_name}")
                            
                            # 移动文件
                            shutil.move(source_path, dest_path)
                            logger.info(f"已将处理过的文件移动到: {dest_path}")
                        except Exception as e:
                            logger.error(f"移动文件 {file_name} 时出错: {e}")
                            
                    # 创建交易分析器实例
                    logger.info("开始分析交易数据")
                    analyzer = TransactionAnalyzer(db_manager)
                    
                    # 从数据库加载数据
                    if analyzer.load_data():
                        # 生成分析数据
                        analysis_data = analyzer.analyze_transaction_data()
                        if analysis_data:
                            # 保存分析结果到JSON文件
                            output_file = os.path.join(DATA_FOLDER, 'analysis_data.json')
                            with open(output_file, 'w', encoding='utf-8') as f:
                                json.dump(analysis_data, f, ensure_ascii=False, indent=2)
                            logger.info(f"分析数据已保存到: {output_file}")
                        else:
                            logger.warning("未能生成分析数据")
                    else:
                        logger.warning("未能从数据库加载数据进行分析")
                else:
                    logger.warning("未能成功处理任何文件")
        
        # 获取数据库统计信息
        stats = db_manager.get_statistics()
        
        if stats and stats.get('total_transactions', 0) > 0:
            logger.info(f"数据库已加载，包含 {stats.get('total_transactions', 0)} 条交易记录")
            return True
        else:
            logger.info("数据库为空或新创建")
            return False
    except Exception as e:
        logger.error(f"初始化数据库时出错: {str(e)}")
        logger.error(traceback.format_exc())
        return False

# 在应用启动时调用
init_database()

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
            
            # 检查文件名是否已存在于已处理文件目录中
            processed_files = os.listdir(PROCESSED_FOLDER)
            is_processed = False
            for processed_file in processed_files:
                # 忽略时间戳前缀，检查文件名是否匹配
                if processed_file.endswith(filename):
                    duplicate_files.append(filename)
                    is_processed = True
                    break
            
            if is_processed:
                continue
                
            # 检查文件名是否已存在于上传目录
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
            flash(f'所选文件已存在或已处理过，跳过上传: {", ".join(duplicate_files)}')
            return redirect(url_for('dashboard'))
        
        # 如果有部分文件重复，提示用户
        if duplicate_files:
            flash(f'以下文件已存在或已处理过，跳过上传: {", ".join(duplicate_files)}')
        
        # 运行交易数据自动检测和提取过程
        try:
            if not filenames:
                # 如果没有新文件被保存(都是重复的)，直接返回仪表板
                return redirect(url_for('dashboard'))
                
            logger.info("开始自动检测银行类型并处理交易数据")
            flash('开始处理文件，请稍候...')
            
            # 调用自动检测和处理函数
            upload_dir = Path(UPLOAD_FOLDER)
            
            # 使用提取器工厂自动处理文件
            processed_files = extractor_factory.auto_detect_and_process(upload_dir)
            
            if processed_files:
                # 处理完成后移动已处理的文件到存档目录
                for file_info in processed_files:
                    try:
                        file_name = file_info['file']
                        source_path = os.path.join(UPLOAD_FOLDER, file_name)
                        # 添加时间戳前缀，避免文件名冲突
                        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                        dest_path = os.path.join(PROCESSED_FOLDER, f"{timestamp}_{file_name}")
                        
                        # 移动文件
                        shutil.move(source_path, dest_path)
                        logger.info(f"已将处理过的文件移动到: {dest_path}")
                    except Exception as e:
                        logger.error(f"移动文件 {file_name} 时出错: {e}")
                
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

@app.route('/dashboard')
def dashboard():
    """仪表盘页面"""
    try:
        # 获取账户余额
        balance_summary = db_manager.get_balance_summary()
        
        # 计算总余额
        total_balance = sum(float(account.get('latest_balance', 0) or 0) for account in balance_summary)
        
        # 取得近期交易记录（最新的10条）
        recent_transactions = db_manager.get_transactions(limit=10, distinct=True)
        
        # 格式化余额列表用于展示
        account_balances = []
        for account in balance_summary:
            account_balances.append({
                'account': account['account_number'],
                'bank': account['bank_name'],
                'balance': float(account['latest_balance'] or 0),
                'update_date': account['balance_date']
            })
        
        # 获取统计信息
        db_stats = db_manager.get_statistics()
        
        # 获取余额范围（最高和最低）
        balance_range = db_manager.get_balance_range()
        
        # 获取月度余额历史数据
        monthly_balance_history = db_manager.get_monthly_balance_history(months=12)
        
        # 收支数据
        income = db_stats.get('total_income', 0)
        expense = db_stats.get('total_expense', 0)  # 保留原值，不转为正数
        net_income = db_stats.get('net_amount', 0)  
        
        # 计算月份数量（如果有开始和结束日期）
        months_count = 1
        if db_stats.get('min_date') and db_stats.get('max_date'):
            try:
                start_date = datetime.strptime(db_stats['min_date'], '%Y-%m-%d')
                end_date = datetime.strptime(db_stats['max_date'], '%Y-%m-%d')
                months_count = (end_date.year - start_date.year) * 12 + end_date.month - start_date.month + 1
                if months_count < 1:
                    months_count = 1
            except Exception as e:
                logger.warning(f"计算月份数时出错: {e}")
        
        # 计算平均交易金额
        avg_transaction = 0
        if db_stats.get('total_transactions', 0) > 0:
            total_amount = abs(income) + abs(expense)
            avg_transaction = total_amount / db_stats['total_transactions']
        
        # 组织返回数据
        data = {
            'summary': {
                'account_balance': total_balance,
                'account_balance_list': account_balances,
                'total_income': income,
                'total_expense': expense,
                'net_amount': net_income,
                'income_count': db_stats.get('income_count', 0),
                'expense_count': db_stats.get('expense_count', 0),
                'total_transactions': db_stats.get('total_transactions', 0),
                'start_date': db_stats.get('min_date'),
                'end_date': db_stats.get('max_date')
            },
            'transactions': recent_transactions,
            'charts': {
                'balance_history': monthly_balance_history,
                'monthly_labels': [],
                'monthly_income': [],
                'monthly_expense': [],
                'monthly_net': [],
                'income_source_labels': [],
                'income_source_values': [],
                'expense_category_labels': [],
                'expense_category_values': []
            },
            'max_balance': balance_range.get('max_balance', 0),
            'min_balance': balance_range.get('min_balance', 0),
            'months_count': months_count,
            'avg_transaction': avg_transaction
        }
        
        # 如果有近期交易，添加到数据中
        if recent_transactions:
            logger.info(f"仪表盘显示 {len(recent_transactions)} 条近期交易")
        else:
            logger.warning("没有近期交易数据可显示")
            
        # 记录余额历史数据
        if monthly_balance_history:
            logger.info(f"仪表盘显示 {len(monthly_balance_history)} 个月的余额历史数据")
        
        # 日志记录总余额和余额范围
        logger.info(f"仪表盘总余额: {total_balance}")
        logger.info(f"余额范围: 最高 = {balance_range.get('max_balance', 0)}, 最低 = {balance_range.get('min_balance', 0)}")
        
        # 调试储蓄率计算
        logger.info(f"储蓄率调试 - 总收入: {income}, 总支出: {expense}, 月数: {months_count}")
        if income > 0:
            monthly_income = income / months_count
            monthly_expense_abs = abs(expense) / months_count
            monthly_savings = monthly_income - monthly_expense_abs
            savings_rate = (monthly_savings / monthly_income * 100) if monthly_income > 0 else 0
            logger.info(f"储蓄率调试 - 月收入: {monthly_income}, 月支出(绝对值): {monthly_expense_abs}, 月储蓄: {monthly_savings}, 储蓄率: {savings_rate}%")
        
        return render_template('dashboard.html', data=data)
        
    except Exception as e:
        error_message = str(e)
        logger.error(f"仪表盘加载出错: {error_message}")
        logger.error(traceback.format_exc())
        flash(f'加载仪表盘数据时出错: {error_message}')
        # 返回带有默认值的数据结构
        return render_template('dashboard.html', data={
            'summary': {
                'account_balance': 0,
                'account_balance_list': [],
                'total_income': 0,
                'total_expense': 0,
                'net_amount': 0,
                'income_count': 0,
                'expense_count': 0,
                'total_transactions': 0,
                'start_date': None,
                'end_date': None
            },
            'transactions': [],
            'charts': {
                'balance_history': [],
                'monthly_labels': [],
                'monthly_income': [],
                'monthly_expense': [],
                'monthly_net': [],
                'income_source_labels': [],
                'income_source_values': [],
                'expense_category_labels': [],
                'expense_category_values': []
            },
            'max_balance': 0,
            'min_balance': 0,
            'months_count': 1,
            'avg_transaction': 0
        })

@app.route('/transactions')
def transactions():
    """交易记录页面"""
    try:
        # 解析查询参数
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 20, type=int)
        account_id = request.args.get('account_id', None, type=int)
        account_number = request.args.get('account_number', None)
        bank_name = request.args.get('bank', None)
        start_date = request.args.get('start_date', None)
        end_date = request.args.get('end_date', None)
        min_amount = request.args.get('min_amount', None, type=float)
        max_amount = request.args.get('max_amount', None, type=float)
        transaction_type = request.args.get('type', None)
        counterparty = request.args.get('counterparty', None)
        
        # 如果提供了account_number，查找对应的account_id
        if account_number and not account_id:
            conn = db_manager.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM accounts WHERE account_number = ?", (account_number,))
            result = cursor.fetchone()
            if result:
                account_id = result['id']
            conn.close()
        
        # 如果提供了bank_name，则只获取该银行的交易
        bank_id = None
        if bank_name:
            conn = db_manager.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM banks WHERE bank_name = ?", (bank_name,))
            result = cursor.fetchone()
            if result:
                bank_id = result['id']
            conn.close()
        
        # 计算偏移量
        offset = (page - 1) * limit
        
        # 构建查询参数
        query_params = {
            'account_id': account_id,
            'start_date': start_date,
            'end_date': end_date,
            'min_amount': min_amount,
            'max_amount': max_amount,
            'transaction_type': transaction_type,
            'counterparty': counterparty,
            'limit': limit,
            'offset': offset,
            'distinct': True  # 使用去重逻辑
        }
        
        # 获取交易记录总数
        total_count = db_manager.get_transactions_count(**{k: v for k, v in query_params.items() if k not in ['limit', 'offset']})
        
        # 获取当前页的交易记录
        transactions = db_manager.get_transactions(**query_params)
        
        # 为前端准备带有中文字段名的交易数据
        transactions_with_chinese_fields = []
        for tx in transactions:
            # 不再映射为中文字段名，保持英文字段名
            transactions_with_chinese_fields.append(tx)
        
        # 获取所有账户信息，用于过滤选择
        accounts = db_manager.get_accounts()
        
        # 获取所有交易类型（独立查询，确保获取所有类型）
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT type_name FROM transaction_types WHERE type_name IS NOT NULL ORDER BY type_name")
        transaction_types = [row['type_name'] for row in cursor.fetchall()]
        conn.close()
        
        # 组织返回数据
        data = {
            'transactions': transactions,
            'accounts': accounts,
            'categories': transaction_types,
            'filters': {
                'account_id': account_id,
                'account_number': account_number,
                'bank': bank_name,
                'start_date': start_date,
                'end_date': end_date,
                'min_amount': min_amount,
                'max_amount': max_amount,
                'type': transaction_type,
                'counterparty': counterparty
            },
            'pagination': {
                'page': page,
                'limit': limit,
                'total': total_count,
                'pages': (total_count + limit - 1) // limit
            }
        }
        
        # 将交易数据转换为JSON字符串，用于前端处理
        transactions_json = json.dumps(transactions_with_chinese_fields, ensure_ascii=False)
        
        # 将银行账户数据转换为JSON字符串
        bank_accounts_json = json.dumps(accounts, ensure_ascii=False)
        
        return render_template('transactions.html', 
                             data=data, 
                             transactions_json=transactions_json, 
                             bank_accounts_json=bank_accounts_json,
                             total_count=total_count)
        
    except Exception as e:
        error_message = str(e)
        logger.error(f"加载交易记录出错: {error_message}")
        logger.error(traceback.format_exc())
        flash(f'加载交易记录时出错: {error_message}')
        return render_template('transactions.html', 
                             data={'transactions': [], 'accounts': [], 'categories': []}, 
                             transactions_json="[]", 
                             bank_accounts_json="[]",
                             total_count=0)

@app.route('/api/data')
def api_data():
    """API接口获取分析数据"""
    try:
        # 获取查询参数
        start_date = request.args.get('start_date', None)
        end_date = request.args.get('end_date', None)
        account_id = request.args.get('account_id', None, type=int)
        
        # 如果没有指定结束日期，使用当前日期
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')
            
        # 如果没有指定开始日期，默认使用一年前的日期
        if not start_date:
            start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
        
        # 创建分析器并直接分析数据
        analyzer = TransactionAnalyzer(db_manager)
        data = analyzer.analyze_transaction_data_direct(start_date=start_date, end_date=end_date, account_id=account_id)
        
        if data and isinstance(data, dict) and 'summary' in data:
            # 直接返回分析数据
            return jsonify({
                'success': True,
                'data': data
            })
        else:
            # 分析失败，尝试检查是否存在缓存的分析文件
            analysis_file = os.path.join(DATA_FOLDER, 'analysis_data.json')
            if os.path.exists(analysis_file):
                with open(analysis_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                if data and isinstance(data, dict) and 'summary' in data:
                    logger.info("无法直接分析数据，使用缓存的分析文件")
                    return jsonify({
                        'success': True,
                        'data': data,
                        'cached': True
                    })
            
            # 无法分析数据且无缓存文件
            return jsonify({
                'success': False,
                'error': '无法分析交易数据'
            })
    except Exception as e:
        logger.error(f"获取分析数据时出错: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/export_transactions')
def export_transactions():
    """导出交易记录为CSV文件"""
    try:
        # 解析查询参数
        account_id = request.args.get('account_id', None, type=int)
        account_number = request.args.get('account_number', None)
        bank_name = request.args.get('bank', None)
        start_date = request.args.get('start_date', None)
        end_date = request.args.get('end_date', None)
        min_amount = request.args.get('min_amount', None, type=float)
        max_amount = request.args.get('max_amount', None, type=float)
        transaction_type = request.args.get('type', None)
        counterparty = request.args.get('counterparty', None)
        
        # 如果提供了account_number，查找对应的account_id
        if account_number and not account_id:
            conn = db_manager.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM accounts WHERE account_number = ?", (account_number,))
            result = cursor.fetchone()
            if result:
                account_id = result['id']
            conn.close()
        
        # 构建查询参数
        query_params = {
            'account_id': account_id,
            'start_date': start_date,
            'end_date': end_date,
            'min_amount': min_amount,
            'max_amount': max_amount,
            'transaction_type': transaction_type,
            'counterparty': counterparty,
            'distinct': True
        }
        
        # 导出CSV文件
        output_file = db_manager.export_to_csv(query_params)
        
        if output_file and os.path.exists(output_file):
            # 创建随机文件名
            filename = f"交易记录_{datetime.now().strftime('%Y%m%d%H%M%S')}.csv"
            
            # 返回文件下载响应
            return send_file(
                output_file,
                as_attachment=True,
                download_name=filename,
                mimetype='text/csv'
            )
        else:
            flash('导出失败，未找到符合条件的交易记录')
            return redirect(url_for('transactions'))
            
    except Exception as e:
        error_message = str(e)
        logger.error(f"导出交易记录时出错: {error_message}")
        logger.error(traceback.format_exc())
        flash(f'导出交易记录时出错: {error_message}')
        return redirect(url_for('transactions'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000) 