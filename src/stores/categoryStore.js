import { defineStore } from 'pinia'
import { categoriesRepo, transactionCategoriesRepo, correctionsRepo, configRepo } from '../repositories/index.js'
import { rowsToMapping, mappingToRows } from '../utils/categoryMapping.js'
import { errorHandler } from '../utils/errorHandler.js'
import { useNotificationStore } from './notificationStore.js'

export const useCategoryStore = defineStore('category', {
  state: () => ({
    // AI 生成的分类体系
    categories: [],

    // 交易分类映射
    // 格式: { transactionId: { categoryId, subcategory, confidence, classifiedAt, isManual } }
    transactionCategories: {},

    // 用户纠正历史
    corrections: [],

    // AI 配置(唯一真源)
    // ⚠️ API Key 策略: 前端本地保存,后端不存储
    // - 前端: apiKey 保存在 IndexedDB/app_config (当前实现)
    // - 导出/备份: apiKey 脱敏为 '******' 或 undefined (dataExporter.js, backupManager.js)
    // - 后端迁移: 后端数据库不存储 apiKey,仅存储 provider/baseURL/model/enabled/fallbackToRules
    // - 恢复逻辑: 导入后用户需重新填写 apiKey
    aiConfig: {
      provider: 'ollama', // 'ollama' | 'openai' | 'qianwen'
      apiKey: '',         // ⚠️ 敏感信息,不导出到后端
      baseURL: 'http://localhost:11434/v1',
      model: 'qwen2.5:7b',
      timeout: 30000,
      enabled: false,           // 是否启用 AI 分类
      fallbackToRules: true     // AI 失败时回退到规则分类
    }
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
          correctionsRepo.getAll(),
          configRepo.get('ai_config')
        ])

        this.categories = categoriesData[0]
        // transactionCategories: 数组行 → 对象映射
        this.transactionCategories = rowsToMapping(categoriesData[1])
        this.corrections = categoriesData[2]
        this.aiConfig = categoriesData[3] || this.aiConfig
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
        // ⚠️ 深拷贝 aiConfig,避免保存响应式对象
        const aiConfigPlain = JSON.parse(JSON.stringify(this.aiConfig))
        await configRepo.set('ai_config', aiConfigPlain)
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
     * 更新 AI 配置
     */
    async updateAIConfig(config) {
      this.aiConfig = { ...this.aiConfig, ...config }
      await this.saveToStorage()
    },

    /**
     * 清空分类数据（保留 AI 配置）
     */
    async clearCategories() {
      this.categories = []
      this.transactionCategories = {}
      this.corrections = []
      await this.saveToStorage()
    }
  }
})
