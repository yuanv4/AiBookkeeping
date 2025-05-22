"""
模板过滤器模块 - 包含所有自定义Jinja2模板过滤器
"""
from flask import Flask
import math

def register_template_filters(app: Flask):
    """注册所有自定义模板过滤器"""
    
    # 数学函数过滤器
    @app.template_filter('abs')
    def abs_filter(n):
        """绝对值"""
        return abs(n)
    
    @app.template_filter('round')
    def round_filter(n, precision=0):
        """四舍五入，可指定小数位数"""
        return round(n, precision)
    
    @app.template_filter('ceil')
    def ceil_filter(n):
        """向上取整"""
        return math.ceil(n)
    
    @app.template_filter('floor')
    def floor_filter(n):
        """向下取整"""
        return math.floor(n)
    
    @app.template_filter('min')
    def min_filter(*args):
        """取最小值"""
        return min(args)
    
    @app.template_filter('max')
    def max_filter(*args):
        """取最大值"""
        return max(args)
    
    # 格式化过滤器
    @app.template_filter('currency')
    def currency_filter(n):
        """货币格式化，保留2位小数，加¥符号"""
        if n is None:
            return "¥0.00"
        return f"¥{float(n):.2f}"
    
    @app.template_filter('percent')
    def percent_filter(n, precision=1):
        """百分比格式化，默认保留1位小数，加%符号"""
        if n is None:
            return f"0.{'0' * precision}%"
        return f"{float(n):.{precision}f}%"
    
    @app.template_filter('decimal')
    def decimal_filter(n, precision=2):
        """小数格式化，默认保留2位小数"""
        if n is None:
            return f"0.{'0' * precision}"
        return f"{float(n):.{precision}f}"
    
    # 数据处理过滤器
    @app.template_filter('attr_list')
    def attr_list_filter(obj_list, attr_name):
        """从对象列表中提取指定属性，形成新列表
        等效于 list|map(attribute=attr_name)|list
        """
        if not obj_list:
            return []
        return [getattr(obj, attr_name, None) for obj in obj_list]
    
    @app.template_filter('dict_list')
    def dict_list_filter(dict_list, key):
        """从字典列表中提取指定键的值，形成新列表"""
        if not dict_list:
            return []
        return [item.get(key) for item in dict_list]
    
    # 为了保持兼容性，可以添加一些别名
    app.add_template_filter(currency_filter, 'rmb')
    app.add_template_filter(percent_filter, 'pct')
    
    app.logger.info("已注册自定义模板过滤器") 