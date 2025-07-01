/**
 * 现金流健康仪表盘 JavaScript
 */

import BasePage from '../common/BasePage.js';
import { formatDate, showNotification, apiService, getCSSColor } from '../common/utils.js';

/**
 * 动态模块管理器
 * 负责处理带有独立时间选择器的仪表盘模块
 */
class DashboardModule {
    constructor({ name, controlsId, apiEndpoint, dataUpdater }) {
        this.name = name;
        this.controlsContainer = document.getElementById(controlsId);
        this.apiEndpoint = apiEndpoint;
        this.dataUpdater = dataUpdater;
        this.dateRange = { start: null, end: null };

        if (!this.controlsContainer) {
            console.error(`模块 [${this.name}] 的控制容器 #${controlsId} 未找到。`);
        }
    }

    init() {
        if (!this.controlsContainer) return;
        this.setDefaultDateRange('month');
        this.setupEventListeners();
        this.fetchData();
    }

    setDefaultDateRange(defaultPeriod) {
        const { start, end } = this.calculateDates(defaultPeriod);
        this.dateRange.start = formatDate(start);
        this.dateRange.end = formatDate(end);
    }

    calculateDates(period) {
        const today = new Date();
        let startDate;

        switch (period) {
            case 'week':
                const dayOfWeek = today.getDay();
                const diff = today.getDate() - dayOfWeek + (dayOfWeek === 0 ? -6 : 1);
                startDate = new Date(new Date().setDate(diff));
                break;
            case 'year':
                startDate = new Date(today.getFullYear(), 0, 1);
                break;
            case 'month':
            default:
                startDate = new Date(today.getFullYear(), today.getMonth(), 1);
                break;
        }
        return { start: startDate, end: new Date() };
    }

    setupEventListeners() {
        this.controlsContainer.querySelectorAll('[data-period]').forEach(button => {
            button.addEventListener('click', (e) => {
                const period = e.target.dataset.period;
                const { start, end } = this.calculateDates(period);
                this.dateRange.start = formatDate(start);
                this.dateRange.end = formatDate(end);
                
                this.fetchData();

                this.controlsContainer.querySelectorAll('[data-period]').forEach(btn => btn.classList.remove('active'));
                e.target.classList.add('active');
            });
        });
    }

    async fetchData() {
        // You might want to show a loading indicator here
        const url = `${this.apiEndpoint}?start_date=${this.dateRange.start}&end_date=${this.dateRange.end}`;
        const result = await apiService.get(url);
        
        if (result.success) {
            this.dataUpdater(result.data);
        } else {
            console.error(`获取模块 [${this.name}] 数据失败:`, result.error);
        }
        // Hide loading indicator here
    }

