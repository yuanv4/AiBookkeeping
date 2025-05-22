from flask import Blueprint

main = Blueprint('main', __name__, template_folder='../templates') # 指定模板文件夹相对路径

# 导入路由模块，确保在蓝图实例化之后导入以避免循环依赖
from . import routes 