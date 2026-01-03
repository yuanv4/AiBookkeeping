<template>
  <div class="chart-container">
    <h3 class="chart-title">📊 年度对比分析</h3>
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
import { ref, computed } from 'vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { BarChart, LineChart } from 'echarts/charts'
import {
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent
} from 'echarts/components'
import { processYearlyComparison } from '../../utils/chartDataProcessor.js'

// 注册 ECharts 组件
use([
  CanvasRenderer,
  BarChart,
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

// 图表数据
const chartData = computed(() => {
  if (!props.transactions || props.transactions.length === 0) {
    return null
  }

  // 处理年度对比数据
  return processYearlyComparison(props.transactions)
})

// ECharts 配置
const chartOption = computed(() => {
  if (!chartData.value || chartData.value.length === 0) return {}

  const years = chartData.value.map(d => `${d.year}年`)
  const income = chartData.value.map(d => d.income)
  const expense = chartData.value.map(d => d.expense)
  const net = chartData.value.map(d => d.net)

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
      data: years
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
        type: 'bar',
        data: income,
        itemStyle: {
          color: '#28a745',
          borderRadius: [4, 4, 0, 0]
        },
        barWidth: '30%'
      },
      {
        name: '支出',
        type: 'bar',
        data: expense,
        itemStyle: {
          color: '#dc3545',
          borderRadius: [4, 4, 0, 0]
        },
        barWidth: '30%'
      },
      {
        name: '净收支',
        type: 'line',
        data: net,
        smooth: true,
        lineStyle: {
          width: 3,
          color: '#667eea'
        },
        itemStyle: {
          color: '#667eea'
        },
        symbolSize: 8
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
