import { db } from './indexedDB.js'
import { exportToJSON, verifyChecksum } from './dataExporter.js'

/**
 * 创建完整备份
 */
export async function createBackup() {
  const transactions = await db.transactions.toArray()
  const categories = await db.categories.toArray()
  const transactionCategories = await db.transaction_categories.toArray()
  const corrections = await db.corrections.toArray()
  const aiConfig = await db.app_config.get('ai_config')

  const backupData = {
    schemaVersion: '1.0.0',
    appVersion: import.meta.env.VITE_APP_VERSION || '1.0.0',
    createdAt: new Date().toISOString(),
    data: {
      transactions,
      categories,
      transactionCategories,
      corrections,
      aiConfig: {
        ...aiConfig,
        apiKey: aiConfig?.apiKey ? '******' : ''
      }
    }
  }

  // 计算校验和
  const checksum = await calculateChecksum(JSON.stringify(backupData.data))
  backupData.checksum = checksum

  return backupData
}

/**
 * 保存备份到 IndexedDB
 */
export async function saveBackup(backupData) {
  const backupId = await db.backups.add({
    timestamp: Date.now(),
    data: backupData
  })

  // 保留最近 10 个备份
  const allBackups = await db.backups.orderBy('timestamp').reverse().toArray()
  if (allBackups.length > 10) {
    const toDelete = allBackups.slice(10)
    await db.backups.bulkDelete(toDelete.map(b => b.id))
  }

  return backupId
}

/**
 * 从备份恢复
 */
export async function restoreBackup(backupData, onProgress) {
  let currentSnapshot = null

  try {
    onProgress?.({ step: 1, message: '验证备份完整性...' })

    // 验证校验和
    const verification = await verifyChecksum(backupData)
    if (!verification.valid) {
      throw new Error(verification.message)
    }

    onProgress?.({ step: 2, message: '创建当前状态快照...' })

    // 创建当前状态快照(用于回滚)
    currentSnapshot = await createBackup()

    onProgress?.({ step: 3, message: '清空现有数据...' })

    // 清空现有数据
    await db.transactions.clear()
    await db.categories.clear()
    await db.transaction_categories.clear()
    await db.corrections.clear()

    onProgress?.({ step: 4, message: '恢复交易记录...' })

    // 恢复数据(使用无副用的 applyBackupToDb 函数,避免递归)
    await applyBackupToDb(backupData.data)

    onProgress?.({ step: 5, message: '恢复完成!' })

    return {
      success: true,
      rollbackSnapshot: currentSnapshot
    }
  } catch (error) {
    // 恢复失败,尝试回滚
    console.error('恢复失败,正在回滚...', error)
    try {
      if (currentSnapshot) {
        await applyBackupToDb(currentSnapshot.data)
      }
    } catch (rollbackError) {
      console.error('回滚也失败了:', rollbackError)
      throw new Error(`恢复失败且回滚失败: ${error.message}`)
    }
    throw error
  }
}

/**
 * 将备份数据应用到数据库(无副作用,不创建快照)
 * 抽取此函数避免 restoreBackup 递归调用
 */
async function applyBackupToDb(data) {
  // 清空现有数据
  await db.transactions.clear()
  await db.categories.clear()
  await db.transaction_categories.clear()
  await db.corrections.clear()

  // 写入备份数据
  await db.transactions.bulkPut(data.transactions || [])
  await db.categories.bulkPut(data.categories || [])

  // transactionCategories: 对象映射 → 数组行
  const txCategoriesRows = Object.entries(data.transactionCategories || {}).map(([txId, categoryData]) => ({
    transactionId: txId,
    ...categoryData
  }))
  await db.transaction_categories.bulkPut(txCategoriesRows)

  await db.corrections.bulkPut(data.corrections || [])
  await db.app_config.put({ key: 'ai_config', value: data.aiConfig })
}

/**
 * 获取备份列表
 */
export async function getBackupList() {
  const backups = await db.backups.orderBy('timestamp').reverse().toArray()
  return backups.map(backup => ({
    id: backup.id,
    timestamp: backup.timestamp,
    formattedTime: new Date(backup.timestamp).toLocaleString('zh-CN'),
    size: JSON.stringify(backup.data).length
  }))
}

/**
 * 删除备份
 */
export async function deleteBackup(backupId) {
  await db.backups.delete(backupId)
}

async function calculateChecksum(dataString) {
  const encoder = new TextEncoder()
  const dataBuffer = encoder.encode(dataString)
  const hashBuffer = await crypto.subtle.digest('SHA-256', dataBuffer)
  const hashArray = Array.from(new Uint8Array(hashBuffer))
  return hashArray.map(b => b.toString(16).padStart(2, '0')).join('')
}
