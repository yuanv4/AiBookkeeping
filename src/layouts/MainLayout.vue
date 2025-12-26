<template>
  <div class="main-layout">
    <AppSidebar />
    <div class="main-content-wrapper">
      <AppHeader />
      <main class="main-content">
        <slot />
      </main>
    </div>
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import AppSidebar from './components/AppSidebar.vue'
import AppHeader from './components/AppHeader.vue'
import { useAppStore } from '../stores/appStore.js'
import { authApi } from '../api/index.js'
import { isRemoteMode } from '../repositories/index.js'

const appStore = useAppStore()

onMounted(() => {
  // 只在 local 模式或已登录状态下加载数据
  const isRemote = isRemoteMode()
  const isAuthenticated = authApi.isAuthenticated()

  if (!isRemote || isAuthenticated) {
    // 加载保存的交易数据
    appStore.loadTransactions()
  }
})
</script>

<style scoped>
.main-layout {
  display: flex;
  min-height: 100vh;
  background: var(--bg-body);
}

.main-content-wrapper {
  flex: 1;
  margin-left: var(--sidebar-width);
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}

.main-content {
  flex: 1;
  padding: var(--spacing-6);
  overflow-y: auto;
}

/* 路由过渡动画 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity var(--duration-slow) var(--ease-out);
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* 响应式 */
@media (max-width: 768px) {
  .main-content-wrapper {
    margin-left: var(--sidebar-width-collapsed);
  }

  .main-content {
    padding: var(--spacing-4);
  }
}
</style>
