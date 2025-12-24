<template>
  <div class="chart-container">
    <h3 class="chart-title">📈 月度收支趋势</h3>
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
    <v-chart
      v-if="!loading && chartData"
      class="chart"
      :option="chartOption"
      autoresize
    />
    <div v-if="loading" class="chart-loading">
      <div class="spinner"></div>
      <span>加载中...</span>
    </div>
    <div v-if="!loading && !chartData" class="chart-empty">
      暂无数据
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart } from 'echarts/charts'
import {
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent
} from 'echarts/components'
import { format, subMonths, startOfMonth, endOfMonth } from 'date-fns'

// 注册 ECharts 组件
use([
  CanvasRenderer,
  LineChart,
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
const selectedRange = ref(12) // 默认显示12个月
const timeRanges = [
  { label: '近3个月', value: 3 },
  { label: '近6个月', value: 6 },
  { label: '近12个月', value: 12 }
]

// 图表数据
const chartData = computed(() => {
  if (!props.transactions || props.transactions.length === 0) {
    return null
  }

  // 按月分组统计
  const monthlyData = groupByMonth(props.transactions, selectedRange.value)

  // 生成图表数据
  const months = monthlyData.map(d => d.month)
  const income = monthlyData.map(d => d.income)
  const expense = monthlyData.map(d => Math.abs(d.expense))
  const net = monthlyData.map(d => d.income + d.expense)

  return { months, income, expense, net }
})

// ECharts 配置
const chartOption = computed(() => {
  if (!chartData.value) return {}

  return {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross'
      },
      formatter: (params) => {
        let tooltip = `<div style="font-weight: bold; margin-bottom: 8px;">${params[0].axisValue}</div>`
        params.forEach(param => {
          tooltip += `
            <div style="display: flex; justify-content: space-between; gap: 20px;">
              <span>${param.marker} ${param.seriesName}：</span>
              <span style="font-weight: bold;">¥${param.value.toFixed(2)}</span>
            </div>
          `
        })
        return tooltip
      }
    },
    legend: {
      data: ['收入', '支出', '净收支'],
      top: 10
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: chartData.value.months,
      boundaryGap: false
    },
    yAxis: {
      type: 'value',
      axisLabel: {
        formatter: '¥{value}'
      }
    },
    series: [
      {
        name: '收入',
        type: 'line',
        data: chartData.value.income,
        smooth: true,
        lineStyle: {
          width: 3,
          color: '#28a745'
        },
        areaStyle: {
          color: {
            type: 'linear',
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(40, 167, 69, 0.3)' },
              { offset: 1, color: 'rgba(40, 167, 69, 0.05)' }
            ]
          }
        }
      },
      {
        name: '支出',
        type: 'line',
        data: chartData.value.expense,
        smooth: true,
        lineStyle: {
          width: 3,
          color: '#dc3545'
        },
        areaStyle: {
          color: {
            type: 'linear',
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(220, 53, 69, 0.3)' },
              { offset: 1, color: 'rgba(220, 53, 69, 0.05)' }
            ]
          }
        }
      },
      {
        name: '净收支',
        type: 'line',
        data: chartData.value.net,
        smooth: true,
        lineStyle: {
          width: 2,
          type: 'dashed',
          color: '#667eea'
        }
      }
    ]
  }
})

/**
 * 按月分组统计数据
 */
function groupByMonth(transactions, months) {
  const result = []
  const now = new Date()

  for (let i = months - 1; i >= 0; i--) {
    const date = subMonths(now, i)
    const monthStart = startOfMonth(date)
    const monthEnd = endOfMonth(date)

    // 筛选当月交易
    const monthTransactions = transactions.filter(t => {
      const txDate = new Date(t.transactionTime)
      return txDate >= monthStart && txDate <= monthEnd
    })

    // 统计收支
    const income = monthTransactions
      .filter(t => t.amount > 0)
      .reduce((sum, t) => sum + t.amount, 0)

    const expense = monthTransactions
      .filter(t => t.amount < 0)
      .reduce((sum, t) => sum + t.amount, 0)

    result.push({
      month: format(date, 'yyyy年MM月'),
      income,
      expense,
      net: income + expense
    })
  }

  return result
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
  margin-bottom: 16px;
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

.chart {
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
</style>
