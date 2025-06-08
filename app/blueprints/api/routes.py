from flask import request, jsonify, send_file, current_app
from datetime import datetime, timedelta
import os # For send_file basename

# 使用新的分析服务
from app.services.analysis.analysis_service import ComprehensiveService as AnalysisService

from . import api_bp

@api_bp.route('/data') # API 路径 /api/data
def api_data_route(): #重命名函数
    """API接口获取分析数据"""
    try:
        # 使用新的分析服务
        analysis_service = AnalysisService()

        start_date = request.args.get('start_date', None)
        end_date = request.args.get('end_date', None)
        account_number = request.args.get('account_number', None)
        currency = request.args.get('currency', None)
        account_name = request.args.get('account_name', None)
        
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')
        if not start_date:
            start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
        
        # 转换日期格式
        if start_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        if end_date:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()

        # 获取账户ID（如果指定了账户号码）
        account_id = None
        if account_number:
            from app.models import Account
            account = Account.query.filter_by(account_number=account_number).first()
            if account:
                account_id = account.id

        # 获取分析数据
        data = analysis_service.generate_financial_report(
            account_id=account_id,
            start_date=start_date,
            end_date=end_date
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
        db_facade = current_app.db_facade
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
        
        output_file = db_facade.export_to_csv(query_params=query_params)
        
        if output_file and os.path.exists(output_file):
            return send_file(output_file, as_attachment=True, download_name=os.path.basename(output_file))
        else:
            current_app.logger.warning(f"API /export_transactions: 无法导出交易记录或文件未找到. Output file: {output_file}")
            return jsonify({"success": False, "error": "无法导出交易记录或文件未找到"}), 404

    except Exception as e:
        current_app.logger.error(f"API /export_transactions 时出错: {e}", exc_info=True)
        raise