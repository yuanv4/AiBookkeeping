/**
 * 现金流健康仪表盘 JavaScript
 */

import BasePage from '../common/BasePage.js';
import { getCSSColor } from '../common/utils.js';

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
        // 净现金趋势图
        this.charts.netWorth = new Chart(document.getElementById('netWorthChart'), {
            type: 'line',
            data: { labels: [], datasets: [{ label: '净现金', data: [], borderColor: getCSSColor('--bs-primary'), backgroundColor: getCSSColor('--bs-primary-100'), fill: true, tension: 0.4 }] },
            options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false }, datalabels: { display: 'auto', align: 'top', anchor: 'end', offset: 8, font: { size: 10 }, color: '#6c757d', formatter: (value) => '¥' + value.toLocaleString('zh-CN', { notation: 'compact', minimumFractionDigits: 0, maximumFractionDigits: 1 }) } }, scales: { y: { beginAtZero: false, ticks: { callback: (value) => '¥' + value.toLocaleString() } } } }
        });
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
        const labels = trendData.map(d => d.date);
        const data = trendData.map(d => d.value);
        this.charts.netWorth.data.labels = labels;
        this.charts.netWorth.data.datasets[0].data = data;
        this.charts.netWorth.update();
    }
}

// 初始化页面
document.addEventListener('DOMContentLoaded', () => {
    const page = new FinancialDashboard();
    page.init();
});

 