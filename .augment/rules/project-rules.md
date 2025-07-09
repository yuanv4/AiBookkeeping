---
type: "always_apply"
description: "globs:"
---
# AiBookkeeping 项目 Cursor 规则
# ==========================================
# 
# 项目简介：基于Flask的AI智能银行记账系统
# 主要功能：银行对账单Excel文件解析、交易数据标准化、财务分析和报表生成
# 技术栈：Python/Flask + SQLite + Vanilla JavaScript + Bootstrap + 数据分析库
# 
# 本规则文件为Cursor AI提供项目特定的编程指导，确保代码质量和架构一致性
# 规则优先级：P1(Critical) > P2(Important) > P3(Nice-to-have)

## 项目架构特征
- Flask应用工厂模式 + 蓝图架构
- 服务层依赖注入模式
- 分层清晰：Models -> Services -> Blueprints -> Templates
- 银行数据提取的插件化扩展设计
- 双语代码体系：英文代码 + 中文业务术语

## 业务领域特点
- 金融数据处理：严格的数值精度要求
- 银行格式解析：多银行Excel文件标准化
- 交易管理：CRUD操作、复杂查询、重复检测
- 中国银行业务：本土化需求和中文术语

---

# 核心规则 (Critical Priority - P1)

## 0. 项目定义 (P1)
- 此项目是个人项目，严格禁止过度工程化。
- 代码必须保证简洁性，可维护性，避免冗余和重复。
- 禁止使用企业级的复杂架构。
- 必须符合Flask项目最佳实践。

## 1. Flask应用工厂模式 (P1)
- 必须使用create_app()工厂函数创建Flask应用实例
- 所有扩展初始化在工厂函数内完成：db.init_app(app), migrate.init_app(app, db)
- 配置类通过config.init_app(app)方式注入
- 服务实例在app_context()内创建并附加到app对象：app.xxx_service = XxxService()

## 2. 服务层依赖注入模式 (P1)
- 所有业务逻辑封装在Service类中，命名规范：XxxService
- 服务类构造函数接收依赖参数，支持Mock和测试：def __init__(self, db_session=None)
- 服务实例通过current_app.xxx_service访问，如：current_app.transaction_service
- 服务类无状态设计，不存储实例变量，依赖Flask应用上下文

## 3. 分层架构约束 (P1)
- 严格遵循分层：Models(数据层) -> Services(业务层) -> Blueprints(控制层) -> Templates(视图层)
- Models层：只负责数据定义、验证、ORM映射，不包含业务逻辑
- Services层：封装所有业务逻辑，提供统一的业务接口
- Blueprints层：处理HTTP请求/响应，调用Services，不直接操作Models
- Templates层：纯粹的视图渲染，使用过滤器处理数据格式化

## 4. 蓝图模块化组织 (P1)
- 每个功能模块使用独立的Blueprint：main_bp, transactions_bp, settings_bp
- 蓝图文件位置：app/blueprints/模块名/routes.py
- 蓝图注册使用url_prefix：app.register_blueprint(transactions_bp, url_prefix='/transactions')
- 蓝图间不直接相互调用，通过Services层交互

---

# 代码质量规则 (Critical Priority - P1)

## 5. 双语代码标准 (P1)
- 变量名、函数名、类名使用英文：transaction_service, get_transactions, TransactionService
- 中文用于：docstring文档、注释说明、日志消息、用户界面文本
- 业务术语保持中文原意：如"交易对方"(counterparty)、"余额"(balance_after)、"账户"(account)
- 示例格式：
```python
def get_transactions(self, filters: Dict[str, Any]) -> List[Transaction]:
    """获取交易记录列表
    
    Args:
        filters: 过滤条件字典
        
    Returns:
        List[Transaction]: 交易记录列表
    """
```

