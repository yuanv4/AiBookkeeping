from flask import Blueprint

# 创建main蓝图
main_bp = Blueprint('main', __name__)

# 导入路由
from . import routes