<template>
  <div class="large-transaction-list">
    <div class="list-header">
      <h3 class="list-title"><PayCircleOutlined /> 近期大额支出</h3>
      <div class="time-range-badge">
        {{ timeRangeLabel }}
      </div>
    </div>

    <div v-if="transactions.length > 0" class="transaction-list">
      <div
        v-for="(tx, index) in transactions"
        :key="tx.transactionId"
        class="transaction-item"
        @click="handleTransactionClick(tx)"
      >
        <div class="transaction-rank">{{ index + 1 }}</div>
        <div class="transaction-icon"><TagOutlined /></div>
        <div class="transaction-info">
          <div class="transaction-merchant">{{ tx.counterparty || tx.description || '未知商户' }}</div>
          <div class="transaction-meta">
            <span class="transaction-category">{{ tx.category || '未分类' }}</span>
            <span class="transaction-date">{{ formatDate(tx.transactionTime) }}</span>
          </div>
        </div>
        <div class="transaction-amount num">{{ formatMoney(-tx.absoluteAmount) }}</div>
      </div>
    </div>

    <div v-else class="empty-state">
      <div class="empty-icon"><BarChartOutlined /></div>
      <p>暂无大额支出记录</p>
    </div>
  </div>
</template>

<script setup>
import { computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { determineSmartTimeRange, getTopLargeTransactions } from '../../utils/chartDataProcessor.js'
import { format } from 'date-fns'
import {
  PayCircleOutlined,
  TagOutlined,
  BarChartOutlined
} from '@ant-design/icons-vue'

// 人民币格式化
const moneyFormatter = new Intl.NumberFormat('zh-CN', {
  style: 'currency',
  currency: 'CNY',
  signDisplay: 'always'
})

function formatMoney(amount) {
  return moneyFormatter.format(amount)
}

const props = defineProps({
  transactions: {
    type: Array,
    default: () => []
  },
  limit: {
    type: Number,
    default: 10
  }
})

const emit = defineEmits(['time-range-change'])

const router = useRouter()

// 智能时间范围
const timeRange = computed(() => determineSmartTimeRange(props.transactions))

// 时间范围标签
const timeRangeLabel = computed(() => timeRange.value.label)

// 大额交易列表
const transactions = computed(() =>
  getTopLargeTransactions(props.transactions, props.limit, timeRange.value.days)
)

// 触发时间范围变化事件
watch(timeRange, (newRange) => {
  emit('time-range-change', newRange)
}, { immediate: true })

function handleTransactionClick(transaction) {
  router.push('/transactions')
}

function formatDate(dateStr) {
  try {
    return format(new Date(dateStr), 'MM月dd日 HH:mm')
  } catch (error) {
    return '无效日期'
  }
}
</script>

<style scoped>
.large-transaction-list {
  background: var(--bg-card, #ffffff);
  border: var(--card-border, 1px solid #e5e7eb);
  border-radius: var(--radius-lg, 12px);
  padding: var(--spacing-6, 24px);
}

.list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-4, 16px);
}

.list-title {
  font-size: var(--text-xl, 20px);
  font-weight: var(--font-semibold, 600);
  color: var(--text-primary, #1f2937);
  margin: 0;
}

.time-range-badge {
  padding: var(--spacing-1, 4px) var(--spacing-3, 12px);
  background: var(--color-gray-100, #f3f4f6);
  border-radius: var(--radius-md, 8px);
  font-size: var(--text-sm, 14px);
  color: var(--text-secondary, #6b7280);
  font-weight: var(--font-medium, 500);
}

.transaction-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-3, 12px);
}

.transaction-item {
  display: grid;
  grid-template-columns: 32px 40px 1fr auto;
  align-items: center;
  gap: var(--spacing-3, 12px);
  padding: var(--spacing-3, 12px) var(--spacing-4, 16px);
  border-radius: var(--radius-md, 8px);
  background: var(--color-gray-50, #f9fafb);
  border: var(--border-default, 1px solid #e5e7eb);
  cursor: pointer;
  transition: all var(--duration-base, 0.2s) var(--ease-out, ease-out);
}

.transaction-item:hover {
  background: var(--color-gray-100, #f3f4f6);
  border-color: var(--border-strong, #d1d5db);
  transform: translateX(2px);
}

.transaction-rank {
  font-size: var(--text-sm, 14px);
  font-weight: var(--font-bold, 700);
  color: var(--text-tertiary, #9ca3af);
  text-align: center;
}

.transaction-icon {
  font-size: var(--text-xl, 20px);
  display: flex;
  align-items: center;
  justify-content: center;
}

.transaction-info {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-1, 4px);
  min-width: 0;
  flex: 1;
}

.transaction-merchant {
  font-weight: var(--font-medium, 500);
  color: var(--text-primary, #1f2937);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.transaction-meta {
  display: flex;
  gap: var(--spacing-2, 8px);
  font-size: var(--text-sm, 14px);
}

.transaction-category {
  color: var(--text-secondary, #6b7280);
}

.transaction-date {
  color: var(--text-tertiary, #9ca3af);
}

.transaction-amount {
  font-size: var(--text-lg, 18px);
  font-weight: var(--font-bold, 700);
  color: var(--color-danger, #ef4444);
  white-space: nowrap;
}

.empty-state {
  text-align: center;
  padding: var(--spacing-8, 32px) var(--spacing-4, 16px);
  color: var(--text-tertiary, #9ca3af);
}

.empty-icon {
  font-size: var(--text-4xl, 36px);
  margin-bottom: var(--spacing-3, 12px);
  opacity: 0.5;
}

.empty-state p {
  font-size: var(--text-sm, 14px);
  margin: 0;
}

/* 响应式 */
@media (max-width: 768px) {
  .large-transaction-list {
    padding: var(--spacing-4, 16px);
  }

  .transaction-item {
    grid-template-columns: 24px 32px 1fr;
    gap: var(--spacing-2, 8px);
  }

  .transaction-amount {
    grid-column: 3;
    justify-self: end;
  }

  .transaction-meta {
    flex-direction: column;
    gap: var(--spacing-1, 4px);
  }
}
</style>
