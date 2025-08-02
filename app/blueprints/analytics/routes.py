"""分析页面路由"""

from flask import render_template, jsonify
from app.utils import get_transaction_service, has_financial_data, handle_errors, DataUtils
from app.models import Transaction
from app.models.base import db
from sqlalchemy import func
from . import analytics_bp
import logging

logger = logging.getLogger(__name__)


@analytics_bp.route('/')
def analytics_index():
    """分析页面主页"""
    # 检查是否有财务数据
    has_data = has_financial_data()
    return render_template('analytics.html',
                             has_data=has_data)


@analytics_bp.route('/api/monthly-expenses')
@handle_errors
def get_monthly_expenses():
    """获取月度分类支出数据API"""
    try:
        # 检查是否有已分类的支出数据
        categorized_expense_count = Transaction.query.filter(
            Transaction.amount < 0,
            Transaction.category != 'uncategorized'
        ).count()

        if categorized_expense_count == 0:
            # 返回测试数据用于演示
            from app.configs.categories import CATEGORIES
            test_months = ['2024-01', '2024-02', '2024-03', '2024-04', '2024-05', '2024-06']
            test_series = []

            # 为每个分类生成测试数据
            test_data = {
                'dining': [1500, 1800, 1600, 1700, 1900, 1650],
                'transport': [800, 900, 750, 850, 950, 800],
                'shopping': [1200, 1400, 1100, 1300, 1500, 1250],
                'services': [600, 700, 550, 650, 750, 600],
                'healthcare': [400, 300, 500, 350, 450, 400]
            }

            for category, amounts in test_data.items():
                category_info = CATEGORIES.get(category, {})
                test_series.append({
                    'name': category_info.get('name', category),
                    'data': amounts
                })

            return DataUtils.format_api_response(True, data={
                'months': test_months,
                'series': test_series
            })

        # 查询月度分类支出数据 (使用SQLite兼容的strftime函数)
        query_result = db.session.query(
            func.strftime('%Y-%m', Transaction.date).label('month'),
            Transaction.category,
            func.sum(func.abs(Transaction.amount)).label('amount')
        ).filter(
            Transaction.amount < 0,
            Transaction.category != 'uncategorized'
        ).group_by('month', Transaction.category).order_by('month').all()

        # 构造ECharts所需的数据格式
        months_set = set()
        categories_data = {}

        # 收集所有月份和分类数据
        for row in query_result:
            month = row.month
            category = row.category
            amount = float(row.amount)

            months_set.add(month)
            if category not in categories_data:
                categories_data[category] = {}
            categories_data[category][month] = amount

        # 排序月份
        months = sorted(list(months_set))

        # 构造系列数据
        from app.configs.categories import CATEGORIES
        series = []
        for category, amounts_by_month in categories_data.items():
            category_info = CATEGORIES.get(category, {})
            series_data = []

            # 为每个月份填充数据，缺失的月份填0
            for month in months:
                series_data.append(amounts_by_month.get(month, 0))

            series.append({
                'name': category_info.get('name', category),
                'data': series_data
            })

        return DataUtils.format_api_response(True, data={
            'months': months,
            'series': series
        })

    except Exception as e:
        logger.error(f"获取月度支出数据失败: {e}")
        return DataUtils.format_api_response(False, error='获取数据失败')
