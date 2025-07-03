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
                // 保存完整的支出分析数据供展开功能使用
                this.currentData.expenseAnalysisData = result.data;
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



        // 更新固定支出明细表格（现在显示分组统计）
        this.updateRecurringExpensesTable(data.recurring_expenses || [], data.recurring_transactions || []);

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
     * 格式化频率天数为用户友好的显示文本
     */
    formatFrequencyDays(days) {
        if (!days || days <= 0) return '不规律';
        if (days <= 10) return `${days}天`;
        if (days <= 35) return `${days}天`;
        if (days <= 100) return `约${Math.round(days/7)}周`;
        return `约${Math.round(days/30)}个月`;
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
     * 更新固定支出分组统计表格
     */
    updateRecurringExpensesTable(recurringExpenses, recurringTransactions) {
        const tableBody = document.getElementById('recurring-expenses-table-body');
        if (!tableBody) return;

        tableBody.innerHTML = '';

        if (!recurringExpenses || recurringExpenses.length === 0) {
            tableBody.innerHTML = `<tr><td colspan="7" class="text-center text-muted py-3">暂无固定支出</td></tr>`;
            return;
        }

        // 构建交易明细映射表
        const transactionsByKey = {};
        if (recurringTransactions) {
            recurringTransactions.forEach(group => {
                transactionsByKey[group.combination_key] = group.transactions || [];
            });
        }

        // 显示分组统计信息
        recurringExpenses.forEach((expense, index) => {
            const row = document.createElement('tr');
            row.className = 'recurring-expense-row';
            row.dataset.combinationKey = expense.combination_key || '';
            
            // 频率显示转换
            const frequencyText = this.formatFrequencyDays(expense.frequency);

            // 置信度百分比
            const confidencePercentage = `${expense.confidence_score}%`;

            // 格式化最近发生日期
            const lastOccurrence = new Date(expense.last_occurrence).toLocaleDateString('zh-CN');

            row.innerHTML = `
                <td>
                    <span class="d-inline-block text-truncate" style="max-width: 120px;" title="${expense.combination_key}">
                        ${expense.combination_key}
                    </span>
                </td>
                <td>${frequencyText}</td>
                <td class="text-center">
                    <span class="badge ${expense.confidence_score >= 80 ? 'bg-success' : expense.confidence_score >= 60 ? 'bg-warning' : 'bg-secondary'}">
                        ${confidencePercentage}
                    </span>
                </td>
                <td class="text-center">${expense.count}</td>
                <td>${lastOccurrence}</td>
                <td class="text-end">¥${expense.total_amount.toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</td>
                <td class="text-center">
                    <button class="btn btn-sm btn-outline-primary toggle-details-btn" 
                            data-combination-key="${expense.combination_key || ''}"
                            title="查看交易明细">
                        ▼
                    </button>
                </td>
            `;
            
            tableBody.appendChild(row);

            // 为展开按钮添加事件监听器
            const toggleBtn = row.querySelector('.toggle-details-btn');
            toggleBtn.addEventListener('click', (e) => {
                this.toggleTransactionDetails(e.target.closest('button'));
            });
        });
    }

    /**
     * 切换交易明细的显示/隐藏
     */
    toggleTransactionDetails(button) {
        const combinationKey = button.dataset.combinationKey;
        const row = button.closest('tr');
        const tableBody = row.parentNode;
        
        // 查找是否已有明细行
        let detailsRow = row.nextElementSibling;
        const isDetailsRow = detailsRow && detailsRow.classList.contains('transaction-details-row');
        
        if (isDetailsRow) {
            // 已展开，收起明细
            detailsRow.remove();
            button.innerHTML = '▼';
            button.title = '查看交易明细';
        } else {
            // 未展开，显示明细
            const detailsRowElement = this.createTransactionDetailsRow(combinationKey);
            if (detailsRowElement) {
                row.insertAdjacentElement('afterend', detailsRowElement);
                button.innerHTML = '▲';
                button.title = '收起明细';
            }
        }
    }

    /**
     * 创建交易明细行
     */
    createTransactionDetailsRow(combinationKey) {
        // 从当前数据中查找交易明细
        const expenseData = this.currentData.expenseAnalysisData || {};
        const recurringTransactions = expenseData.recurring_transactions || [];
        
        const transactionGroup = recurringTransactions.find(group => 
            group.combination_key === combinationKey
        );
        
        if (!transactionGroup || !transactionGroup.transactions || transactionGroup.transactions.length === 0) {
            return null;
        }

        const detailsRow = document.createElement('tr');
        detailsRow.className = 'transaction-details-row';
        
        const detailsCell = document.createElement('td');
        detailsCell.colSpan = 7;
        detailsCell.className = 'p-0';
        
        // 创建明细表格
        const detailsTable = document.createElement('div');
        detailsTable.className = 'table-responsive bg-light';
        
        let detailsHtml = `
            <table class="table table-sm table-borderless mb-0 small">
                <thead class="bg-light">
                    <tr>
                        <th class="text-muted" style="padding-left: 2rem;">日期</th>
                        <th class="text-muted">账户</th>
                        <th class="text-muted text-end">金额</th>
                        <th class="text-muted">对手信息</th>
                        <th class="text-muted">摘要</th>
                    </tr>
                </thead>
                <tbody>
        `;
        
        transactionGroup.transactions.forEach(transaction => {
            const dateStr = new Date(transaction.date).toLocaleDateString('zh-CN');
            const amount = Math.abs(transaction.amount || 0);
            const amountStr = `¥${amount.toLocaleString('zh-CN')}`;
            
            detailsHtml += `
                <tr>
                    <td style="padding-left: 2rem;">${dateStr}</td>
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
                </tr>
            `;
        });
        
        detailsHtml += `
                </tbody>
            </table>
        `;
        
        detailsTable.innerHTML = detailsHtml;
        detailsCell.appendChild(detailsTable);
        detailsRow.appendChild(detailsCell);
        
        return detailsRow;
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

 