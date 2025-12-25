# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

AI 账单汇集工具是一个支持多平台(微信支付、支付宝、各大银行)账单解析、智能分类和数据可视化的 Vue 3 + Vite 应用。

**核心特性**:
- 多平台账单解析:支付宝 CSV、微信支付 Excel、建设银行 Excel、招商银行 PDF
- AI 智能分类:支持 Ollama 本地模型、OpenAI 兼容 API、通义千问、文心一言
- 数据迁移:从 localStorage 自动迁移到 IndexedDB
- 备份恢复:完整数据备份、恢复、导出功能
- 数据可视化:收支趋势、分类统计、智能洞察

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
- **数据库**: Dexie 4.x (IndexedDB ORM)
- **数据处理**:
  - XLSX (Excel 文件解析)
  - PapaParse (CSV 文件解析)
  - pdfjs-dist (PDF 文件解析)
- **日期处理**: date-fns 4.x

### 目录结构
```
src/
├── App.vue                    # 主应用组件
├── main.js                    # 应用入口(Pinia + Router)
├── config/
│   └── aiConfig.js           # AI 配置默认值和校验
├── router/
│   └── index.js              # 路由配置
├── layouts/
│   ├── MainLayout.vue         # 主布局
│   └── components/
│       ├── AppSidebar.vue     # 侧边栏导航
│       └── AppHeader.vue      # 顶部栏
├── views/                     # 页面视图
│   ├── DashboardView.vue      # 仪表板
│   ├── AnalysisView.vue       # 数据分析页
│   ├── TransactionsView.vue   # 账单明细页
│   ├── SettingsView.vue       # 设置页
│   └── settings/
│       └── DataSettings.vue   # 数据管理子页面
├── components/
│   ├── common/
│   │   ├── FileUploader.vue   # 文件上传组件
│   │   └── Notification.vue   # 通知组件
│   ├── analysis/
│   │   ├── AnalysisPanel.vue  # 分析面板
│   │   ├── InsightCard.vue    # 智能洞察卡片
│   │   └── CategoryRanking.vue # 分类排行榜
│   ├── charts/
│   │   ├── TrendChart.vue     # 趋势图
│   │   └── CategoryPie.vue    # 饼图
│   ├── settings/
│   │   └── AIConfig.vue       # AI 配置面板
│   └── MigrationWizard.vue    # 数据迁移向导
├── stores/                    # Pinia 状态管理
│   ├── appStore.js           # 应用全局状态
│   ├── categoryStore.js      # 分类体系状态
│   ├── filterStore.js        # 筛选器状态
│   └── notificationStore.js  # 通知状态
├── repositories/              # 数据访问层(Repository 模式)
│   ├── index.js              # 统一导出
│   ├── transactionsRepo.js   # 交易数据 CRUD
│   ├── categoriesRepo.js     # 分类数据 CRUD
│   └── configRepo.js         # 配置数据 CRUD
├── services/                  # AI 服务适配器
│   ├── aiAdapter.js          # AI 适配器基类
│   ├── ollamaAdapter.js      # Ollama 适配器
│   ├── openaiAdapter.js      # OpenAI 适配器
│   └── prompts.js            # AI 提示词
├── composables/
│   └── useClassification.js   # 分类逻辑
├── utils/
│   ├── dataModel.js          # 统一数据模型
│   ├── pdfParser.js          # PDF 解析
│   ├── categoryRules.js      # 分类规则
│   ├── categorizer.js        # 分类引擎
│   ├── aiCategorizer.js      # AI 分类器
│   ├── storage.js            # localStorage 封装
│   ├── indexedDB.js          # IndexedDB 封装
│   ├── categoryMapping.js    # 分类映射转换
│   ├── dataExporter.js       # 数据导出
│   ├── dataMigrator.js       # 数据迁移
│   ├── backupManager.js      # 备份管理
│   ├── errorHandler.js       # 错误处理
│   └── chartDataProcessor.js # 图表数据处理
└── style.css                 # 全局样式
```

## 核心架构设计

### 1. 数据存储架构(Repository + IndexedDB)

项目采用 **Repository 模式** 统一数据访问,从 localStorage 迁移到 IndexedDB:

**IndexedDB 数据库** ([utils/indexedDB.js](src/utils/indexedDB.js)):
- 数据库名: `AiBookkeepingDB`
- 使用 Dexie 4.x ORM
- 表结构:
  - `transactions` - 交易记录(主键: transactionId)
  - `categories` - AI 生成的分类
  - `transaction_categories` - 交易分类映射
  - `corrections` - 用户纠正历史
  - `app_config` - 应用配置(如 AI 配置)
  - `backups` - 备份数据
  - `migration_state` - 迁移状态

**Repository 层** ([repositories/](src/repositories/)):
- **transactionsRepo.js** - 交易数据 CRUD
  - `getAll()`, `bulkAdd()`, `clear()`, `queryByMonth()`, `queryByPlatform()`
- **categoriesRepo.js** - 分类和映射管理
  - `getAll()`, `bulkAdd()`, `bulkSet()` (用于对象映射)
