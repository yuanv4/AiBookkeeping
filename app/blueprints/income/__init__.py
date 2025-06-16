from flask import Blueprint

# 创建income蓝图实例
income_bp = Blueprint(
    'income',
    __name__,
    template_folder='templates',
    static_folder='static'
)

# 导入路由（避免循环导入）
from . import routes