# 脚本目录结构说明

根据功能将脚本分为以下几个模块：

## 1. 数据提取模块 - /extractors

负责从不同银行的Excel文件中提取交易数据。

- `bank_transaction_extractor.py` - 银行交易提取器基类
- `cmb_transaction_extractor.py` - 招商银行交易提取器
- `ccb_transaction_extractor.py` - 建设银行交易提取器
- 未来可添加更多银行的提取器...

## 2. 数据分析模块 - /analyzers

负责分析交易数据，生成各类统计结果。

- `transaction_analyzer.py` - 交易数据分析器，提供各种分析功能

## 3. 数据可视化模块 - /visualization

负责生成图表和可视化展示。

- `visualization_helper.py` - 数据可视化助手，生成各类图表

## 4. 数据库管理模块 - /db

负责数据库操作和数据存储。

- `db_manager.py` - 数据库管理器，处理所有数据库操作

## 5. 自动化工具模块 - /automation

负责自动处理流程和脚本运行。

## 使用场景

1. 数据导入：使用提取器模块处理银行交易文件
2. 数据存储：提取的数据通过数据库管理模块存入数据库
3. 数据分析：使用分析模块对数据进行分析统计
4. 数据可视化：使用可视化模块生成各类图表
5. 自动流程：使用自动化模块一键完成整个处理流程 