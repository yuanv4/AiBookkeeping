/**
 * 现金流健康仪表盘 JavaScript
 */

import BasePage from '../common/BasePage.js';
import { getCSSColor, getEChartsTheme, getCommonChartConfig, formatCurrency, ChartManager } from '../common/utils.js';

export default class FinancialDashboard extends BasePage {
    constructor() {
        super();
        this.charts = {};
        this.currentData = {};
    }
    
    init() {
        super.init();
        
        const dataContainer = document.getElementById('dashboard-data');
        if (dataContainer) {
            this.currentData = JSON.parse(dataContainer.dataset.initialData);
        }

        this.initializeCharts();
        this.updateDashboard(this.currentData);
    }

    getChartColors() {
        return [
            getCSSColor('--bs-primary'),
            getCSSColor('--bs-success'),
            getCSSColor('--bs-warning'),
            getCSSColor('--bs-info'),
            getCSSColor('--bs-danger'),
            getCSSColor('--bs-secondary'),
            getCSSColor('--bs-primary-600'),
            getCSSColor('--bs-success-600')
        ];
    }
    
    initializeCharts() {
        // 净现金趋势图 - 直接使用ECharts
        const container = document.getElementById('netWorthChart');
        if (!container) {
            console.warn('找不到图表容器 #netWorthChart');
            return;
        }

        // 初始化ECharts实例
        const chart = echarts.init(container);

        // 配置选项
        const option = {
            tooltip: {
                trigger: 'axis',
                axisPointer: {
                    type: 'cross',
                    label: {
                        backgroundColor: getCSSColor('--bs-secondary') || '#6c757d'
                    }
                },
                formatter: (params) => {
                    if (params && params.length > 0) {
                        const param = params[0];
                        return `${param.name}<br/>净现金: ¥${param.value.toLocaleString('zh-CN', {
                            minimumFractionDigits: 2,
                            maximumFractionDigits: 2
                        })}`;
                    }
                    return '';
                }
            },
            grid: {
                left: '3%',
                right: '4%',
                bottom: '3%',
                containLabel: true
            },
            xAxis: {
                type: 'category',
                boundaryGap: false,
                data: [],
                axisLine: {
                    lineStyle: {
                        color: getCSSColor('--bs-border-color') || '#dee2e6'
                    }
                },
                axisLabel: {
                    color: getCSSColor('--bs-secondary') || '#6c757d'
                }
            },
            yAxis: {
                type: 'value',
                axisLine: {
                    lineStyle: {
                        color: getCSSColor('--bs-border-color') || '#dee2e6'
                    }
                },
                axisLabel: {
                    color: getCSSColor('--bs-secondary') || '#6c757d',
                    formatter: (value) => '¥' + value.toLocaleString('zh-CN', {
                        notation: 'compact',
                        minimumFractionDigits: 0,
                        maximumFractionDigits: 1
                    })
                },
                splitLine: {
                    lineStyle: {
                        color: getCSSColor('--bs-border-color-translucent') || 'rgba(0,0,0,.125)'
                    }
                }
            },
            series: [{
                name: '净现金',
                type: 'line',
                smooth: true,
                symbol: 'circle',
                symbolSize: 6,
                lineStyle: {
                    color: getCSSColor('--bs-primary') || '#0d6efd',
                    width: 3
                },
                itemStyle: {
                    color: getCSSColor('--bs-primary') || '#0d6efd'
                },
                areaStyle: {
                    color: {
                        type: 'linear',
                        x: 0,
                        y: 0,
                        x2: 0,
                        y2: 1,
                        colorStops: [{
                            offset: 0,
                            color: getCSSColor('--bs-primary-100') || 'rgba(13, 110, 253, 0.2)'
                        }, {
                            offset: 1,
                            color: 'rgba(13, 110, 253, 0.02)'
                        }]
                    }
                },
                data: []
            }]
        };

        // 设置配置
        chart.setOption(option);

        // 注册到管理器
        ChartManager.register('netWorthChart', chart);

        // 保存引用
        this.charts.netWorth = chart;
    }

    updateDashboard(data) {
        if (!data) return;
        this.updateCoreMetrics(data.core_metrics);
        this.updateNetWorthChart(data.net_worth_trend);
    }

    updateCoreMetrics(metrics) {
        if (!metrics) return;
        document.getElementById('currentAssets').textContent = `¥${metrics.current_total_assets.toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
        document.getElementById('netIncome').textContent = `¥${metrics.net_income.toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
        this.updateEmergencyReserveMonths(metrics.emergency_reserve_months);
    }

    updateEmergencyReserveMonths(months) {
        const element = document.getElementById('emergencyReserveMonths');
        if (months < 0) {
            element.textContent = '无限';
        } else {
            element.textContent = `${months.toFixed(1)}个月`;
        }
    }

    updateNetWorthChart(trendData) {
        if (!trendData || !this.charts.netWorth) return;

        try {
            const labels = trendData.map(d => d.date);
            const data = trendData.map(d => d.value);

            // 直接使用ECharts API更新数据
            this.charts.netWorth.setOption({
                xAxis: {
                    data: labels
                },
                series: [{
                    data: data
                }]
            });
        } catch (error) {
            console.error('更新净现金趋势图失败:', error);
        }
    }
}

// 初始化页面
document.addEventListener('DOMContentLoaded', () => {
    const page = new FinancialDashboard();
    page.init();
});

 