- **configRepo.js** - 配置管理
  - `get()`, `set()`, `clear()`

**数据迁移** ([utils/dataMigrator.js](src/utils/dataMigrator.js)):
- 自动检测 localStorage 是否有数据需要迁移
- 迁移流程: 读取 localStorage → 写入 IndexedDB → 验证 → 创建备份
- 支持回滚(从备份恢复到 localStorage)
- 迁移状态跟踪: NOT_STARTED → IN_PROGRESS → COMPLETED/FAILED/ROLLED_BACK

**备份恢复** ([utils/backupManager.js](src/utils/backupManager.js)):
- `createBackup()` - 创建完整备份(包含校验和)
- `saveBackup()` - 保存到 IndexedDB(保留最近 10 个)
- `restoreBackup()` - 恢复备份(失败自动回滚)
- `getBackupList()`, `deleteBackup()`

**数据导出** ([utils/dataExporter.js](src/utils/dataExporter.js)):
- `exportToJSON()` - 导出完整数据(带 SHA-256 校验和)
- `exportToCSV()` - 导出交易数据为 CSV
- `verifyChecksum()` - 验证校验和

### 2. 应用状态管理 (Pinia Stores)

**appStore.js** - 应用全局状态:
- 文件管理: `files`, `addFiles()`, `removeFile()`, `clearFiles()`
- 交易数据: `transactions`, `loadTransactions()`, `processFiles()`
- 统计信息: `statistics` (computed)
- 清空数据: `clearAllData()`, `performClearAll()`
- 平台检测: `detectPlatform()`, `parseCSV()`, `parseExcel()`, `parsePDF()`

**categoryStore.js** - 分类体系状态:
- AI 生成的分类体系: `categories[]`
- 交易分类映射: `transactionCategories[txId]` (对象格式)
- 用户纠正历史: `corrections[]`
- AI 配置(唯一真源): `aiConfig` (provider, apiKey, baseURL, model, enabled, fallbackToRules)
- 数据加载/保存: `loadFromStorage()`, `saveToStorage()` (使用 Repository)

**filterStore.js** - 筛选器状态:
- 时间范围、分类筛选、金额筛选等

**notificationStore.js** - 通知状态:
- `show(message, type, duration)`, `remove(id)`

### 3. AI 配置和分类系统

**AI 配置** ([config/aiConfig.js](src/config/aiConfig.js)):
- 支持的提供商:
  - `ollama` - Ollama 本地模型 (qwen2.5:7b, llama3, mistral)
  - `openai` - OpenAI API (gpt-3.5-turbo, gpt-4)
  - `qianwen` - 通义千问 (qwen-turbo, qwen-plus, qwen-max)
- `validateAIConfig()` - 配置验证
- `getProviderConfig()` - 获取提供商配置

**AI 分类器** ([utils/aiCategorizer.js](src/utils/aiCategorizer.js)):
- `categorizeByAI(transaction, aiConfig)` - 使用 AI 分类单笔交易
- `testAIConfig(config)` - 测试 AI 配置是否有效
- 支持多种 AI 提供商(OpenAI 兼容、文心一言等)

**分类引擎** ([utils/categorizer.js](src/utils/categorizer.js)):
- 混合分类策略: 规则分类 + AI 分类
- `batchCategorize()` - 批量分类交易
- 优先使用规则分类,失败时回退到 AI(如果启用)

**分类映射转换** ([utils/categoryMapping.js](src/utils/categoryMapping.js)):
- `mappingToRows()` - 对象映射 → 数组行(存储到 IndexedDB)
- `rowsToMapping()` - 数组行 → 对象映射(业务层使用)
- ⚠️ 所有代码必须使用此函数进行转换

### 4. AI 适配器架构 (services/)

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

### 5. 分类逻辑 Composable (composables/useClassification.js)

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

### 6. 统一数据模型 (utils/dataModel.js)

跨平台账单数据的统一映射:
- **平台支持**: 支付宝 (csv)、微信支付 (xlsx)、建设银行 (xls)、招商银行 (pdf)
- **统一格式**: `UNIFIED_TRANSACTION_SCHEMA` 定义标准字段
- **核心函数**:
  - `mapTransactions()` - 批量映射原始数据到统一格式
  - `mergeTransactions()` - 合并多平台数据并按时间排序
  - `deduplicateTransactions()` - 基于交易单号/时间/金额去重
  - `parseTransactionTime()` - 支持多种时间格式解析

**金额约定**: 负数表示支出,正数表示收入

### 7. 路由架构 (router/index.js)

主要路由:
- `/dashboard` - 仪表板(文件上传 + 欢迎页)
- `/analysis` - 数据分析(图表 + 洞察)
- `/transactions` - 账单明细(交易列表)
- `/settings` - 设置页(嵌套路由)
  - `/settings/ai` - AI 配置
  - `/settings/data` - 数据管理

### 8. 数据可视化

**图表组件** (使用 ECharts):
- `TrendChart` - 月度收支趋势折线图
- `CategoryPie` - 消费构成环形饼图
- `CategoryRanking` - Top 10 分类排行榜

