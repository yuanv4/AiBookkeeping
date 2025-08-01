"""分析页面蓝图

提供数据分析和可视化功能，包括：
- 财务数据统计概览
- 图表可视化展示
- 快速操作入口
"""

from flask import Blueprint

analytics_bp = Blueprint(
    'analytics',
    __name__,
    template_folder='templates'
)

from . import routes
