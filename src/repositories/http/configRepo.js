import { configApi } from '../../api/index.js'

/**
 * 应用配置 HTTP Repository
 * 对齐本地 configRepo 接口，通过 HTTP 访问后端
 */
export const configRepo = {
  /**
   * 获取配置项
   */
  async get(key) {
    try {
      const result = await configApi.get(key)
      return result.value
    } catch (error) {
      // 404 错误返回 null
      if (error.message?.includes('不存在')) {
        return null
      }
      throw error
    }
  },

  /**
   * 设置配置项
   */
  async set(key, value) {
    const result = await configApi.set(key, value)
    return result.value
  },

  /**
   * 删除配置项
   */
  async remove(key) {
    return await configApi.remove(key)
  },

  /**
   * 清空所有配置
   */
  async clear() {
    return await configApi.clear()
  }
}