**图表数据处理** (utils/chartDataProcessor.js):
- 聚合月度数据
- 计算分类汇总
- 格式化图表所需的数据结构

### 9. 错误处理 (utils/errorHandler.js)

统一错误处理和用户友好的错误提示:
- `normalizeStorageError()` - 规范化存储错误
- `normalizeAIError()` - 规范化 AI 调用错误
- 错误类型映射: QuotaExceededError → "存储空间不足"

### 10. PDF 解析 (utils/pdfParser.js)

专门针对招商银行 PDF 账单:
- 使用 pdf.js 提取文本内容
- 正则表达式匹配交易记录格式
- 匹配模式: `日期 + 货币 + 金额 + 余额 + 摘要 + 对手信息`

## 开发注意事项

### 数据访问规范
- ⚠️ **永远不要直接访问 IndexedDB**,必须通过 Repository 层
- Store 层负责业务逻辑,Repository 层负责数据访问
- 交易分类映射使用对象格式 `{txId: data}`,存储时转换为数组行

### 添加新平台支持
1. 在 `dataModel.js` 中添加平台字段映射
2. 在 `appStore.js` 的 `detectPlatform()` 函数中添加识别逻辑
3. 在 `appStore.js` 中实现对应的解析函数(如 `parseCSV`, `parseExcel`, `parsePDF`)

### 添加新 AI 适配器
1. 继承 `AIAdapter` 基类 (services/aiAdapter.js)
2. 实现所有必须的接口方法
3. 在 `aiCategorizer.js` 的 `callAIAPI()` 中添加支持
4. 在 `config/aiConfig.js` 的 `AI_PROVIDERS` 中添加配置

### 添加新数据表
1. 在 `utils/indexedDB.js` 中添加表定义
2. 在 `repositories/` 中创建对应的 Repository
3. 在 `repositories/index.js` 中导出

### 分类体系工作流程

**首次使用流程**:
1. 用户上传账单文件
2. 调用 `initializeCategories(transactions)` 生成分类体系
3. AI 根据交易样本生成 8-12 个一级分类
4. 分类体系保存到 `categoryStore.categories`

**交易分类流程**:
1. 调用 `classifyTransaction(transaction)` 或 `classifyBatch(transactions)`
2. 检查缓存,已分类则直接返回
3. 使用规则分类优先,失败时回退到 AI(如果启用)
4. 保存结果到 `categoryStore.transactionCategories`
5. 用户可手动纠正,记录到 `corrections` 历史

### 文件解析要点
- **支付宝 CSV**: GBK 编码,需跳过说明行查找表头
- **微信 Excel**: 跳过前 16 行说明(`range: 16`)
- **建设银行 Excel**: 跳过前 3 行(`range: 2`)
- **招商银行 PDF**: 使用 pdf.js + 正则表达式提取

### 数据持久化策略

**当前架构**: 使用 IndexedDB (通过 Repository 模式)
- 无容量限制(相比 localStorage 的 5MB)
- 支持事务、索引、复杂查询
- 所有数据访问通过 Repository 层

**localStorage 工具** ([utils/storage.js](src/utils/storage.js)):
- 仅用于迁移和小配置存储
- 提供 `getStorageInfo()` 查询已用空间
- 统一错误处理(QuotaExceeded, 等)
- 键名常量管理: `STORAGE_KEYS`

**迁移**: 自动检测 localStorage 数据并迁移到 IndexedDB
- 迁移前创建备份
- 支持回滚
- 迁移后保留 localStorage 备份(用户手动清除)

## 已知问题

1. **招商银行 PDF 解析**: 依赖正则表达式匹配,格式变化可能导致解析失败
2. **AI 分类稳定性**: 依赖第三方 API,网络或 API 变更可能导致失败
3. **IndexedDB 兼容性**: 需要现代浏览器支持(IE 不支持)
4. **数据迁移**: 仅支持从 localStorage 迁移到 IndexedDB,不支持反向同步

## 依赖版本说明

- `pdfjs-dist`: 使用 3.x 版本
- `dexie`: 4.x 版本(用于 IndexedDB ORM)
- `echarts` & `vue-echarts`: 需要按需导入 ECharts 组件以减小打包体积
- `date-fns`: 4.x 版本,API 与 3.x 有差异
- `pinia`: 3.x 版本,Composition API 风格

## Git 工作流

当前分支: `videcoding`(开发分支)
主分支: `master`(用于 PR)

最近的提交包括重构应用架构、实现智能分类和数据可视化功能。

## CSS 变量系统

项目使用 CSS 变量实现主题系统,定义在 `src/style.css`:
- 颜色变量: `--color-primary`, `--color-success`, `--color-danger`, 等
- 间距变量: `--spacing-1` 到 `--spacing-8`
- 布局变量: `--sidebar-width`, `--header-height`
- 阴影变量: `--shadow-sm`, `--shadow-md`, `--shadow-lg`

新增组件应使用这些变量以保持一致性。
