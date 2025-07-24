"""财务分析模块蓝图

合并仪表盘和支出分析功能的统一分析模块
提供现金流健康监控与支出分类分析功能
"""

from flask import Blueprint

analysis_bp = Blueprint(
    'analysis',
    __name__,
    template_folder='templates'
)

from . import routes
