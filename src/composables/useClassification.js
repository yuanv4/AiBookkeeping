import { ref, computed } from 'vue'
import { useCategoryStore } from '../stores/categoryStore'
import { OllamaAdapter } from '../services/ollamaAdapter.js'
import { OpenAIAdapter } from '../services/openaiAdapter.js'

/**
 * 分类逻辑 Composable
 * 提供交易分类的核心功能
 */
export function useClassification() {
  const categoryStore = useCategoryStore()
  const adapter = ref(null)
  const isClassifying = ref(false)
  const error = ref(null)
  const progress = ref({ current: 0, total: 0 })

  /**
   * 初始化 AI 适配器
   */
  async function initAdapter() {
    const config = categoryStore.aiConfig

    if (config.provider === 'ollama') {
      adapter.value = new OllamaAdapter(config)
    } else if (config.provider === 'openai') {
      adapter.value = new OpenAIAdapter(config)
    } else {
      throw new Error(`不支持的 AI 提供商：${config.provider}`)
    }

    await adapter.value.init()
  }

  /**
   * 首次使用：生成分类体系
   */
  async function initializeCategories(transactions) {
    if (categoryStore.categories.length > 0) {
      console.log('已有分类体系，跳过初始化')
      return categoryStore.categories
    }

    isClassifying.value = true
    error.value = null

    try {
      await initAdapter()

      console.log('正在生成分类体系...')
      const categories = await adapter.value.generateCategorySystem(transactions)

      categoryStore.setCategories(categories)
      console.log(`✅ 分类体系生成成功，共 ${categories.length} 个分类`)

      return categories
    } catch (err) {
      error.value = err.message
      console.error('分类体系生成失败：', err)
      throw err
    } finally {
      isClassifying.value = false
    }
  }

  /**
   * 分类单笔交易
   */
  async function classifyTransaction(transaction) {
    // 生成交易 ID
    const txId = transaction.id || generateTransactionId(transaction)

    // 检查缓存
    const cached = categoryStore.getTransactionCategory(txId)
    if (cached) {
      return cached
    }

    isClassifying.value = true
    error.value = null

    try {
      if (!adapter.value) {
        await initAdapter()
      }

      const result = await adapter.value.classifyTransaction(
        transaction,
        categoryStore.categories
      )

      // 保存分类结果
      categoryStore.updateCategory(txId, {
        category: result.category,
        subcategory: result.subcategory,
        confidence: result.confidence,
        reasoning: result.reasoning,
        isManual: false
      })

      return result
    } catch (err) {
      error.value = err.message
      console.error('交易分类失败：', err)
      throw err
    } finally {
      isClassifying.value = false
    }
  }

  /**
   * 批量分类交易
   */
  async function classifyBatch(transactions) {
    if (transactions.length === 0) {
      return []
    }

    isClassifying.value = true
    error.value = null
    progress.value = { current: 0, total: transactions.length }

    try {
      if (!adapter.value) {
        await initAdapter()
      }

      console.log(`开始批量分类 ${transactions.length} 笔交易...`)

      const results = await adapter.value.classifyBatch(
        transactions,
        categoryStore.categories
      )

      // 批量保存结果
      const updates = results.map((result, index) => {
        const tx = transactions[index]
        const txId = tx.id || generateTransactionId(tx)
        return {
          transactionId: txId,
          categoryData: {
            category: result.category,
            subcategory: result.subcategory,
            confidence: result.confidence,
            reasoning: result.reasoning,
            isManual: false
          }
        }
      })

      categoryStore.batchUpdateCategories(updates)

      progress.value.current = transactions.length
      console.log(`✅ 批量分类完成，共 ${results.length} 笔`)

      return results
    } catch (err) {
      error.value = err.message
      console.error('批量分类失败：', err)
      throw err
    } finally {
      isClassifying.value = false
      progress.value = { current: 0, total: 0 }
    }
  }

  /**
   * 手动更新交易分类
   */
  function updateTransactionCategory(transaction, categoryName) {
    const txId = transaction.id || generateTransactionId(transaction)
    const existing = categoryStore.getTransactionCategory(txId)

    // 记录纠正历史
    if (existing && existing.category !== categoryName) {
      categoryStore.addCorrection(txId, existing.category, categoryName)
    }

    categoryStore.updateCategory(txId, {
      category: categoryName,
      isManual: true
    })
  }

  /**
   * 生成交易唯一标识
   */
  function generateTransactionId(transaction) {
    const { transactionTime, counterparty, amount, description } = transaction
    return `${transactionTime}_${counterparty}_${amount}_${description || ''}`
      .replace(/\s+/g, '_')
      .substring(0, 100)
  }

  /**
   * 获取交易分类
   */
  function getTransactionCategory(transaction) {
    const txId = transaction.id || generateTransactionId(transaction)
    return categoryStore.getTransactionCategory(txId)
  }

  return {
    // 状态
    isClassifying,
    error,
    progress,

    // 计算属性
    categories: computed(() => categoryStore.categories),
    isInitialized: computed(() => categoryStore.categories.length > 0),

    // 方法
    initializeCategories,
    classifyTransaction,
    classifyBatch,
    updateTransactionCategory,
    getTransactionCategory
  }
}
