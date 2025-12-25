<template>
  <div v-if="loading" class="app-loading">
    <div class="loading-content">
      <div class="spinner"></div>
      <p>正在加载数据...</p>
    </div>
  </div>
  <template v-else>
    <MainLayout />
    <MigrationWizard />
    <Notification />
  </template>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import MainLayout from './layouts/MainLayout.vue'
import { useAppStore } from './stores/appStore.js'
import { useCategoryStore } from './stores/categoryStore.js'

const appStore = useAppStore()
const categoryStore = useCategoryStore()
const loading = ref(true)

onMounted(async () => {
  try {
    // 优先加载数据,再渲染页面
    await Promise.all([
      appStore.loadTransactions(),
      categoryStore.loadFromStorage()
    ])
  } catch (error) {
    console.error('加载数据失败:', error)
    // 继续执行,用户可以看到错误
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.app-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100vh;
  background: var(--bg-primary);
}

.loading-content {
  text-align: center;
}

.spinner {
  width: 48px;
  height: 48px;
  margin: 0 auto 16px;
  border: 4px solid var(--border-color);
  border-top-color: var(--color-primary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.loading-content p {
  font-size: 16px;
  color: var(--text-secondary);
  margin: 0;
}
</style>

<style>
/* 全局样式已在 src/style.css 中定义 */
</style>
