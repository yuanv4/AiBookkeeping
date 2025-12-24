<template>
  <div class="main-layout">
    <AppSidebar />
    <div class="main-content-wrapper">
      <AppHeader />
      <main class="main-content">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </main>
    </div>
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import AppSidebar from './components/AppSidebar.vue'
import AppHeader from './components/AppHeader.vue'
import { useAppStore } from '../stores/appStore.js'

const appStore = useAppStore()

onMounted(() => {
  // 加载保存的交易数据
  appStore.loadTransactions()
})
</script>

<style scoped>
.main-layout {
  display: flex;
  min-height: 100vh;
  background: #f3f4f6;
}

.main-content-wrapper {
  flex: 1;
  margin-left: 240px;
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}

.main-content {
  flex: 1;
  padding: 30px;
  overflow-y: auto;
}

/* 路由过渡动画 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* 响应式 */
@media (max-width: 768px) {
  .main-content-wrapper {
    margin-left: 70px;
  }

  .main-content {
    padding: 15px;
  }
}
</style>
