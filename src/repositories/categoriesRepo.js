import { db } from '../utils/indexedDB.js'

/**
 * 分类数据 Repository
 * 统一分类体系和交易分类映射的 CRUD 操作
 */

// 分类体系 Repository
export const categoriesRepo = {
  async getAll() {
    return await db.categories.toArray()
  },

  async bulkAdd(categories) {
    return await db.categories.bulkPut(categories)
  },

  async clear() {
    return await db.categories.clear()
  }
}

// 交易分类映射 Repository
export const transactionCategoriesRepo = {
  async getAll() {
    return await db.transaction_categories.toArray()
  },

  async set(transactionId, categoryData) {
    await db.transaction_categories.put({ transactionId, ...categoryData })
  },

  async bulkSet(mapping) {
    const data = Object.entries(mapping).map(([transactionId, categoryData]) => ({
      transactionId,
      ...categoryData
    }))
    await db.transaction_categories.bulkPut(data)
  },

  async get(transactionId) {
    return await db.transaction_categories.get(transactionId)
  },

  async clear() {
    return await db.transaction_categories.clear()
  }
}

// 用户纠正历史 Repository
export const correctionsRepo = {
  async getAll() {
    return await db.corrections.toArray()
  },

  async add(correction) {
    return await db.corrections.add(correction)
  },

  async bulkAdd(corrections) {
    return await db.corrections.bulkAdd(corrections)
  },

  async clear() {
    return await db.corrections.clear()
  }
}
