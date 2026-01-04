<template>
  <div class="analysis-panel">
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
</style>
