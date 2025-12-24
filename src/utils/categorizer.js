/**
 * 智能分类引擎
 * 基于规则 + AI 的混合分类系统
 */

import { CATEGORY_RULES, CATEGORIES } from './categoryRules.js'
import { categorizeByAI } from './aiCategorizer.js'

/**
 * 使用规则引擎分类交易
 * @param {Object} transaction - 交易对象
 * @returns {string|null} - 分类名称，如果无法匹配返回 null
 */
export function categorizeByRules(transaction) {
  const textToMatch = buildSearchText(transaction)

  // 遍历所有分类规则（按优先级排序）
  const sortedCategories = Object.entries(CATEGORY_RULES)
    .sort(([, a], [, b]) => a.priority - b.priority)

  for (const [category, rules] of sortedCategories) {
    if (category === '其他') continue // 跳过默认分类

    // 1. 关键词匹配
    if (rules.keywords && rules.keywords.length > 0) {
      for (const keyword of rules.keywords) {
        if (textToMatch.includes(keyword)) {
          return category
        }
      }
    }

    // 2. 正则表达式匹配
    if (rules.patterns && rules.patterns.length > 0) {
      for (const pattern of rules.patterns) {
        if (pattern.test(textToMatch)) {
          return category
        }
      }
    }
  }

  return null // 无法匹配
}

/**
 * 构建搜索文本（合并多个字段）
 */
function buildSearchText(transaction) {
  const parts = [
    transaction.counterparty || '',
    transaction.description || '',
    transaction.remark || '',
    transaction.paymentMethod || ''
  ]

  return parts.join(' ').toLowerCase()
}

/**
 * 主分类函数 - 混合模式（规则优先 + AI 兜底）
 * @param {Object} transaction - 交易对象
 * @param {Object} options - 配置选项
 * @returns {Promise<string>} - 分类名称
 */
export async function categorizeTransaction(transaction, options = {}) {
  const {
    useAI = true,           // 是否启用 AI
    aiConfig = null,        // AI 配置
    fallbackToRules = true  // AI 失败时回退到规则
  } = options

  // 1. 优先使用规则引擎（快速、免费）
  const ruleCategory = categorizeByRules(transaction)
  if (ruleCategory) {
    return ruleCategory
  }

  // 2. 规则无法匹配，尝试 AI
  if (useAI && aiConfig && aiConfig.apiKey) {
    try {
      const aiCategory = await categorizeByAI(transaction, aiConfig)

      // 验证 AI 返回的分类是否有效
      if (aiCategory && CATEGORIES.includes(aiCategory)) {
        return aiCategory
      }

      // AI 返回了无效分类，回退到规则
      if (fallbackToRules) {
        console.warn(`AI 返回无效分类: ${aiCategory}，使用规则引擎`)
        return categorizeByRulesWithFallback(transaction)
      }
    } catch (error) {
      console.error('AI 分类失败:', error.message)

      // AI 失败，回退到规则
      if (fallbackToRules) {
        return categorizeByRulesWithFallback(transaction)
      }
    }
  }

  // 3. 无法分类，返回"其他"
  return '其他'
}

/**
 * 规则引擎的最终兜底方案
 */
function categorizeByRulesWithFallback(transaction) {
  const ruleCategory = categorizeByRules(transaction)
  return ruleCategory || '其他'
}

/**
 * 批量分类交易
 * @param {Array} transactions - 交易数组
 * @param {Object} options - 配置选项
 * @returns {Promise<Array>} - 分类后的交易数组
 */
export async function batchCategorize(transactions, options = {}) {
  const results = []

  for (const transaction of transactions) {
    const category = await categorizeTransaction(transaction, options)

    results.push({
      ...transaction,
      category
    })
  }

  return results
}

/**
 * 更新交易分类（用户手动纠正）
 * 用于学习用户偏好
 */
export function updateTransactionCategory(transaction, newCategory) {
  return {
    ...transaction,
    category: newCategory,
    manualCategory: true // 标记为手动分类
  }
}

/**
 * 统计分类准确率
 * @param {Array} transactions - 已分类的交易数组
 * @returns {Object} - 统计信息
 */
export function analyzeClassificationAccuracy(transactions) {
  const total = transactions.length
  const categorized = transactions.filter(t => t.category && t.category !== '其他').length
  const uncategorized = total - categorized
  const manual = transactions.filter(t => t.manualCategory).length

  return {
    total,
    categorized,
    uncategorized,
    manual,
    accuracy: total > 0 ? ((categorized / total) * 100).toFixed(2) + '%' : '0%'
  }
}
