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

        // 初始化支出结构透视模块（月份选择器）
        this.initializeExpenseModule();
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
        


        // 近6个月支出趋势图
        this.charts.expenseTrend = new Chart(document.getElementById('expenseTrendChart'), {
            type: 'bar',
            data: { 
                labels: [], 
                datasets: [{ 
                    label: '支出金额', 
                    data: [], 
                    borderColor: getCSSColor('--bs-warning'), 
                    backgroundColor: getCSSColor('--bs-warning-200'),
                    borderWidth: 1,
                    borderRadius: 4,
                    borderSkipped: false
                }] 
            },
            options: { 
                responsive: true, 
                maintainAspectRatio: false,
                plugins: { 
                    legend: { display: false },
                    datalabels: { 
                        display: 'auto', 
                        align: 'top', 
                        anchor: 'end', 
                        offset: 8, 
                        font: { size: 10 }, 
                        color: '#6c757d', 
                        formatter: (value) => '¥' + value.toLocaleString('zh-CN', { notation: 'compact', minimumFractionDigits: 0, maximumFractionDigits: 1 }) 
                    } 
                }, 
                scales: { 
                    y: { 
                        beginAtZero: true, 
                        ticks: { 
                            callback: (value) => '¥' + value.toLocaleString() 
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

    /**
     * 初始化支出结构透视模块
     * 包含月份选择器和数据获取逻辑
     */
    initializeExpenseModule() {
        this.currentExpenseMonth = new Date(); // 默认当前月份
        this.initializeMonthSelector();
        this.loadExpenseAnalysisData();
    }

    /**
     * 初始化月份选择器
     */
    initializeMonthSelector() {
        const selector = document.getElementById('expense-month-selector');
        if (!selector) return;

        // 生成最近12个月的选项
        const currentDate = new Date();
        for (let i = 0; i < 12; i++) {
            const date = new Date(currentDate.getFullYear(), currentDate.getMonth() - i, 1);
            const value = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`;
            const text = `${date.getFullYear()}年${date.getMonth() + 1}月`;
            
            const option = document.createElement('option');
            option.value = value;
            option.textContent = text;
            if (i === 0) option.selected = true; // 默认选中当前月
            
            selector.appendChild(option);
        }

        // 添加变化事件监听器
        selector.addEventListener('change', (e) => {
            const selectedMonth = e.target.value;
            this.currentExpenseMonth = new Date(selectedMonth + '-01');
            this.loadExpenseAnalysisData();
        });
    }

    /**
     * 加载支出分析数据
     */
    async loadExpenseAnalysisData() {
        try {
            const monthStr = `${this.currentExpenseMonth.getFullYear()}-${String(this.currentExpenseMonth.getMonth() + 1).padStart(2, '0')}`;
            const url = `/api/dashboard/expense-analysis?target_month=${monthStr}`;
            
            const result = await apiService.get(url);
            
            if (result.success) {
                this.updateExpenseAnalysisModule(result.data);
            } else {
                console.error('获取支出分析数据失败:', result.error);
                showNotification('获取支出分析数据失败', 'error');
            }
        } catch (error) {
            console.error('支出分析数据加载异常:', error);
            showNotification('支出分析数据加载异常', 'error');
        }
    }

    /**
     * 更新支出分析模块的所有组件
     */
    updateExpenseAnalysisModule(data) {
        if (!data) return;

        // 更新总支出显示
        this.updateTotalExpense(data.total_expense || 0);

        // 更新近6个月趋势图
        this.updateExpenseTrendChart(data.expense_trend || []);

        // 更新支出分类排行Top10表格
        this.updateExpenseTopCategoriesTable(data.top_expense_categories || []);

        // 更新固定周期性支出明细表格
        this.updateRecurringExpensesTable(data.recurring_transactions || []);

        // 更新弹性支出明细表格
        this.updateFlexibleExpensesTable(data.flexible_transactions || []);
    }

    /**
     * 更新总支出显示
     */
    updateTotalExpense(totalExpense) {
        const element = document.getElementById('total-expense-amount');
        if (element) {
            element.textContent = `¥${totalExpense.toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
        }
    }

    /**
     * 更新近6个月支出趋势图
     */
    updateExpenseTrendChart(trendData) {
        if (!this.charts.expenseTrend || !trendData) return;

        const labels = trendData.map(d => {
            const date = new Date(d.date);
            return `${date.getMonth() + 1}月`;
        });
        const values = trendData.map(d => d.value);

        this.charts.expenseTrend.data.labels = labels;
        this.charts.expenseTrend.data.datasets[0].data = values;
        this.charts.expenseTrend.update();
    }



    /**
     * 更新支出分类排行Top10表格
     */
    updateExpenseTopCategoriesTable(topCategoriesData) {
        const tableBody = document.getElementById('expense-top-categories-table-body');
        if (!tableBody) return;

        tableBody.innerHTML = '';

        if (!topCategoriesData || topCategoriesData.length === 0) {
            tableBody.innerHTML = `<tr><td colspan="4" class="text-center text-muted py-3">当前月份无支出数据</td></tr>`;
            return;
        }

        const totalExpense = topCategoriesData.reduce((sum, item) => sum + item.total_amount, 0);

        // 限制显示前10项
        const top10Data = topCategoriesData.slice(0, 10);

        top10Data.forEach((item, index) => {
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

    /**
     * 更新固定周期性支出明细表格
     */
    updateRecurringExpensesTable(recurringTransactions) {
        const tableBody = document.getElementById('recurring-expenses-table-body');
        if (!tableBody) return;

        tableBody.innerHTML = '';

        if (!recurringTransactions || recurringTransactions.length === 0) {
            tableBody.innerHTML = `<tr><td colspan="5" class="text-center text-muted py-3">暂无固定周期性支出</td></tr>`;
            return;
        }

        recurringTransactions.slice(0, 10).forEach((transaction) => {
            const row = document.createElement('tr');
            
            // 格式化日期
            const dateStr = new Date(transaction.date).toLocaleDateString('zh-CN');
            
            // 格式化金额（支出显示为负数）
            const amount = transaction.amount || 0;
            const amountStr = amount < 0 ? `¥${Math.abs(amount).toLocaleString('zh-CN')}` : `¥${amount.toLocaleString('zh-CN')}`;

            row.innerHTML = `
                <td>${dateStr}</td>
                <td>
                    <span class="d-inline-block text-truncate" style="max-width: 80px;" title="${transaction.account_name || ''}">
                        ${transaction.account_name || ''}
                    </span>
                </td>
                <td class="text-end text-danger">${amountStr}</td>
                <td>
                    <span class="d-inline-block text-truncate" style="max-width: 100px;" title="${transaction.counterparty || ''}">
                        ${transaction.counterparty || ''}
                    </span>
                </td>
                <td>
                    <span class="d-inline-block text-truncate" style="max-width: 120px;" title="${transaction.description || ''}">
                        ${transaction.description || ''}
                    </span>
                </td>
            `;
            
            tableBody.appendChild(row);
        });
    }

    /**
     * 更新弹性支出明细表格
     */
    updateFlexibleExpensesTable(flexibleTransactions) {
        const tableBody = document.getElementById('flexible-expenses-table-body');
        if (!tableBody) return;

        tableBody.innerHTML = '';

        if (!flexibleTransactions || flexibleTransactions.length === 0) {
            tableBody.innerHTML = `<tr><td colspan="5" class="text-center text-muted py-3">暂无弹性支出</td></tr>`;
            return;
        }

        flexibleTransactions.slice(0, 10).forEach((transaction) => {
            const row = document.createElement('tr');
            
            // 格式化日期
            const dateStr = new Date(transaction.date).toLocaleDateString('zh-CN');
            
            // 格式化金额（支出显示为负数）
            const amount = transaction.amount || 0;
            const amountStr = amount < 0 ? `¥${Math.abs(amount).toLocaleString('zh-CN')}` : `¥${amount.toLocaleString('zh-CN')}`;

            row.innerHTML = `
                <td>${dateStr}</td>
                <td>
                    <span class="d-inline-block text-truncate" style="max-width: 80px;" title="${transaction.account_name || ''}">
                        ${transaction.account_name || ''}
                    </span>
                </td>
                <td class="text-end text-danger">${amountStr}</td>
                <td>
                    <span class="d-inline-block text-truncate" style="max-width: 100px;" title="${transaction.counterparty || ''}">
                        ${transaction.counterparty || ''}
                    </span>
                </td>
                <td>
                    <span class="d-inline-block text-truncate" style="max-width: 120px;" title="${transaction.description || ''}">
                        ${transaction.description || ''}
                    </span>
                </td>
            `;
            
            tableBody.appendChild(row);
        });
    }
}

// 初始化页面
document.addEventListener('DOMContentLoaded', () => {
    const page = new FinancialDashboard();
    page.init();
});

 