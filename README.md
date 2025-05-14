# AI Bookkeeping

## 项目结构
```
AiBookkeeping/
├── app.py                 # Flask应用主文件
├── data/                  # 数据目录
│   ├── transactions.db    # SQLite数据库文件
│   └── analysis_data.json # 分析结果数据
├── scripts/               # 脚本目录
│   ├── bank_transaction_extractor.py  # 银行交易提取器基类
│   ├── ccb_transaction_extractor.py   # 建设银行交易提取器
│   ├── cmb_transaction_extractor.py   # 招商银行交易提取器
│   ├── transaction_analyzer.py        # 交易分析器
│   ├── visualization_helper.py        # 可视化助手
│   └── db_manager.py                  # 数据库管理器
├── templates/             # HTML模板目录
│   ├── base.html         # 基础模板
│   ├── dashboard.html    # 仪表盘页面
│   ├── transactions.html # 交易记录页面
│   └── upload.html       # 上传页面
├── uploads/              # 上传文件目录
├── tests/                # 测试目录
│   ├── unit/            # 单元测试
│   └── integration/     # 集成测试
├── requirements.txt      # 依赖包列表
└── README.md            # 项目说明文档
```

## 功能特点
- 自动识别银行交易明细文件格式
- 支持多银行交易数据导入
- 自动分析交易数据
- 生成可视化报表
- 支持数据导出功能

## 数据存储
- 所有交易数据存储在SQLite数据库中
- 分析结果保存在JSON文件中
- 支持导出数据为CSV格式

## 使用说明
1. 将银行交易明细文件（Excel格式）放入uploads目录
2. 启动应用，系统会自动处理文件并导入数据库
3. 在仪表板查看分析结果
4. 可以导出数据为CSV格式

## 开发说明
- 使用Flask作为Web框架
- 使用SQLite作为数据库
- 使用pandas进行数据分析
- 使用matplotlib和seaborn进行数据可视化

## 交互式图表功能

系统中的所有图表都是交互式的，支持以下操作：

- **悬停查看详情**：将鼠标悬停在图表上，查看详细数据
- **图例交互**：点击图例可以隐藏/显示对应的数据系列
- **缩放功能**：使用滚轮可以放大/缩小图表，聚焦于感兴趣的数据区域
- **平移功能**：在图表上拖动可以平移查看更多数据
- **点击功能**：点击图表元素（如条形图、扇形图的扇区）可以跳转到相关的详细分析页面
- **数据标签**：部分图表显示数据标签，提供直观的数值参考

这些交互式功能让数据分析变得更加直观和灵活，用户可以根据自己的需求自由探索数据。

## 安装

1. 确保已安装Python 3.6或更高版本
2. 安装所需的依赖：

```bash
pip install -r requirements.txt
```

## 使用方法

### 方法一：直接运行
1. 双击`start_app.bat`文件
2. 在浏览器中访问 http://localhost:5000

### 方法二：命令行启动
1. 打开命令提示符或终端
2. 进入项目目录
3. 运行以下命令：

```bash
python app.py
```

4. 在浏览器中访问 http://localhost:5000

## 使用流程

1. 首次使用时，系统会自动跳转到上传页面
2. 选择要处理的招商银行Excel文件（支持多选）
3. 点击"上传并处理"按钮
4. 处理完成后，系统会自动分析数据并跳转到仪表盘
5. 通过顶部导航菜单，可以访问不同的分析维度

## 数据安全

- 所有数据都在本地处理和存储，不会上传到任何服务器
- 交易数据中的账号信息已做脱敏处理

## 系统要求

- 操作系统: Windows 7/10/11, macOS, Linux
- 浏览器: Chrome, Firefox, Edge (最新版本)
- 内存: 至少4GB RAM
- 硬盘: 至少100MB可用空间

## 注意事项

- 支持的文件类型：.xlsx, .xls
- 上传的文件将保存在uploads目录中
- 所有数据存储在SQLite数据库中
- 分析结果保存在JSON文件中
- 所有文件采用UTF-8编码

## 交易类别说明

系统会根据交易描述自动对交易进行分类，主要分类包括：
- 餐饮
- 交通
- 购物
- 娱乐
- 住房
- 医疗
- 教育
- 通讯
- 投资
- 保险
- 工资
- 转账
- 退款
- 其他 

## 测试

项目测试文件位于`tests`目录下，按照功能分为单元测试和集成测试：

### 单元测试

* `tests/unit/test_bank_detection.py` - 测试银行类型自动检测功能

### 集成测试

* `tests/integration/test_load_csv.py` - 测试CSV文件加载
* `tests/integration/test_generate_analysis.py` - 测试数据分析功能

### 运行测试

可以通过运行根目录下的`run_tests.bat`批处理文件来执行所有测试：

```
run_tests.bat
```

或者单独运行某个测试：

```
python -m tests.unit.test_bank_detection
python -m tests.integration.test_load_csv
python -m tests.integration.test_generate_analysis
```

## 最近代码优化

为了提高代码质量和可维护性，我们对提取器结构进行了以下优化：

1. 在基类`BankTransactionExtractor`中添加了`create_standard_dataframe`方法，用于创建标准格式的DataFrame
2. 统一了`extract_account_info`方法的接口，使其返回格式一致
3. 从子类中移除了重复的代码逻辑，如标准日期字段、默认值设置等
4. 改进了数据提取失败的处理机制，确保在关键数据字段缺失时明确返回提取失败，而不是使用默认值
5. 增强了数据验证逻辑，对于账号、交易日期、金额等关键字段进行严格检查
6. 添加了`validate_transaction_data`方法，对标准格式DataFrame的所有字段进行全面验证：
   - 必要字段存在性检查（交易日期、金额、账号等）
   - 数据有效性检查（无空值、无无效值）
   - 数据类型检查（日期格式、数值类型）
   - 业务逻辑检查（金额不为零）
7. 优化了验证流程，将严格验证集中在基类的`save_to_database`方法中执行，避免在各银行提取器中重复验证
8. 在数据导入数据库前进行严格验证，确保只有高质量的数据被保存
9. 通过这些修改，使得添加新银行的提取器更加简单，仅需专注于特定银行的数据提取逻辑 