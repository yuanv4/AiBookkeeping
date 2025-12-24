<template>
  <div class="ranking-container">
    <div class="ranking-header">
      <h3 class="ranking-title">🏆 分类支出排行榜</h3>
      <div class="time-range-selector">
        <button
          v-for="range in timeRanges"
          :key="range.value"
          @click="selectedRange = range.value"
          class="range-button"
          :class="{ active: selectedRange === range.value }"
        >
          {{ range.label }}
        </button>
      </div>
    </div>

    <div v-if="!loading && rankings.length > 0" class="ranking-list">
      <div
        v-for="(item, index) in rankings"
        :key="item.name"
        class="ranking-item"
        :class="{ top: index < 3 }"
      >
        <div class="ranking-rank">
          <span v-if="index < 3" class="medal">{{ ['🥇', '🥈', '🥉'][index] }}</span>
          <span v-else class="rank-number">{{ index + 1 }}</span>
        </div>
        <div class="ranking-icon">{{ item.icon }}</div>
        <div class="ranking-info">
          <div class="ranking-name">{{ item.name }}</div>
          <div class="ranking-amount">¥{{ item.total.toFixed(2) }}</div>
        </div>
        <div class="ranking-bar-wrapper">
          <div
            class="ranking-bar"
            :style="{
              width: item.percent + '%',
              backgroundColor: item.color
            }"
          ></div>
        </div>
        <div class="ranking-stats">
          <span class="ranking-percent">{{ item.percent }}%</span>
          <span
            v-if="item.trend !== 'stable'"
            class="ranking-trend"
            :class="{ up: item.trend === 'up', down: item.trend === 'down' }"
          >
            {{ item.trend === 'up' ? '↑' : '↓' }}
            {{ item.trendValue }}
          </span>
        </div>
      </div>
    </div>

    <div v-if="loading" class="ranking-loading">
      <div class="spinner"></div>
      <span>加载中...</span>
    </div>

    <div v-if="!loading && rankings.length === 0" class="ranking-empty">
      <div class="empty-icon">📊</div>
      <p>暂无支出数据</p>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { CATEGORY_RULES } from '../../utils/categoryRules.js'
import { startOfMonth, endOfMonth, subMonths } from 'date-fns'

// Props
const props = defineProps({
  transactions: {
    type: Array,
    default: () => []
  }
})

// 状态
const loading = ref(false)
const selectedRange = ref(1) // 默认显示本月
const timeRanges = [
  { label: '本月', value: 1 },
  { label: '近3月', value: 3 },
  { label: '近半年', value: 6 },
  { label: '近一年', value: 12 }
]

// 排行榜数据
const rankings = computed(() => {
  if (!props.transactions || props.transactions.length === 0) {
    return []
  }

  // 计算分类统计
  const stats = calculateCategoryStats(props.transactions, selectedRange.value)

  // 按金额降序排序
  const sorted = stats
    .filter(item => item.total > 0)
    .sort((a, b) => b.total - a.total)

  // 计算百分比和趋势
  const total = sorted.reduce((sum, item) => sum + item.total, 0)

  return sorted.map(item => ({
    ...item,
    percent: total > 0 ? ((item.total / total) * 100).toFixed(1) : 0,
    ...calculateTrend(item.name, selectedRange.value)
  }))
})

/**
 * 计算分类统计数据
 */
function calculateCategoryStats(transactions, months) {
  const stats = []
  const now = new Date()
  const startDate = startOfMonth(subMonths(now, months - 1))
  const endDate = endOfMonth(now)

  // 初始化所有分类
  for (const [name, config] of Object.entries(CATEGORY_RULES)) {
    if (name === '其他') continue

    stats.push({
      name,
      icon: config.icon,
      color: config.color,
      total: 0
    })
  }

  // 统计每个分类的支出
  transactions.forEach(t => {
    // 只统计指定时间范围内的支出
    const txDate = new Date(t.transactionTime)
    if (txDate < startDate || txDate > endDate) return

    // 只统计支出（负数）
    if (t.amount >= 0) return

    const category = t.category || '其他'
    const stat = stats.find(s => s.name === category)

    if (stat) {
      stat.total += Math.abs(t.amount)
    }
  })

  return stats
}

/**
 * 计算趋势（与上期对比）
 */
