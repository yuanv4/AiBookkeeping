<template>
  <div class="analysis-panel">
    <!-- AI 配置（可折叠） -->
    <div class="config-section">
      <div class="section-header" @click="showAIConfig = !showAIConfig">
        <h4>⚙️ AI 智能分类配置</h4>
        <span class="toggle-icon">{{ showAIConfig ? '▼' : '▶' }}</span>
      </div>
      <div v-show="showAIConfig" class="section-content">
        <AIConfig />
      </div>
    </div>

    <!-- 洞察卡片 -->
    <div class="section">
      <InsightCard :transactions="transactions" />
    </div>

    <!-- 图表网格 -->
    <div class="charts-grid">
      <!-- 趋势图 -->
      <div class="chart-section full-width">
        <TrendChart :transactions="transactions" />
      </div>

      <!-- 饼图 -->
      <div class="chart-section half-width">
        <CategoryPie
          :transactions="transactions"
          @category-select="handleCategorySelect"
        />
      </div>

      <!-- 排行榜 -->
      <div class="chart-section half-width">
        <CategoryRanking :transactions="transactions" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import AIConfig from '../settings/AIConfig.vue'
import InsightCard from './InsightCard.vue'
import TrendChart from '../charts/TrendChart.vue'
import CategoryPie from '../charts/CategoryPie.vue'
import CategoryRanking from './CategoryRanking.vue'

// Props
const props = defineProps({
  transactions: {
    type: Array,
    default: () => []
  }
})

// Emits
const emit = defineEmits(['category-filter'])

// 状态
const showAIConfig = ref(false)

/**
 * 处理分类选择（从饼图点击）
 */
function handleCategorySelect(category) {
  emit('category-filter', category)
}
</script>

<style scoped>
.analysis-panel {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.config-section {
  background: #f8f9fa;
  border-radius: 12px;
  overflow: hidden;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  cursor: pointer;
  user-select: none;
  transition: background 0.3s;
}

.section-header:hover {
  background: #e9ecef;
}

.section-header h4 {
  margin: 0;
  font-size: 1rem;
  color: #333;
}

.toggle-icon {
  font-size: 0.8rem;
  color: #666;
  transition: transform 0.3s;
}

.section-content {
  padding: 0 20px 20px 20px;
  animation: slideDown 0.3s ease;
}

@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.section {
  margin-bottom: 20px;
}

.charts-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20px;
}

.chart-section {
  width: 100%;
}

.chart-section.full-width {
  grid-column: 1 / -1;
}

.chart-section.half-width {
  grid-column: span 1;
}

/* 响应式 */
@media (max-width: 1024px) {
  .charts-grid {
    grid-template-columns: 1fr;
  }

  .chart-section.half-width {
    grid-column: 1 / -1;
  }
}

@media (max-width: 768px) {
  .section-header {
    padding: 12px 16px;
  }

  .section-content {
    padding: 0 16px 16px 16px;
  }
}
</style>
