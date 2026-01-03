<template>
  <div class="chart-container">
    <h3 class="chart-title">🏗️ 收支结构分析</h3>
    <div class="type-selector">
      <button
        v-for="type in typeOptions"
        :key="type.value"
        @click="selectedType = type.value"
        class="type-button"
        :class="{ active: selectedType === type.value }"
      >
        {{ type.label }}
      </button>
    </div>

    <div v-if="!loading && structureData" class="charts-wrapper">
      <!-- 堆叠柱状图 -->
      <v-chart class="stacked-chart" :option="stackedOption" autoresize />

      <!-- 环形图 -->
      <v-chart class="pie-chart" :option="pieOption" autoresize />
    </div>

    <div v-if="loading" class="chart-loading">
      <div class="spinner"></div>
      <span>加载中...</span>
    </div>
    <div v-if="!loading && !structureData" class="chart-empty">
      暂无数据
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { BarChart, PieChart } from 'echarts/charts'
import {
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent
} from 'echarts/components'
import { processStructureAnalysis } from '../../utils/chartDataProcessor.js'
import { getCategoryColor } from '../../utils/categoryRules.js'

// 注册 ECharts 组件
use([
  CanvasRenderer,
  BarChart,
  PieChart,
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent
])

// Props
const props = defineProps({
  transactions: {
    type: Array,
    default: () => []
  }
})

// 状态
const loading = ref(false)
const selectedType = ref('expense')

const typeOptions = [
  { label: '支出', value: 'expense' },
  { label: '收入', value: 'income' }
]

// 结构图数据
const structureData = computed(() => {
  if (!props.transactions || props.transactions.length === 0) {
    return null
  }

  return processStructureAnalysis(props.transactions, selectedType.value)
})

// 环形图数据(总体分类占比)
const pieData = computed(() => {
  if (!structureData.value) return null

  const { categories, data } = structureData.value

  // 计算每个分类的总额
  const categoryTotals = categories.map((cat, idx) => {
    const total = data.reduce((sum, periodData) => sum + periodData[idx], 0)
    return { name: cat, value: total }
  })

  // 按金额降序排序
  return categoryTotals.sort((a, b) => b.value - a.value)
})

// 堆叠柱状图配置
const stackedOption = computed(() => {
  if (!structureData.value) return {}

  const { periods, categories, data } = structureData.value
  const colors = categories.map(cat => getCategoryColor(cat))

  // 生成系列数据
  const series = categories.map((cat, index) => ({
    name: cat,
    type: 'bar',
    stack: 'total',
    data: data.map(d => d[index]),
    itemStyle: {
      color: colors[index]
    },
    emphasis: {
      focus: 'series'
    }
  }))

  return {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      formatter: (params) => {
        let tooltip = `<div style="font-weight: bold; margin-bottom: 8px;">${params[0].axisValue}</div>`
        let total = 0
        params.forEach(param => {
          tooltip += `
            <div style="display: flex; justify-content: space-between; gap: 20px;">
              <span>${param.marker} ${param.seriesName}：</span>
              <span style="font-weight: bold;">¥${param.value.toFixed(2)}</span>
            </div>
          `
          total += param.value
        })
        tooltip += `<div style="margin-top: 8px; padding-top: 8px; border-top: 1px solid #ddd;">
          <strong>合计：¥${total.toFixed(2)}</strong>
        </div>`
        return tooltip
      }
    },
    legend: {
      data: categories,
      top: 10,
      type: 'scroll'
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: periods
    },
    yAxis: {
      type: 'value',
      axisLabel: {
        formatter: '¥{value}'
      }
    },
    series
  }
})

// 环形图配置
const pieOption = computed(() => {
  if (!pieData.value || pieData.value.length === 0) return {}

  return {
    tooltip: {
      trigger: 'item',
      formatter: '{b}: ¥{c} ({d}%)'
    },
    legend: {
      orient: 'vertical',
      right: 10,
      top: 20,
      data: pieData.value.map(d => d.name)
    },
    series: [
      {
        type: 'pie',
        radius: ['40%', '70%'],
        center: ['35%', '50%'],
        data: pieData.value,
        itemStyle: {
          borderRadius: 8,
          borderColor: '#fff',
          borderWidth: 2
        },
        label: {
          formatter: '{b}\n{d}%'
        }
      }
    ]
  }
})
</script>

<style scoped>
.chart-container {
  background: white;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.chart-title {
  margin: 0 0 16px 0;
  font-size: 1.2rem;
  color: #333;
}

.type-selector {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
}

.type-button {
  padding: 6px 16px;
  background: #f5f5f5;
  border: 1px solid #ddd;
  border-radius: 20px;
  font-size: 0.9rem;
  cursor: pointer;
  transition: all 0.3s;
}

.type-button:hover {
  background: #e8e8e8;
}

.type-button.active {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-color: transparent;
}

.charts-wrapper {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 20px;
}

.stacked-chart,
.pie-chart {
  width: 100%;
  height: 350px;
}

.chart-loading,
.chart-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 350px;
  color: #999;
  font-size: 0.95rem;
}

.chart-loading {
  gap: 12px;
}

.spinner {
  width: 20px;
  height: 20px;
  border: 3px solid #f3f3f3;
  border-top: 3px solid #667eea;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

@media (max-width: 1024px) {
  .charts-wrapper {
    grid-template-columns: 1fr;
  }
}
</style>
