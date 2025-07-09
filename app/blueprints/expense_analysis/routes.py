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

                    // 测试固定支出API
                    const response = await fetch('/expense-analysis/api/fixed-expenses');
                    console.log('API响应状态:', response.status);

                    if (!response.ok) {
                        throw new Error(`HTTP error! status: ${response.status}`);
                    }

                    const data = await response.json();
                    console.log('API响应数据:', data);

                    if (data.success) {
                        const fixedExpenses = data.data;
                        console.log('固定支出数据:', fixedExpenses);

                        // 测试数据访问
                        const dailyData = fixedExpenses.daily_fixed_expenses;
                        console.log('日常固定支出数据:', dailyData);

                        const monthlyAvg = dailyData.monthly_average;
                        console.log('月均金额:', monthlyAvg);

                        document.getElementById('result').innerHTML = `
                            <h2>测试成功！</h2>
                            <p>日常固定支出月均: ${monthlyAvg}元</p>
                            <p>商户数量: ${dailyData.merchants.length}个</p>
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


@expense_analysis_bp.route('/api/fixed-expenses')
@handle_errors
def api_fixed_expenses():
    """获取固定支出分析数据API"""
    try:
        # 获取报告服务
        report_service = current_app.report_service
        
        # 获取固定支出分析数据
        analysis_data = report_service.get_fixed_expenses_analysis()
        
        return jsonify({
            'success': True,
            'data': analysis_data
        })
        
    except Exception as e:
        logger.error(f"Error getting fixed expenses data: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@expense_analysis_bp.route('/api/monthly-trend')
@handle_errors
def api_monthly_trend():
    """获取月度趋势数据API"""
    try:
        # 获取报告服务
        report_service = current_app.report_service
        
        # 获取固定支出分析数据
        analysis_data = report_service.get_fixed_expenses_analysis()
        
        # 提取月度趋势数据
        daily_monthly = analysis_data['daily_fixed_expenses']['monthly_data']
        large_monthly = analysis_data['large_fixed_expenses']['monthly_data']
        
        # 合并月度数据
        monthly_trend = {}
        
        # 添加日常固定支出数据
        for item in daily_monthly:
            month = item['month']
            if month not in monthly_trend:
                monthly_trend[month] = {
                    'month': month,
                    'daily_fixed': 0,
                    'large_fixed': 0,
                    'total_fixed': 0,
                    'daily_transactions': 0,
                    'large_transactions': 0
                }
            monthly_trend[month]['daily_fixed'] = item['amount']
            monthly_trend[month]['daily_transactions'] = item['transaction_count']
        
        # 添加大额固定支出数据
        for item in large_monthly:
            month = item['month']
            if month not in monthly_trend:
                monthly_trend[month] = {
                    'month': month,
                    'daily_fixed': 0,
                    'large_fixed': 0,
                    'total_fixed': 0,
                    'daily_transactions': 0,
                    'large_transactions': 0
                }
            monthly_trend[month]['large_fixed'] = item['amount']
            monthly_trend[month]['large_transactions'] = item['transaction_count']
        
        # 计算总计
        for month_data in monthly_trend.values():
            month_data['total_fixed'] = month_data['daily_fixed'] + month_data['large_fixed']
        
        # 按月份排序
        trend_list = sorted(monthly_trend.values(), key=lambda x: x['month'], reverse=True)
        
        return jsonify({
            'success': True,
            'data': {
                'monthly_trend': trend_list,
                'summary': {
                    'daily_average': analysis_data['daily_fixed_expenses']['monthly_average'],
                    'large_average': analysis_data['large_fixed_expenses']['monthly_average'],
                    'total_average': analysis_data['daily_fixed_expenses']['monthly_average'] + analysis_data['large_fixed_expenses']['monthly_average']
                }
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting monthly trend data: {e}")
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
        
        # 获取商户的所有交易记录
        from app.models import Transaction
        transactions = report_service.db.query(Transaction).filter(
            Transaction.amount < 0,
            Transaction.counterparty == merchant_name
        ).order_by(Transaction.date.desc()).limit(20).all()
        
        # 转换为字典格式
        transaction_list = []
        for t in transactions:
            transaction_list.append({
                'date': t.date.strftime('%Y-%m-%d'),
                'amount': float(abs(t.amount)),
                'description': t.description or '',
                'account': t.account.account_name if t.account else ''
            })
        
        # 计算统计信息
        total_amount = sum(abs(t.amount) for t in transactions)
        avg_amount = total_amount / len(transactions) if transactions else 0
        
        return jsonify({
            'success': True,
            'data': {
                'merchant_name': merchant_name,
                'transactions': transaction_list,
                'statistics': {
                    'total_amount': float(total_amount),
                    'average_amount': float(avg_amount),
                    'transaction_count': len(transactions)
                }
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting merchant details for {merchant_name}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
