<template>
  <div class="settings-view">
    <div class="settings-container">
      <!-- 侧边栏标签 -->
      <div class="settings-tabs">
        <router-link
          to="/settings/ai"
          class="tab-item"
          :class="{ active: $route.path.startsWith('/settings/ai') || $route.path === '/settings' }"
        >
          <span class="tab-icon">🤖</span>
          <span class="tab-label">AI 配置</span>
        </router-link>
        <router-link
          to="/settings/data"
          class="tab-item"
          :class="{ active: $route.path.startsWith('/settings/data') }"
        >
          <span class="tab-icon">💾</span>
          <span class="tab-label">数据管理</span>
        </router-link>
      </div>

      <!-- 内容区域 -->
      <div class="settings-content">
        <router-view />
      </div>
    </div>
  </div>
</template>

<script setup>
</script>

<style scoped>
.settings-view {
  width: 100%;
}

.settings-container {
  display: grid;
  grid-template-columns: 250px 1fr;
  gap: 20px;
  background: white;
  border-radius: 12px;
  overflow: hidden;
  border: 1px solid #e5e7eb;
  min-height: 500px;
}

.settings-tabs {
  background: #f9fafb;
  border-right: 1px solid #e5e7eb;
  padding: 20px 0;
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.tab-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 20px;
  color: #4b5563;
  text-decoration: none;
  transition: all 0.2s ease;
  border-left: 3px solid transparent;
}

.tab-item:hover {
  background: rgba(102, 126, 234, 0.05);
  color: #667eea;
}

.tab-item.active {
  background: rgba(102, 126, 234, 0.1);
  color: #667eea;
  border-left-color: #667eea;
  font-weight: 500;
}

.tab-icon {
  font-size: 20px;
}

.tab-label {
  font-size: 14px;
}

.settings-content {
  padding: 30px;
}

/* 响应式 */
@media (max-width: 768px) {
  .settings-container {
    grid-template-columns: 1fr;
  }

  .settings-tabs {
    flex-direction: row;
    border-right: none;
    border-bottom: 1px solid #e5e7eb;
    padding: 10px;
  }

  .tab-item {
    flex: 1;
    justify-content: center;
    border-left: none;
    border-bottom: 3px solid transparent;
    flex-direction: column;
    gap: 5px;
    padding: 10px;
  }

  .tab-item.active {
    border-left: none;
    border-bottom-color: #667eea;
  }

  .tab-label {
    font-size: 12px;
  }

  .settings-content {
    padding: 20px;
  }
}
</style>
