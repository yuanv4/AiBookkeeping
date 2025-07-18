# AiBookkeeping 项目开发规范

> **核心原则**: 简单、实用、易维护 - 适合个人项目的轻量级开发规范

## 🎯 项目定位与核心价值 (P1)

### 项目特色
- **AI增强财务管理**: 智能商户分类、支出分析、数据提取
- **轻量级架构**: SQLite数据库，单机部署，无复杂依赖
- **现代化前端**: Bootstrap + Tabulator + ECharts 技术栈
- **多银行支持**: 智能识别Excel对账单格式

### 维护原则
- **严禁过度工程化**: 保持代码简单直观
- **技术栈稳定**: 优先使用成熟方案
- **立即修复**: 不积累技术债务

## 🏗️ 技术栈规范 (P1)

### 后端技术栈
```python
Flask>=3.0.0, SQLAlchemy>=2.0.23, Flask-Migrate>=4.0.5
pandas>=2.1.0, openpyxl>=3.1.0  # 数据处理
SQLite  # 数据库
```

### 前端技术栈
```html
Bootstrap 5.3+, Lucide Icons
Tabulator 5.5+, ECharts 5.4+
Vanilla JavaScript, CSS3
```

### 禁用技术
❌ React/Vue/Angular, Tailwind, Webpack, TensorFlow等重型框架

## 📁 项目结构规范 (P1)

### 目录组织
```
app/
├── models/          # 数据模型
├── blueprints/      # 蓝图路由
├── services/        # 业务逻辑(AI功能)
├── utils/           # 工具函数
├── templates/       # Jinja2模板
└── static/css/js/   # 前端资源
```

### 命名约定
Python: `snake_case`, CSS: `kebab-case`, JS: `camelCase`

## 💾 数据库操作规范 (P1)

### SQLAlchemy规范
```python
# 使用会话管理，异常回滚
def create_transaction(data):
    try:
        transaction = Transaction(**data)
        db.session.add(transaction)
        db.session.commit()
        return transaction
    except Exception as e:
        db.session.rollback()
        raise
```

### 优化原则
- 使用索引、分页、缓存
- 避免N+1查询
- `flask db migrate/upgrade`

## 🎨 前端开发规范 (P2)

### 核心规范
```javascript
// ES6模块化，禁止全局变量
import { utils } from '../common/utils.js';
export default class PageClass { }

// 组件使用
new Tabulator("#table", { virtualDom: true });
echarts.init(document.getElementById('chart'));
```

## 🔧 代码质量规范 (P2)

### Python规范
```python
# 类型提示 + 文档字符串
def process_transaction(data: Dict[str, Any]) -> Transaction:
    """处理交易数据"""
    pass

# 统一错误处理
from app.utils.error_handler import ErrorHandler
@handle_errors(template='errors/500.html')
def risky_operation(): pass
```

### 日志配置
```python
# RotatingFileHandler, 10MB, 5个备份
logger.info("重要操作")
logger.error("系统错误")
```

## 🤖 AI增强功能规范 (P1)

### 智能商户分类
```python
# MerchantClassificationService - 关键词匹配算法
categories = {
    'dining': ['餐厅', '咖啡', '外卖'],
    'transport': ['地铁', '打车', '加油'],
    'shopping': ['京东', '淘宝', '超市']
}
@cached_query(ttl=3600)
def classify_merchant(name): return category
```

### 支出分析引擎
- 多维度分析：按类别统计、月度趋势、商户详情
- 数据可视化：ECharts交互图表、Tabulator虚拟滚动
- 智能处理：自动过滤收入、商户名称标准化

### 数据提取器
- 智能识别银行Excel格式
- 标准化数据结构和货币代码
- 重复数据检测和验证

---

**最后更新**: 2025-01-18 | **版本**: v2.1 | **特色**: AI增强财务管理