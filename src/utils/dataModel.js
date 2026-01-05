/**
 * 统一账单数据模型
 * 将各平台账单字段映射到统一格式
 */

// 统一账单数据结构
export const UNIFIED_TRANSACTION_SCHEMA = {
  // 基础信息
  transactionId: 'string',         // 唯一标识（主键）
  platform: 'string',              // 平台: alipay/wechat/bank
  bankName: 'string',              // 银行名称（仅银行账单）
  originalData: 'object',          // 原始数据

  // 交易信息
  transactionTime: 'string',       // 交易时间 ISO格式
  transactionType: 'string',       // 交易类型: income/expense/transfer
  amount: 'number',                // 金额（负数表示支出）
  fee: 'number',                   // 手续费

  // 交易对方
  counterparty: 'string',          // 交易对方/商户名称
  category: 'string',              // 分类
  description: 'string',           // 商品/服务描述/摘要

  // 支付信息
  paymentMethod: 'string',         // 支付方式
  account: 'string',               // 账户信息

  // 状态
  status: 'string',                // 交易状态

  // 订单信息
  merchantOrderId: 'string',       // 商户单号
  remark: 'string'                 // 备注
}

/**
 * 支付宝字段映射
 */
export const ALIPAY_FIELD_MAPPING = {
  '交易时间': 'transactionTime',
  '交易分类': 'category',
  '交易对方': 'counterparty',
  '商品说明': 'description',
  // '收/支': 'incomeExpense', // 不在 schema 中,仅用于计算 transactionType
  '金额': 'amount',
  '收/付款方式': 'paymentMethod',
  '交易状态': 'status',
  '交易订单号': 'transactionId',
  '商家订单号': 'merchantOrderId',
  '备注': 'remark',
  '对方账号': 'account'
}

/**
 * 微信支付字段映射
 */
export const WECHAT_FIELD_MAPPING = {
  '交易时间': 'transactionTime',
  '交易类型': 'category',
  '交易对方': 'counterparty',
  '商品': 'description',
  // '收/支': 'incomeExpense', // 不在 schema 中,仅用于计算 transactionType
  '金额(元)': 'amount',
  '支付方式': 'paymentMethod',
  '当前状态': 'status',
  '交易单号': 'transactionId',
  '商户单号': 'merchantOrderId',
  '备注': 'remark'
}

/**
 * 建设银行字段映射
 */
export const CCB_FIELD_MAPPING = {
  '交易日期': 'transactionDate',
  '摘要': 'description',
  '交易金额': 'amount',
  '账户余额': 'balance',
  '交易地点': 'location',
  '对方账号与户名': 'counterparty'
}

/**
 * 招商银行字段映射
 */
export const CMB_FIELD_MAPPING = {
  '记账日期': 'transactionDate',
  '货币': 'currency',
  '交易金额': 'amount',
  '联机余额': 'balance',
  '交易摘要': 'description',
  '对手信息': 'counterparty'
}

/**
 * 生成唯一交易ID（transactionId）
 * 格式: platform_原始单号_时间戳_random
 */
export function generateTransactionId(platform, merchantTransactionId, time) {
  const hash = merchantTransactionId || time || Date.now()
  return `${platform}_${hash}_${Math.random().toString(36).substr(2, 9)}`
}

/**
 * 解析交易时间
 * 支持多种时间格式
 */
export function parseTransactionTime(timeStr) {
  if (!timeStr) return null

  // 标准格式: 2025-12-24 09:43:58
  const standardFormat = /(\d{4})-(\d{2})-(\d{2})\s+(\d{2}):(\d{2}):(\d{2})/
  const match = timeStr.match(standardFormat)
  if (match) {
    const [, year, month, day, hour, minute, second] = match
    return new Date(year, month - 1, day, hour, minute, second).toISOString()
  }

  // 紧凑格式: 20250113
  const compactFormat = /(\d{4})(\d{2})(\d{2})/
  const compactMatch = timeStr.match(compactFormat)
  if (compactMatch) {
    const [, year, month, day] = compactMatch
    return new Date(year, month - 1, day).toISOString()
  }

  // 尝试直接解析
  const date = new Date(timeStr)
  if (!isNaN(date.getTime())) {
    return date.toISOString()
  }

  return null
}

/**
 * 解析收支类型
 */
export function parseIncomeExpense(value) {
  if (!value) return 'unknown'

  const val = value.toLowerCase().trim()

  // 收入
  if (val === '收' || val === '收入' || val === 'income' || val === '电子汇入' || val === '代发工资' || val === '快捷退款') {
    return 'income'
  }

  // 支出
  if (val === '支' || val === '支出' || val === 'expense') {
    return 'expense'
  }

  // 根据金额判断（银行账单通常没有明确的收/支字段）
  return 'unknown'
}