    getCurrentDateRange() {
        return this.dateRange;
    }
}

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

        // 初始化资金流模块
        this.cashFlowModule = new DashboardModule({
            name: 'cashFlow',
            controlsId: 'cashflow-module-controls',
            apiEndpoint: '/api/dashboard/cash-flow',
            dataUpdater: (data) => {
                this.updateCashFlowChart(data.cash_flow);
                this.updateIncomeCompositionChart(data.income_composition);
            }
        });
        this.cashFlowModule.init();

        // 初始化支出模块
        this.expenseModule = new DashboardModule({
            name: 'expense',
            controlsId: 'expense-module-controls',
            apiEndpoint: '/api/dashboard/expense-analysis',
            dataUpdater: (data) => {
                this.updateExpenseAnalysisModule(data.top_expense_categories);
            }
        });
        this.expenseModule.init();
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
        
        // 资金流分析图
        this.charts.cashFlow = new Chart(document.getElementById('cashFlowChart'), {
            type: 'bar',
            data: { labels: [], datasets: [ { label: '净现金流', data: [], backgroundColor: (context) => { if (!context.parsed || context.parsed.y === undefined) return getCSSColor('--bs-primary-100'); const value = context.parsed.y; return value >= 0 ? getCSSColor('--bs-success-100') : getCSSColor('--bs-danger-100'); }, borderColor: (context) => { if (!context.parsed || context.parsed.y === undefined) return getCSSColor('--bs-primary'); const value = context.parsed.y; return value >= 0 ? getCSSColor('--bs-success') : getCSSColor('--bs-danger'); }, borderWidth: 1 } ] },
            options: { responsive: true, maintainAspectRatio: false, scales: { y: { beginAtZero: true, ticks: { callback: (value) => '¥' + value.toLocaleString() } } } }
        });
        
        // 收入构成图
        this.charts.incomeComposition = new Chart(document.getElementById('incomeCompositionChart'), {
            type: 'doughnut',
            data: { labels: [], datasets: [{ data: [], backgroundColor: this.getChartColors() }] },
            options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { position: 'bottom' } } }
        });
        
        // 支出分类排行图（带点击事件）
        this.charts.expenseTopCategories = new Chart(document.getElementById('expenseTopCategoriesChart'), {
            type: 'doughnut',
            data: { 
                labels: [], 
                datasets: [{ 
                    data: [], 
                    backgroundColor: this.getChartColors(),
                    borderColor: getCSSColor('--bs-body-bg'),
                    borderWidth: 2,
                    hoverOffset: 8
                }] 
            },
            options: {
                responsive: true, 
                maintainAspectRatio: false, 
                cutout: '60%',
                layout: {
                    padding: {
                        top: 50,
                        bottom: 50,
                        left: 50,
                        right: 50
                    }
                },
                plugins: { 
                    legend: { display: false },
                    datalabels: {
                        formatter: (value, context) => {
                            const label = context.chart.data.labels[context.dataIndex];
                            const sum = context.chart.data.datasets[0].data.reduce((a, b) => a + b, 0);
                            const percentage = sum > 0 ? ((value / sum) * 100).toFixed(1) + '%' : '0%';
                            // 返回一个多行标签，显示分类和百分比
                            return `${label} (${percentage})`;
                        },
                        color: getCSSColor('--bs-body-color'),
                        anchor: 'end',
                        align: 'end',
                        offset: 15,
                        textAlign: 'left'
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                let label = context.label || '';
                                if (label) {
                                    label += ': ';
                                }
                                if (context.parsed !== null) {
                                    const value = context.parsed;
                                    const sum = context.dataset.data.reduce((a, b) => a + b, 0);
                                    const percentage = sum > 0 ? ((value / sum) * 100).toFixed(2) + '%' : '0%';
                                    label += `¥${value.toLocaleString('zh-CN')} (${percentage})`;
                                }
                                return label;
                            }
                        }
                    }
                }
            }
        });
    }

    updateDashboard(data) {
        if (!data) return;
        this.updateCoreMetrics(data.core_metrics);
        this.updateNetWorthChart(data.net_worth_trend);
        // The rest of the charts are updated by their respective modules
    }

    updateCoreMetrics(metrics) {
        if (!metrics) return;
        document.getElementById('currentAssets').textContent = `¥${metrics.current_total_assets.toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
        document.getElementById('netIncome').textContent = `¥${metrics.net_income.toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
        this.updateEmergencyReserveMonths(metrics.emergency_reserve_months);
        this.updateChangeIndicator('netChange', metrics.net_change_percentage);
    }

    updateChangeIndicator(elementId, percentage) {
        // This indicator might be deprecated as period-over-period comparison is removed for KPIs
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

    updateCashFlowChart(cashFlowData) {
        if (!cashFlowData || !this.charts.cashFlow) return;
        this.charts.cashFlow.data.labels = cashFlowData.map(d => d.date);
        this.charts.cashFlow.data.datasets[0].data = cashFlowData.map(d => d.value);
        this.charts.cashFlow.update();
    }

    updateIncomeCompositionChart(compositionData) {
        if (!compositionData || !this.charts.incomeComposition) return;
        this.charts.incomeComposition.data.labels = compositionData.map(d => d.label);
        this.charts.incomeComposition.data.datasets[0].data = compositionData.map(d => d.value);
        this.charts.incomeComposition.update();
    }

    updateExpenseAnalysisModule(topCategoriesData) {
        if (!topCategoriesData) return;

        // 更新图表
        if (this.charts.expenseTopCategories) {
            this.charts.expenseTopCategories.data.labels = topCategoriesData.map(d => d.category);
            this.charts.expenseTopCategories.data.datasets[0].data = topCategoriesData.map(d => d.total_amount);
            this.charts.expenseTopCategories.update();
        }

        // 更新表格
        const tableBody = document.getElementById('expense-top-categories-table-body');
        if (tableBody) {
            tableBody.innerHTML = ''; // 清空现有内容

            if (topCategoriesData.length === 0) {
                tableBody.innerHTML = `<tr><td colspan="4" class="text-center text-muted py-3">当前时段无支出数据</td></tr>`;
                return;
            }

            const totalExpense = topCategoriesData.reduce((sum, item) => sum + item.total_amount, 0);

            topCategoriesData.forEach((item, index) => {
                const percentage = totalExpense > 0 ? ((item.total_amount / totalExpense) * 100).toFixed(1) : 0;
                const row = document.createElement('tr');

                row.innerHTML = `
                    <td class="text-center">${index + 1}</td>
                    <td>
                        <span class="d-inline-block text-truncate" style="max-width: 120px;" title="${item.category}">
                            ${item.category}
                        </span>
                    </td>
                    <td class="text-end">¥${item.total_amount.toLocaleString('zh-CN')}</td>
                    <td class="text-end">${percentage}%</td>
                `;
                
                tableBody.appendChild(row);
            });
        }
    }
}

// 初始化页面
document.addEventListener('DOMContentLoaded', () => {
    const page = new FinancialDashboard();
    page.init();
});

 