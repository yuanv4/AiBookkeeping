import { categoriesApi } from '../../api/index.js'

/**
 * 分类数据 HTTP Repository
 * 对齐本地 categoriesRepo 接口，通过 HTTP 访问后端
 */

// 分类体系 Repository
export const categoriesRepo = {
  async getAll() {
    return await categoriesApi.getAll()
  },

  async bulkAdd(categories) {
    return await categoriesApi.bulkSet(categories)
  },

  async clear() {
    // 后端没有单独清空分类的接口，通过全量替换实现
    return await categoriesApi.bulkSet([])
  }
}

// 交易分类映射 Repository
export const transactionCategoriesRepo = {
  async getAll() {
    // 后端返回的是对象映射，转换为数组格式以保持接口一致
    const mapping = await categoriesApi.getTransactionCategories()
    return Object.entries(mapping).map(([transactionId, data]) => ({
      transactionId,
      ...data
    }))
  },

  async set(transactionId, categoryData) {
    return await categoriesApi.updateTransactionCategory(transactionId, categoryData)
  },

  async bulkSet(mapping) {
    // 转换为后端需要的格式
    const updates = Object.entries(mapping).map(([transactionId, categoryData]) => ({
      transactionId,
      categoryData
    }))
    return await categoriesApi.batchUpsertTransactionCategories(updates)
  },

  async get(transactionId) {
    const mapping = await categoriesApi.getTransactionCategories()
    return mapping[transactionId] || null
  },

  async clear() {
    return await categoriesApi.clearTransactionCategories()
  }
}

// 用户纠正历史 Repository
export const correctionsRepo = {
  async getAll() {
    return await categoriesApi.getCorrections()
  },

  async add(correction) {
    return await categoriesApi.addCorrection(correction)
  },

  async bulkAdd(corrections) {
    // 后端没有批量添加接口，逐个添加
    const results = []
    for (const correction of corrections) {
      const result = await this.add(correction)
      results.push(result)
    }
    return results
  },

  async clear() {
    return await categoriesApi.clearCorrections()
  }
}
