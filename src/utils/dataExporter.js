const SCHEMA_VERSION = '1.0.0'
const APP_VERSION = import.meta.env.VITE_APP_VERSION || '1.0.0'

/**
 * 导出完整应用数据为 JSON
 */
export async function exportToJSON(transactions, categories, transactionCategories, corrections) {
  const data = {
    schemaVersion: SCHEMA_VERSION,
    appVersion: APP_VERSION,
    exportedAt: new Date().toISOString(),
    data: {
      transactions,
      categories,
      transactionCategories, // 对象映射(业务层格式)
      corrections
    }
  }

  // 计算校验和(防止文件损坏)
  const checksum = await calculateChecksum(JSON.stringify(data.data))
  data.checksum = checksum

  return data
}

/**
 * 计算数据的 SHA-256 校验和
 * 用途: 防止文件损坏/误改,不用于防篡改
 */
async function calculateChecksum(dataString) {
  const encoder = new TextEncoder()
  const dataBuffer = encoder.encode(dataString)
  const hashBuffer = await crypto.subtle.digest('SHA-256', dataBuffer)
  const hashArray = Array.from(new Uint8Array(hashBuffer))
  return hashArray.map(b => b.toString(16).padStart(2, '0')).join('')
}

/**
 * 验证校验和
 */
export async function verifyChecksum(exportData) {
  if (!exportData.checksum || !exportData.data) {
    return { valid: false, message: '数据格式不完整' }
  }

  const calculatedChecksum = await calculateChecksum(JSON.stringify(exportData.data))
  if (calculatedChecksum !== exportData.checksum) {
    return { valid: false, message: '校验和失败,文件可能已损坏' }
  }

  return { valid: true, message: '校验通过' }
}

/**
 * 导出为 CSV(仅交易数据)
 */
export function exportToCSV(transactions) {
  const headers = ['交易时间', '平台', '类型', '交易对方', '描述', '金额', '分类']
  const rows = transactions.map(t => [
    new Date(t.transactionTime).toLocaleString('zh-CN'),
    t.platform === 'alipay' ? '支付宝' : t.platform === 'wechat' ? '微信支付' : t.bankName || '银行',
    t.transactionType === 'income' ? '收入' : '支出',
    t.counterparty || '',
    t.description || '',
    t.amount,
    t.category || '未分类'
  ])

  return [headers, ...rows]
    .map(row => row.map(cell => `"${cell}"`).join(','))
    .join('\n')
}
