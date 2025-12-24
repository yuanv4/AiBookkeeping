<template>
  <aside class="sidebar" :class="{ collapsed: isCollapsed }">
    <div class="sidebar-header">
      <div v-if="!isCollapsed" class="brand">
        <span class="brand-icon">📊</span>
        <span class="brand-text">AI 账单汇集</span>
      </div>
      <button v-else class="brand-icon-only" @click="toggleCollapse">📊</button>
    </div>

    <nav class="sidebar-nav">
      <router-link
        v-for="item in menuItems"
        :key="item.path"
        :to="item.path"
        class="nav-item"
        :class="{ active: isActive(item.path) }"
      >
        <span class="nav-icon">{{ item.icon }}</span>
        <span v-if="!isCollapsed" class="nav-text">{{ item.label }}</span>
      </router-link>
    </nav>

    <div class="sidebar-footer">
      <button class="collapse-btn" @click="toggleCollapse">
        {{ isCollapsed ? '→' : '←' }}
      </button>
    </div>
  </aside>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const isCollapsed = ref(false)

const menuItems = [
  { path: '/dashboard', icon: '📊', label: '仪表板' },
  { path: '/analysis', icon: '📈', label: '数据分析' },
  { path: '/transactions', icon: '📋', label: '账单明细' },
  { path: '/settings', icon: '⚙️', label: '设置' }
]

function isActive(path) {
  if (path === '/settings') {
    return route.path.startsWith('/settings')
  }
  return route.path === path
}

function toggleCollapse() {
  isCollapsed.value = !isCollapsed.value
}
</script>

<style scoped>
.sidebar {
  width: 240px;
  height: 100vh;
  background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
  display: flex;
  flex-direction: column;
  transition: width 0.3s ease;
  position: fixed;
  left: 0;
  top: 0;
  z-index: 100;
}

.sidebar.collapsed {
  width: 70px;
}

.sidebar-header {
  padding: 20px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.brand {
  display: flex;
  align-items: center;
  gap: 12px;
  color: white;
}

.brand-icon {
  font-size: 28px;
}

.brand-text {
  font-size: 18px;
  font-weight: bold;
}

.brand-icon-only {
  background: none;
  border: none;
  font-size: 28px;
  cursor: pointer;
  padding: 0;
  width: 100%;
  display: flex;
  justify-content: center;
}

.sidebar-nav {
  flex: 1;
  padding: 20px 10px;
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 15px;
  color: rgba(255, 255, 255, 0.8);
  text-decoration: none;
  border-radius: 8px;
  transition: all 0.2s ease;
  white-space: nowrap;
  overflow: hidden;
}

.nav-item:hover {
  background: rgba(255, 255, 255, 0.1);
  color: white;
}

.nav-item.active {
  background: rgba(255, 255, 255, 0.2);
  color: white;
  font-weight: 500;
}

.nav-icon {
  font-size: 20px;
  flex-shrink: 0;
}

.nav-text {
  font-size: 15px;
}

.sidebar-footer {
  padding: 20px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}

.collapse-btn {
  width: 100%;
  padding: 8px;
  background: rgba(255, 255, 255, 0.1);
  border: none;
  border-radius: 6px;
  color: white;
  cursor: pointer;
  transition: background 0.2s ease;
}

.collapse-btn:hover {
  background: rgba(255, 255, 255, 0.2);
}

/* 响应式 */
@media (max-width: 768px) {
  .sidebar {
    width: 70px;
  }

  .sidebar.collapsed {
    width: 0;
    overflow: hidden;
  }
}
</style>
