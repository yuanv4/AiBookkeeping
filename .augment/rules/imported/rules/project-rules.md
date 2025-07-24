---
type: "always_apply"
---

# AiBookkeeping 项目开发规范

## 核心原则与定位 (P0)
- **核心原则**：简洁、实用、易维护（个人项目规范）
- **维护铁律**：
  - ❌ 禁止过度工程化/抽象（需3+相似用例才抽象）
  - ✅ 代码简单直观优先
  - 🔧 技术债务立即修复
  - 📄 代码变更同步文档

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

### SQLAlchemy最佳实践
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
# ❌ 禁止：直接操作数据库连接
# ❌ 禁止：在模板中进行数据库查询
# ❌ 禁止：N+1查询问题
```

### 查询优化原则
- **使用eager loading**: 避免N+1查询
- **添加数据库索引**: 对常用查询字段建索引
- **限制查询结果**: 使用分页，避免大量数据加载
- **缓存查询结果**: 对重复查询使用缓存

## 🎨 前端开发规范 (P2)

### CSS架构：
- 变量定义 → 基础样式 → 组件 → 响应式

### JS模块化：
```javascript
// ✅ ES6模块化
export default class TransactionPage {
  constructor() { this.init() }
}
```
- 禁止：全局变量/jQuery/内联JS

### 组件约束：
- 必须使用Tabulator表格+ECharts图表
- ❌ 禁止自定义表格/第三方图表

## 🔧 代码质量规范 (P2)

### Python标准：
- 强制类型提示+文档字符串
```python
def process(data: Dict[str, Any]) -> Transaction:
    """函数说明"""
```
### 错误处理：
- 统一装饰器处理 @handle_errors
- API/HTML请求自动区分响应格式

### 日志规范：
- 分级输出（DEBUG→CRITICAL）
- 双通道：控制台+10MB轮转文件

---

**最后更新**: 2025-01-18 | **版本**: v2.1 | **特色**: AI增强财务管理