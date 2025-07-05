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
        this.trendChartBaseMonth = new Date(); // 添加：趋势图表的基准月份（结束月份）
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
                    },
                    tooltip: {
                        callbacks: {
                            title: (tooltipItems) => {
                                return '点击选择此月份';
                            }
                        }
                    } 
                }, 
                scales: { 
                    y: { 
                        beginAtZero: true, 
                        ticks: { 
                            callback: (value) => '¥' + value.toLocaleString() 
                        } 
                    } 
                },
                onClick: (event, elements, chart) => {
                    // 处理柱状图点击事件
                    if (elements && elements.length > 0) {
                        const clickedIndex = elements[0].index;
                        const trendData = this.currentData.expenseAnalysisData?.expense_trend || [];
                        if (trendData[clickedIndex]) {
                            const dateStr = trendData[clickedIndex].date;
                            this.selectMonthFromTrendChart(dateStr);
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
     * 包含数据获取逻辑
     */
    initializeExpenseModule() {
        this.currentExpenseMonth = new Date(); // 默认当前月份
        this.selectedTrendMonth = null; // 跟踪当前选中的月份索引
        this.trendChartBaseMonth = new Date(); // 趋势图的基准月份
        this.setupTrendNavigation(); // 设置趋势图导航
        this.loadExpenseAnalysisData();
    }

    /**
     * 设置趋势图导航按钮
     */
    setupTrendNavigation() {
        // 添加翻页按钮事件监听
        const prevButton = document.getElementById('prev-trend-months');
        const nextButton = document.getElementById('next-trend-months');
        
        if (prevButton) {
            prevButton.addEventListener('click', () => this.navigateTrendMonths('prev'));
        }
        
        if (nextButton) {
            nextButton.addEventListener('click', () => this.navigateTrendMonths('next'));
        }
        
        // 初始化趋势图标题
        this.updateTrendDateRangeText();
    }

    /**
     * 导航趋势图月份
     * @param {string} direction - 导航方向：'prev' 或 'next'
     */
    navigateTrendMonths(direction) {
        // 根据方向调整基准月份
        if (direction === 'prev') {
            // 向前翻页：基准月份减去6个月
            this.trendChartBaseMonth = new Date(
                this.trendChartBaseMonth.getFullYear(),
                this.trendChartBaseMonth.getMonth() - 6,
                1
            );
        } else if (direction === 'next') {
            // 向后翻页：基准月份加上6个月，但不超过当前月份
            const newBaseMonth = new Date(
                this.trendChartBaseMonth.getFullYear(),
                this.trendChartBaseMonth.getMonth() + 6,
                1
            );
            
            const currentMonth = new Date();
            currentMonth.setDate(1); // 设置为当月1日
            
            if (newBaseMonth > currentMonth) {
                this.trendChartBaseMonth = currentMonth;
            } else {
                this.trendChartBaseMonth = newBaseMonth;
            }
        }
        
        // 重新加载趋势图数据
        this.loadTrendChartData();
        
        // 更新日期范围文本
        this.updateTrendDateRangeText();
    }

    /**
     * 更新趋势图日期范围文本
     */
    updateTrendDateRangeText() {
        const rangeElement = document.getElementById('expense-trend-range');
        if (!rangeElement) return;
        
        // 计算起始月份（当前基准月份减5个月）
        const startMonth = new Date(
            this.trendChartBaseMonth.getFullYear(),
            this.trendChartBaseMonth.getMonth() - 5,
            1
        );
        
        // 格式化日期范围
        const startMonthText = `${startMonth.getFullYear()}年${startMonth.getMonth() + 1}月`;
        const endMonthText = `${this.trendChartBaseMonth.getFullYear()}年${this.trendChartBaseMonth.getMonth() + 1}月`;
        
        rangeElement.textContent = `(${startMonthText} - ${endMonthText})`;
        
        // 处理按钮禁用状态
        this.updateTrendNavigationButtons();
    }

    /**
     * 更新趋势图导航按钮状态
     */
    updateTrendNavigationButtons() {
        const prevButton = document.getElementById('prev-trend-months');
        const nextButton = document.getElementById('next-trend-months');
        
        if (nextButton) {
            // 如果基准月份是当前月份，则禁用"下一页"按钮
            const currentMonth = new Date();
            currentMonth.setDate(1); // 设置为当月1日
            
            const isCurrentMonth = this.trendChartBaseMonth.getFullYear() === currentMonth.getFullYear() && 
                                this.trendChartBaseMonth.getMonth() === currentMonth.getMonth();
            
            nextButton.disabled = isCurrentMonth;
        }
        
        // "上一页"按钮始终启用，因为我们可以无限往前查看历史数据
    }

    /**
     * 加载趋势图数据
     */
    async loadTrendChartData() {
        try {
            // 格式化基准月份
            const monthStr = `${this.trendChartBaseMonth.getFullYear()}-${String(this.trendChartBaseMonth.getMonth() + 1).padStart(2, '0')}`;
            const url = `/api/dashboard/expense-analysis?target_month=${monthStr}`;
            
            // 显示加载状态
            const chartCanvas = document.getElementById('expenseTrendChart');
            if (chartCanvas) {
                chartCanvas.style.opacity = '0.5';
            }
            
            const result = await apiService.get(url);
            
            if (result.success && result.data && result.data.expense_trend) {
                // 更新趋势图
                this.updateExpenseTrendChart(result.data.expense_trend);
                
                // 保存趋势数据供高亮显示使用
                if (!this.currentData.expenseAnalysisData) {
                    this.currentData.expenseAnalysisData = {};
                }
                this.currentData.expenseAnalysisData.expense_trend = result.data.expense_trend;
                
                // 更新高亮显示
                this.updateExpenseTrendChartHighlight();
            } else {
                console.error('获取支出趋势数据失败:', result.error);
            }
            
            // 恢复显示
            if (chartCanvas) {
                chartCanvas.style.opacity = '1';
            }
        } catch (error) {
            console.error('加载趋势图数据异常:', error);
        }
    }

    /**
     * 通过趋势图选择月份
     * @param {string} dateStr 格式为YYYY-MM的日期字符串
     */
    selectMonthFromTrendChart(dateStr) {
        try {
            // 解析日期字符串为Date对象 (格式: YYYY-MM)
            const dateParts = dateStr.split('-');
            if (dateParts.length >= 2) {
                const year = parseInt(dateParts[0], 10);
                const month = parseInt(dateParts[1], 10) - 1; // 月份从0开始
                
                // 更新当前选择的月份
                this.currentExpenseMonth = new Date(year, month, 1);
                
                // 保存选中的月份字符串用于高亮显示
                this.selectedTrendMonth = dateStr;
                
                // 重新加载详情数据，但不重新加载趋势图数据
                this.loadMonthlyDetailsData();
                
                // 高亮显示选中的月份
                this.updateExpenseTrendChartHighlight();
                
                // 显示通知
                showNotification(`已选择 ${year}年${month + 1}月 的数据`, 'info', 2000);
            }
        } catch (error) {
            console.error('选择月份出错:', error);
        }
    }

    /**
     * 更新趋势图高亮显示
     */
    updateExpenseTrendChartHighlight() {
        if (!this.charts.expenseTrend) return;
        
        // 获取当前数据
        const datasets = this.charts.expenseTrend.data.datasets;
        if (!datasets || datasets.length === 0) return;
        
        // 检查当前趋势图是否包含选中的月份
        const trendData = this.currentData.expenseAnalysisData?.expense_trend || [];
        
        // 更新背景颜色数组
        const backgroundColors = trendData.map(d => {
            // 如果有选中的月份且与当前数据项匹配，则高亮显示
            if (this.selectedTrendMonth && d.date === this.selectedTrendMonth) {
                return getCSSColor('--bs-warning'); // 高亮颜色
            }
            return getCSSColor('--bs-warning-200'); // 默认颜色
        });
        
        // 更新数据集的背景颜色
        datasets[0].backgroundColor = backgroundColors;
        
        // 更新图表
        this.charts.expenseTrend.update();
    }

    /**
     * 加载选定月份的详情数据
     */
    async loadMonthlyDetailsData() {
        try {
            // 只加载选中月份的详细数据
            const monthStr = `${this.currentExpenseMonth.getFullYear()}-${String(this.currentExpenseMonth.getMonth() + 1).padStart(2, '0')}`;
            const url = `/api/dashboard/expense-analysis?target_month=${monthStr}`;
            
            const result = await apiService.get(url);
            
            if (result.success) {
                // 更新详情数据
                
                // 保存完整的数据用于展开交易明细功能
                if (!this.currentData.expenseAnalysisData) {
                    this.currentData.expenseAnalysisData = {};
                }
                // 只更新详情相关的数据，保留趋势图数据
                const trendData = this.currentData.expenseAnalysisData.expense_trend || [];
                this.currentData.expenseAnalysisData = {
                    ...result.data,
                    expense_trend: trendData
                };
                
                // 更新UI组件
                this.updateMonthlyDetails(result.data);
            } else {
                console.error('获取月度详情数据失败:', result.error);
                showNotification('获取月度详情数据失败', 'error');
            }
        } catch (error) {
            console.error('月度详情数据加载异常:', error);
        }
    }

    /**
     * 更新月度详情数据
     */
    updateMonthlyDetails(data) {
        if (!data) return;
        
        // 更新总支出显示
        this.updateTotalExpense(data.total_expense || 0);
        
        // 更新固定支出明细表格
        this.updateRecurringExpensesTable(data.recurring_expenses || [], data.recurring_transactions || []);
        
        // 更新弹性支出明细表格
        this.updateFlexibleExpensesTable(data.flexible_transactions || []);
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
                
                // 初始化趋势图
                this.updateExpenseTrendChart(result.data.expense_trend || []);
                
                // 设置初始趋势图基准月份
                this.trendChartBaseMonth = new Date(this.currentExpenseMonth);
                
                // 更新日期范围文本
                this.updateTrendDateRangeText();
                
                // 更新详情数据
                this.updateMonthlyDetails(result.data);
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
     * 获取排名样式类
     */
    getRankClass(rank) {
        if (rank <= 3) return 'bg-warning text-dark'; // 前三名
        if (rank <= 10) return 'bg-primary'; // 前10名
        return 'bg-secondary'; // 其他排名
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
        
        // 设置默认颜色（不再处理高亮，由updateExpenseTrendChartHighlight负责）
        const defaultColor = getCSSColor('--bs-warning-200');
        const backgroundColors = new Array(trendData.length).fill(defaultColor);

        this.charts.expenseTrend.data.labels = labels;
        this.charts.expenseTrend.data.datasets[0].data = values;
        this.charts.expenseTrend.data.datasets[0].backgroundColor = backgroundColors;
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
            tableBody.innerHTML = `<tr><td colspan="9" class="text-center text-muted py-3">暂无固定支出</td></tr>`;
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
            row.className = 'recurring-expense-row clickable-row';
            row.dataset.combinationKey = expense.combination_key || '';
            row.tabIndex = '0';
            row.setAttribute('role', 'button');
            row.setAttribute('aria-expanded', 'false');
            
            // 排名计算
            const rank = index + 1;
            const rankClass = this.getRankClass(rank);
            
            // 频率显示转换
            const frequencyText = this.formatFrequencyDays(expense.frequency);

            // 置信度百分比
            const confidencePercentage = `${expense.confidence_score}%`;

            // 格式化最近发生日期
            const lastOccurrence = new Date(expense.last_occurrence).toLocaleDateString('zh-CN');

            row.innerHTML = `
                <td class="text-center">
                    <span class="badge ${rankClass}">${rank}</span>
                </td>
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
                <td class="text-end text-danger position-relative">
                    ¥${expense.total_amount.toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                    <span class="expand-indicator"></span>
                </td>
            `;
            
            tableBody.appendChild(row);

            // 为整行添加点击事件监听器
            row.addEventListener('click', (e) => {
                this.toggleTransactionDetails(row);
            });

            // 添加键盘导航支持
            row.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    this.toggleTransactionDetails(row);
                }
            });
        });
    }

    /**
     * 切换交易明细的显示/隐藏
     */
    toggleTransactionDetails(row) {
        const combinationKey = row.dataset.combinationKey;
        const tableBody = row.parentNode;
        
        // 查找是否已有明细行
        let detailsRow = row.nextElementSibling;
        const isDetailsRow = detailsRow && detailsRow.classList.contains('transaction-details-row');
        
        if (isDetailsRow) {
            // 已展开，收起明细
            detailsRow.remove();
            row.setAttribute('aria-expanded', 'false');
        } else {
            // 未展开，显示明细
            const detailsRowElement = this.createTransactionDetailsRow(combinationKey);
            if (detailsRowElement) {
                row.insertAdjacentElement('afterend', detailsRowElement);
                row.setAttribute('aria-expanded', 'true');
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
            tableBody.innerHTML = `<tr><td colspan="6" class="text-center text-muted py-3">暂无弹性支出</td></tr>`;
            return;
        }

        flexibleTransactions.forEach((transaction, index) => {
            const row = document.createElement('tr');
            const rank = index + 1; // 排名从1开始
            
            // 格式化日期
            const dateStr = new Date(transaction.date).toLocaleDateString('zh-CN');
            
            // 格式化金额（支出显示为负数）
            const amount = transaction.amount || 0;
            const amountStr = amount < 0 ? `¥${Math.abs(amount).toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` : `¥${amount.toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;

            row.innerHTML = `
                <td class="text-center">
                    <span class="badge ${this.getRankClass(rank)}">${rank}</span>
                </td>
                <td>${dateStr}</td>
                <td>
                    <span class="d-inline-block text-truncate" style="max-width: 80px;" title="${transaction.account_name || ''}">
                        ${transaction.account_name || ''}
                    </span>
                </td>
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
                <td class="text-end text-danger">${amountStr}</td>
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

 