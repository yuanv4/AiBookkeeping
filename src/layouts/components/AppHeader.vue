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
  height: 70px;
  background: white;
  border-bottom: 1px solid #e5e7eb;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 30px;
  position: sticky;
  top: 0;
  z-index: 50;
}

.header-left {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.page-title {
  font-size: 20px;
  font-weight: 600;
  color: #1f2937;
  margin: 0;
}

.page-subtitle {
  font-size: 13px;
  color: #6b7280;
  margin: 0;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 15px;
}

.data-info {
  display: flex;
  align-items: center;
  gap: 10px;
}

.data-count {
  padding: 6px 12px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-radius: 20px;
  font-size: 13px;
  font-weight: 500;
}

/* 响应式 */
@media (max-width: 768px) {
  .app-header {
    padding: 0 15px;
    height: 60px;
  }

  .page-title {
    font-size: 17px;
  }

  .page-subtitle {
    display: none;
  }
}
</style>
