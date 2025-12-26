import { transactionsApi } from '../../api/index.js'

/**
 * 交易数据 HTTP Repository
 * 对齐本地 transactionsRepo 接口，通过 HTTP 访问后端
 */
export const transactionsRepo = {
  /**
   * 获取所有交易
   */
  async getAll() {
    return await transactionsApi.getAll()
  },

  /**
   * 批量添加交易(存在则覆盖,不存在则添加)
   * 注意: 后端接口是 batch-upsert
   */
  async bulkAdd(transactions) {
    return await transactionsApi.batchUpsert(transactions)
  },

  /**
   * 清空所有交易
   */
  async clear() {
    return await transactionsApi.clear()
  },

  /**
   * 统计交易数量
   */
  async count() {
    const transactions = await this.getAll()
    return transactions.length
  },

  /**
   * 按月查询交易
   */
  async queryByMonth(year, month) {
    const result = await transactionsApi.queryByMonth(year, month)
    return result.transactions
  },

  /**
   * 按平台查询交易
   */
  async queryByPlatform(platform) {
    const result = await transactionsApi.queryByPlatform(platform)
    return result.transactions
  }
}
