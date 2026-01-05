<template>
  <div v-if="loading" class="app-loading">
    <div class="loading-content">
      <div class="spinner"></div>
      <p>正在加载数据...</p>
    </div>
  </div>
  <template v-else>
    <!-- 登录页使用独立布局，其他页面使用 MainLayout -->
    <router-view v-if="$route.name === 'Login'" />
    <MainLayout v-else>
      <router-view v-slot="{ Component }">
        <transition name="fade" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </MainLayout>
    <!-- <MigrationWizard /> -->
    <Notification />
  </template>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import MainLayout from './layouts/MainLayout.vue'
import { useAppStore } from './stores/appStore.js'
import { useCategoryStore } from './stores/categoryStore.js'
import { useNotificationStore } from './stores/notificationStore.js'
import { authApi } from './api/index.js'
import { isRemoteMode } from './repositories/index.js'

const route = useRoute()
const appStore = useAppStore()
const categoryStore = useCategoryStore()
const notificationStore = useNotificationStore()
const loading = ref(true)

onMounted(async () => {
  try {
    // 在 remote 模式下，检查用户是否已登录
    const isRemote = isRemoteMode()
    const isAuthenticated = authApi.isAuthenticated()

    if (isRemote && !isAuthenticated) {
      // remote 模式下未登录，不加载数据（路由守卫会跳转到登录页）
      console.log('🔒 未登录状态，跳过数据加载')
      loading.value = false
      return
    }

    // local 模式或已登录状态下，加载数据
    await Promise.all([
      appStore.loadTransactions(),
      categoryStore.loadFromStorage()
    ])
  } catch (error) {
    console.error('加载数据失败:', error)
    // 显示可视化错误提示
    const errorMsg = error.message?.includes('网络') || error.message?.includes('连接')
      ? '网络连接失败，请检查后端服务是否启动'
      : '数据加载失败，请刷新页面重试'
    notificationStore.show(errorMsg, 'error', 5000)
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
  background: var(--bg-body);
}

.loading-content {
  text-align: center;
}

.spinner {
  width: 48px;
  height: 48px;
  margin: 0 auto 16px;
  border: 4px solid var(--border-default);
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

/* 页面过渡动画 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
