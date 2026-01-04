<template>
  <div class="financial-metrics">
    <!-- 收支比 -->
    <div class="metric-card ratio-card">
      <div class="metric-icon">📊</div>
      <div class="metric-content">
        <div class="metric-label">收支比</div>
        <div class="metric-value" :class="ratioClass">
          {{ ratio }}
        </div>
        <div class="metric-hint">收入 / 支出</div>
      </div>
    </div>

    <!-- 累计净额 -->
    <div class="metric-card balance-card">
      <div class="metric-icon">💰</div>
      <div class="metric-content">
        <div class="metric-label">累计净额</div>
        <div class="metric-value" :class="balanceClass">
          ¥{{ balance.toFixed(2) }}
        </div>
        <div class="metric-hint">以 0 为起点</div>
      </div>
    </div>

    <!-- 本月收支 -->
    <div class="metric-card monthly-card">
      <div class="metric-icon">📅</div>
      <div class="metric-content">
        <div class="metric-label">本月收支</div>
        <div class="metric-value-group">
          <div class="metric-value-inline income">+¥{{ monthlyIncome.toFixed(2) }}</div>
          <div class="metric-value-inline expense">-¥{{ monthlyExpense.toFixed(2) }}</div>
        </div>
        <div class="metric-hint">净收支: ¥{{ monthlyNet.toFixed(2) }}</div>
      </div>
    </div>

    <!-- 本年累计 -->
    <div class="metric-card yearly-card">
      <div class="metric-icon">📈</div>
      <div class="metric-content">
        <div class="metric-label">本年累计</div>
        <div class="metric-value" :class="yearlyNetClass">
          ¥{{ yearlyNet.toFixed(2) }}
        </div>
        <div class="metric-hint">{{ year }}年净收支</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  statistics: {
    type: Object,
    required: true,
    validator: (value) => {
      return ['total', 'income', 'expense', 'net'].every(key => key in value)
    }
  },
  monthlyStats: {
    type: Object,
    required: true,
    validator: (value) => {
      return ['income', 'expense', 'net'].every(key => key in value)
    }
  },
  yearlyStats: {
    type: Object,
    required: true,
    validator: (value) => {
      return ['income', 'expense', 'net'].every(key => key in value)
    }
  }
})

const year = computed(() => new Date().getFullYear())

// 收支比（expense 是负数）
const ratio = computed(() => {
  const { income, expense } = props.statistics
  const absExpense = Math.abs(expense)
  if (absExpense === 0) {
    return income > 0 ? '∞' : '0.00'
  }
  return (income / absExpense).toFixed(2)
})

const ratioClass = computed(() => {
  const r = parseFloat(ratio.value)
  if (isNaN(r)) return 'excellent' // ∞ 的情况
  if (r === 0) return 'neutral'
  if (r >= 1.5) return 'excellent'
  if (r >= 1.0) return 'good'
  if (r >= 0.5) return 'warning'
  return 'danger'
})

// 累计净额（直接使用 statistics.net）
const balance = computed(() => props.statistics.net)

const balanceClass = computed(() => {
  return balance.value >= 0 ? 'positive' : 'negative'
})

// 本月收支
const monthlyIncome = computed(() => props.monthlyStats.income)
const monthlyExpense = computed(() => Math.abs(props.monthlyStats.expense))
const monthlyNet = computed(() => props.monthlyStats.net)

// 本年累计
const yearlyNet = computed(() => props.yearlyStats.net)

const yearlyNetClass = computed(() => {
  return yearlyNet.value >= 0 ? 'positive' : 'negative'
})
</script>

<style scoped>
.financial-metrics {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: var(--spacing-4, 16px);
}

.metric-card {
  background: var(--bg-card, #ffffff);
  border: var(--card-border, 1px solid #e5e7eb);
  border-radius: var(--radius-lg, 12px);
  padding: var(--spacing-5, 20px);
  display: flex;
  align-items: center;
  gap: var(--spacing-3, 12px);
  transition: all var(--duration-base, 0.2s) var(--ease-out, ease-out);
}

.metric-card:hover {
  border-color: var(--border-strong, #d1d5db);
  box-shadow: var(--shadow-sm, 0 1px 3px rgba(0, 0, 0, 0.1));
}

.metric-icon {
  font-size: var(--text-3xl, 30px);
  flex-shrink: 0;
}

.metric-content {
  flex: 1;
  min-width: 0;
}

.metric-label {
  font-size: var(--text-sm, 14px);
  color: var(--text-secondary, #6b7280);
  margin-bottom: var(--spacing-1, 4px);
}

.metric-value {
  font-size: var(--text-2xl, 24px);
  font-weight: var(--font-bold, 700);
  margin-bottom: var(--spacing-1, 4px);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.metric-value.excellent {
  color: var(--color-success, #10b981);
}

.metric-value.good {
  color: var(--color-info, #3b82f6);
}

.metric-value.warning {
  color: var(--color-warning, #f59e0b);
}

.metric-value.danger {
  color: var(--color-danger, #ef4444);
}

.metric-value.neutral {
  color: var(--text-primary, #1f2937);
}

.metric-value.positive {
  color: var(--color-success, #10b981);
}

.metric-value.negative {
  color: var(--color-danger, #ef4444);
}

.metric-value-group {
  display: flex;
  gap: var(--spacing-2, 8px);
  margin-bottom: var(--spacing-1, 4px);
}

.metric-value-inline {
  font-size: var(--text-base, 16px);
  font-weight: var(--font-semibold, 600);
  white-space: nowrap;
}

.metric-value-inline.income {
  color: var(--color-success, #10b981);
}

.metric-value-inline.expense {
  color: var(--color-danger, #ef4444);
}

.metric-hint {
  font-size: var(--text-xs, 12px);
  color: var(--text-tertiary, #9ca3af);
}

/* 响应式 */
@media (max-width: 768px) {
  .financial-metrics {
    grid-template-columns: 1fr;
  }

  .metric-card {
    padding: var(--spacing-4, 16px);
  }

  .metric-value {
    font-size: var(--text-xl, 20px);
  }

  .metric-value-group {
    flex-direction: column;
    gap: var(--spacing-1, 4px);
  }
}
</style>
