import apiClient from './apiClient.js'

/**
 * 分类相关 API
 */
export const categoriesApi = {
  // ============ 分类体系 API (对齐 categoriesRepo) ============

  /**
   * 获取所有分类
   * @returns {Promise<Array>}
   */
  async getAll() {
    const response = await apiClient.get('/categories/')
    return response.data
  },

  /**
   * 全量替换分类（幂等 upsert）
   * @param {Array} categories - 分类数组
   * @returns {Promise<{success: boolean, count: number}>}
   */
  async bulkSet(categories) {
    const response = await apiClient.put('/categories/', { categories })
    return response.data
  },

  /**
   * 批量添加分类（用于兼容旧接口）
   * @param {Array} categories - 分类数组
   * @returns {Promise<{success: boolean, count: number}>}
   */
  async bulkAdd(categories) {
    // 使用 bulkSet 实现
    return this.bulkSet(categories)
  },

  // ============ 交易分类映射 API (对齐 transactionCategoriesRepo) ============

  /**
   * 获取所有交易分类映射（返回对象映射格式）
   * @returns {Promise<{[transactionId]: categoryData}>}
   */
  async getTransactionCategories() {
    const response = await apiClient.get('/categories/transaction-categories')
    return response.data
  },

  /**
   * 更新单个交易的分类
   * @param {string} transactionId - 交易 ID
   * @param {object} categoryData - 分类数据
   * @returns {Promise<object>}
   */
  async updateTransactionCategory(transactionId, categoryData) {
    const response = await apiClient.put(`/categories/transaction-categories/${transactionId}`, categoryData)
    return response.data
  },

  /**
   * 批量 upsert 交易分类映射
   * @param {Array<{transactionId: string, categoryData: object}>} updates - 更新数组
   * @returns {Promise<{success: boolean, count: number}>}
   */
  async batchUpsertTransactionCategories(updates) {
    const response = await apiClient.post('/categories/transaction-categories/batch-upsert', { updates })
    return response.data
  },

  /**
   * 清空交易分类映射
   * @returns {Promise<{success: boolean, message: string}>}
   */
  async clearTransactionCategories() {
    const response = await apiClient.delete('/categories/transaction-categories')
    return response.data
  },

  // ============ 用户纠正历史 API (对齐 correctionsRepo) ============

  /**
   * 获取所有纠正历史
   * @returns {Promise<Array>}
   */
  async getCorrections() {
    const response = await apiClient.get('/categories/corrections')
    return response.data
  },

  /**
   * 添加纠正记录
   * @param {object} correction - 纠正数据
   * @returns {Promise<object>}
   */
  async addCorrection(correction) {
    const response = await apiClient.post('/categories/corrections', correction)
    return response.data
  },

  /**
   * 清空纠正历史
   * @returns {Promise<{success: boolean, message: string}>}
   */
  async clearCorrections() {
    const response = await apiClient.delete('/categories/corrections')
    return response.data
  },

  /**
   * 清空所有分类数据（分类 + 映射 + 纠正）
   * @returns {Promise<{success: boolean, message: string}>}
   */
  async clearAll() {
    const response = await apiClient.delete('/categories/classification')
    return response.data
  }
}