/**
 * 解析金额
 * 负数表示支出，正数表示收入
 */
export function parseAmount(value, incomeExpense = null) {
  if (typeof value === 'number') return value
  if (typeof value === 'string') {
    // 移除货币符号、逗号和空格
    const cleaned = value.replace(/[¥￥$,，\s]/g, '').trim()
    const num = parseFloat(cleaned)
    if (!isNaN(num)) {
      // 如果有明确的收支类型，转换正负号
      const type = parseIncomeExpense(incomeExpense)
      if (type === 'expense' && num > 0) {
        return -num
      }
      if (type === 'income' && num < 0) {
        return Math.abs(num)
      }
      return num
    }
  }
  return 0
}

/**
 * 映射支付宝账单到统一格式
 */
export function mapAlipayTransaction(raw) {
  const mapped = {}

  for (const [sourceField, targetField] of Object.entries(ALIPAY_FIELD_MAPPING)) {
    if (raw[sourceField] !== undefined) {
      mapped[targetField] = raw[sourceField]
    }
  }

  // 特殊处理
  const incomeExpense = raw['收/支'] || raw['收支']
  mapped.transactionType = parseIncomeExpense(incomeExpense)
  mapped.amount = parseAmount(raw['金额'], incomeExpense)
  mapped.transactionTime = parseTransactionTime(raw['交易时间'])
  mapped.platform = 'alipay'
  mapped.transactionId = generateTransactionId('alipay', raw['交易订单号'] || '', raw['交易时间'])
  mapped.originalData = raw

  return mapped
}

/**
 * 映射微信账单到统一格式
 */
export function mapWechatTransaction(raw) {
  const mapped = {}

  for (const [sourceField, targetField] of Object.entries(WECHAT_FIELD_MAPPING)) {
    if (raw[sourceField] !== undefined) {
      mapped[targetField] = raw[sourceField]
    }
  }

  // 特殊处理
  const incomeExpense = raw['收/支']
  mapped.transactionType = parseIncomeExpense(incomeExpense)
  mapped.amount = parseAmount(raw['金额(元)'], incomeExpense)
  mapped.transactionTime = parseTransactionTime(raw['交易时间'])
  mapped.platform = 'wechat'
  mapped.transactionId = generateTransactionId('wechat', raw['交易单号'] || '', raw['交易时间'])
  mapped.originalData = raw

  return mapped
}

/**
 * 映射建设银行账单到统一格式
 */
export function mapCCBTransaction(raw) {
  const mapped = {
    transactionType: 'unknown',
    status: 'completed'
  }

  // 解析金额（负数为支出，正数为收入）
  const amount = parseAmount(raw['交易金额'])
  mapped.amount = amount
  mapped.transactionType = amount >= 0 ? 'income' : 'expense'

  // 映射其他字段
  mapped.description = raw['摘要'] || ''
  mapped.counterparty = raw['对方账号与户名'] || ''
  mapped.transactionTime = parseTransactionTime(raw['交易日期'])
  // balance 和 location 不在数据库 schema 中,保持在 originalData 中即可
  // mapped.balance = parseAmount(raw['账户余额'])
  // mapped.location = raw['交易地点/附言'] || ''

  mapped.platform = 'bank'
  mapped.bankName = '建设银行'
  mapped.transactionId = generateTransactionId('ccb', raw['序号'] || '', raw['交易日期'])
  mapped.originalData = raw

  return mapped
}

/**
 * 映射招商银行账单到统一格式
 */
export function mapCMBTransaction(raw) {
  const mapped = {
    transactionType: 'unknown',
    status: 'completed'
  }

  // 解析金额（负数为支出，正数为收入）
  const amount = parseAmount(raw['交易金额'])
  mapped.amount = amount
  mapped.transactionType = amount >= 0 ? 'income' : 'expense'

  // 映射其他字段
  mapped.description = raw['交易摘要'] || ''
  mapped.counterparty = raw['对手信息'] || ''
  mapped.transactionTime = parseTransactionTime(raw['记账日期'])
  // balance 和 currency 不在数据库 schema 中,保持在 originalData 中即可
  // mapped.balance = parseAmount(raw['联机余额'])
  // mapped.currency = raw['货币'] || 'CNY'

  mapped.platform = 'bank'
  mapped.bankName = '招商银行'
  mapped.transactionId = generateTransactionId('cmb', raw['记账日期'] + raw['交易金额'], raw['记账日期'])
  mapped.originalData = raw

  return mapped
}

/**
 * 映射银行账单到统一格式（根据银行类型）
 */
