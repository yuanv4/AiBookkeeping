/**
 * 本地存储工具
 * 使用 localStorage 存储配置和小数据
 */
export const storage = {
  /**
   * 保存数据到 localStorage
   * @param {string} key - 存储键名
   * @param {*} value - 要存储的值（会自动序列化）
   */
  set(key, value) {
    try {
      localStorage.setItem(key, JSON.stringify(value))
    } catch (error) {
      console.error(`存储失败 [${key}]:`, error)
    }
  },

  /**
   * 从 localStorage 获取数据
   * @param {string} key - 存储键名
   * @param {*} defaultValue - 默认值
   * @returns {*} 存储的值或默认值
   */
  get(key, defaultValue = null) {
    try {
      const item = localStorage.getItem(key)
      return item ? JSON.parse(item) : defaultValue
    } catch (error) {
      console.error(`读取失败 [${key}]:`, error)
      return defaultValue
    }
  },

  /**
   * 从 localStorage 删除数据
   * @param {string} key - 存储键名
   */
  remove(key) {
    try {
      localStorage.removeItem(key)
    } catch (error) {
      console.error(`删除失败 [${key}]:`, error)
    }
  },

  /**
   * 清空所有数据
   */
  clear() {
    try {
      localStorage.clear()
    } catch (error) {
      console.error('清空失败:', error)
    }
  }
}

/**
 * 存储键名常量
 */
export const STORAGE_KEYS = {
  CATEGORIES: 'categories',
  TRANSACTION_CATEGORIES: 'transaction_categories',
  CORRECTIONS: 'corrections',
  AI_CONFIG: 'ai_config'
}
