"""
模板过滤器模块 - 包含所有自定义Jinja2模板过滤器
"""
from flask import Flask
from typing import Union, Any, Optional

def register_template_filters(app: Flask) -> None:
    """注册所有自定义模板过滤器"""

    # 数学函数过滤器（保留常用的round过滤器）
    @app.template_filter('round')
    def round_filter(n: Union[int, float], precision: int = 0) -> Union[int, float]:
        """四舍五入，可指定小数位数"""
        return round(n, precision)
    
    app.logger.info("已注册自定义模板过滤器") 