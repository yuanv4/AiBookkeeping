# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

AI 账单汇集工具是一个支持多平台（微信支付、支付宝、各大银行）账单解析、智能分类和数据可视化的 Vue 3 + Vite 应用。

## 开发命令

### 基础命令
```bash
# 启动开发服务器（端口 3000，自动打开浏览器）
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
- **前端框架**: Vue 3 (Composition API)
- **构建工具**: Vite 5
- **图表库**: ECharts 5.4 + vue-echarts 6.6
- **数据处理**:
  - XLSX (Excel 文件解析)
  - PapaParse (CSV 文件解析)
  - pdfjs-dist (PDF 文件解析)
- **日期处理**: date-fns 4.x

### 目录结构
```
src/
├── App.vue                    # 主应用组件（文件上传、交易列表、统计）
├── main.js                    # 应用入口
├── config/
│   └── aiConfig.js           # AI 配置（支持通义千问、文心一言、ChatGPT）
├── components/
│   ├── analysis/
│   │   ├── AnalysisPanel.vue  # 分析面板容器（AI配置、洞察、图表）
│   │   ├── InsightCard.vue    # 智能洞察卡片
│   │   └── CategoryRanking.vue # 分类排行榜
│   ├── charts/
│   │   ├── TrendChart.vue     # 月度收支趋势图
│   │   └── CategoryPie.vue    # 消费构成饼图
│   └── settings/
│       └── AIConfig.vue       # AI 服务配置面板
├── utils/
│   ├── dataModel.js          # 核心数据模型（统一账单格式）
│   ├── pdfParser.js          # 招商银行 PDF 解析工具
│   ├── categoryRules.js      # 12 大分类规则定义
│   ├── categorizer.js        # 混合分类引擎（规则 + AI）
│   └── aiCategorizer.js      # AI 分类器（支持多 AI 提供商）
└── style.css                 # 全局样式
```

## 核心架构设计

### 1. 统一数据模型（dataModel.js）

项目核心是跨平台账单数据的统一映射：

- **平台支持**: 支付宝 (csv)、微信支付 (xlsx)、建设银行 (xls)、招商银行 (pdf)
- **统一格式**: `UNIFIED_TRANSACTION_SCHEMA` 定义标准字段
- **字段映射**: 每个平台有独立的 `FIELD_MAPPING` 配置
- **核心函数**:
  - `mapTransactions()` - 批量映射原始数据到统一格式
  - `mergeTransactions()` - 合并多平台数据并按时间排序
  - `deduplicateTransactions()` - 基于交易单号/时间/金额去重
  - `parseTransactionTime()` - 支持多种时间格式解析

**金额约定**: 负数表示支出，正数表示收入

### 2. 智能分类引擎

**混合分类策略** (categorizer.js):
1. 优先使用规则引擎匹配（快速、免费）
2. 规则无法匹配时调用 AI（需配置）
3. AI 失败时回退到规则引擎兜底
4. 最终返回"其他"分类

**分类规则** (categoryRules.js):
- 12 大预设分类：餐饮、交通、购物、娱乐、居住、医疗、教育、通讯、保险、投资、转账、其他
- 每个分类包含：
  - `keywords` - 关键词列表（精确匹配）
  - `patterns` - 正则表达式列表
  - `priority` - 优先级（数字越小越优先）
  - `icon` - 图标 emoji
  - `color` - 颜色值

**AI 分类器** (aiCategorizer.js):
- **支持的 AI 提供商**:
  - 通义千问（阿里云 DashScope）- 推荐
  - 文心一言（百度千帆）
  - ChatGPT（OpenAI）
- **API 调用方式**: 前端直接调用，API Key 存储在 localStorage
- **提示词**: 要求 AI 返回简洁分类名称，避免额外解释

### 3. PDF 解析（pdfParser.js）

专门针对招商银行 PDF 账单：
- 使用 pdf.js 提取文本内容
- 正则表达式匹配交易记录格式
- 匹配模式: `日期 + 货币 + 金额 + 余额 + 摘要 + 对手信息`

### 4. 数据可视化

**图表组件** (使用 ECharts):
- `TrendChart` - 月度收支趋势折线图（收入/支出/净收支）
- `CategoryPie` - 消费构成环形饼图
- `CategoryRanking` - Top 10 分类排行榜

**分析面板**:
- 可折叠的 AI 配置区域
- 洞察卡片（统计数据摘要）
- 响应式网格布局（2列 → 移动端1列）

### 5. AI 配置系统

**配置存储**: localStorage (`ai_config` 键)

**配置结构**:
```javascript
{
  provider: 'qianwen',      // AI 提供商
  apiKey: 'sk-xxx',         // API Key
  model: 'qwen-turbo',      // 模型名称
  enabled: false,           // 是否启用
  fallbackToRules: true,    // AI 失败是否回退到规则
  timeout: 10000           // 超时时间
}
```

**相关函数**:
- `loadAIConfig()` - 从 localStorage 加载配置
- `saveAIConfig()` - 保存配置到 localStorage
- `validateAIConfig()` - 验证配置有效性
- `testAIConfig()` - 测试 API 连接

## 开发注意事项

### 添加新平台支持
1. 在 `dataModel.js` 中添加平台字段映射
2. 在 `App.vue` 的 `detectPlatform()` 函数中添加识别逻辑
3. 实现对应的解析函数（如 `parseCSV`, `parseExcel`, `parsePDF`）

### 添加新分类
在 `categoryRules.js` 的 `CATEGORY_RULES` 对象中添加新分类规则：
```javascript
'新分类': {
  keywords: ['关键词1', '关键词2'],
  patterns: [/.*正则.*/],
  priority: 1,
  icon: '🏷️',
  color: '#HEX'
}
```

### 添加新 AI 提供商
1. 在 `aiConfig.js` 的 `AI_PROVIDERS` 中添加提供商配置
2. 在 `aiCategorizer.js` 的 `callAIAPI()` 函数中添加调用逻辑
3. 如需特殊格式，参考 `callWenxinAPI()` 实现单独的调用函数

### 文件解析要点
- **支付宝 CSV**: GBK 编码，需跳过说明行查找表头
- **微信 Excel**: 跳过前 16 行说明（`range: 16`）
- **建设银行 Excel**: 跳过前 3 行（`range: 2`）
- **招商银行 PDF**: 使用 pdf.js + 正则表达式提取

### 分类优先级
在 `categoryRules.js` 中，`priority` 值越小优先级越高。当交易匹配多个分类时，选择优先级最高的。

## 已知问题

1. **招商银行 PDF 解析**: 依赖正则表达式匹配，格式变化可能导致解析失败
2. **AI 分类稳定性**: 依赖第三方 API，网络或 API 变更可能导致失败
3. **规则匹配覆盖**: 预设规则可能无法覆盖所有商户名称

## 依赖版本说明

- `pdfjs-dist`: 使用 legacy 版本以兼容传统浏览器环境
- `echarts` & `vue-echarts`: 需要按需导入 ECharts 组件以减小打包体积
- `date-fns`: 4.x 版本，API 与 3.x 有差异

## Git 工作流

当前分支: `videcoding`（开发分支）
主分支: `master`（用于 PR）

最近的提交包括招商银行 PDF 解析功能的实现。
