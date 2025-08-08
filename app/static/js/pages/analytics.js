/**
 * 数据分析页面JavaScript
 * 实现月度分类支出堆叠面积图
 */

import { getCSSColorValue } from '../common/utils.js';

// 加载月度支出数据
async function loadExpenseData() {
    try {
        const response = await fetch('/analytics/api/monthly-expenses');
        const result = await response.json();

        if (result.success) {
            return result.data;
        } else {
            console.error('API返回错误:', result.error);
            return null;
        }
    } catch (error) {
        console.error('获取数据失败:', error);
        return null;
    }
}

// 创建堆叠面积图
function createChart(data) {
    const chart = window.echarts.init(document.getElementById('expense-chart'));
    const { categories } = data;

    // 获取分类颜色
    function getCategoryColor(category) {
        const categoryInfo = categories[category];
        const colorName = categoryInfo?.color || 'secondary';
        return getCSSColorValue(colorName);
    }

    // 获取分类中文名称
    function getCategoryName(category) {
        const categoryInfo = categories[category];
        return categoryInfo?.name || category;
    }

    // 构造ECharts配置
    const option = {
        title: {
            text: '月度分类支出趋势',
            left: 'center',
            textStyle: {
                fontSize: 16,
                fontWeight: 'bold'
            }
        },
        tooltip: {
            trigger: 'axis',
            axisPointer: {
                type: 'cross',
                label: {
                    backgroundColor: '#6a7985'
                }
            },
            formatter: function(params) {
                let result = params[0].axisValue + '<br/>';
                let total = 0;
                params.forEach(function(item) {
                    if (item.value > 0) {
                        result += item.marker + ' ' + item.seriesName + ': ¥' + item.value.toFixed(2) + '<br/>';
                        total += item.value;
                    }
                });
                result += '<strong>总计: ¥' + total.toFixed(2) + '</strong>';
                return result;
            }
        },
        legend: {
            data: data.series.map(s => getCategoryName(s.category)),
            top: 30
        },
        grid: {
            left: '3%',
            right: '4%',
            bottom: '15%',
            top: '15%',
            containLabel: true
        },
        dataZoom: [
            {
                type: 'slider',
                show: true,
                xAxisIndex: [0],
                start: 0,
                end: 100,
                bottom: '5%'
            },
            {
                type: 'inside',
                xAxisIndex: [0],
                start: 0,
                end: 100
            }
        ],
        xAxis: [
            {
                type: 'category',
                boundaryGap: false,
                data: data.months,
                axisLabel: {
                    formatter: function(value) {
                        // 将 2024-01 格式转换为 2024年1月
                        const [year, month] = value.split('-');
                        return year + '年' + parseInt(month) + '月';
                    }
                }
            }
        ],
        yAxis: [
            {
                type: 'value',
                axisLabel: {
                    formatter: '¥{value}'
                }
            }
        ],
        series: data.series.map(seriesItem => ({
            name: getCategoryName(seriesItem.category),
            type: 'line',
            stack: 'Total',
            areaStyle: {},
            emphasis: {
                focus: 'series'
            },
            data: seriesItem.data,
            itemStyle: {
                color: getCategoryColor(seriesItem.category)
            }
        }))
    };

    chart.setOption(option);

    // 响应式调整
    window.addEventListener('resize', function() {
        chart.resize();
    });

    return chart;
}

// 页面初始化
document.addEventListener('DOMContentLoaded', async function() {
    const chartElement = document.getElementById('expense-chart');
    if (chartElement) {
        const data = await loadExpenseData();
        if (data && data.series && data.series.length > 0) {
            createChart(data);
        } else {
            chartElement.innerHTML = '<div style="text-align: center; padding: 50px; color: #6c757d;">暂无支出数据</div>';
        }
    }
});