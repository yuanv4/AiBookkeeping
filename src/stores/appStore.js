import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import * as XLSX from 'xlsx'
import Papa from 'papaparse'
import {
  mapTransactions,
  mergeTransactions,
  deduplicateTransactions
} from '../utils/dataModel.js'
import { useCategoryStore } from './categoryStore.js'
import { transactionsRepo, configRepo } from '../repositories/index.js'
import { errorHandler } from '../utils/errorHandler.js'
import { useNotificationStore } from './notificationStore.js'

export const useAppStore = defineStore('app', () => {
  // 状态
  const files = ref([])
  const transactions = ref([])
  const processing = ref(false)
  const dragging = ref(false)

  // 统计信息
  const statistics = computed(() => {
    const total = transactions.value.length
    const income = transactions.value
      .filter(t => t.amount > 0)
      .reduce((sum, t) => sum + t.amount, 0)
    const expense = transactions.value
      .filter(t => t.amount < 0)
      .reduce((sum, t) => sum + t.amount, 0)

    return {
      total,
      income,
      expense,
      net: income + expense
    }
  })

  // 是否有数据
  const hasData = computed(() => transactions.value.length > 0)

  // 添加文件
  function addFiles(newFiles) {
    newFiles.forEach(file => {
      const id = Date.now() + Math.random().toString(36).substr(2, 9)
      const platform = detectPlatform(file)
      files.value.push({
        id,
        platform,
        name: file.name,
        size: file.size,
        type: file.type,
        lastModified: file.lastModified,
        raw: file
      })
    })
  }

  // 删除文件
  function removeFile(id) {
    files.value = files.value.filter(f => f.id !== id)
  }

  // 清空文件
  function clearFiles() {
    files.value = []
  }

  // 清空所有数据(需要确认)
  function clearAllData() {
    // 不在 store 里直接清理,而是返回清理指令,由 UI 层处理
    return {
      needConfirm: true,
      message: '清除所有数据将删除所有已上传的文件和解析结果,建议先导出备份。',
      dataTypes: [
        `交易记录 (${transactions.value.length} 条)`,
        `分类数据`,
        `筛选器和偏好设置`
      ]
    }
  }

  // 执行清理(由 UI 调用)
  async function performClearAll() {
    const categoryStore = useCategoryStore()
    const notificationStore = useNotificationStore()

    try {
      files.value = []
      transactions.value = []
      await transactionsRepo.clear()
      await configRepo.clear()
      categoryStore.$reset() // 重置 categoryStore
      notificationStore.show('数据已清除', 'success')
      return { success: true }
    } catch (error) {
      const { message, type } = errorHandler.normalizeStorageError(error)
      notificationStore.show(message, type)
      throw error
    }
  }

  // 检测平台
  function detectPlatform(file) {
    const name = file.name.toLowerCase()

    if (name.includes('支付宝') || name.includes('alipay')) {
      return 'alipay'
    }
    if (name.includes('微信') || name.includes('wechat') || name.includes('weixin')) {
      return 'wechat'
    }
    if (name.includes('建设银行') || name.includes('ccb')) {
      return 'ccb'
    }
    if (name.includes('招商银行') || name.includes('cmb')) {
      return 'cmb'
    }

    // 根据扩展名猜测
    if (name.endsWith('.csv')) return 'alipay'
    if (name.endsWith('.xlsx')) return 'wechat'
    if (name.endsWith('.xls')) return 'bank'
    if (name.endsWith('.pdf')) return 'bank'

    return 'unknown'
  }

  // 获取银行名称
  function getBankName(platform) {
    const names = {
      ccb: '建设银行',
      cmb: '招商银行'
    }
    return names[platform] || '银行'
  }

  // 解析文件
  async function parseFile(file) {
    let platform = file.platform || detectPlatform(file)
    let bankName = ''

    // 将具体的银行代码统一为 'bank'
    if (platform === 'ccb' || platform === 'cmb' || platform === 'bank') {
      bankName = getBankName(platform)
      platform = 'bank'
    }

    // CSV文件（支付宝）
    if (file.name.endsWith('.csv')) {
      return await parseCSV(file, platform)
    }

    // Excel文件（微信、建行）
    if (file.name.endsWith('.xlsx') || file.name.endsWith('.xls')) {
      return await parseExcel(file, platform, bankName)
    }

    // PDF文件（招商银行）
    if (file.name.endsWith('.pdf')) {
      return await parsePDF(file, platform, bankName)
    }

    throw new Error(`不支持的文件格式: ${file.name}`)
  }

  // 解析CSV（支付宝）
  function parseCSV(file, platform) {
    return new Promise((resolve, reject) => {
      Papa.parse(file, {
        encoding: 'GBK', // 支付宝使用GBK编码
        complete: (results) => {
          try {
            // 找到数据开始的行（跳过说明部分）
            const dataStartIndex = results.data.findIndex(row =>
              row[0] && row[0].includes('交易时间')
            )

            if (dataStartIndex === -1) {
              resolve([])
              return
            }

            // 提取列名和数据
            const headers = results.data[dataStartIndex]
            const dataRows = results.data.slice(dataStartIndex + 1)

            // 转换为对象数组
            const objects = dataRows
              .filter(row => row[0] && row[0].match(/\d{4}-\d{2}-\d{2}/))
              .map(row => {
                const obj = {}
                headers.forEach((header, index) => {
                  if (header) obj[header.trim()] = row[index] || ''
                })
                return obj
              })
              .filter(obj => Object.keys(obj).length > 0)

            const mapped = mapTransactions(objects, platform)
            resolve(mapped)
          } catch (error) {
            reject(error)
          }
        },
        error: reject
      })
    })
  }

  // 解析Excel
  function parseExcel(file, platform, bankName = '') {
    return new Promise((resolve, reject) => {
      const reader = new FileReader()

      reader.onload = (e) => {
        try {
          const data = new Uint8Array(e.target.result)
          const workbook = XLSX.read(data, { type: 'array' })
          const sheetName = workbook.SheetNames[0]
          const worksheet = workbook.Sheets[sheetName]

          // 根据不同平台跳过说明行
          let jsonData
          if (platform === 'wechat' || file.name.toLowerCase().includes('微信')) {
            // 微信账单需要跳过前16行说明
            jsonData = XLSX.utils.sheet_to_json(worksheet, { range: 16 })
          } else if (platform === 'bank') {
            // 建设银行等银行账单需要跳过前3行说明
            jsonData = XLSX.utils.sheet_to_json(worksheet, { range: 2 })
          } else {
            jsonData = XLSX.utils.sheet_to_json(worksheet)
          }

          const mapped = mapTransactions(jsonData, platform, bankName)
          resolve(mapped)
        } catch (error) {
          reject(error)
        }
      }

      reader.onerror = reject
      reader.readAsArrayBuffer(file)
    })
  }

  // 解析PDF（招商银行）
  async function parsePDF(file, platform, bankName = '招商银行') {
    try {
      // 使用新的 PDF 解析工具
      const { parseCMBPDF } = await import('../utils/pdfParser.js')
      console.log(`📄 开始解析PDF: ${file.name}`)
      const transactions = await parseCMBPDF(file)
      console.log(`✅ PDF解析完成,提取 ${transactions.length} 条交易记录`)
      return transactions
    } catch (error) {
      console.error('❌ PDF解析失败:', error)
      throw new Error(`PDF解析失败: ${error.message}`)
    }
  }

  // 处理所有文件
  async function processFiles() {
    processing.value = true
    const allTransactions = []

    try {
      for (const file of files.value) {
        const txs = await parseFile(file.raw || file)
        allTransactions.push(...txs)
      }

      // 合并和去重
      const uniqueTransactions = deduplicateTransactions(allTransactions)
      transactions.value = uniqueTransactions

      // 保存到 IndexedDB
      await saveTransactions()
      console.log(`✅ 处理完成，共 ${uniqueTransactions.length} 条交易`)
    } catch (error) {
      console.error('处理文件失败:', error)
      throw error
    } finally {
      processing.value = false
    }
  }

  // 保存交易数据到 IndexedDB
  async function saveTransactions() {
    try {
      await transactionsRepo.bulkAdd(transactions.value)
    } catch (error) {
      const { message, type } = errorHandler.normalizeStorageError(error)
      const notificationStore = useNotificationStore()
      notificationStore.show(message, type)
      throw error
    }
  }

  // 从 IndexedDB 加载交易数据
  async function loadTransactions() {
    try {
      transactions.value = await transactionsRepo.getAll()
    } catch (error) {
      const { message, type } = errorHandler.normalizeStorageError(error)
      const notificationStore = useNotificationStore()
      notificationStore.show(message, type)
      throw error
    }
  }

  return {
    // 状态
    files,
    transactions,
    processing,
    dragging,
    statistics,
    hasData,

    // 方法
    addFiles,
    removeFile,
    clearFiles,
    clearAllData,
    performClearAll,
    detectPlatform,
    parseFile,
    processFiles,
    saveTransactions,
    loadTransactions
  }
})
