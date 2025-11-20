"""分析页面路由"""

from flask import render_template
from app.utils import has_financial_data, handle_errors, DataUtils
from app.models import CoreTransaction, Entry, Account
from app.models.base import db
from app.configs.categories import CATEGORIES
from sqlalchemy import func, and_
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
    """获取月度商户类型支出数据API"""
    try:
        # 获取所有 ASSET 类型的账户（实际资金账户）
        asset_accounts = Account.query.filter_by(type='ASSET').all()
        asset_account_ids = [acc.id for acc in asset_accounts]
        
        if not asset_account_ids:
            return DataUtils.format_api_response(True, data={
                'months': [],
                'series': [],
                'categories': CATEGORIES
            })
        
        # 查询这些账户的支出分录（amount < 0）
        # 并关联交易获取日期信息
        query_result = db.session.query(
            func.strftime('%Y-%m', CoreTransaction.date).label('month'),
            func.sum(func.abs(Entry.amount)).label('amount')
        ).join(
            Entry, Entry.transaction_id == CoreTransaction.id
        ).filter(
            Entry.account_id.in_(asset_account_ids),
            Entry.amount < 0,  # 支出
            CoreTransaction.type == 'EXPENSE'
        ).group_by('month').order_by('month').all()

        # 简化版：暂时不按分类统计（因为需要重新设计分类逻辑）
        # 构造ECharts所需的数据格式
        months = [row.month for row in query_result]
        amounts = [float(row.amount) for row in query_result]

        # 构造系列数据（单一系列：总支出）
        series = [{
            'category': 'lifestyle',  # 默认分类
            'data': amounts
        }]

        return DataUtils.format_api_response(True, data={
            'months': months,
            'series': series,
            'categories': CATEGORIES
        })

    except Exception as e:
        logger.error(f"获取月度支出数据失败: {e}")
        return DataUtils.format_api_response(False, error='获取数据失败')
