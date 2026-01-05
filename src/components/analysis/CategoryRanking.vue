<template>
  <div class="ranking-container">
    <div class="ranking-header">
      <h3 class="ranking-title"><TrophyOutlined /> 分类支出排行榜</h3>
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
          <span class="rank-number" :class="{ 'rank-top': index < 3 }">{{ index + 1 }}</span>
        </div>
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
      <div class="empty-icon"><BarChartOutlined /></div>
      <p>暂无支出数据</p>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { startOfMonth, endOfMonth, subMonths } from 'date-fns'
import { TrophyOutlined, BarChartOutlined } from '@ant-design/icons-vue'

// 分类配色（克制但有区分度）
const COLORS = [
  '#1677ff', // 主色蓝（第一名）
  '#389e0d', // 克制绿
  '#595959', // 深灰
  '#d46b08', // 暖橙
  '#8c8c8c', // 中灰
  '#531dab', // 深紫
  '#bfbfbf', // 浅灰
  '#08979c', // 青色
  '#c41d7f'  // 洋红
]

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
    .map((item, index) => ({
      ...item,
      color: COLORS[index % COLORS.length]
    }))

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
  const stats = new Map()
  const now = new Date()
  const startDate = startOfMonth(subMonths(now, months - 1))
  const endDate = endOfMonth(now)

  // 统计每个分类的支出
  transactions.forEach(t => {
    // 只统计指定时间范围内的支出
    const txDate = new Date(t.transactionTime)
    if (txDate < startDate || txDate > endDate) return

    // 只统计支出（负数）
    if (t.amount >= 0) return

    const category = t.category || '未分类'

    if (!stats.has(category)) {
      stats.set(category, {
        name: category,
        total: 0
      })
    }

    stats.get(category).total += Math.abs(t.amount)
  })

  return Array.from(stats.values())
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
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  padding: 24px;
  border: var(--card-border);
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
  color: var(--text-primary);
}

.time-range-selector {
  display: flex;
  gap: 8px;
}

.range-button {
  padding: 6px 16px;
  background: var(--color-gray-50);
  border: var(--border-default);
  border-radius: 20px;
  font-size: 0.9rem;
  cursor: pointer;
  transition: all var(--duration-base) ease;
}

.range-button:hover {
  background: var(--color-gray-100);
}

.range-button.active {
  background: var(--color-primary);
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
  grid-template-columns: 40px 1fr 2fr auto;
  align-items: center;
  gap: 16px;
  padding: 16px;
  border-radius: var(--radius-md);
  background: var(--color-gray-50);
  transition: background var(--duration-base) ease;
}

.ranking-item:hover {
  background: var(--color-gray-100);
}

.ranking-item.top {
  background: var(--color-gray-50);
  border: 1px solid var(--border-default);
}

.ranking-rank {
  font-size: 1rem;
  display: flex;
  align-items: center;
  justify-content: center;
}

.rank-number {
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  color: var(--text-tertiary);
  background: var(--color-gray-100);
  border-radius: var(--radius-sm);
}

.rank-number.rank-top {
  background: var(--color-primary);
  color: white;
}

.ranking-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.ranking-name {
  font-weight: 600;
  color: var(--text-primary);
  font-size: 1rem;
}

.ranking-amount {
  font-size: 0.9rem;
  color: var(--text-secondary);
}

.ranking-bar-wrapper {
  height: 8px;
  background: var(--color-gray-200);
  border-radius: var(--radius-sm);
  overflow: hidden;
  align-self: center;
}

.ranking-bar {
  height: 100%;
  border-radius: var(--radius-sm);
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
  color: var(--text-primary);
  font-size: 1.1rem;
}

.ranking-trend {
  font-size: 0.85rem;
  font-weight: 500;
}

.ranking-trend.up {
  color: var(--color-danger);
}

.ranking-trend.down {
  color: var(--color-success);
}

.ranking-loading,
.ranking-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  color: var(--text-tertiary);
}

.ranking-loading {
  flex-direction: row;
  gap: 12px;
}

.empty-icon {
  font-size: 3rem;
  margin-bottom: 16px;
  color: var(--text-tertiary);
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
  .ranking-item {
    grid-template-columns: 30px 1fr;
    gap: 8px;
  }

  .ranking-bar-wrapper {
    grid-column: 2 / -1;
  }

  .ranking-stats {
    grid-column: 2 / -1;
    flex-direction: row;
    justify-content: space-between;
  }
}
</style>
