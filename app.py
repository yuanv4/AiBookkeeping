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
from datetime import datetime

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
from scripts.extractors.bank_transaction_extractor import BankTransactionExtractor
from scripts.db.db_manager import DBManager

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # 用于flash消息

# 配置上传文件夹和数据文件夹
UPLOAD_FOLDER = os.path.join(ROOT_DIR, 'uploads')
DATA_FOLDER = os.path.join(ROOT_DIR, 'data')
SCRIPTS_FOLDER = os.path.join(ROOT_DIR, 'scripts')
ALLOWED_EXTENSIONS = {'xlsx', 'xls'}

# 确保上传文件夹和数据文件夹存在
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(DATA_FOLDER, exist_ok=True)

# 初始化数据库管理器
db_manager = DBManager()

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
                
                # 使用自动检测功能处理文件
                processed_files = BankTransactionExtractor.auto_detect_bank_and_process(upload_dir)
                
                if processed_files:
                    logger.info(f"成功处理 {len(processed_files)} 个文件")
                    # 处理完成后删除已处理的文件
                    # for file in excel_files:
                    #     try:
                    #         file.unlink()
                    #         logger.info(f"已删除处理过的文件: {file}")
                    #     except Exception as e:
                    #         logger.error(f"删除文件 {file} 时出错: {e}")
                            
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
            
            # 使用自动检测功能处理文件
            processed_files = BankTransactionExtractor.auto_detect_bank_and_process(upload_dir)
            
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
        
        # 收支数据
        income = db_stats.get('total_income', 0)
        expense = abs(db_stats.get('total_expense', 0))  # 转为正数以便于展示
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
                'total_transactions': db_stats.get('total_transactions', 0)
            },
            'transactions': recent_transactions,
            'charts': {},  # 添加空的charts对象
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
        
        # 日志记录总余额和余额范围
        logger.info(f"仪表盘总余额: {total_balance}")
        logger.info(f"余额范围: 最高 = {balance_range.get('max_balance', 0)}, 最低 = {balance_range.get('min_balance', 0)}")
        
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
                'total_transactions': 0
            },
            'transactions': [],
            'charts': {},  # 添加空的charts对象
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
        limit = request.args.get('limit', 50, type=int)
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
            # 映射英文字段名到中文字段名
            mapped_tx = {
                '交易日期': tx.get('transaction_date', ''),
                '交易金额': tx.get('amount', 0),
                '账户余额': tx.get('balance', 0),
                '交易对象': tx.get('counterparty', ''),
                '交易类型': tx.get('transaction_type', ''),
                '户名': tx.get('account_name', ''),
                '账号': tx.get('account_number', ''),
                '银行': tx.get('bank_name', ''),
                '货币': tx.get('currency', 'CNY'),
                '备注': tx.get('description', '')
            }
            transactions_with_chinese_fields.append(mapped_tx)
        
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
        
        return render_template('transactions.html', data=data, transactions_json=transactions_json, total_count=total_count)
        
    except Exception as e:
        error_message = str(e)
        logger.error(f"加载交易记录出错: {error_message}")
        logger.error(traceback.format_exc())
        flash(f'加载交易记录时出错: {error_message}')
        return render_template('transactions.html', data={'transactions': [], 'accounts': [], 'categories': []}, transactions_json="[]", total_count=0)

@app.route('/api/data')
def api_data():
    """API接口获取分析数据"""
    try:
        # 检查是否有data/analysis_data.json文件
        analysis_file = os.path.join(DATA_FOLDER, 'analysis_data.json')
        if os.path.exists(analysis_file):
            with open(analysis_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # 如果数据为空或无效，重新生成分析数据
            if not data or not isinstance(data, dict) or 'summary' not in data:
                analyzer = TransactionAnalyzer(db_manager)
                if analyzer.load_data():
                    data = analyzer.analyze_transaction_data()
                    # 保存最新分析结果
                    with open(analysis_file, 'w', encoding='utf-8') as f:
                        json.dump(data, f, ensure_ascii=False, indent=2)
                else:
                    # 如果加载数据失败，返回空结果
                    return jsonify({
                        'success': False,
                        'error': 'Failed to load transaction data'
                    })
            
            # 返回分析数据
            return jsonify({
                'success': True,
                'data': data
            })
        else:
            # 如果分析文件不存在，尝试重新生成
            analyzer = TransactionAnalyzer(db_manager)
            if analyzer.load_data():
                data = analyzer.analyze_transaction_data()
                # 保存分析结果
                with open(analysis_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                
                # 返回分析数据
                return jsonify({
                    'success': True,
                    'data': data
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'No analysis data found and failed to generate'
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
        start_date = request.args.get('start_date', None)
        end_date = request.args.get('end_date', None)
        min_amount = request.args.get('min_amount', None, type=float)
        max_amount = request.args.get('max_amount', None, type=float)
        transaction_type = request.args.get('type', None)
        counterparty = request.args.get('counterparty', None)
        
        # 构建查询参数
        query_params = {
            'account_id': account_id,
            'start_date': start_date,
            'end_date': end_date,
            'min_amount': min_amount,
            'max_amount': max_amount,
            'transaction_type': transaction_type,
            'counterparty': counterparty,
            'distinct': True  # 使用去重逻辑
        }
        
        # 导出文件名
        filename = f'交易记录_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        
        # 获取导出路径
        temp_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'temp')
        os.makedirs(temp_path, exist_ok=True)
        output_path = os.path.join(temp_path, filename)
        
        # 导出CSV文件
        result = db_manager.export_to_csv(query_params, output_path)
        
        if result and os.path.exists(output_path):
            # 返回CSV文件
            return send_file(output_path, 
                            mimetype='text/csv',
                            as_attachment=True,
                            download_name=filename)
        else:
            flash('导出CSV文件失败，请重试')
            return redirect(url_for('transactions'))
    
    except Exception as e:
        error_message = str(e)
        logger.error(f"导出交易记录时出错: {error_message}")
        logger.error(traceback.format_exc())
        flash(f'导出交易记录时出错: {error_message}')
        return redirect(url_for('transactions'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000) 