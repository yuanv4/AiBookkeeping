"""分析页面路由"""

from flask import render_template
from app.utils import get_transaction_service, has_financial_data
from app.models import Transaction
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
