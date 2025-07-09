"""新服务架构的API路由示例

展示如何使用新的统一服务 DataService, ImportService, ReportService
"""

from flask import request, jsonify, current_app
from datetime import datetime, date
from . import api_bp

@api_bp.route('/v2/dashboard')
def dashboard_v2():
    """使用新 ReportService 的仪表盘数据接口"""
    try:
        # 使用新的报告服务
        report_service = current_app.report_service
        
        # 获取查询参数
        months = request.args.get('months', 12, type=int)
        
        # 获取仪表盘数据
        dashboard_data = report_service.get_dashboard_data(months=months)
        
        return jsonify({
            'success': True,
            'data': dashboard_data
        })
        
    except Exception as e:
        current_app.logger.error(f"获取仪表盘数据失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/v2/accounts')
def accounts_v2():
    """使用新 DataService 的账户列表接口"""
    try:
        # 使用新的数据服务
        data_service = current_app.data_service
        
        # 获取所有账户
        accounts = data_service.get_all_accounts()
        
        # 转换为JSON格式
        accounts_data = []
        for account in accounts:
            accounts_data.append({
                'id': account.id,
                'account_name': account.account_name,
                'account_number': account.account_number,
                'bank_name': account.bank.name if account.bank else None,
                'currency': account.currency
            })
        
        return jsonify({
            'success': True,
            'data': accounts_data
        })
        
    except Exception as e:
        current_app.logger.error(f"获取账户列表失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/v2/transactions')
def transactions_v2():
    """使用新 DataService 的交易记录接口"""
    try:
        # 使用新的数据服务
        data_service = current_app.data_service
        
        # 获取查询参数
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        account_id = request.args.get('account_id', type=int)
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        transaction_type = request.args.get('type')  # 'income', 'expense', 'all'
        
        # 解析日期
        start_date = None
        end_date = None
        if start_date_str:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        if end_date_str:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        
        # 构建过滤器
        filters = {}
        if start_date_str:
            filters['start_date'] = start_date_str
        if end_date_str:
            filters['end_date'] = end_date_str
        
        # 获取分页数据
        pagination = data_service.get_transactions_paginated(
            filters=filters,
            page=page,
            per_page=per_page,
            transaction_type_filter=transaction_type
        )
        
        # 转换为JSON格式
        transactions_data = []
        for transaction in pagination.items:
            transactions_data.append({
                'id': transaction.id,
                'date': transaction.date.strftime('%Y-%m-%d'),
                'amount': float(transaction.amount),
                'currency': transaction.currency,
                'description': transaction.description,
                'counterparty': transaction.counterparty,
                'account_name': transaction.account.account_name if transaction.account else None,
                'bank_name': transaction.account.bank.name if transaction.account and transaction.account.bank else None
            })
        
        return jsonify({
            'success': True,
            'data': {
                'transactions': transactions_data,
                'pagination': {
                    'page': pagination.page,
                    'per_page': pagination.per_page,
                    'total': pagination.total,
                    'pages': pagination.pages,
                    'has_prev': pagination.has_prev,
                    'has_next': pagination.has_next
                }
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"获取交易记录失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/v2/upload', methods=['POST'])
def upload_v2():
    """使用新 ImportService 的文件上传接口"""
    try:
        # 使用新的导入服务
        import_service = current_app.import_service
        
        # 检查是否有文件上传
        if 'files' not in request.files:
            return jsonify({
                'success': False,
                'error': '没有上传文件'
            }), 400
        
        files = request.files.getlist('files')
        if not files or files[0].filename == '':
            return jsonify({
                'success': False,
                'error': '没有选择文件'
            }), 400
        
        # 处理上传的文件
        results, message = import_service.process_uploaded_files(files)
        
        if results is None:
            return jsonify({
                'success': False,
                'error': message
            }), 400
        
        # 统计处理结果
        total_records = sum(result.get('record_count', 0) for result in results)
        processed_files = len(results)
        
        return jsonify({
            'success': True,
            'message': message,
            'data': {
                'processed_files': processed_files,
                'total_records': total_records,
                'details': results
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"文件上传处理失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/v2/reports/period-summary')
def period_summary_v2():
    """使用新 ReportService 的期间汇总接口"""
    try:
        # 使用新的报告服务
        report_service = current_app.report_service
        
        # 获取查询参数
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        
        if not start_date_str or not end_date_str:
            return jsonify({
                'success': False,
                'error': '缺少必要的日期参数'
            }), 400
        
        # 解析日期
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        
        # 获取期间汇总
        summary = report_service.get_period_summary(start_date, end_date)
        
        return jsonify({
            'success': True,
            'data': summary
        })
        
    except Exception as e:
        current_app.logger.error(f"获取期间汇总失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/v2/reports/monthly-trend')
def monthly_trend_v2():
    """使用新 ReportService 的月度趋势接口"""
    try:
        # 使用新的报告服务
        report_service = current_app.report_service
        
        # 获取查询参数
        months = request.args.get('months', 12, type=int)
        
        # 获取月度趋势
        trend = report_service.get_monthly_trend(months=months)
        
        return jsonify({
            'success': True,
            'data': trend
        })
        
    except Exception as e:
        current_app.logger.error(f"获取月度趋势失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/v2/status')
def service_status():
    """新服务状态检查接口"""
    try:
        # 检查所有新服务的状态
        data_service = current_app.data_service
        import_service = current_app.import_service
        report_service = current_app.report_service

        # 基础功能测试
        banks_count = len(data_service.get_all_banks())
        accounts_count = len(data_service.get_all_accounts())
        extractors_count = len(import_service._extractors)

        return jsonify({
            'success': True,
            'status': {
                'data_service': 'active',
                'import_service': 'active',
                'report_service': 'active',
                'banks_count': banks_count,
                'accounts_count': accounts_count,
                'extractors_count': extractors_count
            }
        })

    except Exception as e:
        current_app.logger.error(f"服务状态检查失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
