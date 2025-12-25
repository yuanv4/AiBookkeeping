<template>
  <div class="insight-container">
    <h3 class="insight-title">💡 消费洞察</h3>

    <div v-if="!loading && insights" class="insight-grid">
      <!-- 本月支出总览 -->
      <div class="insight-card primary">
        <div class="insight-icon">💰</div>
        <div class="insight-content">
          <div class="insight-label">本月总支出</div>
          <div class="insight-value">¥{{ insights.monthlyExpense.toFixed(2) }}</div>
          <div
            v-if="insights.expenseChange"
            class="insight-change"
            :class="{ up: insights.expenseChange > 0, down: insights.expenseChange < 0 }"
          >
            <span>{{ insights.expenseChange > 0 ? '↑' : '↓' }}</span>
            <span>{{ Math.abs(insights.expenseChange) }}%</span>
            <span>较上月</span>
          </div>
        </div>
      </div>

      <!-- 平均每笔支出 -->
      <div class="insight-card secondary">
        <div class="insight-icon">📊</div>
        <div class="insight-content">
          <div class="insight-label">平均每笔</div>
          <div class="insight-value">¥{{ insights.avgPerTransaction.toFixed(2) }}</div>
          <div class="insight-desc">共 {{ insights.transactionCount }} 笔交易</div>
        </div>
      </div>

      <!-- 最大单笔支出 -->
      <div class="insight-card accent" v-if="insights.maxExpense">
        <div class="insight-icon">🏆</div>
        <div class="insight-content">
          <div class="insight-label">最大单笔支出</div>
          <div class="insight-value">¥{{ insights.maxExpense.amount.toFixed(2) }}</div>
          <div class="insight-desc">{{ insights.maxExpense.counterparty || '未知' }}</div>
        </div>
      </div>

      <!-- Top 分类 -->
      <div class="insight-card success" v-if="insights.topCategory">
        <div class="insight-icon">{{ insights.topCategory.icon }}</div>
        <div class="insight-content">
          <div class="insight-label">最高支出分类</div>
          <div class="insight-value">{{ insights.topCategory.name }}</div>
          <div class="insight-desc">占 {{ insights.topCategory.percent }}%</div>
        </div>
      </div>

      <!-- 消费习惯 -->
      <div class="insight-card info full-width" v-if="insights.habits && insights.habits.length > 0">
        <div class="insight-icon">🎯</div>
        <div class="insight-content">
          <div class="insight-label">消费习惯分析</div>
          <ul class="insight-list">
            <li v-for="(habit, index) in insights.habits" :key="index">
              {{ habit }}
            </li>
          </ul>
        </div>
      </div>
    </div>

    <div v-if="loading" class="insight-loading">
      <div class="spinner"></div>
      <span>分析中...</span>
    </div>

    <div v-if="!loading && !insights" class="insight-empty">
      <div class="empty-icon">📊</div>
      <p>暂无足够数据进行分析</p>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { startOfMonth, endOfMonth, subMonths, format } from 'date-fns'
import { getCategoryIcon } from '../../utils/categoryRules.js'

// Props
const props = defineProps({
  transactions: {
    type: Array,
    default: () => []
  }
})

// 状态
const loading = ref(false)

// 洞察数据
const insights = computed(() => {
  if (!props.transactions || props.transactions.length === 0) {
    return null
  }

  const now = new Date()
  const monthStart = startOfMonth(now)
  const monthEnd = endOfMonth(now)

  // 本月支出
  const monthlyTransactions = props.transactions.filter(t => {
    const txDate = new Date(t.transactionTime)
    return txDate >= monthStart && txDate <= monthEnd && t.amount < 0
  })

  if (monthlyTransactions.length === 0) {
    return null
  }

  const monthlyExpense = monthlyTransactions.reduce((sum, t) => sum + Math.abs(t.amount), 0)

  // 上月支出（用于对比）
  const lastMonthStart = startOfMonth(subMonths(now, 1))
  const lastMonthEnd = endOfMonth(subMonths(now, 1))

  const lastMonthTransactions = props.transactions.filter(t => {
    const txDate = new Date(t.transactionTime)
    return txDate >= lastMonthStart && txDate <= lastMonthEnd && t.amount < 0
  })

  const lastMonthExpense = lastMonthTransactions.reduce((sum, t) => sum + Math.abs(t.amount), 0)

  // 计算变化百分比
  let expenseChange = null
  if (lastMonthExpense > 0) {
    expenseChange = ((monthlyExpense - lastMonthExpense) / lastMonthExpense * 100).toFixed(0)
  }

  // 平均每笔
  const avgPerTransaction = monthlyExpense / monthlyTransactions.length

  // 最大单笔支出
  const maxExpense = monthlyTransactions.reduce((max, t) => {
    return Math.abs(t.amount) > Math.abs(max.amount) ? t : max
  }, { amount: 0 })

  // Top 分类
  const categoryStats = {}
  monthlyTransactions.forEach(t => {
    const cat = t.category || '其他'
    if (!categoryStats[cat]) {
      categoryStats[cat] = 0
    }
    categoryStats[cat] += Math.abs(t.amount)
  })

  const topCategoryEntry = Object.entries(categoryStats).sort((a, b) => b[1] - a[1])[0]
  const topCategory = topCategoryEntry ? {
    name: topCategoryEntry[0],
    amount: topCategoryEntry[1],
    percent: ((topCategoryEntry[1] / monthlyExpense) * 100).toFixed(1),
    icon: getCategoryIcon(topCategoryEntry[0])
  } : null

  // 消费习惯分析
  const habits = analyzeHabits(monthlyTransactions)

  return {
    monthlyExpense,
    expenseChange: expenseChange ? parseFloat(expenseChange) : null,
    transactionCount: monthlyTransactions.length,
    avgPerTransaction,
    maxExpense: maxExpense.amount > 0 ? {
      amount: Math.abs(maxExpense.amount),
      counterparty: maxExpense.counterparty || maxExpense.description
    } : null,
    topCategory,
    habits
  }
})

