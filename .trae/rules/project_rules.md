# AiBookkeeping 项目开发规范

## 1. 项目概述

本项目是一个基于Flask的智能记账系统，用于自动识别和分析银行交易明细数据。请遵循Flask最佳实践，确保代码的可读性、可维护性和可扩展性。

## 2. 技术栈和框架版本

### 2.1 核心框架
- **Flask**: >=2.2.3
- **Flask-SQLAlchemy**: >=3.0.5
- **Flask-Migrate**: >=4.0.5
- **Werkzeug**: >=2.2.3

### 2.2 数据库
- **SQLAlchemy**: >=2.0.0
- **Alembic**: >=1.12.0
- **数据库**: SQLite（开发/生产环境）

### 2.3 数据处理
- **pandas**: >=1.5.0
- **numpy**: >=1.23.0
- **openpyxl**: >=3.0.10
- **xlrd**: >=2.0.1
- **matplotlib**: >=3.6.0
- **seaborn**: >=0.11.0

### 2.4 文本处理
- **jieba**: >=0.42

### 2.5 工具库
- **jsonschema**: >=4.17.0
- **validators**: >=0.22.0
- **python-dateutil**: >=2.8.2
- **python-dotenv**: >=0.21.0

### 2.6 开发和测试
- **pytest**: >=7.4.0
- **pytest-flask**: >=1.2.0
- **flake8**: >=6.0.0
- **black**: >=23.0.0

## 3. 项目结构规范

### 3.1 目录结构
```
AiBookkeeping/
├── .env.example          # 环境变量示例文件
├── .gitignore           # Git忽略文件
├── README.md            # 项目说明文档
├── requirements.txt     # Python依赖包列表
├── run.py              # 应用启动入口
├── app/                # 主应用目录
│   ├── __init__.py     # 应用工厂函数
│   ├── config.py       # 配置管理
│   ├── template_filters.py  # 模板过滤器
│   ├── analyzers/      # 数据分析器
│   ├── extractors/     # 数据提取器
│   ├── models/         # 数据模型层
│   ├── services/       # 业务逻辑层
│   ├── blueprints/     # 路由蓝图
│   ├── static/         # 静态资源
│   │   ├── charts/     # 图表文件
│   │   ├── css/        # 样式文件
│   │   └── js/         # JavaScript文件
│   ├── templates/      # HTML模板
│   └── utils/          # 工具函数
├── migrations/         # 数据库迁移文件
├── tests/              # 测试文件目录
└── uploads/            # 文件上传目录
```

### 3.2 蓝图组织
- `main/` - 主页面和仪表盘
- `api/` - API接口
- `transactions/` - 交易记录管理
- `income_analysis/` - 收入分析
- `settings/` - 系统设置

## 4. 编码规范

### 4.1 Python代码规范
- 遵循PEP 8编码规范
- 使用black进行代码格式化
- 使用flake8进行代码检查
- 类名使用PascalCase（如：`TransactionService`）
- 函数和变量名使用snake_case（如：`get_transaction_data`）
- 常量使用UPPER_CASE（如：`DEFAULT_PAGE_SIZE`）

### 4.2 注释和文档
- 所有公共函数必须包含docstring
- 复杂业务逻辑必须添加中文注释
- 模块级别需要包含模块说明

### 4.3 导入规范
```python
# 标准库导入
import os
import sys
from datetime import datetime

# 第三方库导入
from flask import Flask, request
import pandas as pd

# 本地应用导入
from .models import db
from .services import TransactionService
```

## 5. 数据库规范

### 5.1 模型设计
- 所有模型必须继承`BaseModel`
- 使用SQLAlchemy 2.0+语法
- 模型文件按功能模块分离（如：`transaction.py`, `account.py`）

### 5.2 迁移管理
- 使用Flask-Migrate管理数据库迁移
- 迁移文件必须包含描述性注释
- 生产环境部署前必须测试迁移脚本

### 5.3 标准DataFrame格式
所有银行数据处理必须转换为标准格式：
- `transaction_date`: 交易日期 (YYYY-MM-DD)
- `amount`: 交易金额 (float)
- `balance`: 账户余额 (float)
- `transaction_type`: 交易类型 (string)
- `counterparty`: 交易对手方 (string)
- `currency`: 币种 (string)
- `account_number`: 账号 (string)
- `account_name`: 户名 (string)

## 6. 配置管理

### 6.1 环境配置
- 使用`.env`文件管理环境变量
- 支持三种环境：`development`, `testing`, `production`
- 生产环境必须设置强密钥

### 6.2 必需环境变量
```bash
FLASK_CONFIG=development|testing|production
SECRET_KEY=your-secret-key-here
LOG_LEVEL=INFO
DEBUG=true|false
```

## 7. 服务层架构

### 7.1 服务类设计
- 每个服务类负责单一业务领域
- 服务类方法必须包含错误处理
- 使用依赖注入模式

### 7.2 核心服务
- `DatabaseService`: 数据库操作
- `TransactionService`: 交易数据管理
- `AnalysisService`: 数据分析
- `ExtractorService`: 数据提取
- `FileProcessorService`: 文件处理

## 8. API设计规范

### 8.1 RESTful API
- 遵循RESTful设计原则
- 使用标准HTTP状态码
- 统一的错误响应格式

### 8.2 响应格式
```json
{
  "success": true|false,
  "data": {},
  "message": "操作结果描述",
  "error_code": "错误代码（可选）"
}
```

## 9. 前端规范

### 9.1 模板组织
- 使用Jinja2模板引擎
- 基础模板：`base.html`
- 错误页面统一放在`errors/`目录

### 9.2 静态资源
- CSS文件放在`static/css/`
- JavaScript文件放在`static/js/`
- 图表文件放在`static/charts/`

## 10. 禁用的APIs和做法

### 10.1 禁用的Flask功能
- 禁止使用`app.run(debug=True)`在生产环境
- 禁止在模板中执行复杂业务逻辑
- 禁止在视图函数中直接操作数据库

### 10.2 禁用的Python特性
- 避免使用`eval()`和`exec()`
- 避免使用全局变量存储状态
- 避免在循环中进行数据库查询

### 10.3 数据库操作限制
- 禁止在模型中包含业务逻辑
- 禁止使用原生SQL（除非必要）
- 禁止在事务外进行数据修改