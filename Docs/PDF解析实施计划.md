# 招商银行PDF账单解析功能实施计划(折中方案)

## 目标
实现招商银行PDF账单的自动化解析,使用 pdf.js 提取文本并通过正则表达式匹配交易数据。

## 方案特点
- ✅ 基础实用: 满足当前需求
- ✅ 易于维护: 正则表达式可调整
- ✅ 可升级: 后续可无缝升级到完整版
- ✅ 轻量实现: 不增加过多复杂度

## 实施步骤

### 第一步: 安装依赖

```bash
npm install pdfjs-dist@3.11.174
```

**安装文件**: `package.json` (自动更新)

---

### 第二步: 创建PDF解析工具模块

**新建文件**: `src/utils/pdfParser.js`

**功能说明**:
1. 使用 pdf.js 提取PDF文本内容
2. 通过正则表达式匹配招商银行交易数据格式
3. 将匹配结果转换为统一的交易对象数组

**核心逻辑**:
```javascript
// 导入 pdf.js
import * as pdfjsLib from 'pdfjs-dist/legacy/build/pdf.js'
import { mapCMBTransaction } from './dataModel.js'

// 设置 worker
pdfjsLib.GlobalWorkerOptions.workerSrc =
  'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js'

// 主解析函数
export async function parseCMBPDF(file) {
  // 1. 读取文件为 ArrayBuffer
  // 2. 使用 pdf.js 提取所有页面的文本
  // 3. 合并文本内容
  // 4. 使用正则表达式匹配交易记录
  // 5. 转换为统一格式
  return transactions
}

// 正则表达式匹配交易记录
function extractTransactions(text) {
  // 匹配模式: 日期 + 摘要 + 金额 + 对手信息
  const pattern = /(\d{4}\/\d{2}\/\d{2})\s+(.+?)\s+(-?\d+\.?\d*)\s+(.+)/g
  // ...
}
```

---

### 第三步: 更新 App.vue 中的 parsePDF 函数

**修改文件**: `src/App.vue`

**修改位置**: 第 488-506 行

**当前代码**:
```javascript
async function parsePDF(file, platform, bankName = '招商银行') {
  console.warn('PDF解析功能需要额外的库支持，当前为简化版本')
  return [{ /* 示例数据 */ }]
}
```

**修改为**:
```javascript
async function parsePDF(file, platform, bankName = '招商银行') {
  try {
    // 使用新的 PDF 解析工具
    const { parseCMBPDF } = await import('./utils/pdfParser.js')
    return await parseCMBPDF(file)
  } catch (error) {
    console.error('PDF解析失败:', error)
    throw new Error(`PDF解析失败: ${error.message}`)
  }
}
```

---

### 第四步: 测试验证

**测试文件**: `tmp/招商银行交易流水(申请时间2025年06月05日21时06分15秒).pdf`

**验证步骤**:
1. 上传测试PDF文件
2. 点击"开始处理账单"
3. 检查解析结果:
   - ✅ 交易数量是否正确
   - ✅ 日期格式是否正确
   - ✅ 金额是否正确(正负号)
   - ✅ 交易对方信息是否完整
   - ✅ 摘要信息是否准确

**调试方法**:
- 在浏览器控制台查看提取的原始文本
- 在控制台查看正则匹配结果
- 根据实际情况调整正则表达式

---

## 关键技术细节

### PDF文本提取
- 使用 `pdfjsLib.getDocument()` 加载PDF
- 遍历所有页面使用 `page.getTextContent()` 提取文本
- 合并所有页面的文本内容

### 正则表达式设计
根据招商银行PDF的实际格式设计,例如:
```
交易日期    摘要        支出金额     收入金额    对手信息
2025/01/01  购物        -100.00                某某商店
2025/01/02  工资                    +5000.00   公司
```

正则模式示例:
```javascript
const linePattern = /(\d{4}\/\d{2}\/\d{2})\s{2,}(.+?)\s{2,}(-?\d+\.?\d*)?\s{2,}(-?\d+\.?\d*)?\s{2,}(.+)/
```

### 数据映射
使用现有的 `mapCMBTransaction` 函数将解析结果映射到统一格式

---

## 升级路径(从折中方案到完整版)

### 升级点1: 更精确的表格解析
- **当前**: 正则表达式匹配
- **升级**: 使用 pdf.js 的坐标信息精确提取表格单元格
- **修改位置**: `src/utils/pdfParser.js` 中的 `extractTransactions` 函数

### 升级点2: 多银行支持
- **当前**: 只支持招商银行
- **升级**: 添加银行识别逻辑,支持多种PDF格式
- **方法**: 根据 PDF 内容特征识别银行类型

### 升级点3: 复杂格式支持
- **当前**: 简单表格格式
- **升级**: 支持合并单元格、跨页表格等复杂情况

---

## 修改文件清单

1. **package.json** - 添加依赖(自动)
2. **src/utils/pdfParser.js** - 新建文件,核心解析逻辑
3. **src/App.vue** - 更新 parsePDF 函数

---

## 预期时间
- 安装依赖: 2分钟
- 编写代码: 15分钟
- 测试调试: 10分钟
- **总计**: 约30分钟

---

## 风险与应对

### 风险1: PDF格式变化
- **应对**: 正则表达式易于调整,只需修改模式即可

### 风险2: 特殊字符或编码问题
- **应对**: 添加文本清理逻辑,处理空格、换行等

### 风险3: 某些PDF无法提取文本
- **应对**: 给出友好提示,建议用户转换为Excel

---

## 成功标准
- ✅ 能成功解析测试PDF文件
- ✅ 提取的交易数据准确率 > 95%
- ✅ 用户体验良好,无报错
- ✅ 代码结构清晰,易于维护
