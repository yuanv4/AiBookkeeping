/**
 * 图表数据处理工具
 */

/**
 * 按月聚合交易数据（趋势图）
 * @param {Array} transactions - 交易列表
 * @returns {Array} 月度数据
 */
export function processTrendData(transactions) {
  const monthlyData = new Map()

  transactions.forEach(tx => {
    if (!tx.transactionTime) return

    const month = tx.transactionTime.substring(0, 7) // YYYY-MM

    if (!monthlyData.has(month)) {
      monthlyData.set(month, { income: 0, expense: 0, net: 0 })
    }

    const data = monthlyData.get(month)
    if (tx.amount > 0) {
      data.income += tx.amount
      data.net += tx.amount
    } else {
      data.expense += Math.abs(tx.amount)
      data.net += tx.amount
    }
  })

  // 排序并转换为数组
  return Array.from(monthlyData.entries())
    .sort((a, b) => a[0].localeCompare(b[0]))
    .map(([month, data]) => ({
      month,
      ...data
    }))
}

/**
 * 计算分类统计数据（饼图）
 * @param {Array} transactions - 交易列表
 * @returns {Array} 分类数据
 */
export function processCategoryData(transactions) {
  const expenses = transactions.filter(t => t.amount < 0)
  const totalExpense = Math.abs(expenses.reduce((sum, t) => sum + t.amount, 0))

  if (totalExpense === 0) {
    return []
  }

  const categoryMap = new Map()

  expenses.forEach(tx => {
    const category = tx.category || '未分类'
    if (!categoryMap.has(category)) {
      categoryMap.set(category, 0)
    }
    categoryMap.set(category, categoryMap.get(category) + Math.abs(tx.amount))
  })

  let chartData = Array.from(categoryMap.entries())
    .map(([name, value]) => ({ name, value }))
    .sort((a, b) => b.value - a.value)

  // 合并小额分类（< 5%）
  const threshold = totalExpense * 0.05
  const bigCategories = chartData.filter(d => d.value >= threshold)
  const smallCategories = chartData.filter(d => d.value < threshold)

  if (smallCategories.length > 0) {
    bigCategories.push({
      name: '其他',
      value: smallCategories.reduce((sum, d) => sum + d.value, 0)
    })
  }

  return bigCategories
}

/**
 * 计算 Top 10 商户（柱状图）
 * @param {Array} transactions - 交易列表
 * @returns {Array} 商户数据
 */
export function processMerchantData(transactions) {
  const expenses = transactions.filter(t => t.amount < 0)

  const merchantMap = new Map()

  expenses.forEach(tx => {
    const merchant = tx.counterparty || '未知商户'
    if (!merchantMap.has(merchant)) {
      merchantMap.set(merchant, 0)
    }
    merchantMap.set(merchant, merchantMap.get(merchant) + Math.abs(tx.amount))
  })

  let chartData = Array.from(merchantMap.entries())
    .map(([name, value]) => ({ name, value }))
    .sort((a, b) => b.value - a.value)
    .slice(0, 10)

  return chartData
}

/**
 * 计算汇总统计数据
 * @param {Array} transactions - 交易列表
 * @returns {Object} 统计数据
 */
export function calculateSummary(transactions) {
  const income = transactions
    .filter(t => t.amount > 0)
    .reduce((sum, t) => sum + t.amount, 0)

  const expense = Math.abs(
    transactions
      .filter(t => t.amount < 0)
      .reduce((sum, t) => sum + t.amount, 0)
  )

  const net = income - expense

  const transactionCount = transactions.length

  const avgIncome = income > 0 ? income / transactions.filter(t => t.amount > 0).length : 0
  const avgExpense = expense > 0 ? expense / transactions.filter(t => t.amount < 0).length : 0

  return {
    income,
    expense,
    net,
    transactionCount,
    avgIncome,
    avgExpense
  }
}

/**
 * 按分类统计详细信息
 * @param {Array} transactions - 交易列表
 * @param {Array} categories - 分类列表
 * @returns {Array} 分类统计
 */
export function calculateCategoryStats(transactions, categories) {
  const expenses = transactions.filter(t => t.amount < 0)
  const totalExpense = Math.abs(expenses.reduce((sum, t) => sum + t.amount, 0))

  const stats = categories.map(cat => {
    const catTransactions = expenses.filter(t => t.category === cat.name)
    const amount = Math.abs(catTransactions.reduce((sum, t) => sum + t.amount, 0))

    return {
      id: cat.id,
      name: cat.name,
      icon: cat.icon,
      amount,
      transactionCount: catTransactions.length,
      percentage: totalExpense > 0 ? (amount / totalExpense * 100) : 0
    }
  })

  // 添加"未分类"
  const uncategorized = expenses.filter(t => !t.category)
  if (uncategorized.length > 0) {
    const amount = Math.abs(uncategorized.reduce((sum, t) => sum + t.amount, 0))
    stats.push({
      id: 'uncategorized',
      name: '未分类',
      icon: '📦',
      amount,
      transactionCount: uncategorized.length,
      percentage: totalExpense > 0 ? (amount / totalExpense * 100) : 0
    })
  }

  return stats.filter(s => s.transactionCount > 0)
}
