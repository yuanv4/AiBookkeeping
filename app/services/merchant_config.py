"""商户分类配置

统一管理所有商户分类规则，支持多种匹配策略
"""

MERCHANT_CATEGORIES = {
    # 精确匹配规则 - 最高优先级
    'exact_match': {
    },
    
    # 关键词匹配规则 - 中等优先级
    'keyword_match': {
        '医院': 'healthcare',
        '药店': 'healthcare',
        '药房': 'healthcare',
        '诊所': 'healthcare',
        '体检': 'healthcare',
        '银行': 'finance',
        '保险': 'finance',
        '证券': 'finance',
        '基金': 'finance',
        '超市': 'shopping',
        '商场': 'shopping',
        '百货': 'shopping',
        '购物': 'shopping',
        '餐厅': 'dining',
        '咖啡': 'dining',
        '茶饮': 'dining',
        '火锅': 'dining',
        '烧烤': 'dining',
        '地铁': 'transport',
        '公交': 'transport',
        '出租': 'transport',
        '加油': 'transport',
        '停车': 'transport',
        '快递': 'services',
        '物流': 'services',
        '通信': 'services',
        '宽带': 'services',
        '理发': 'services',
        '美容': 'services',
    },
    
    # 模式匹配规则 - 最低优先级
    'pattern_match': [
        {'pattern': r'.*医院.*', 'category': 'healthcare'},
        {'pattern': r'.*药房.*', 'category': 'healthcare'},
        {'pattern': r'.*诊所.*', 'category': 'healthcare'},
        {'pattern': r'.*银行.*', 'category': 'finance'},
        {'pattern': r'.*保险.*', 'category': 'finance'},
        {'pattern': r'.*证券.*', 'category': 'finance'},
        {'pattern': r'.*超市.*', 'category': 'shopping'},
        {'pattern': r'.*商城.*', 'category': 'shopping'},
        {'pattern': r'.*商场.*', 'category': 'shopping'},
        {'pattern': r'.*餐厅.*', 'category': 'dining'},
        {'pattern': r'.*咖啡.*', 'category': 'dining'},
        {'pattern': r'.*茶.*', 'category': 'dining'},
        {'pattern': r'.*地铁.*', 'category': 'transport'},
        {'pattern': r'.*公交.*', 'category': 'transport'},
        {'pattern': r'.*出租.*', 'category': 'transport'},
        {'pattern': r'.*快递.*', 'category': 'services'},
        {'pattern': r'.*物流.*', 'category': 'services'},
        {'pattern': r'.*通信.*', 'category': 'services'},
    ]
}