from flask import Blueprint

# template_folder='templates' 意味着期望模板在 app/upload_bp/templates/ 目录下
# 如果模板仍在 app/templates/upload.html，则 main 蓝图的 template_folder 设置 ('../templates')
# 或者 app 本身的 template_folder ('templates', Flask默认在 app/templates 查找) 会处理它。
# 为清晰起见，如果此蓝图有特定模板，可以指定 template_folder='templates' 并将 upload.html 移入。
# 假设 upload.html 仍在 app/templates/ 目录下，由应用或 main 蓝图的设置找到。
upload_bp = Blueprint('upload_bp', __name__) 

from . import routes 