function calculateTrend(categoryName, currentMonths) {
  const now = new Date()

  // 当前周期
  const currentStart = startOfMonth(subMonths(now, currentMonths - 1))
  const currentEnd = endOfMonth(now)

  // 上期周期（同样时长）
  const previousStart = startOfMonth(subMonths(currentStart, currentMonths))
  const previousEnd = endOfMonth(subMonths(currentEnd, currentMonths))

  // 统计当前周期支出
  const currentTotal = props.transactions
    .filter(t => {
      const txDate = new Date(t.transactionTime)
      return (
        txDate >= currentStart &&
        txDate <= currentEnd &&
        t.amount < 0 &&
        (t.category || '其他') === categoryName
      )
    })
    .reduce((sum, t) => sum + Math.abs(t.amount), 0)

  // 统计上期周期支出
  const previousTotal = props.transactions
    .filter(t => {
      const txDate = new Date(t.transactionTime)
      return (
        txDate >= previousStart &&
        txDate <= previousEnd &&
        t.amount < 0 &&
        (t.category || '其他') === categoryName
      )
    })
    .reduce((sum, t) => sum + Math.abs(t.amount), 0)

  // 计算趋势
  if (previousTotal === 0) {
    return { trend: 'stable', trendValue: '' }
  }

  const changePercent = ((currentTotal - previousTotal) / previousTotal) * 100

  if (Math.abs(changePercent) < 5) {
    return { trend: 'stable', trendValue: '' }
  }

  return {
    trend: changePercent > 0 ? 'up' : 'down',
    trendValue: Math.abs(changePercent).toFixed(0) + '%'
  }
}
</script>

<style scoped>
.ranking-container {
  background: white;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.ranking-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  flex-wrap: wrap;
  gap: 12px;
}

.ranking-title {
  margin: 0;
  font-size: 1.2rem;
  color: #333;
}

.time-range-selector {
  display: flex;
  gap: 8px;
}

.range-button {
  padding: 6px 16px;
  background: #f5f5f5;
  border: 1px solid #ddd;
  border-radius: 20px;
  font-size: 0.9rem;
  cursor: pointer;
  transition: all 0.3s;
}

.range-button:hover {
  background: #e8e8e8;
}

.range-button.active {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-color: transparent;
}

.ranking-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.ranking-item {
  display: grid;
  grid-template-columns: 40px 40px 1fr 2fr auto;
  align-items: center;
  gap: 16px;
  padding: 16px;
  border-radius: 8px;
  background: #f8f9fa;
  transition: all 0.3s;
}

.ranking-item:hover {
  background: #f0f1f3;
  transform: translateX(4px);
}

.ranking-item.top {
  background: linear-gradient(135deg, #fff5f5 0%, #fff 100%);
  border: 1px solid #ffe0e0;
}

.ranking-rank {
  font-size: 1.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
}

.medal {
  font-size: 2rem;
}

.rank-number {
  font-weight: bold;
  color: #999;
}

.ranking-icon {
  font-size: 2rem;
  display: flex;
  align-items: center;
  justify-content: center;
}

.ranking-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.ranking-name {
  font-weight: 600;
  color: #333;
  font-size: 1rem;
}

.ranking-amount {
  font-size: 0.9rem;
  color: #666;
}

.ranking-bar-wrapper {
  height: 8px;
  background: #e9ecef;
  border-radius: 4px;
  overflow: hidden;
  align-self: center;
}

.ranking-bar {
  height: 100%;
  border-radius: 4px;
  transition: width 0.5s ease;
}

.ranking-stats {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 4px;
}

.ranking-percent {
  font-weight: bold;
  color: #333;
  font-size: 1.1rem;
}

.ranking-trend {
  font-size: 0.85rem;
  font-weight: 500;
}

.ranking-trend.up {
  color: #dc3545;
}

.ranking-trend.down {
  color: #28a745;
}

.ranking-loading,
.ranking-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  color: #999;
}

.ranking-loading {
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
  border: 3px solid #f3f3f3;
  border-top: 3px solid #667eea;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

/* 响应式 */
@media (max-width: 768px) {
  .ranking-item {
    grid-template-columns: 30px 30px 1fr;
    gap: 8px;
  }

  .ranking-bar-wrapper {
    grid-column: 3 / -1;
  }

  .ranking-stats {
    grid-column: 3 / -1;
    flex-direction: row;
    justify-content: space-between;
  }
}
</style>
