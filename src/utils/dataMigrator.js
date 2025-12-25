import { storage } from './storage.js'
import { db } from './indexedDB.js'
import { transactionsRepo, categoriesRepo, transactionCategoriesRepo, correctionsRepo, configRepo } from '../repositories/index.js'

/**
 * 迁移状态枚举
 */
export const MigrationState = {
  NOT_STARTED: 'NOT_STARTED',
  IN_PROGRESS: 'IN_PROGRESS',
  COMPLETED: 'COMPLETED',
  FAILED: 'FAILED',
  ROLLED_BACK: 'ROLLED_BACK'
}

/**
 * 检测是否需要迁移
 */
export async function shouldMigrate() {
  const localStorageHasData = localStorage.getItem('transactions') ||
                              localStorage.getItem('categories')
  const indexedDBIsEmpty = await db.transactions.count() === 0

  return localStorageHasData && indexedDBIsEmpty
}

/**
 * 获取迁移状态
 */
export async function getMigrationState() {
  const state = await db.migration_state.get('localStorage_to_indexedDB')
  return state || { status: MigrationState.NOT_STARTED }
}

/**
 * 执行迁移
 * @param {Function} onProgress - 进度回调 { step, current, total, message }
 */
export async function migrateToIndexedDB(onProgress) {
  try {
    // 1. 记录迁移状态
    await db.migration_state.put({
      key: 'localStorage_to_indexedDB',
      status: MigrationState.IN_PROGRESS,
      startedAt: Date.now()
    })

    onProgress?.({ step: 1, current: 0, total: 5, message: '读取旧数据...' })

    // 2. 读取 localStorage 数据
    const oldData = {
      transactions: storage.get('transactions', []),
      categories: storage.get('categories', []),
      transactionCategories: storage.get('transaction_categories', {}),
      corrections: storage.get('corrections', []),
      aiConfig: storage.get('ai_config', {})
    }

    onProgress?.({ step: 2, current: 1, total: 5, message: `迁移交易记录 (${oldData.transactions.length} 条)...` })

    // 3. 迁移交易记录
    await db.transactions.bulkPut(oldData.transactions)

    onProgress?.({ step: 3, current: 2, total: 5, message: '迁移分类数据...' })

    // 4. 迁移分类
    await db.categories.bulkPut(oldData.categories)

    // 5. 迁移交易分类映射(对象 → 数组行)
    const txCategoriesData = Object.entries(oldData.transactionCategories).map(([txId, data]) => ({
      transactionId: txId,
      ...data
    }))
    await db.transaction_categories.bulkPut(txCategoriesData)

    onProgress?.({ step: 4, current: 3, total: 5, message: '迁移纠正历史...' })

    // 6. 迁移纠正历史
    await db.corrections.bulkPut(oldData.corrections)

    // 7. 迁移配置
    await configRepo.set('ai_config', oldData.aiConfig)

    onProgress?.({ step: 5, current: 4, total: 5, message: '验证迁移结果...' })

    // 8. 验证迁移结果(数量 + 抽样校验)
    const txCount = await db.transactions.count()
    if (txCount !== oldData.transactions.length) {
      throw new Error(`迁移验证失败: 交易数量不匹配 (预期 ${oldData.transactions.length}, 实际 ${txCount})`)
    }

    const categoryCount = await db.categories.count()
    if (categoryCount !== oldData.categories.length) {
      throw new Error(`迁移验证失败: 分类数量不匹配 (预期 ${oldData.categories.length}, 实际 ${categoryCount})`)
    }

    // 抽样校验: 随机取 5 条记录检查关键字段
    const sampleSize = Math.min(5, oldData.transactions.length)
    for (let i = 0; i < sampleSize; i++) {
      const idx = Math.floor(Math.random() * oldData.transactions.length)
      const oldTx = oldData.transactions[idx]
      const newTx = await db.transactions.get(oldTx.transactionId)
      if (!newTx) {
        throw new Error(`迁移验证失败: 交易 ${oldTx.transactionId} 未找到`)
      }
      if (newTx.amount !== oldTx.amount || newTx.transactionTime !== oldTx.transactionTime) {
        throw new Error(`迁移验证失败: 交易 ${oldTx.transactionId} 字段不一致`)
      }
    }

    onProgress?.({ step: 5, current: 5, total: 5, message: '迁移完成!' })

    // 9. 记录迁移成功
    await db.migration_state.update('localStorage_to_indexedDB', {
      status: MigrationState.COMPLETED,
      completedAt: Date.now(),
      migratedCounts: {
        transactions: txCount,
        categories: categoryCount,
        transactionCategories: txCategoriesData.length,
        corrections: oldData.corrections.length
      }
    })

    // 10. 创建 localStorage 备份(不清除旧数据)
    await db.backups.add({
      timestamp: Date.now(),
      source: 'localStorage',
      data: oldData
    })

    return {
      success: true,
      migratedCounts: {
        transactions: txCount,
        categories: categoryCount,
        transactionCategories: txCategoriesData.length,
        corrections: oldData.corrections.length
      }
    }

  } catch (error) {
    console.error('迁移失败:', error)

    // 记录失败状态
    await db.migration_state.update('localStorage_to_indexedDB', {
      status: MigrationState.FAILED,
      failedAt: Date.now(),
      error: error.message
    })

    throw error
  }
}

/**
 * 回滚迁移(从 IndexedDB 恢复到 localStorage)
 */
export async function rollbackMigration() {
  try {
    const backup = await db.backups
      .where('source')
      .equals('localStorage')
      .last()

    if (!backup) {
      throw new Error('未找到备份,无法回滚')
    }

    // 恢复到 localStorage
    storage.set('transactions', backup.data.transactions)
    storage.set('categories', backup.data.categories)
    storage.set('transaction_categories', backup.data.transactionCategories)
    storage.set('corrections', backup.data.corrections)
    storage.set('ai_config', backup.data.aiConfig)

    // 记录回滚状态
    await db.migration_state.update('localStorage_to_indexedDB', {
      status: MigrationState.ROLLED_BACK,
      rolledBackAt: Date.now()
    })

    return { success: true }
  } catch (error) {
    console.error('回滚失败:', error)
    throw error
  }
}

/**
 * 清除 localStorage 旧数据(用户确认后)
 */
export async function clearLocalStorageAfterMigration() {
  const state = await getMigrationState()
  if (state.status !== MigrationState.COMPLETED) {
    throw new Error('迁移未完成,不能清除旧数据')
  }

  storage.clearAppData()
  return { success: true }
}
