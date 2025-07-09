"""支出分析蓝图

提供智能的固定支出分析功能，包括：
- 日常固定支出识别和分析
- 大额固定支出分类
- 月度趋势和历史数据展示
- 支出分类和商户详情
"""

from flask import Blueprint

expense_analysis_bp = Blueprint(
    'expense_analysis',
    __name__,
    template_folder='templates',
    static_folder='static'
)

from . import routes
