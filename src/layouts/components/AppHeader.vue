<template>
  <header class="app-header">
    <div class="header-left">
      <h1 class="page-title">{{ pageTitle }}</h1>
      <p v-if="pageSubtitle" class="page-subtitle">{{ pageSubtitle }}</p>
    </div>

    <div class="header-right">
      <div v-if="hasData" class="data-info">
        <span class="data-count">{{ transactions.length }} 条交易</span>
      </div>
    </div>
  </header>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useAppStore } from '../../stores/appStore.js'

const route = useRoute()
const appStore = useAppStore()

const transactions = computed(() => appStore.transactions)
const hasData = computed(() => appStore.hasData)

const pageTitle = computed(() => {
  return route.meta?.title || 'AI 账单汇集工具'
})

const pageSubtitle = computed(() => {
  const subtitles = {
    '/dashboard': hasData.value ? '数据概览' : '开始上传您的第一笔账单',
    '/analysis': '深入分析您的消费习惯',
    '/transactions': '查看和管理所有交易记录',
    '/settings': '配置应用设置'
  }
  return subtitles[route.path] || ''
})
</script>

<style scoped>
.app-header {
  height: var(--header-height);
  background: var(--header-bg);
  border-bottom: var(--header-border);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 var(--spacing-6);
  position: sticky;
  top: 0;
  z-index: 50;
}

.header-left {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-1);
}

.page-title {
  font-size: var(--text-xl);
  font-weight: var(--font-semibold);
  color: var(--text-primary);
  margin: 0;
}

.page-subtitle {
  font-size: var(--text-sm);
  color: var(--text-secondary);
  margin: 0;
}

.header-right {
  display: flex;
  align-items: center;
  gap: var(--spacing-4);
}

.data-info {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
}

.data-count {
  padding: var(--spacing-1) var(--spacing-3);
  background: var(--color-primary);
  color: var(--text-inverse);
  border-radius: var(--radius-sm);
  font-size: var(--text-sm);
  font-weight: var(--font-medium);
  border: 1px solid var(--color-primary);
  transition: background-color var(--duration-base) var(--ease-out);
}

.data-count:hover {
  background: var(--color-primary-hover);
  border-color: var(--color-primary-hover);
}

/* 响应式 */
@media (max-width: 768px) {
  .app-header {
    padding: 0 var(--spacing-4);
    height: 56px;
  }

  .page-title {
    font-size: var(--text-lg);
  }

  .page-subtitle {
    display: none;
  }
}
</style>
