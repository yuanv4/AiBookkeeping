/**
 * 统一存储工具
 * 应用代码所有存储操作必须通过此工具,禁止直接使用 localStorage
 */

// 错误类型定义
export class StorageError extends Error {
  constructor(message, code) {
    super(message)
    this.code = code
  }
}

export const ERROR_CODES = {
  QUOTA_EXCEEDED: 'QUOTA_EXCEEDED',      // 存储空间不足
  WRITE_FAILED: 'WRITE_FAILED',          // 写入失败
  READ_FAILED: 'READ_FAILED',            // 读取失败
  KEY_NOT_FOUND: 'KEY_NOT_FOUND'         // 键不存在
}

// 存储键名常量(所有键名统一管理)
export const STORAGE_KEYS = {
  TRANSACTIONS: 'transactions',       // 新增!当前代码遗漏
  CATEGORIES: 'categories',
  TRANSACTION_CATEGORIES: 'transaction_categories',
  CORRECTIONS: 'corrections',
  FILTERS: 'filters',                 // 预留
  PREFERENCES: 'preferences'          // 预留
}

export const storage = {
  /**
   * 获取存储空间信息(估算值)
   * 注意: 不同浏览器配额不同,不写死总容量
   */
  getStorageInfo() {
    let totalChars = 0
    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i)
      const value = localStorage.getItem(key)
      totalChars += key.length + value.length
    }
    // UTF-16 编码,每个字符 2 字节
    const usedBytes = totalChars * 2
    return {
      used: usedBytes,
      usedFormatted: this._formatBytes(usedBytes),
      // 总容量因浏览器而异,不写死 5MB,UI 上显示"已用空间"即可
      itemCount: localStorage.length
    }
  },

  /**
   * 检查是否接近容量上限(>90%)
   */
  isNearQuotaLimit() {
    const info = this.getStorageInfo()
    // 假设常见浏览器配额为 5MB,但实际可能有差异
    const assumedQuota = 5 * 1024 * 1024
    return info.used > assumedQuota * 0.9
  },

  /**
   * 保存数据,失败时抛出可识别的错误类型
   * @throws {StorageError}
   */
  set(key, value) {
    try {
      const serialized = JSON.stringify(value)
      localStorage.setItem(key, serialized)
      return { success: true }
    } catch (error) {
      // 兼容不同浏览器的 QuotaExceeded 错误
      const isQuotaExceeded =
        error.name === 'QuotaExceededError' ||
        error.name === 'NS_ERROR_DOM_QUOTA_REACHED' || // Firefox
        error.code === 22 || // IE
        (error instanceof DOMException && error.name === 'QuotaExceededError')

      if (isQuotaExceeded) {
        throw new StorageError(
          `存储空间不足,已用 ${this.getStorageInfo().usedFormatted}`,
          ERROR_CODES.QUOTA_EXCEEDED
        )
      }
      throw new StorageError(
        `存储失败 [${key}]: ${error.message}`,
        ERROR_CODES.WRITE_FAILED
      )
    }
  },

  /**
   * 获取数据
   * @param {string} key - 键名
   * @param {*} defaultValue - 默认值(使用 undefined 作为"未提供"的哨兵值)
   * @throws {StorageError}
   */
  get(key, defaultValue = undefined) {
    try {
      const item = localStorage.getItem(key)
      if (item === null) {
        // 如果未提供 defaultValue(即 undefined),抛出错误
        if (defaultValue === undefined) {
          throw new StorageError(
            `键不存在: ${key}`,
            ERROR_CODES.KEY_NOT_FOUND
          )
        }
        // 如果提供了 defaultValue(包括 null),返回默认值
        return defaultValue
      }
      return JSON.parse(item)
    } catch (error) {
      if (error instanceof StorageError) throw error
      throw new StorageError(
        `读取失败 [${key}]: ${error.message}`,
        ERROR_CODES.READ_FAILED
      )
    }
  },

  /**
   * 检查键是否存在
   */
  has(key) {
    return localStorage.getItem(key) !== null
  },

  /**
   * 删除数据
   */
  remove(key) {
    try {
      localStorage.removeItem(key)
      return { success: true }
    } catch (error) {
      throw new StorageError(
        `删除失败 [${key}]: ${error.message}`,
        ERROR_CODES.WRITE_FAILED
      )
    }
  },

  /**
   * 清空所有应用数据(完整清理)
   */
  clearAppData() {
    const keys = Object.values(STORAGE_KEYS)
    keys.forEach(key => this.remove(key))
    return { success: true, clearedCount: keys.length }
  },

  /**
   * 格式化字节数
   */
  _formatBytes(bytes) {
    if (bytes === 0) return '0 B'
    const k = 1024
    const sizes = ['B', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i]
  }
}
