from flask import Blueprint

# 创建收入分析蓝图
income_analysis_bp = Blueprint('income_analysis_bp', __name__)

from . import routes 