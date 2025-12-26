import apiClient from './apiClient.js'

/**
 * 交易相关 API
 */
export const transactionsApi = {
  /**
   * 获取所有交易
   * @returns {Promise<Array>}
   */
  async getAll() {
    const response = await apiClient.get('/transactions')
    return response.data
  },

  /**
   * 批量 upsert 交易（幂等）
   * @param {Array} transactions - 交易数组
   * @returns {Promise<{success: boolean, count: number}>}
   */
  async batchUpsert(transactions) {
    const response = await apiClient.post('/transactions/batch-upsert', {
      transactions
    })
    return response.data
  },

  /**
   * 清空所有交易
   * @returns {Promise<{success: boolean, message: string}>}
   */
  async clear() {
    const response = await apiClient.delete('/transactions')
    return response.data
  },

  /**
   * 按月查询交易
   * @param {number} year - 年份
   * @param {number} month - 月份 (1-12)
   * @returns {Promise<{year: number, month: number, count: number, transactions: Array}>}
   */
  async queryByMonth(year, month) {
    const response = await apiClient.get(`/transactions/month/${year}/${month}`)
    return response.data
  },

  /**
   * 按平台查询交易
   * @param {string} platform - 平台名称 ('alipay' | 'wechat' | 'bank')
   * @returns {Promise<{platform: string, count: number, transactions: Array}>}
   */
  async queryByPlatform(platform) {
    const response = await apiClient.get(`/transactions/platform/${platform}`)
    return response.data
  }
}
