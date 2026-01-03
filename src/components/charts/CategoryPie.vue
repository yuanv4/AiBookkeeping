<template>
  <div class="chart-container">
    <h3 class="chart-title">🥧 消费构成分析</h3>
    <div class="time-range-selector">
      <button
        v-for="range in timeRanges"
        :key="range.value"
        @click="selectedRange = range.value"
        class="range-button"
        :class="{ active: selectedRange === range.value }"
      >
        {{ range.label }}
      </button>
    </div>
    <div class="chart-content">
      <div v-if="!loading && pieData" class="chart-wrapper">
        <v-chart
          class="chart"
          :option="chartOption"
          autoresize
          @click="onChartClick"
        />
        <div class="chart-legend">
          <div
            v-for="item in sortedCategories"
            :key="item.name"
            class="legend-item"
            :class="{ active: selectedCategory === item.name }"
            @click="toggleCategory(item.name)"
          >
            <span
              class="legend-color"
              :style="{ backgroundColor: item.color }"
            ></span>
            <span class="legend-name">{{ item.name }}</span>
            <span class="legend-value">¥{{ item.value.toFixed(2) }}</span>
            <span class="legend-percent">{{ item.percent }}%</span>
          </div>
        </div>
      </div>
      <div v-if="loading" class="chart-loading">
        <div class="spinner"></div>
        <span>加载中...</span>
      </div>
      <div v-if="!loading && !pieData" class="chart-empty">
        暂无数据
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { PieChart } from 'echarts/charts'
import {
  TitleComponent,
  TooltipComponent,
  LegendComponent
} from 'echarts/components'
import { startOfMonth, endOfMonth, subMonths } from 'date-fns'

// 预定义颜色数组
const COLORS = [
  '#5470c6', '#91cc75', '#fac858', '#ee6666', '#73c0de',
  '#3ba272', '#fc8452', '#9a60b4', '#ea7ccc'
]

// 注册 ECharts 组件
use([
  CanvasRenderer,
  PieChart,
  TitleComponent,
  TooltipComponent,
  LegendComponent
])

// Props
const props = defineProps({
  transactions: {
    type: Array,
    default: () => []
  }
})

// Emits
const emit = defineEmits(['category-select'])

// 状态
const loading = ref(false)
const selectedRange = ref(1) // 默认显示本月
const selectedCategory = ref(null)
const timeRanges = [
  { label: '本月', value: 1 },
  { label: '近3个月', value: 3 },
  { label: '近6个月', value: 6 },
  { label: '近12个月', value: 12 }
]

// 饼图数据
const pieData = computed(() => {
  if (!props.transactions || props.transactions.length === 0) {
    return null
  }

  // 按分类统计支出
  const categoryStats = calculateCategoryStats(props.transactions, selectedRange.value)

  // 过滤掉零支出的分类
  const data = categoryStats
    .filter(cat => cat.total > 0)
    .map((cat, index) => ({
      name: cat.name,
      value: cat.total,
      color: COLORS[index % COLORS.length]
    }))

  return data.length > 0 ? data : null
})

// 排序后的分类（按金额降序）
const sortedCategories = computed(() => {
  if (!pieData.value) return []

  const total = pieData.value.reduce((sum, item) => sum + item.value, 0)

  return pieData.value
    .sort((a, b) => b.value - a.value)
    .map(item => ({
      ...item,
      percent: ((item.value / total) * 100).toFixed(1)
    }))
})

// ECharts 配置
const chartOption = computed(() => {
  if (!pieData.value) return {}

  const data = sortedCategories.value

  return {
    tooltip: {
      trigger: 'item',
      formatter: (params) => {
        return `
          <div style="font-weight: bold; margin-bottom: 6px;">${params.name}</div>
          <div>支出：¥${params.value.toFixed(2)}</div>
          <div>占比：${params.percent}%</div>
        `
      }
    },
    legend: {
      show: false
    },
    series: [
      {
        type: 'pie',
        radius: ['40%', '70%'],
        center: ['50%', '50%'],
        data: data,
        emphasis: {
          itemStyle: {
            shadowBlur: 10,
            shadowOffsetX: 0,
            shadowColor: 'rgba(0, 0, 0, 0.5)'
          }
        },
        label: {
          show: true,
          formatter: (params) => {
            return params.percent > 5 ? `${params.percent}%` : ''
          }
        },
        labelLine: {
          show: true
        }
      }
    ]
  }
})

/**
 * 计算分类统计数据
 */
function calculateCategoryStats(transactions, months) {
  const stats = new Map()
  const now = new Date()
  const startDate = startOfMonth(subMonths(now, months - 1))
  const endDate = endOfMonth(now)

  // 统计每个分类的支出
  transactions.forEach(t => {
    // 只统计指定时间范围内的支出
    const txDate = new Date(t.transactionTime)
    if (txDate < startDate || txDate > endDate) return

    // 只统计支出（负数）
    if (t.amount >= 0) return

    const category = t.category || '未分类'

    if (!stats.has(category)) {
      stats.set(category, {
        name: category,
        total: 0
      })
    }

    stats.get(category).total += Math.abs(t.amount)
  })

  return Array.from(stats.values())
}

/**
 * 图表点击事件
 */
function onChartClick(params) {
  selectedCategory.value = selectedCategory.value === params.name ? null : params.name
  emit('category-select', selectedCategory.value)
}

/**
 * 切换分类选择
 */
function toggleCategory(name) {
  selectedCategory.value = selectedCategory.value === name ? null : name
  emit('category-select', selectedCategory.value)
}
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

.time-range-selector {
  display: flex;
  gap: 8px;
  margin-bottom: 20px;
}

.range-button {
  padding: 6px 16px;
  background: #f5f5f5;
  border: 1px solid #ddd;
  border-radius: 20px;
  font-size: 0.9rem;
  cursor: pointer;
  transition: all 0.3s;
}

.range-button:hover {
  background: #e8e8e8;
}

.range-button.active {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-color: transparent;
}

.chart-content {
  min-height: 400px;
}

.chart-wrapper {
  display: flex;
  gap: 40px;
  align-items: center;
}

.chart {
  flex: 1;
  height: 350px;
  min-width: 0;
}

.chart-legend {
  width: 220px;
  max-height: 350px;
  overflow-y: auto;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border-radius: 6px;
  cursor: pointer;
  transition: background 0.2s;
  margin-bottom: 4px;
}

.legend-item:hover {
  background: #f5f5f5;
}

.legend-item.active {
  background: #e8f0fe;
}

.legend-color {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  flex-shrink: 0;
}

.legend-name {
  flex: 1;
  font-size: 0.95rem;
  color: #333;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.legend-value {
  font-size: 0.9rem;
  color: #666;
  font-weight: 500;
}

.legend-percent {
  font-size: 0.85rem;
  color: #999;
  min-width: 45px;
  text-align: right;
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

/* 滚动条样式 */
.chart-legend::-webkit-scrollbar {
  width: 6px;
}

.chart-legend::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 3px;
}

.chart-legend::-webkit-scrollbar-thumb {
  background: #ccc;
  border-radius: 3px;
}

.chart-legend::-webkit-scrollbar-thumb:hover {
  background: #999;
}
</style>
