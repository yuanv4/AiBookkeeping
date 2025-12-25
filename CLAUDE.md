# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

AI 账单汇集工具是一个支持多平台(微信支付、支付宝、各大银行)账单解析、智能分类和数据可视化的 Vue 3 + Vite 应用。

## 开发命令

### 基础命令
```bash
# 启动开发服务器(端口 3000,自动打开浏览器)
npm run dev

# 生产构建
npm run build

# 预览生产构建
npm run preview
```

### 安装依赖
```bash
npm install
```

## 项目架构

### 技术栈
- **前端框架**: Vue 3 (Composition API + `<script setup>`)
- **构建工具**: Vite 5.1
- **状态管理**: Pinia 3.x
- **路由**: Vue Router 4.x
- **图表库**: ECharts 5.4 + vue-echarts 6.6
- **数据处理**:
  - XLSX (Excel 文件解析)
  - PapaParse (CSV 文件解析)
  - pdfjs-dist (PDF 文件解析)
- **日期处理**: date-fns 4.x

### 目录结构
```
src/
├── App.vue                    # 主应用组件(只包含 MainLayout)
├── main.js                    # 应用入口(Pinia + Router)
├── router/
│   └── index.js              # 路由配置(4个主要视图)
├── layouts/
│   └── MainLayout.vue         # 主布局(侧边栏 + 主内容区)
├── views/                     # 页面视图
│   ├── DashboardView.vue      # 仪表板(首页、文件上传)
│   ├── AnalysisView.vue       # 数据分析页
│   ├── TransactionsView.vue   # 账单明细页
│   ├── SettingsView.vue       # 设置页(路由容器)
│   └── settings/
│       └── DataSettings.vue   # 数据管理子页面
├── components/
│   ├── common/
│   │   └── FileUploader.vue   # 通用文件上传组件
│   ├── analysis/
│   │   ├── AnalysisPanel.vue  # 分析面板容器
│   │   ├── InsightCard.vue    # 智能洞察卡片
│   │   └── CategoryRanking.vue # 分类排行榜
│   ├── charts/
│   │   ├── TrendChart.vue     # 月度收支趋势图
│   │   └── CategoryPie.vue    # 消费构成饼图
│   └── settings/
│       └── AIConfig.vue       # AI 服务配置面板
├── stores/                    # Pinia 状态管理
│   ├── appStore.js           # 应用全局状态(文件、交易、统计)
│   ├── categoryStore.js      # 分类体系状态(AI生成的分类、映射)
│   └── filterStore.js        # 筛选器状态
├── services/                  # AI 服务适配器
│   ├── aiAdapter.js          # AI 适配器基类(接口定义)
│   ├── ollamaAdapter.js      # Ollama 本地 AI 适配器
│   ├── openaiAdapter.js      # OpenAI 兼容适配器
│   └── prompts.js            # AI 提示词模板
├── composables/
│   └── useClassification.js   # 分类逻辑 Composable
├── utils/
│   ├── dataModel.js          # 核心数据模型(统一账单格式)
│   ├── pdfParser.js          # 招商银行 PDF 解析工具
│   ├── categoryRules.js      # 预设分类规则(12大分类)
│   ├── categorizer.js        # 混合分类引擎(规则 + AI)
│   ├── storage.js            # localStorage 封装
│   └── chartDataProcessor.js # 图表数据处理
└── style.css                 # 全局样式
```

## 核心架构设计

### 1. 应用状态管理 (Pinia Stores)

**appStore.js** - 应用全局状态:
- 文件管理: `files`, `addFiles()`, `removeFile()`, `clearFiles()`
- 交易数据: `transactions`, `processFiles()`, `parseFile()`
- 统计信息: `statistics` (computed: total, income, expense, net)
- 数据持久化: `saveTransactions()`, `loadTransactions()` (localStorage)
- 平台检测: `detectPlatform()`, `parseCSV()`, `parseExcel()`, `parsePDF()`

**categoryStore.js** - 分类体系状态:
- AI 动态生成的分类体系(区别于旧的固定 12 分类)
- 交易分类映射: `transactionCategories[txId] = { category, subcategory, confidence, reasoning, isManual }`
- 用户纠正历史: `corrections[]`
- AI 配置管理: 支持 Ollama 和 OpenAI 适配器

**filterStore.js** - 筛选器状态:
- 时间范围、分类筛选、金额筛选等

### 2. AI 适配器架构 (services/)

**aiAdapter.js (基类)**:
定义所有 AI 适配器必须实现的接口:
- `init()` - 初始化 AI 服务
- `classifyTransaction(tx, categories)` - 分类单笔交易
- `classifyBatch(transactions, categories)` - 批量分类
- `generateCategorySystem(transactions)` - 生成初始分类体系
- `testConnection()` - 测试连接
- `parseJSONResponse(content)` - 解析 AI 返回的 JSON

**ollamaAdapter.js**:
- 本地 Ollama 集成(默认 `qwen2.5:7b` 模型)
- 支持 OpenAI 兼容的 `/v1/chat/completions` 端点

**openaiAdapter.js**:
- OpenAI API 兼容适配器
- 可用于任何 OpenAI 兼容的服务

