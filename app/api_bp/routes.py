from flask import request, jsonify, send_file, current_app
from datetime import datetime, timedelta
import os # For send_file basename

# TransactionAnalyzer 需要在运行时从 scripts 模块导入
# (scripts 目录已由 app/__init__.py 添加到 sys.path)
from scripts.analyzers.transaction_analyzer import TransactionAnalyzer

from . import api_bp

@api_bp.route('/data') # API 路径 /api/data
def api_data_route(): #重命名函数
    """API接口获取分析数据"""
    try:
        db_manager = current_app.db_manager
        analyzer = TransactionAnalyzer(db_manager) # 实例化分析器

        start_date = request.args.get('start_date', None)
        end_date = request.args.get('end_date', None)
        account_number = request.args.get('account_number', None)
        currency = request.args.get('currency', None)
        account_name = request.args.get('account_name', None)
        
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')
        if not start_date:
            start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
        
        data = analyzer.analyze_transaction_data_direct(
            start_date=start_date, 
            end_date=end_date, 
            account_number=account_number,
            currency=currency,
            account_name=account_name
        )
        
        if data and isinstance(data, dict) and 'summary' in data:
            return jsonify({
                'success': True,
                'data': data
            })
        else:
            current_app.logger.warning("API /data: 直接从数据库分析数据失败或未返回有效数据结构")
            return jsonify({
                'success': False,
                'error': '无法分析交易数据'
            }), 400 # Bad request or no data for parameters
    except Exception as e:
        current_app.logger.error(f"API /data 时出错: {e}", exc_info=True)
        # 依赖全局错误处理器返回 500 JSON 响应
        raise

@api_bp.route('/export_transactions') # API 路径 /api/export_transactions
def export_transactions_route(): # 重命名函数
    """导出交易记录为CSV文件"""
    try:
        db_manager = current_app.db_manager
        query_params = {
            'account_number_filter': request.args.get('account_number', None),
            'start_date': request.args.get('start_date', None),
            'end_date': request.args.get('end_date', None),
            'min_amount': request.args.get('min_amount', None, type=float),
            'max_amount': request.args.get('max_amount', None, type=float),
            'transaction_type_filter': request.args.get('type', None),
            'counterparty_filter': request.args.get('counterparty', None),
            'currency_filter': request.args.get('currency', None),
            'account_name_filter': request.args.get('account_name_filter', None),
            'distinct': request.args.get('distinct', False, type=lambda v: v.lower() == 'true')
        }
        
        output_file = db_manager.export_to_csv(query_params=query_params)
        
        if output_file and os.path.exists(output_file):
            return send_file(output_file, as_attachment=True, download_name=os.path.basename(output_file))
        else:
            current_app.logger.warning(f"API /export_transactions: 无法导出交易记录或文件未找到. Output file: {output_file}")
            return jsonify({"success": False, "error": "无法导出交易记录或文件未找到"}), 404

    except Exception as e:
        current_app.logger.error(f"API /export_transactions 时出错: {e}", exc_info=True)
        raise 