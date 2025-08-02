/**
 * 数据分析页面JavaScript
 * 实现月度分类支出堆叠面积图
 */

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
    const chart = echarts.init(document.getElementById('expense-chart'));

    // 分类颜色配置
    const categoryColors = {
        'dining': '#0d6efd',      // primary
        'transport': '#198754',   // success
        'shopping': '#0dcaf0',    // info
        'services': '#ffc107',    // warning
        'healthcare': '#dc3545',  // danger
        'finance': '#6c757d'      // secondary
    };

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
            data: data.series.map(s => s.name),
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
            name: seriesItem.name,
            type: 'line',
            stack: 'Total',
            areaStyle: {},
            emphasis: {
                focus: 'series'
            },
            data: seriesItem.data,
            itemStyle: {
                color: categoryColors[Object.keys(categoryColors).find(key =>
                    seriesItem.name.includes(key) ||
                    (key === 'dining' && seriesItem.name.includes('餐饮')) ||
                    (key === 'transport' && seriesItem.name.includes('交通')) ||
                    (key === 'shopping' && seriesItem.name.includes('购物')) ||
                    (key === 'services' && seriesItem.name.includes('服务')) ||
                    (key === 'healthcare' && seriesItem.name.includes('医疗')) ||
                    (key === 'finance' && seriesItem.name.includes('金融'))
                )] || '#6c757d'
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