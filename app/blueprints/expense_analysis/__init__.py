"""支出分析蓝图模块

提供支出分析相关的页面和API功能
"""

from flask import Blueprint

expense_analysis_bp = Blueprint('expense_analysis_bp', __name__, 
                               url_prefix='/expense-analysis')

from . import routes 