import { defineStore } from 'pinia'
import { storage, STORAGE_KEYS } from '../utils/storage'

export const useCategoryStore = defineStore('category', {
  state: () => ({
    // AI 生成的分类体系
    categories: [],

    // 交易分类映射
    // 格式: { transactionId: { categoryId, subcategory, confidence, classifiedAt, isManual } }
    transactionCategories: {},

    // 用户纠正历史
    corrections: [],

    // AI 配置
    aiConfig: {
      provider: 'ollama', // 'ollama' | 'openai'
      apiKey: '',
      baseURL: 'http://localhost:11434/v1',
      model: 'qwen2.5:7b',
      timeout: 30000
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
     * 从 localStorage 加载数据
     */
    loadFromStorage() {
      this.categories = storage.get(STORAGE_KEYS.CATEGORIES, [])
      this.transactionCategories = storage.get(STORAGE_KEYS.TRANSACTION_CATEGORIES, {})
      this.corrections = storage.get(STORAGE_KEYS.CORRECTIONS, [])
      this.aiConfig = storage.get(STORAGE_KEYS.AI_CONFIG, this.aiConfig)
    },

    /**
     * 保存数据到 localStorage
     */
    saveToStorage() {
      storage.set(STORAGE_KEYS.CATEGORIES, this.categories)
      storage.set(STORAGE_KEYS.TRANSACTION_CATEGORIES, this.transactionCategories)
      storage.set(STORAGE_KEYS.CORRECTIONS, this.corrections)
      storage.set(STORAGE_KEYS.AI_CONFIG, this.aiConfig)
    },

    /**
     * 更新分类体系
     */
    setCategories(categories) {
      this.categories = categories
      this.saveToStorage()
    },

    /**
     * 更新交易的分类
     */
    updateCategory(transactionId, categoryData) {
      this.transactionCategories[transactionId] = {
        ...categoryData,
        updatedAt: new Date().toISOString()
      }
      this.saveToStorage()
    },

    /**
     * 批量更新交易分类
     */
    batchUpdateCategories(updates) {
      updates.forEach(({ transactionId, categoryData }) => {
        this.transactionCategories[transactionId] = {
          ...categoryData,
          updatedAt: new Date().toISOString()
        }
      })
      this.saveToStorage()
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
    addCorrection(transactionId, originalCategory, correctedCategory) {
      this.corrections.push({
        transactionId,
        originalCategory,
        correctedCategory,
        timestamp: new Date().toISOString()
      })
      this.saveToStorage()
    },

    /**
     * 更新 AI 配置
     */
    updateAIConfig(config) {
      this.aiConfig = { ...this.aiConfig, ...config }
      this.saveToStorage()
    },

    /**
     * 清空分类数据（保留 AI 配置）
     */
    clearCategories() {
      this.categories = []
      this.transactionCategories = {}
      this.corrections = []
      this.saveToStorage()
    }
  }
})
