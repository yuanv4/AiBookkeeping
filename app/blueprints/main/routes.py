"""主路由模块

提供基础路由和首页重定向功能
"""

import logging
from flask import redirect, url_for

from . import main_bp

logger = logging.getLogger(__name__)


@main_bp.route('/')
def index():
    """应用首页 - 重定向到分析页面"""
    return redirect(url_for('analysis.index'))