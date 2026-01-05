<template>
  <div class="analysis-view">
    <!-- 空状态 -->
    <div v-if="!hasData" class="empty-state">
      <div class="empty-icon"><LineChartOutlined /></div>
      <h3>暂无分析数据</h3>
      <p>请先在设置页面上传账单文件</p>
      <router-link to="/settings/data" class="btn btn-primary">
        前往上传
      </router-link>
    </div>

    <!-- 分析内容 -->
    <div v-else class="analysis-content">
      <!-- 图表网格 -->
      <div class="charts-section">
        <!-- 月度趋势图 -->
        <div class="card chart-card">
          <div class="chart-container">
            <TrendChart :transactions="transactions" />
          </div>
        </div>

        <!-- 消费构成饼图 -->
        <div class="card chart-card">
          <div class="chart-container">
            <CategoryPie :transactions="transactions" @category-select="handleCategoryClick" />
          </div>
        </div>

        <!-- 年度对比分析 -->
        <div class="card chart-card full-width">
          <div class="chart-container">
            <YearlyComparisonChart :transactions="transactions" />
          </div>
        </div>

        <!-- 收支结构分析 -->
        <div class="card chart-card full-width">
          <div class="chart-container">
            <StructureAnalysisChart :transactions="transactions" />
          </div>
        </div>

        <!-- 分类排行榜 -->
        <div class="card chart-card full-width">
          <div class="chart-container">
            <CategoryRanking :transactions="transactions" @category-click="handleCategoryClick" />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAppStore } from '../stores/appStore.js'
import TrendChart from '../components/charts/TrendChart.vue'
import CategoryPie from '../components/charts/CategoryPie.vue'
import CategoryRanking from '../components/analysis/CategoryRanking.vue'
import YearlyComparisonChart from '../components/charts/YearlyComparisonChart.vue'
import StructureAnalysisChart from '../components/charts/StructureAnalysisChart.vue'
import { LineChartOutlined } from '@ant-design/icons-vue'

const router = useRouter()
const appStore = useAppStore()

const transactions = computed(() => appStore.transactions)
const hasData = computed(() => appStore.hasData)

function handleCategoryClick(category) {
  // 跳转到账单明细页面并应用筛选
  router.push({
    path: '/transactions',
    query: { category }
  })
}
</script>

<style scoped>
.analysis-view {
  width: 100%;
}

.empty-state {
  text-align: center;
  padding: 80px 20px;
}

.empty-icon {
  font-size: 64px;
  margin-bottom: 20px;
}

.empty-state h3 {
  font-size: 20px;
  color: var(--text-primary);
  margin: 0 0 10px 0;
}

.empty-state p {
  font-size: 14px;
  color: var(--text-secondary);
  margin: 0 0 20px 0;
}

.analysis-content {
  width: 100%;
}

.charts-section {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(450px, 1fr));
  gap: 20px;
  margin-top: 20px;
}

.chart-card {
  padding: 20px;
}

.chart-card.full-width {
  grid-column: 1 / -1;
}

.chart-container {
  min-height: 350px;
}

/* 响应式 */
@media (max-width: 768px) {
  .charts-section {
    grid-template-columns: 1fr;
  }

  .chart-container {
    min-height: 300px;
  }
}
</style>