## 6. Decimal数值精度强制 (P1)
- 所有金额字段必须使用Decimal类型，禁止使用float
- SQLAlchemy模型中金额字段定义：db.Column(db.Numeric(15, 2))
- 数值转换使用统一方法：Transaction._normalize_decimal(value)
- 金额计算保持精度：from decimal import Decimal
- 模板显示使用过滤器：{{ amount|currency }} 或 {{ amount|decimal }}

## 7. 错误处理模式 (P1)
- 所有路由函数必须使用@handle_errors装饰器统一异常处理
- 装饰器参数格式：@handle_errors(template='page.html', default_data={}, log_prefix="操作描述")
- API接口返回标准JSON格式：{'success': bool, 'data': {}, 'error': str}
- 服务层异常使用具体异常类型，不使用通用Exception
- 关键操作记录详细日志：self.logger.error(f"操作失败: {e}", exc_info=True)

## 8. SQLAlchemy模型验证规范 (P1)
- 必须使用@validates装饰器验证关键字段：@validates('amount', 'date')
- 继承BaseModel提供通用字段：id, created_at, updated_at
- 外键约束显式定义：db.ForeignKey('accounts.id'), nullable=False
- 索引优化复合查询：db.Index('idx_account_date', 'account_id', 'date')
- 数据验证失败抛出ValueError，包含具体错误信息

---

# 开发效率规则 (Important Priority - P2)

## 9. 环境变量配置优先 (P2)
- 所有配置项优先从环境变量获取：os.environ.get('KEY', default_value)
- 配置类方法：_get_bool(), _get_int(), _get_list() 统一处理不同类型
- 开发/测试/生产环境区分：通过FLASK_ENV环境变量控制
- 敏感配置验证：生产环境必须设置有效的SECRET_KEY
- 配置初始化：通过config.init_app(app)方式注入Flask应用

## 10. 日志记录标准 (P2)
- 每个服务类独立logger：self.logger = logging.getLogger(__name__)
- 日志级别使用：INFO(正常操作), ERROR(异常错误), WARNING(警告)
- 日志格式包含：时间戳、级别、模块名、消息内容
- 关键操作日志：开始执行、成功完成、异常失败三个状态
- 日志轮转配置：RotatingFileHandler，按大小轮转，保留历史文件

---

# 前端交互规则 (Nice-to-have Priority - P3)

## 11. ES6模块化JavaScript架构 (P3)
- 页面脚本使用ES6 module语法：import/export
- 页面类继承BasePage：class DashboardPage extends BasePage
- 通用工具函数位置：app/static/js/common/utils.js
- 页面特定脚本位置：app/static/js/pages/页面名.js
- 模块导入示例：import BasePage from '../common/BasePage.js'

## 12. BasePage继承模式 (P3)
- 页面类必须继承BasePage基类，重写生命周期方法
- 必须实现bindElements()方法：绑定页面DOM元素到this.elements
- 可选实现setupEventListeners()：设置事件监听器
- 可选实现renderPage()：动态渲染页面内容
- 页面初始化：const page = new PageClass(); page.init()

## 13. Bootstrap 5 + Lucide Icons使用规范 (P3)
- UI组件优先使用Bootstrap 5类：btn, card, table, form-control等
- 图标使用Lucide Icons：通过icon宏调用 {{ icon("icon-name", "size", "class") }}
- 响应式设计：col-sm-*, col-md-*, col-lg-*网格系统
- 组件状态：btn-primary, alert-success, text-danger等语义化类
- 自定义样式位置：app/static/css/custom.css，不覆盖Bootstrap核心
- 禁止在模板文件中使用硬编码的CSS值。

## 14. 模板宏组件化 (P3)
- 通用组件定义在macros.html：图标、导航链接、表单字段等
- 宏导入语法：{% from "macros.html" import icon, nav_link %}
- 图标宏调用：{{ icon("landmark", "md", "text-primary") }}
- 导航宏调用：{{ nav_link('route_name', '显示文本', 'icon-name') }}
- 复杂组件可创建独立宏文件，按功能模块组织
