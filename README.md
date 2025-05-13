# 银行交易数据分析系统

这是一个全功能的银行交易数据分析系统，用于从招商银行Excel文件中提取交易数据，并提供多维度的账单分析功能。

## 功能

- **数据导入**
  - 上传一个或多个招商银行交易流水Excel文件
  - 自动处理文件，提取交易数据
  - 支持增量更新，避免重复导入相同交易记录

- **多维度分析**
  - **仪表盘**: 总体收支概览和关键指标
  - **月度分析**: 按月份统计收支趋势和变化
  - **分类分析**: 支出类别占比和详情
  - **时间分析**: 按星期/日期的消费模式
  - **商户分析**: 交易商户的消费统计
  - **交易记录**: 完整交易明细查询和筛选

- **数据可视化**
  - 月度收支趋势图
  - 支出类别饼图
  - 按星期消费柱状图
  - 消费最多的商户条形图
  - 日支出趋势线图
  - 类别-月份热力图
  - **所有图表均支持交互式操作**，如缩放、平移、点击查看详情等

## 交互式图表功能

系统中的所有图表都是交互式的，支持以下操作：

- **悬停查看详情**：将鼠标悬停在图表上，查看详细数据
- **图例交互**：点击图例可以隐藏/显示对应的数据系列
- **缩放功能**：使用滚轮可以放大/缩小图表，聚焦于感兴趣的数据区域
- **平移功能**：在图表上拖动可以平移查看更多数据
- **点击功能**：点击图表元素（如条形图、扇形图的扇区）可以跳转到相关的详细分析页面
- **数据标签**：部分图表显示数据标签，提供直观的数值参考

这些交互式功能让数据分析变得更加直观和灵活，用户可以根据自己的需求自由探索数据。

## 项目结构

```
/
├── app.py                         # Web应用主程序
├── scripts/                       # 脚本目录
│   ├── cmb_transaction_extractor.py  # 招商银行交易数据提取脚本
│   ├── transaction_analyzer.py    # 交易数据分析器
│   └── visualization_helper.py    # 可视化助手
├── data/                          # 数据目录
│   ├── bank_transactions.csv      # 交易数据CSV文件
│   └── analysis_data.json         # 分析结果JSON数据
├── uploads/                       # 上传文件目录
├── templates/                     # HTML模板目录
│   ├── base.html                  # 基础模板
│   ├── dashboard.html             # 仪表盘页面
│   ├── monthly.html               # 月度分析页面
│   ├── category.html              # 分类分析页面
│   ├── time.html                  # 时间分析页面
│   ├── merchant.html              # 商户分析页面
│   ├── transactions.html          # 交易记录页面
│   ├── upload.html                # 上传页面
│   └── download.html              # 下载页面
├── requirements.txt               # 依赖包列表
├── start_app.bat                  # 启动应用的批处理文件
└── README.md                      # 项目说明文档
```

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

- 支持的文件类型：.xlsx
- 上传的文件将保存在uploads目录中
- 提取的数据将保存为data目录下的"bank_transactions.csv"文件
- 分析结果将保存为data目录下的"analysis_data.json"文件
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