from flask import Blueprint

# 创建设置页面蓝图
settings_bp = Blueprint('settings_bp', __name__, template_folder='../templates')

# 导入路由模块，确保在蓝图实例化之后导入以避免循环依赖
from . import routes