from flask import Blueprint

# 创建支出分析蓝图
expense_analysis_bp = Blueprint('expense_analysis_bp', __name__)

from . import routes