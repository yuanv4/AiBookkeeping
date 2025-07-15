"""支出分析路由

提供支出分析页面和API端点
"""

from flask import render_template, jsonify, current_app
from . import expense_analysis_bp
from app.utils.decorators import handle_errors
import logging

logger = logging.getLogger(__name__)


@expense_analysis_bp.route('/')
@handle_errors
def index():
    """支出分析主页面"""
    return render_template('expense_analysis.html')


@expense_analysis_bp.route('/debug')
@handle_errors
def debug():
    """调试页面"""
    return '''
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>JavaScript调试测试</title>
    </head>
    <body>
        <h1>JavaScript调试测试</h1>
        <div id="result"></div>

        <script>
            async function testAPI() {
                try {
                    console.log('开始测试API...');

                    // 测试商户分析API
                    const response = await fetch('/expense-analysis/api/merchant-analysis');
                    console.log('API响应状态:', response.status);

                    if (!response.ok) {
                        throw new Error(`HTTP error! status: ${response.status}`);
                    }

                    const data = await response.json();
                    console.log('API响应数据:', data);

                    if (data.success) {
                        const analysisData = data.data;
                        console.log('商户分析数据:', analysisData);

                        // 测试数据访问
                        const categories = analysisData.categories;
                        const summary = analysisData.summary;
                        console.log('分类数据:', categories);
                        console.log('汇总数据:', summary);

                        const categoryCount = Object.keys(categories).length;
                        const totalExpense = summary.total_expense || 0;
                        const totalMerchants = summary.total_merchants || 0;

                        document.getElementById('result').innerHTML = `
                            <h2>测试成功！</h2>
                            <p>总支出: ¥${totalExpense.toFixed(2)}</p>
                            <p>分类数量: ${categoryCount}个</p>
                            <p>商户数量: ${totalMerchants}个</p>
                        `;
                    } else {
                        throw new Error(data.error || 'API返回失败');
                    }

                } catch (error) {
                    console.error('测试失败:', error);
                    document.getElementById('result').innerHTML = `
                        <h2>测试失败</h2>
                        <p>错误: ${error.message}</p>
                    `;
                }
            }

            // 页面加载后自动测试
            document.addEventListener('DOMContentLoaded', testAPI);
        </script>
    </body>
    </html>
    '''


@expense_analysis_bp.route('/api/merchant-analysis')
@handle_errors
def api_merchant_analysis():
    """获取商户分类支出分析数据API"""
    try:
        from flask import request
        from datetime import date, datetime

        # 获取查询参数
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        month_str = request.args.get('month')  # 新增月份参数 (YYYY-MM格式)
        category_filter = request.args.get('category_filter')
        search_term = request.args.get('search_term')

        # 解析日期参数
        start_date = None
        end_date = None

        # 优先处理月份参数
        if month_str:
            try:
                from calendar import monthrange
                month_date = datetime.strptime(month_str, '%Y-%m').date()
                start_date = month_date.replace(day=1)
                last_day = monthrange(month_date.year, month_date.month)[1]
                end_date = month_date.replace(day=last_day)
            except ValueError:
                return jsonify({
                    'success': False,
                    'error': '月份格式错误，请使用 YYYY-MM 格式'
                }), 400
        else:
            # 处理日期范围参数
            if start_date_str:
                try:
                    start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
                except ValueError:
                    return jsonify({
                        'success': False,
                        'error': '开始日期格式错误，请使用 YYYY-MM-DD 格式'
                    }), 400

            if end_date_str:
                try:
                    end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
                except ValueError:
                    return jsonify({
                        'success': False,
                        'error': '结束日期格式错误，请使用 YYYY-MM-DD 格式'
                    }), 400

        # 验证分类筛选参数
        valid_categories = ['dining', 'transport', 'shopping', 'services', 'healthcare', 'finance', 'other']
        if category_filter and category_filter not in valid_categories:
            return jsonify({
                'success': False,
                'error': f'无效的分类筛选参数，支持的分类: {", ".join(valid_categories)}'
            }), 400

        # 获取报告服务
        report_service = current_app.report_service

        # 根据参数类型选择不同的分析方法
        if month_str:
            # 使用月份分析方法，包含完整历史数据
            analysis_data = report_service.get_month_expense_analysis(
                target_month=month_str,
                category_filter=category_filter,
                search_term=search_term
            )
        else:
            # 使用日期范围分析方法
            analysis_data = report_service.get_merchant_expense_analysis(
                start_date=start_date,
                end_date=end_date,
                category_filter=category_filter,
                search_term=search_term
            )

        return jsonify({
            'success': True,
            'data': analysis_data,
            'filters': {
                'month': month_str,
                'start_date': start_date_str,
                'end_date': end_date_str,
                'category_filter': category_filter,
                'search_term': search_term
            }
        })

    except Exception as e:
        logger.error(f"Error getting merchant analysis data: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500




@expense_analysis_bp.route('/api/available-months')
@handle_errors
def api_available_months():
    """获取可用月份列表API"""
    try:
        # 获取报告服务
        report_service = current_app.report_service

        # 获取有数据的月份列表
        months_data = report_service.merchant_service.get_available_months()

        return jsonify({
            'success': True,
            'data': months_data
        })

    except Exception as e:
        logger.error(f"Error getting available months: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@expense_analysis_bp.route('/api/merchant-details/<merchant_name>')
@handle_errors
def api_merchant_details(merchant_name):
    """获取商户详情API"""
    try:
        # 获取报告服务
        report_service = current_app.report_service

        # 使用商户分类服务获取商户交易详情
        merchant_data = report_service.merchant_service.get_merchant_transactions(merchant_name)

        return jsonify({
            'success': True,
            'data': merchant_data
        })

    except Exception as e:
        logger.error(f"Error getting merchant details for {merchant_name}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
