/**
 * 招商银行PDF账单解析工具
 * 使用 pdf.js 提取文本并通过正则表达式匹配交易数据
 */

import * as pdfjsLib from 'pdfjs-dist/legacy/build/pdf.js'
import { mapCMBTransaction } from './dataModel.js'

// 设置 worker
pdfjsLib.GlobalWorkerOptions.workerSrc =
  'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js'

/**
 * 主解析函数 - 解析招商银行PDF账单
 * @param {File} file - PDF文件对象
 * @returns {Promise<Array>} - 解析后的交易记录数组
 */
export async function parseCMBPDF(file) {
  try {
    // 1. 读取文件为 ArrayBuffer
    const arrayBuffer = await file.arrayBuffer()

    // 2. 使用 pdf.js 加载PDF文档
    const loadingTask = pdfjsLib.getDocument({ data: arrayBuffer })
    const pdfDocument = await loadingTask.promise

    // 3. 提取所有页面的文本内容
    let fullText = ''
    const numPages = pdfDocument.numPages

    for (let pageNum = 1; pageNum <= numPages; pageNum++) {
      const page = await pdfDocument.getPage(pageNum)
      const textContent = await page.getTextContent()
      const pageText = textContent.items.map(item => item.str).join(' ')
      fullText += pageText + '\n'
    }

    console.log('📄 PDF文本提取完成,总长度:', fullText.length)
    console.log('📝 提取的文本内容(前500字符):', fullText.substring(0, 500))

    // 4. 使用正则表达式匹配交易记录
    const rawTransactions = extractTransactions(fullText)

    console.log(`✅ 成功提取 ${rawTransactions.length} 条交易记录`)

    // 5. 转换为统一格式
    const transactions = rawTransactions.map(raw => mapCMBTransaction(raw))

    return transactions
  } catch (error) {
    console.error('❌ PDF解析失败:', error)
    throw new Error(`PDF解析失败: ${error.message}`)
  }
}

/**
 * 使用正则表达式从文本中提取交易记录
 * @param {string} text - PDF提取的完整文本
 * @returns {Array} - 原始交易记录数组
 */
function extractTransactions(text) {
  const transactions = []

  // 清理文本:移除多余空格,统一换行符
  const cleanText = text
    .replace(/\s+/g, ' ')  // 多个空白字符替换为单个空格
    .trim()

  console.log('🔍 开始正则匹配...')

  // 招商银行PDF交易记录格式分析
  // 实际格式: 记账日期   货币   交易金额   联机余额   交易摘要   对手信息
  // 例如: 2025-01-01   CNY   -5.00   2,271.86   快捷支付   扫二维码付款

  // 根据实际格式设计的正则模式
  // 匹配: 日期 + 多个空格 + 货币 + 多个空格 + 金额 + 多个空格 + 余额 + 多个空格 + 摘要 + 多个空格 + 对手信息
  const cmbPattern = /(\d{4}-\d{2}-\d{2})\s+(\w{3})\s+(-?\d+\.?\d*)\s+(-?[\d,]+\.?\d*)\s+(.+?)\s+(.+?)(?=\s+\d{4}-\d{2}-\d{2}|$)/g

  let matches = [...cleanText.matchAll(cmbPattern)]

  console.log(`📊 正则匹配到 ${matches.length} 个潜在交易记录`)

  // 处理匹配结果
  for (const match of matches) {
    try {
      // 新的正则表达式捕获组:
      // [1] 日期, [2] 货币, [3] 金额, [4] 余额, [5] 摘要, [6] 对手信息
      const dateStr = match[1]
      const currency = match[2]
      const amountStr = match[3]
      const balanceStr = match[4]
      const summary = match[5] ? match[5].trim() : ''
      const counterparty = match[6] ? match[6].trim() : ''

      // 跳过表头
      if (dateStr.includes('交易日期') || dateStr.includes('记账日期') ||
          dateStr.includes('Date') || summary.includes('交易摘要')) {
        continue
      }

      // 解析金额
      const amount = parseFloat(amountStr)
      if (isNaN(amount)) {
        continue
      }

      // 构造交易记录
      const transaction = {
        '记账日期': dateStr,
        '交易金额': amountStr,
        '联机余额': balanceStr,
        '交易摘要': summary,
        '对手信息': counterparty,
        '货币': currency
      }

      transactions.push(transaction)

      console.log(`✓ 提取交易: ${dateStr} | ${amountStr} ${currency} | ${summary} | ${counterparty}`)
    } catch (error) {
      console.warn('⚠️ 跳过无效记录:', match[0], error.message)
    }
  }

  console.log(`✅ 最终提取有效交易记录: ${transactions.length} 条`)

  return transactions
}

/**
 * 辅助函数 - 从文本中提取特定字段
 * @param {string} text - 完整文本
 * @param {string} fieldName - 字段名称
 * @returns {string|null} - 字段值
 */
function extractField(text, fieldName) {
  const pattern = new RegExp(`${fieldName}\\s*[:：]?\\s*([^\\n]+)`)
  const match = text.match(pattern)
  return match ? match[1].trim() : null
}

/**
 * 辅助函数 - 清理和标准化文本
 * @param {string} text - 原始文本
 * @returns {string} - 清理后的文本
 */
function cleanText(text) {
  return text
    .replace(/[\r\n]+/g, ' ')  // 换行符替换为空格
    .replace(/\s+/g, ' ')      // 多个空格替换为单个空格
    .trim()
}
