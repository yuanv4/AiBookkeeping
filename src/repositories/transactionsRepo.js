import { db } from '../utils/indexedDB.js'

/**
 * 交易数据 Repository
 * 统一交易数据的 CRUD 操作
 */
export const transactionsRepo = {
  /**
   * 获取所有交易
   */
  async getAll() {
    return await db.transactions.toArray()
  },

  /**
   * 批量添加交易(存在则覆盖,不存在则添加)
   */
  async bulkAdd(transactions) {
    return await db.transactions.bulkPut(transactions)
  },

  /**
   * 清空所有交易
   */
  async clear() {
    return await db.transactions.clear()
  },

  /**
   * 统计交易数量
   */
  async count() {
    return await db.transactions.count()
  },

  /**
   * 按月查询交易
   */
  async queryByMonth(year, month) {
    const startDate = new Date(year, month - 1, 1).toISOString()
    const endDate = new Date(year, month, 0, 23, 59, 59).toISOString()

    return await db.transactions
      .where('transactionTime')
      .between(startDate, endDate)
      .toArray()
  },

  /**
   * 按平台查询交易
   */
  async queryByPlatform(platform) {
    return await db.transactions
      .where('platform')
      .equals(platform)
      .toArray()
  }
}