export function mapBankTransaction(raw, bankName) {
  const bankMappers = {
    '建设银行': mapCCBTransaction,
    'ccb': mapCCBTransaction,
    '招商银行': mapCMBTransaction,
    'cmb': mapCMBTransaction
  }

  // 优先使用银行名称匹配,否则使用代码匹配
  const mapper = bankMappers[bankName] || bankMappers[bankName.toLowerCase()] || mapCCBTransaction
  const result = mapper(raw)
  result.bankName = bankName
  return result
}

/**
 * 批量映射账单
 */
export function mapTransactions(rawDataList, platform, bankName = '') {
  const mappers = {
    alipay: (raw) => mapAlipayTransaction(raw),
    wechat: (raw) => mapWechatTransaction(raw),
    bank: (raw) => mapBankTransaction(raw, bankName)
  }

  const mapper = mappers[platform]
  if (!mapper) {
    throw new Error(`不支持的平台: ${platform}`)
  }

  return rawDataList.map(raw => mapper(raw))
}

/**
 * 合并多个平台的账单
 */
export function mergeTransactions(transactionGroups) {
  const all = []

  for (const group of transactionGroups) {
    if (Array.isArray(group)) {
      all.push(...group)
    }
  }

  // 按时间排序
  all.sort((a, b) => {
    const timeA = new Date(a.transactionTime || 0).getTime()
    const timeB = new Date(b.transactionTime || 0).getTime()
    return timeB - timeA
  })

  return all
}

/**
 * 去重（基于交易单号和时间）
 */
export function deduplicateTransactions(transactions) {
  const seen = new Set()
  const unique = []

  for (const tx of transactions) {
    // 生成去重键：平台+交易单号 或 平台+时间+金额
    const key = tx.transactionId
      ? `${tx.platform}_${tx.transactionId}`
      : `${tx.platform}_${tx.transactionTime}_${tx.amount}`

    if (!seen.has(key)) {
      seen.add(key)
      unique.push(tx)
    }
  }

  return unique
}

/**
 * 跨平台去重：移除银行流水中与支付宝/微信重复的交易
 * 匹配条件：金额相同 + 时间差<=1天 + (关键词匹配 或 商户名匹配)
 */
export function crossPlatformDeduplication(transactions) {
  const KEYWORDS = ['支付宝', '财付通', '微信']
  const TIME_TOLERANCE = 24 * 60 * 60 * 1000 // 1天（银行记账可能有延迟）

  const paymentTxs = transactions.filter(t => t.platform === 'alipay' || t.platform === 'wechat')
  const bankTxs = transactions.filter(t => t.platform === 'bank')
  const duplicateIds = new Set()

  console.log(`🔍 跨平台去重检测: 支付平台 ${paymentTxs.length} 条, 银行流水 ${bankTxs.length} 条`)

  for (const bankTx of bankTxs) {
    const bankDesc = (bankTx.description || '') + (bankTx.counterparty || '')
    const isQuickPay = bankDesc.includes('快捷支付') || bankDesc.includes('银联快捷')
    const hasPaymentKeyword = KEYWORDS.some(k => bankDesc.includes(k))

    // 检查是否有匹配的支付平台交易
    const match = paymentTxs.find(payTx => {
      // 条件1：金额匹配（容差 0.01）
      const amountMatch = Math.abs(Math.abs(payTx.amount) - Math.abs(bankTx.amount)) < 0.01
      if (!amountMatch) return false

      // 条件2：时间接近
      const timeMatch = Math.abs(new Date(payTx.transactionTime) - new Date(bankTx.transactionTime)) <= TIME_TOLERANCE
      if (!timeMatch) return false

      // 条件3a：银行描述含支付平台关键词（如"支付宝消费"）
      if (hasPaymentKeyword) return true

      // 条件3b：快捷支付类型 + 商户名匹配
      if (isQuickPay && bankTx.counterparty && payTx.counterparty) {
        const bankMerchant = bankTx.counterparty.toLowerCase()
        const payMerchant = payTx.counterparty.toLowerCase()
        // 商户名部分匹配（任一包含另一个）
        if (bankMerchant.includes(payMerchant) || payMerchant.includes(bankMerchant)) {
          return true
        }
      }

      return false
    })

    if (match) {
      duplicateIds.add(bankTx.transactionId)
      console.log(`  ✓ 发现重复: 银行[${bankTx.counterparty}] ¥${bankTx.amount} ↔ ${match.platform}[${match.counterparty}] ¥${match.amount}`)
    }
  }

  const result = transactions.filter(t => !duplicateIds.has(t.transactionId))
  console.log(`🔄 跨平台去重完成: 移除 ${duplicateIds.size} 条重复的银行流水`)
  return result
}
