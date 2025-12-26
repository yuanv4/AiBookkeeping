import apiClient from './apiClient.js'

/**
 * 配置相关 API
 */
export const configApi = {
  /**
   * 获取指定配置
   * @param {string} key - 配置键
   * @returns {Promise<{key: string, value: any}>}
   */
  async get(key) {
    const response = await apiClient.get(`/config/${key}`)
    return response.data
  },

  /**
   * 设置配置
   * @param {string} key - 配置键
   * @param {any} value - 配置值
   * @returns {Promise<{key: string, value: any}>}
   */
  async set(key, value) {
    const response = await apiClient.put(`/config/${key}`, { value })
    return response.data
  },

  /**
   * 删除指定配置
   * @param {string} key - 配置键
   * @returns {Promise<{success: boolean, message: string}>}
   */
  async remove(key) {
    const response = await apiClient.delete(`/config/${key}`)
    return response.data
  },

  /**
   * 清空当前用户的所有配置
   * @returns {Promise<{success: boolean, message: string}>}
   */
  async clear() {
    const response = await apiClient.delete('/config/')
    return response.data
  }
}
