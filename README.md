# AiBookkeeping - AI增强财务管理系统

简单、实用、易维护的个人财务管理工具，专注于核心功能。

## 🚀 核心功能

- **交易记录管理** - 导入银行流水，自动分类交易
- **财务报告** - 收支统计、趋势分析、现金流健康仪表盘
- **支出分析** - 商户分类分析，支出构成可视化
- **数据导入** - 支持招商银行、建设银行Excel文件导入

## 🏗️ 技术架构

### 后端技术栈
- **Flask 3.0+** - Web框架
- **SQLAlchemy 2.0+** - ORM数据库操作
- **SQLite** - 轻量级数据库
- **pandas** - 数据处理

### 前端技术栈
- **Bootstrap 5.3+** - UI框架
- **Vanilla JavaScript** - 原生JS，ES6模块化
- **Tabulator 5.5+** - 数据表格
- **ECharts 5.4+** - 图表可视化
- **Lucide Icons** - 图标库

### 项目结构
```
app/
├── models/              # 数据模型
├── blueprints/          # 路由蓝图
├── services/            # 业务逻辑服务层
├── utils/               # 工具函数
├── templates/           # Jinja2模板
└── static/
    ├── css/             # 样式文件
    └── js/
        ├── common/      # 通用JS模块
        └── pages/       # 页面特定JS
```

## 📦 安装部署

### 环境要求
- Python 3.8+
- pip

### 快速开始
```bash
# 1. 克隆项目
git clone <repository-url>
cd AiBookkeeping

# 2. 安装依赖
pip install -r requirements.txt

# 3. 初始化数据库
flask db upgrade

# 4. 启动应用
python run.py
```

应用将在 http://localhost:5000 启动

## 📊 使用指南

### 数据导入
1. 访问"设置"页面
2. 上传银行Excel流水文件
3. 系统自动识别银行类型并解析数据
4. 支出交易自动进行商户分类

### 查看报告
- **交易记录** - 查看所有交易，支持筛选和导出
- **现金流仪表盘** - 总资产、收支趋势、应急储备分析
- **支出分析** - 按商户分类的支出构成分析

## 🔧 开发规范

### 核心原则
- **简单实用** - 避免过度工程化
- **易维护** - 代码简单直观
- **轻量级** - 专注个人用户核心需求

### 代码规范
- Python: `snake_case`
- JavaScript: `camelCase`
- CSS: `kebab-case`

### 服务层架构
```python
# 服务层提供业务逻辑封装
from app.utils import get_transaction_service

transaction_service = get_transaction_service()
transactions = transaction_service.get_transactions_filtered(
    filters={'start_date': '2024-01-01'},
    include_relations=True
)
```

### 前端模块化
```javascript
// ES6模块化，功能拆分
import { formatCurrency } from '../common/formatters.js';
import { showNotification } from '../common/notifications.js';
import { apiService } from '../common/api-helpers.js';
```

## 🗂️ 主要模块

### 后端服务
- **BankService** - 银行信息管理
- **AccountService** - 账户管理
- **TransactionService** - 交易记录管理
- **ImportService** - 文件导入处理
- **ReportService** - 财务报告生成
- **CategoryService** - 商户分类服务

### 前端模块
- **formatters.js** - 数据格式化函数
- **validators.js** - 数据验证函数
- **notifications.js** - 通知系统
- **api-helpers.js** - API请求封装
- **dom-utils.js** - DOM操作工具
- **utils.js** - 核心工具函数

## 📝 更新日志

### v2.1 (2025-01-23)
- ✅ 重构JavaScript模块，拆分utils.js为专门功能模块
- ✅ 合并TransactionService重复方法，简化API
- ✅ 移除BaseService过度抽象，保留实用功能
- ✅ 统一服务层日志记录方式
- ✅ 修复JavaScript未使用变量警告
- ✅ 更新文档反映重构后结构

### 技术债务清理
- 消除代码重复
- 简化抽象层次
- 提高代码质量
- 统一编码规范

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

### 开发原则
1. 保持简单 - 避免过度复杂的设计
2. 实用优先 - 专注解决实际问题
3. 易于维护 - 代码清晰易懂
4. 轻量级 - 避免重型框架和依赖

---

**项目特色**: AI增强的个人财务管理，简单实用，专注核心功能 🎯