/**
 * 分析消费习惯
 */
function analyzeHabits(transactions) {
  const habits = []

  // 1. 工作日 vs 周末
  const weekdayExpenses = transactions.filter(t => {
    const date = new Date(t.transactionTime)
    const day = date.getDay()
    return day >= 1 && day <= 5 // 周一到周五
  }).reduce((sum, t) => sum + Math.abs(t.amount), 0)

  const weekendExpenses = transactions.filter(t => {
    const date = new Date(t.transactionTime)
    const day = date.getDay()
    return day === 0 || day === 6 // 周六周日
  }).reduce((sum, t) => sum + Math.abs(t.amount), 0)

  if (weekdayExpenses > 0 && weekendExpenses > 0) {
    const ratio = (weekendExpenses / weekdayExpenses).toFixed(1)
    if (ratio > 1.5) {
      habits.push(`周末支出是工作日的 ${ratio} 倍，建议适当控制`)
    } else if (ratio < 0.7) {
      habits.push(`工作日支出较高，注意劳逸结合`)
    }
  }

  // 2. 小额高频交易
  const smallTransactions = transactions.filter(t => Math.abs(t.amount) < 50)
  if (smallTransactions.length > transactions.length * 0.5) {
    habits.push(`小额交易占比高（${smallTransactions.length}笔），建议检查是否有不必要的支出`)
  }

  // 3. 夜间消费
  const nightTransactions = transactions.filter(t => {
    const hour = new Date(t.transactionTime).getHours()
    return hour >= 22 || hour <= 5
  })
  if (nightTransactions.length > 5) {
    habits.push(`有 ${nightTransactions.length} 笔夜间消费，可能影响健康`)
  }

  return habits
}
</script>

<style scoped>
.insight-container {
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  padding: 24px;
  border: var(--card-border);
}

.insight-title {
  margin: 0 0 20px 0;
  font-size: 1.2rem;
  color: var(--text-primary);
}

.insight-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 16px;
}

.insight-card {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 16px;
  border-radius: var(--radius-md);
  background: var(--color-gray-50);
  border: var(--card-border);
  border-left-width: 3px;
  transition: border-color var(--duration-base) ease;
}

.insight-card:hover {
  border-color: var(--border-strong);
}

.insight-card.primary {
  border-left-color: var(--color-gray-800);
}

.insight-card.secondary {
  border-left-color: var(--color-gray-600);
}

.insight-card.accent {
  border-left-color: var(--color-warning);
}

.insight-card.success {
  border-left-color: var(--color-success);
}

.insight-card.info {
  border-left-color: var(--color-info);
}

.insight-card.full-width {
  grid-column: 1 / -1;
}

.insight-icon {
  font-size: 2rem;
  flex-shrink: 0;
}

.insight-content {
  flex: 1;
  min-width: 0;
}

.insight-label {
  font-size: 0.85rem;
  color: var(--text-secondary);
  margin-bottom: 4px;
}

.insight-value {
  font-size: 1.5rem;
  font-weight: bold;
  color: var(--text-primary);
  margin-bottom: 4px;
}

.insight-desc {
  font-size: 0.85rem;
  color: var(--text-tertiary);
}

.insight-change {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 0.85rem;
  font-weight: 500;
  margin-top: 4px;
}

.insight-change.up {
  color: var(--color-danger);
}

.insight-change.down {
  color: var(--color-success);
}

.insight-list {
  list-style: none;
  padding: 0;
  margin: 8px 0 0 0;
}

.insight-list li {
  padding: 6px 0;
  font-size: 0.9rem;
  color: var(--text-secondary);
  position: relative;
  padding-left: 16px;
}

.insight-list li::before {
  content: '•';
  position: absolute;
  left: 0;
  color: var(--color-info);
  font-weight: bold;
}

.insight-loading,
.insight-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  color: var(--text-tertiary);
}

.insight-loading {
  flex-direction: row;
  gap: 12px;
}

.empty-icon {
  font-size: 4rem;
  margin-bottom: 16px;
}

.spinner {
  width: 20px;
  height: 20px;
  border: 3px solid var(--color-gray-200);
  border-top: 3px solid var(--color-primary);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

/* 响应式 */
@media (max-width: 768px) {
  .insight-grid {
    grid-template-columns: 1fr;
  }

  .insight-value {
    font-size: 1.3rem;
  }
}
</style>
