"""商户分类常量定义"""

# 分类元数据定义
CATEGORIES = {
    'dining': {
        'name': '餐饮支出',
        'icon': 'coffee',
        'color': 'primary',
        'description': '餐厅、咖啡、外卖等饮食消费'
    },
    'transport': {
        'name': '交通支出',
        'icon': 'car',
        'color': 'success',
        'description': '地铁、打车、加油等出行费用'
    },
    'shopping': {
        'name': '购物支出',
        'icon': 'shopping-bag',
        'color': 'info',
        'description': '网购、超市、商场等购物消费'
    },
    'services': {
        'name': '生活服务',
        'icon': 'settings',
        'color': 'warning',
        'description': '通信、快递、美容等服务费用'
    },
    'healthcare': {
        'name': '医疗健康',
        'icon': 'heart',
        'color': 'danger',
        'description': '医院、药店、体检等医疗支出'
    },
    'finance': {
        'name': '金融保险',
        'icon': 'credit-card',
        'color': 'secondary',
        'description': '保险、转账等金融相关支出'
    },
    'uncategorized': {
        'name': '未分类',
        'icon': 'help-circle',
        'color': 'warning',
        'description': '尚未分类的交易，需要手动处理'
    }
}


