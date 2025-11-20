"""基础分类配置

预定义的目标分类，用户可以将数据源分类映射到这些分类。
"""

# 基础预设分类（用户映射的目标分类）
BASIC_CATEGORIES = {
    'food': {
        'name': '餐饮',
        'icon': 'utensils',
        'description': '餐厅、外卖、超市采购等'
    },
    'shopping': {
        'name': '购物',
        'icon': 'shopping-bag',
        'description': '商品购买、网购、服装等'
    },
    'transport': {
        'name': '交通',
        'icon': 'car',
        'description': '打车、公共交通、加油等'
    },
    'entertainment': {
        'name': '娱乐',
        'icon': 'gamepad-2',
        'description': '电影、游戏、休闲等'
    },
    'salary': {
        'name': '工资',
        'icon': 'banknote',
        'description': '工资、奖金、补贴等收入'
    },
    'finance': {
        'name': '理财',
        'icon': 'piggy-bank',
        'description': '投资、理财、保险等'
    },
    'utilities': {
        'name': '生活缴费',
        'icon': 'home',
        'description': '房租、水电、物业等'
    },
    'health': {
        'name': '医疗',
        'icon': 'heart',
        'description': '医院、药店、体检等'
    },
    'education': {
        'name': '教育',
        'icon': 'graduation-cap',
        'description': '培训、课程、书籍等'
    },
    'other': {
        'name': '其他',
        'icon': 'more-horizontal',
        'description': '其他未分类支出'
    }
}

def get_basic_categories():
    """
    获取基础分类列表

    Returns:
        dict: 基础分类字典
    """
    return BASIC_CATEGORIES

def get_category_options():
    """
    获取分类选项列表（用于下拉选择）

    Returns:
        list: 分类选项列表，每个元素包含 code、name、icon
    """
    return [
        {
            'code': code,
            'name': info['name'],
            'icon': info['icon'],
            'description': info['description']
        }
        for code, info in BASIC_CATEGORIES.items()
    ]