**prompts.js**:
- `generateCategoriesPrompt()` - 生成分类体系的提示词
- `classifyPrompt()` - 单笔交易分类提示词
- `batchClassifyPrompt()` - 批量分类提示词

### 3. 分类逻辑 Composable (composables/useClassification.js)

统一的分类业务逻辑层:
- `initializeCategories(transactions)` - 首次使用时生成分类体系
- `classifyTransaction(transaction)` - 单笔分类(带缓存)
- `classifyBatch(transactions)` - 批量分类(带进度)
- `updateTransactionCategory(transaction, categoryName)` - 手动纠正
- `getTransactionCategory(transaction)` - 获取分类结果

关键特性:
- 检查缓存避免重复分类
- 记录用户纠正历史用于后续优化
- 统一的错误处理和进度反馈

### 4. 统一数据模型 (utils/dataModel.js)

跨平台账单数据的统一映射:
- **平台支持**: 支付宝 (csv)、微信支付 (xlsx)、建设银行 (xls)、招商银行 (pdf)
- **统一格式**: `UNIFIED_TRANSACTION_SCHEMA` 定义标准字段
- **核心函数**:
  - `mapTransactions()` - 批量映射原始数据到统一格式
  - `mergeTransactions()` - 合并多平台数据并按时间排序
  - `deduplicateTransactions()` - 基于交易单号/时间/金额去重
  - `parseTransactionTime()` - 支持多种时间格式解析

**金额约定**: 负数表示支出,正数表示收入

### 5. 路由架构 (router/index.js)

主要路由:
- `/dashboard` - 仪表板(文件上传 + 欢迎页)
- `/analysis` - 数据分析(图表 + 洞察)
- `/transactions` - 账单明细(交易列表)
- `/settings` - 设置页(嵌套路由)
  - `/settings/ai` - AI 配置
  - `/settings/data` - 数据管理

### 6. 数据可视化

**图表组件** (使用 ECharts):
- `TrendChart` - 月度收支趋势折线图
- `CategoryPie` - 消费构成环形饼图
- `CategoryRanking` - Top 10 分类排行榜

**图表数据处理** (utils/chartDataProcessor.js):
- 聚合月度数据
- 计算分类汇总
- 格式化图表所需的数据结构

### 7. PDF 解析 (utils/pdfParser.js)

专门针对招商银行 PDF 账单:
- 使用 pdf.js 提取文本内容
- 正则表达式匹配交易记录格式
- 匹配模式: `日期 + 货币 + 金额 + 余额 + 摘要 + 对手信息`

## 开发注意事项

### 添加新平台支持
1. 在 `dataModel.js` 中添加平台字段映射
2. 在 `appStore.js` 的 `detectPlatform()` 函数中添加识别逻辑
3. 在 `appStore.js` 中实现对应的解析函数(如 `parseCSV`, `parseExcel`, `parsePDF`)

### 添加新 AI 适配器
1. 继承 `AIAdapter` 基类 (services/aiAdapter.js)
2. 实现所有必须的接口方法
3. 在 `useClassification.js` 的 `initAdapter()` 中添加识别逻辑
4. 在 `categoryStore.js` 的 `aiConfig` 中添加配置选项

### 分类体系工作流程

**首次使用流程**:
1. 用户上传账单文件
2. 调用 `initializeCategories(transactions)` 生成分类体系
3. AI 根据交易样本生成 8-12 个一级分类
4. 分类体系保存到 `categoryStore.categories`

**交易分类流程**:
1. 调用 `classifyTransaction(transaction)` 或 `classifyBatch(transactions)`
2. 检查缓存,已分类则直接返回
3. 使用 AI 适配器进行分类
4. 保存结果到 `categoryStore.transactionCategories`
5. 用户可手动纠正,记录到 `corrections` 历史

### 文件解析要点
- **支付宝 CSV**: GBK 编码,需跳过说明行查找表头
- **微信 Excel**: 跳过前 16 行说明(`range: 16`)
- **建设银行 Excel**: 跳过前 3 行(`range: 2`)
- **招商银行 PDF**: 使用 pdf.js + 正则表达式提取

### 数据持久化

所有数据存储在 localStorage:
- `transactions` - 交易数据
- `categories` - AI 生成的分类体系
- `transactionCategories` - 交易分类映射
- `corrections` - 用户纠正历史
- `ai_config` - AI 配置

使用 `utils/storage.js` 统一管理(带命名空间前缀)

## 已知问题

1. **招商银行 PDF 解析**: 依赖正则表达式匹配,格式变化可能导致解析失败
2. **AI 分类稳定性**: 依赖第三方 API,网络或 API 变更可能导致失败
3. **localStorage 容量**: 大量交易数据可能超出 5MB 限制

## 依赖版本说明

- `pdfjs-dist`: 使用 3.x 版本
- `echarts` & `vue-echarts`: 需要按需导入 ECharts 组件以减小打包体积
- `date-fns`: 4.x 版本,API 与 3.x 有差异
- `pinia`: 3.x 版本,Composition API 风格

## Git 工作流

当前分支: `videcoding`(开发分支)
主分支: `master`(用于 PR)

最近的提交包括重构应用架构、实现智能分类和数据可视化功能。
