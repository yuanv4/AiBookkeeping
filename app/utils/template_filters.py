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
    
    # 格式化过滤器
    @app.template_filter('currency')
    def currency_filter(n: Optional[Union[int, float]]) -> str:
        """货币格式化，保留2位小数，加¥符号"""
        if n is None:
            return "¥0.00"
        return f"¥{float(n):.2f}"


    

    
    # 分页数据序列化过滤器
    @app.template_filter('serialize_pagination')
    def serialize_pagination_filter(pagination):
        """将分页对象序列化为字典，用于前端JSON数据传递"""
        if not pagination:
            return None
        return {
            "current_page": pagination.page,
            "total_pages": pagination.pages,
            "has_prev": pagination.has_prev,
            "has_next": pagination.has_next,
            "prev_num": pagination.prev_num,
            "next_num": pagination.next_num,
            "per_page": pagination.per_page,
            "total": pagination.total
        }
    
    app.logger.info("已注册自定义模板过滤器") 