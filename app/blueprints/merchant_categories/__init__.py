"""商户分类管理蓝图

提供商户分类管理功能，包括：
- 展示所有未分类商户
- 单个商户分类更新
- 用户规则管理
"""

from flask import Blueprint

merchant_categories_bp = Blueprint(
    'merchant_categories',
    __name__,
    template_folder='templates'
)

from . import routes
