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
  background: var(--bg-sidebar);
  display: flex;
  flex-direction: column;
  transition: width var(--duration-slow) var(--ease-in-out);
  position: fixed;
  left: 0;
  top: 0;
  z-index: 100;
  border-right: var(--sidebar-border);
}

.sidebar.collapsed {
  width: 64px;
}

.sidebar-header {
  padding: var(--spacing-5);
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.brand {
  display: flex;
  align-items: center;
  gap: var(--spacing-3);
  color: var(--text-inverse);
}

.brand-icon {
  font-size: 24px;
}

.brand-text {
  font-size: var(--text-lg);
  font-weight: var(--font-semibold);
}

.brand-icon-only {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  padding: 0;
  width: 100%;
  display: flex;
  justify-content: center;
  color: var(--text-inverse);
}

.sidebar-nav {
  flex: 1;
  padding: var(--spacing-5) var(--spacing-2);
  display: flex;
  flex-direction: column;
  gap: var(--spacing-1);
}

.nav-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-3);
  padding: var(--spacing-3) var(--spacing-4);
  color: var(--text-tertiary);
  text-decoration: none;
  border-radius: var(--radius-md);
  transition: all var(--duration-base) var(--ease-out);
  white-space: nowrap;
  overflow: hidden;
  font-size: var(--text-sm);
  font-weight: var(--font-medium);
}

.nav-item:hover {
  background: rgba(255, 255, 255, 0.05);
  color: var(--text-inverse);
}

.nav-item.active {
  background: rgba(255, 255, 255, 0.1);
  color: var(--text-inverse);
  font-weight: var(--font-semibold);
}

.nav-icon {
  font-size: 18px;
  flex-shrink: 0;
}

.nav-text {
  font-size: var(--text-sm);
}

.sidebar-footer {
  padding: var(--spacing-5);
  border-top: 1px solid rgba(255, 255, 255, 0.08);
}

.collapse-btn {
  width: 100%;
  padding: var(--spacing-2);
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: var(--radius-sm);
  color: var(--text-inverse);
  cursor: pointer;
  transition: all var(--duration-base) var(--ease-out);
  font-size: var(--text-sm);
}

.collapse-btn:hover {
  background: rgba(255, 255, 255, 0.1);
  border-color: rgba(255, 255, 255, 0.15);
}

/* 响应式 */
@media (max-width: 768px) {
  .sidebar {
    width: 64px;
  }

  .sidebar.collapsed {
    width: 0;
    overflow: hidden;
  }
}
</style>
