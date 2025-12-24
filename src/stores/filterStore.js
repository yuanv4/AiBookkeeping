import { defineStore } from 'pinia'
import { CATEGORIES } from '../utils/categoryRules.js'

export const useFilterStore = defineStore('filter', {
  state: () => ({
    // 原有筛选
    selectedCategory: null,
    selectedMerchant: null,
    dateRange: null,
    searchKeyword: '',

    // 新增筛选（兼容 App.vue）
    searchQuery: '',
    filterPlatform: '',
    filterType: '',
    filterCategory: '',
    currentPage: 1,
    pageSize: 50
  }),

  getters: {
    /**
     * 是否有激活的筛选
     */
    hasActiveFilter: (state) => {
      return !!(
        state.selectedCategory ||
        state.selectedMerchant ||
        state.dateRange ||
        state.searchKeyword ||
        state.searchQuery ||
        state.filterPlatform ||
        state.filterType ||
        state.filterCategory
      )
    },

    /**
     * 分类列表
     */
    categories: () => CATEGORIES
  },

  actions: {
    /**
     * 设置分类筛选
     */
    setCategory(categoryId) {
      this.selectedCategory = categoryId
      this.selectedMerchant = null // 清空商户筛选
    },

    /**
     * 设置商户筛选
     */
    setMerchant(merchantName) {
      this.selectedMerchant = merchantName
      this.selectedCategory = null // 清空分类筛选
    },

    /**
     * 设置日期范围
     */
    setDateRange(start, end) {
      this.dateRange = { start, end }
    },

    /**
     * 设置搜索关键词
     */
    setSearchKeyword(keyword) {
      this.searchKeyword = keyword
    },

    /**
     * 清空所有筛选
     */
    clearFilters() {
      this.selectedCategory = null
      this.selectedMerchant = null
      this.dateRange = null
      this.searchKeyword = ''
      this.searchQuery = ''
      this.filterPlatform = ''
      this.filterType = ''
      this.filterCategory = ''
      this.currentPage = 1
    },

    /**
     * 应用筛选到交易列表
     */
    applyFilters(transactionList) {
      let result = transactionList

      // 搜索筛选（优先使用 searchQuery）
      const query = this.searchQuery || this.searchKeyword
      if (query) {
        const lowerQuery = query.toLowerCase()
        result = result.filter(t =>
          (t.counterparty || '').toLowerCase().includes(lowerQuery) ||
          (t.description || '').toLowerCase().includes(lowerQuery)
        )
      }

      // 平台筛选
      if (this.filterPlatform) {
        result = result.filter(t => t.platform === this.filterPlatform)
      }

      // 类型筛选
      if (this.filterType) {
        result = result.filter(t => t.transactionType === this.filterType)
      }

      // 分类筛选
      const category = this.filterCategory || (this.selectedCategory ? CATEGORIES[this.selectedCategory]?.name : null)
      if (category) {
        result = result.filter(t => (t.category || '其他') === category)
      }

      // 商户筛选
      if (this.selectedMerchant) {
        result = result.filter(t =>
          (t.counterparty || '').includes(this.selectedMerchant) ||
          (t.description || '').includes(this.selectedMerchant)
        )
      }

      // 日期范围筛选
      if (this.dateRange) {
        result = result.filter(t => {
          const txDate = new Date(t.transactionTime)
          const start = this.dateRange.start ? new Date(this.dateRange.start) : null
          const end = this.dateRange.end ? new Date(this.dateRange.end) : null
          if (start && txDate < start) return false
          if (end && txDate > end) return false
          return true
        })
      }

      return result
    },

    /**
     * 分页
     */
    paginate(transactionList) {
      const start = (this.currentPage - 1) * this.pageSize
      const end = start + this.pageSize
      return transactionList.slice(start, end)
    },

    /**
     * 计算总页数
     */
    getTotalPages(transactionList) {
      return Math.ceil(transactionList.length / this.pageSize)
    },

    /**
     * 重置页码
     */
    resetPage() {
      this.currentPage = 1
    }
  }
})
