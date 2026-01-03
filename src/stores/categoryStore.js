import { defineStore } from 'pinia'
import { categoriesRepo, transactionCategoriesRepo, correctionsRepo } from '../repositories/index.js'
import { rowsToMapping, mappingToRows } from '../utils/categoryMapping.js'
import { errorHandler } from '../utils/errorHandler.js'
import { useNotificationStore } from './notificationStore.js'

export const useCategoryStore = defineStore('category', {
  state: () => ({
    // 分类体系
    categories: [],

    // 交易分类映射
    // 格式: { transactionId: { categoryId, subcategory, confidence, classifiedAt, isManual } }
    transactionCategories: {},

    // 用户纠正历史
    corrections: []
  }),

  getters: {
    /**
     * 获取分类名称列表
     */
    categoryNames: (state) => {
      return state.categories.map(cat => cat.name)
    },

    /**
     * 根据名称查找分类
     */
    getCategoryByName: (state) => (name) => {
      return state.categories.find(cat => cat.name === name)
    },

    /**
     * 根据 ID 查找分类
     */
    getCategoryById: (state) => (id) => {
      return state.categories.find(cat => cat.id === id)
    },

    /**
     * 获取已分类的交易数量
     */
    classifiedCount: (state) => {
      return Object.keys(state.transactionCategories).length
    }
  },

  actions: {
    /**
     * 从 IndexedDB 加载数据
     */
    async loadFromStorage() {
      try {
        const categoriesData = await Promise.all([
          categoriesRepo.getAll(),
          transactionCategoriesRepo.getAll(),
          correctionsRepo.getAll()
        ])

        this.categories = categoriesData[0]
        // transactionCategories: 数组行 → 对象映射
        this.transactionCategories = rowsToMapping(categoriesData[1])
        this.corrections = categoriesData[2]
      } catch (error) {
        const { message, type } = errorHandler.normalizeStorageError(error)
        const notificationStore = useNotificationStore()
        notificationStore.show(message, type)
        throw error
      }
    },

    /**
     * 保存数据到 IndexedDB
     */
    async saveToStorage() {
      try {
        // ⚠️ 深拷贝所有数据,避免保存响应式对象
        await categoriesRepo.bulkAdd(JSON.parse(JSON.stringify(this.categories)))
        // transactionCategories: 对象映射 → 数组行
        await transactionCategoriesRepo.bulkSet(JSON.parse(JSON.stringify(this.transactionCategories)))
        await correctionsRepo.bulkAdd(JSON.parse(JSON.stringify(this.corrections)))
      } catch (error) {
        const { message, type } = errorHandler.normalizeStorageError(error)
        const notificationStore = useNotificationStore()
        notificationStore.show(message, type)
        throw error
      }
    },

    /**
     * 更新分类体系
     */
    async setCategories(categories) {
      this.categories = categories
      await this.saveToStorage()
    },

    /**
     * 更新交易的分类
     */
    async updateCategory(transactionId, categoryData) {
      this.transactionCategories[transactionId] = {
        ...categoryData,
        updatedAt: new Date().toISOString()
      }
      await this.saveToStorage()
    },

    /**
     * 批量更新交易分类
     */
    async batchUpdateCategories(updates) {
      updates.forEach(({ transactionId, categoryData }) => {
        this.transactionCategories[transactionId] = {
          ...categoryData,
          updatedAt: new Date().toISOString()
        }
      })
      await this.saveToStorage()
    },

    /**
     * 获取交易分类
     */
    getTransactionCategory(transactionId) {
      return this.transactionCategories[transactionId] || null
    },

    /**
     * 记录用户纠正
     */
    async addCorrection(transactionId, originalCategory, correctedCategory) {
      this.corrections.push({
        transactionId,
        originalCategory,
        correctedCategory,
        timestamp: new Date().toISOString()
      })
      await this.saveToStorage()
    },

    /**
     * 清空分类数据
     */
    async clearCategories() {
      this.categories = []
      this.transactionCategories = {}
      this.corrections = []
      await this.saveToStorage()
    }
  }
})
