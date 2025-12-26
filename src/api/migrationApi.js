/**
 * 迁移 API 客户端
 * 用于将前端本地数据迁移到后端数据库
 */
import apiClient from './apiClient.js'

export const migrationApi = {
  /**
   * 将前端导出的数据导入到后端
   * @param {Object} exportData - 前端导出的数据(包含 schemaVersion, checksum, data)
   * @returns {Promise<Object>} - 导入结果统计
   */
  async importData(exportData) {
    const response = await apiClient.post('/migration/import', { exportData })
    return response.data
  },

  /**
   * 验证后端数据统计
   * 用于核对前端数据是否成功导入
   * @returns {Promise<Object>} - 后端数据统计信息
   */
  async verify() {
    const response = await apiClient.get('/migration/verify')
    return response.data
  }
}
