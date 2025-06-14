from flask import Blueprint

# 统一的财务分析蓝图
analysis_bp = Blueprint('analysis_bp', __name__)

from . import routes