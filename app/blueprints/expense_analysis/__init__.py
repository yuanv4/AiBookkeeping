"""支出分类分析蓝图

提供基于商户类型的智能支出分类分析功能，包括：
- 商户类型自动识别和分类
- 支出分类汇总和统计
- 月度趋势和历史数据展示
- 商户详情和交易记录查看
"""

from flask import Blueprint

expense_analysis_bp = Blueprint(
    'expense_analysis',
    __name__,
    template_folder='templates',
    static_folder='static'
)

from . import routes
