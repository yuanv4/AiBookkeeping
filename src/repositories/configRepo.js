import { db } from '../utils/indexedDB.js'

/**
 * 应用配置 Repository
 * 统一配置数据的 CRUD 操作
 */
export const configRepo = {
  /**
   * 获取配置项
   */
  async get(key) {
    const result = await db.app_config.get(key)
    return result ? result.value : null
  },

  /**
   * 设置配置项
   */
  async set(key, value) {
    await db.app_config.put({ key, value })
  },

  /**
   * 删除配置项
   */
  async remove(key) {
    await db.app_config.delete(key)
  },

  /**
   * 清空所有配置
   */
  async clear() {
    await db.app_config.clear()
  }
}
