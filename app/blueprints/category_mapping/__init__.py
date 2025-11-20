"""分类映射蓝图

提供分类映射管理功能
"""

from flask import Blueprint

category_mapping_bp = Blueprint('category_mapping', __name__)

# 导入路由
from . import routes