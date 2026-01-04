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

/**
 * 计算年度对比数据
 * @param {Array} transactions - 交易列表
 * @returns {Array} 年度对比数据
 */
export function processYearlyComparison(transactions) {
  const yearlyMap = new Map()

  transactions.forEach(tx => {
    const year = new Date(tx.transactionTime).getFullYear()
    if (!yearlyMap.has(year)) {
      yearlyMap.set(year, { income: 0, expense: 0, count: 0 })
    }
    const data = yearlyMap.get(year)
    if (tx.amount > 0) {
      data.income += tx.amount
    } else {
      data.expense += Math.abs(tx.amount)
    }
    data.count++
  })

  return Array.from(yearlyMap.entries())
    .sort((a, b) => a[0] - b[0])
    .map(([year, data]) => ({
      year,
      income: Number(data.income.toFixed(2)),
      expense: Number(data.expense.toFixed(2)),
      net: Number((data.income - data.expense).toFixed(2)),
      count: data.count
    }))
}

/**
 * 智能确定时间范围
 * 规则：
 * - 数据跨度 < 30天：显示全部
 * - 数据跨度 30-90天：显示最近30天
 * - 数据跨度 > 90天：显示最近90天
 *
 * 边界处理：
 * - 最小钳制到 1 天（避免"近 0 天"导致筛选为空）
 * - 空数据或无效时间默认返回近 30 天
 * @param {Array} transactions - 交易列表
 * @returns {Object} { days: number, label: string }
 */
export function determineSmartTimeRange(transactions) {
  if (!transactions || transactions.length === 0) {
    return { days: 30, label: '近30天' }
  }

  const dates = transactions
    .map(t => t.transactionTime ? new Date(t.transactionTime).getTime() : NaN)
    .filter(d => !isNaN(d))

  if (dates.length === 0) {
    return { days: 30, label: '近30天' }
  }

  const minDate = Math.min(...dates)
  const maxDate = Math.max(...dates)
  let spanDays = Math.ceil((maxDate - minDate) / (1000 * 60 * 60 * 24))

  // 边界处理：最小钳制到 1 天
  if (spanDays < 1) spanDays = 1

  if (spanDays < 30) {
    return { days: spanDays, label: `全部${spanDays}天` }
  } else if (spanDays < 90) {
    return { days: 30, label: '近30天' }
  } else {
    return { days: 90, label: '近90天' }
  }
}

/**
 * 获取大额交易列表（Top N）
 *
 * 边界处理：
 * - 过滤掉 transactionTime 为 null 的记录
 * - 只处理支出交易（amount < 0）
 * @param {Array} transactions - 交易列表
 * @param {number} limit - 返回数量，默认 10
 * @param {number} timeRangeDays - 时间范围（天数），默认 30
 * @returns {Array} 大额交易列表
 */
export function getTopLargeTransactions(transactions, limit = 10, timeRangeDays = 30) {
  const now = new Date()
  const cutoffDate = new Date(now.getTime() - timeRangeDays * 24 * 60 * 60 * 1000)

  return transactions
    .filter(t => {
      // 边界保护：确保时间字段有效
      if (!t.transactionTime) return false

      const txDate = new Date(t.transactionTime)
      // 筛选支出且在时间范围内
      return t.amount < 0 && txDate >= cutoffDate && txDate <= now
    })
    .sort((a, b) => a.amount - b.amount) // 负数排序，从小到大即绝对值从大到小
    .slice(0, limit)
    .map(t => ({
      ...t,
      absoluteAmount: Math.abs(t.amount)
    }))
}

/**
 * 计算收支结构数据
 * @param {Array} transactions - 交易列表
 * @param {string} type - 'income' | 'expense'
 * @returns {Object} 结构数据
 */
export function processStructureAnalysis(transactions, type = 'expense') {
  // 筛选数据
  const filtered = transactions.filter(t => {
    return type === 'income' ? t.amount > 0 : t.amount < 0
  })

  // 按周期分组
  const grouped = new Map()

  filtered.forEach(t => {
    const month = t.transactionTime.substring(0, 7) // YYYY-MM
    if (!grouped.has(month)) {
      grouped.set(month, {})
    }

    const cat = t.category || '未分类'
    if (!grouped.get(month)[cat]) {
      grouped.get(month)[cat] = 0
    }
    grouped.get(month)[cat] += Math.abs(t.amount)
  })

  // 提取所有分类和周期
  const periods = Array.from(grouped.keys()).sort()
  const allCategories = [...new Set(periods.flatMap(p => Object.keys(grouped.get(p))))]

  // 构建数据矩阵
  const data = periods.map(period => {
    const catData = grouped.get(period)
    return allCategories.map(cat => Number((catData[cat] || 0).toFixed(2)))
  })

  return {
    periods,
    categories: allCategories,
    data,
    total: Number(filtered.reduce((sum, t) => sum + Math.abs(t.amount), 0).toFixed(2))
  }
}
