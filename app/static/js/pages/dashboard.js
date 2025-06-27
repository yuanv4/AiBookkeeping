/**
 * 财务健康仪表盘 JavaScript
 */

import BasePage from '../common/BasePage.js';
import { formatDate, showNotification, apiService, getCSSColor } from '../common/utils.js';

export default class FinancialDashboard extends BasePage {
    constructor() {
        super();
        this.charts = {};
        this.currentData = {};
        this.currentDateRange = {
            start: null,
            end: null
        };
    }
    
    init() {
        super.init();
        
        // 获取初始数据
        const dataContainer = document.getElementById('dashboard-data');
        if (dataContainer) {
            this.currentData = JSON.parse(dataContainer.dataset.initialData);
        }
        
        // 设置默认日期范围
        this.setDefaultDateRange();
        
        // 初始化图表
        this.initializeCharts();
        
        // 渲染初始数据
        this.updateDashboard(this.currentData);
    }
    
    setDefaultDateRange() {
        const today = new Date();
        const thirtyDaysAgo = new Date(today.getTime() - 30 * 24 * 60 * 60 * 1000);
        
        this.currentDateRange.end = formatDate(today);
        this.currentDateRange.start = formatDate(thirtyDaysAgo);
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
    
    setupEventListeners() {
        // 预设时间按钮
        document.querySelectorAll('[data-period]').forEach(button => {
            button.addEventListener('click', (e) => {
                this.handlePresetPeriod(e.target.dataset.period);
                
                // 更新按钮状态
                document.querySelectorAll('[data-period]').forEach(btn => btn.classList.remove('active'));
                e.target.classList.add('active');
            });
        });
    }
    
    handlePresetPeriod(days) {
        const today = new Date();
        const startDate = new Date(today.getTime() - parseInt(days) * 24 * 60 * 60 * 1000);
        
        this.currentDateRange.start = formatDate(startDate);
        this.currentDateRange.end = formatDate(today);
        
        // 更新数据
        this.fetchDashboardData();
    }
    
    async fetchDashboardData() {
        const url = `/dashboard-data?start_date=${this.currentDateRange.start}&end_date=${this.currentDateRange.end}`;
        const result = await apiService.get(url);
        
        if (result.success) {
            this.currentData = result.data;
            this.updateDashboard(result.data);
        } else {
            console.error('获取仪表盘数据失败:', result.error);
        }
    }
    
    initializeCharts() {
        // 净资产趋势图
        this.charts.netWorth = new Chart(document.getElementById('netWorthChart'), {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: '净资产',
                    data: [],
                    borderColor: getCSSColor('--bs-primary'),
                    backgroundColor: getCSSColor('--bs-primary-100'),
                    fill: true,
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    },
                    datalabels: {
                        display: 'auto',
                        align: 'top',
                        anchor: 'end',
                        offset: 8,
                        font: {
                            size: 10
                        },
                        color: '#6c757d',
                        formatter: function(value) {
                            // 格式化为紧凑的货币格式
                            return '¥' + value.toLocaleString('zh-CN', {
                                notation: 'compact',
                                minimumFractionDigits: 0,
                                maximumFractionDigits: 1
                            });
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: false,
                        ticks: {
                            callback: function(value) {
                                return '¥' + value.toLocaleString();
                            }
                        }
                    }
                }
            }
        });
        
        // 资金流分析图
        this.charts.cashFlow = new Chart(document.getElementById('cashFlowChart'), {
            type: 'bar',
            data: {
                labels: [],
                datasets: [
                    {
                        label: '净现金流',
                        data: [],
                        backgroundColor: function(context) {
                            // 检查是否有有效的解析数据
                            if (!context.parsed || context.parsed.y === undefined) {
                                return getCSSColor('--bs-primary-100'); // 默认颜色
                            }
                            const value = context.parsed.y;
                            return value >= 0 ? 
                                getCSSColor('--bs-success-100') : 
                                getCSSColor('--bs-danger-100');
                        },
                        borderColor: function(context) {
                            // 检查是否有有效的解析数据
                            if (!context.parsed || context.parsed.y === undefined) {
                                return getCSSColor('--bs-primary'); // 默认颜色
                            }
                            const value = context.parsed.y;
                            return value >= 0 ? 
                                getCSSColor('--bs-success') : 
                                getCSSColor('--bs-danger');
                        },
                        borderWidth: 1
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: function(value) {
                                return '¥' + value.toLocaleString();
                            }
                        }
                    }
                }
            }
        });
        
        // 收入构成图
        this.charts.incomeComposition = new Chart(document.getElementById('incomeCompositionChart'), {
            type: 'doughnut',
            data: {
                labels: [],
                datasets: [{
                    data: [],
                    backgroundColor: this.getChartColors()
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        });
        
        // 支出分类排行图（带点击事件）
        this.charts.expenseTopCategories = new Chart(document.getElementById('expenseTopCategoriesChart'), {
            type: 'bar',
            data: {
                labels: [],
                datasets: [{
                    label: '支出金额',
                    data: [],
                    backgroundColor: getCSSColor('--bs-danger-100'),
                    borderColor: getCSSColor('--bs-danger'),
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                indexAxis: 'y', // 水平条形图
                plugins: {
                    legend: {
                        display: false
                    },
                    datalabels: {
                        display: true,
                        anchor: 'end',
                        align: 'right',
                        offset: 4,
                        clamp: true,
                        font: {
                            size: 10
                        },
                        color: '#6c757d',
                        formatter: function(value, context) {
                            // 显示金额和百分比
                            const percentage = context.dataset.percentages ? context.dataset.percentages[context.dataIndex] : 0;
                            return `¥${value.toLocaleString()} (${percentage}%)`;
                        }
                    }
                },
                scales: {
                    x: {
                        beginAtZero: true,
                        ticks: {
                            callback: function(value) {
                                return '¥' + value.toLocaleString();
                            }
                        }
                    }
                },
                onClick: (event, elements) => {
                    console.log('支出排行图表点击事件触发:', elements);
                    if (elements.length > 0) {
                        const index = elements[0].index;
                        const label = this.charts.expenseTopCategories.data.labels[index];
                        console.log('点击的分类:', label, '索引:', index);
                        this.fetchCategoryTransactions(label);
                    }
                }
            }
        });
    }
    
    updateDashboard(data) {
        // 更新核心指标
        this.updateCoreMetrics(data.core_metrics);
        
        // 更新图表
        this.updateNetWorthChart(data.net_worth_trend);
        this.updateCashFlowChart(data.cash_flow);
        this.updateIncomeCompositionChart(data.income_composition);
        this.updateExpenseTopCategoriesChart(data.top_expense_categories);
    }
    
    updateCoreMetrics(metrics) {
        document.getElementById('currentAssets').textContent = '¥' + metrics.current_total_assets.toLocaleString('zh-CN', {minimumFractionDigits: 2});
        document.getElementById('totalIncome').textContent = '¥' + metrics.total_income.toLocaleString('zh-CN', {minimumFractionDigits: 2});
        document.getElementById('totalExpense').textContent = '¥' + metrics.total_expense.toLocaleString('zh-CN', {minimumFractionDigits: 2});
        document.getElementById('netIncome').textContent = '¥' + metrics.net_income.toLocaleString('zh-CN', {minimumFractionDigits: 2});
        
        // 更新应急储备月数
        this.updateEmergencyReserveMonths(metrics.emergency_reserve_months);
        
        // 更新变化百分比
        this.updateChangeIndicator('incomeChange', metrics.income_change_percentage);
        this.updateChangeIndicator('expenseChange', metrics.expense_change_percentage);
        this.updateChangeIndicator('netChange', metrics.net_change_percentage);
    }
    
    updateChangeIndicator(elementId, percentage) {
        const element = document.getElementById(elementId);
        const absPercentage = Math.abs(percentage);
        const sign = percentage > 0 ? '+' : percentage < 0 ? '-' : '';
        const color = percentage > 0 ? 'text-success' : percentage < 0 ? 'text-danger' : 'text-muted';
        
        element.textContent = `${sign}${absPercentage.toFixed(1)}%`;
        element.className = `stat-change ${color}`;
    }
    
    updateEmergencyReserveMonths(months) {
        const element = document.getElementById('emergencyReserveMonths');
        if (!element) return;
        
        if (months === -1) {
            element.textContent = '无限';
        } else if (months === 0) {
            element.textContent = '0个月';
        } else {
            const roundedMonths = Math.round(months * 10) / 10; // 保留一位小数
            element.textContent = `${roundedMonths}个月`;
        }
    }
    
    updateNetWorthChart(trendData) {
        if (!trendData || trendData.length === 0) {
            // 清空图表数据
            this.charts.netWorth.data.labels = [];
            this.charts.netWorth.data.datasets[0].data = [];
            this.charts.netWorth.update();
            return;
        }
        
        // 智能处理日期格式：日度(YYYY-MM-DD)、周度(YYYY-Www)、月度(YYYY-MM)
        const labels = trendData.map(item => {
            if (item.date.includes('-W')) {
                // 周度数据格式 YYYY-Www (例如 2024-W23)
                const [year, weekStr] = item.date.split('-W');
                const weekNum = weekStr.padStart(2, '0');
                return `${year}年 第${weekNum}周`;
            } else if (item.date.includes('-') && item.date.split('-').length === 2) {
                // 月度数据格式 YYYY-MM
                const [year, month] = item.date.split('-');
                return `${year}年${month}月`;
            } else {
                // 日度数据格式 YYYY-MM-DD
                return new Date(item.date).toLocaleDateString('zh-CN', {month: 'short', day: 'numeric'});
            }
        });
        const data = trendData.map(item => item.value);
        
        this.charts.netWorth.data.labels = labels;
        this.charts.netWorth.data.datasets[0].data = data;
        this.charts.netWorth.update();
    }
    
    updateCashFlowChart(cashFlowData) {
        if (!cashFlowData || cashFlowData.length === 0) {
            // 清空图表数据
            this.charts.cashFlow.data.labels = [];
            this.charts.cashFlow.data.datasets[0].data = [];
            this.charts.cashFlow.update();
            return;
        }
        
        // 智能处理日期格式：日度(YYYY-MM-DD)、周度(YYYY-Www)、月度(YYYY-MM)
        const labels = cashFlowData.map(item => {
            if (item.date.includes('-W')) {
                // 周度数据格式 YYYY-Www (例如 2024-W23)
                const [year, weekStr] = item.date.split('-W');
                const weekNum = weekStr.padStart(2, '0');
                return `${year}年 第${weekNum}周`;
            } else if (item.date.includes('-') && item.date.split('-').length === 2) {
                // 月度数据格式 YYYY-MM
                const [year, month] = item.date.split('-');
                return `${year}年${month}月`;
            } else {
                // 日度数据格式 YYYY-MM-DD
                return new Date(item.date).toLocaleDateString('zh-CN', {month: 'short', day: 'numeric'});
            }
        });
        const netFlowData = cashFlowData.map(item => item.value);
        
        this.charts.cashFlow.data.labels = labels;
        this.charts.cashFlow.data.datasets[0].data = netFlowData;
        this.charts.cashFlow.update();
    }
    
    updateIncomeCompositionChart(compositionData) {
        if (!compositionData || compositionData.length === 0) {
            // 清空图表数据
            this.charts.incomeComposition.data.labels = [];
            this.charts.incomeComposition.data.datasets[0].data = [];
            this.charts.incomeComposition.update();
            return;
        }
        
        const labels = compositionData.map(item => item.name);
        const data = compositionData.map(item => item.amount);
        
        this.charts.incomeComposition.data.labels = labels;
        this.charts.incomeComposition.data.datasets[0].data = data;
        this.charts.incomeComposition.update();
    }
    
    updateExpenseTopCategoriesChart(topCategoriesData) {
        console.log('更新支出分类排行图表:', topCategoriesData);
        
        if (!topCategoriesData || topCategoriesData.length === 0) {
            // 清空图表数据
            this.charts.expenseTopCategories.data.labels = [];
            this.charts.expenseTopCategories.data.datasets[0].data = [];
            this.charts.expenseTopCategories.data.datasets[0].percentages = [];
            this.charts.expenseTopCategories.update();
            console.log('支出分类排行图表标签: []');
            return;
        }
        
        const labels = topCategoriesData.map(item => item.name);
        const data = topCategoriesData.map(item => item.amount);
        const percentages = topCategoriesData.map(item => item.percentage);
        
        this.charts.expenseTopCategories.data.labels = labels;
        this.charts.expenseTopCategories.data.datasets[0].data = data;
        this.charts.expenseTopCategories.data.datasets[0].percentages = percentages;
        this.charts.expenseTopCategories.update();
        console.log('支出分类排行图表标签:', labels);
    }
    
    async fetchCategoryTransactions(category) {
        try {
            const url = `/category-transactions?category=${encodeURIComponent(category)}&start_date=${this.currentDateRange.start}&end_date=${this.currentDateRange.end}`;
            console.log('请求URL:', url);
            
            const response = await fetch(url);
            console.log('响应状态:', response.status);
            
            if (!response.ok) {
                throw new Error('获取交易明细失败');
            }
            
            const data = await response.json();
            console.log('获取到的数据:', data);
            this.displayTransactionDetails(data);
            
        } catch (error) {
            console.error('获取交易明细失败:', error);
            showNotification('获取交易明细失败，请稍后重试', 'error');
        }
    }
    
    displayTransactionDetails(data) {
        const container = document.getElementById('transactionDetails');
        console.log('显示交易明细:', data);
        
        if (!data.transactions || data.transactions.length === 0) {
            container.innerHTML = `
                <div class="text-center text-muted py-4">
                    <i data-lucide="inbox" class="lucide-icon icon-lg text-muted"></i>
                    <p class="mt-2">该分类暂无交易记录</p>
                </div>
            `;
            // 重新初始化Lucide图标
            if (typeof lucide !== 'undefined') {
                lucide.createIcons();
            }
            return;
        }
        
        let html = `
            <div class="transaction-header mb-3">
                <h6 class="mb-1">${data.category}</h6>
                <small class="text-muted">共 ${data.total_count} 笔交易</small>
            </div>
            <div class="transaction-list">
        `;
        
        data.transactions.forEach(transaction => {
            const amountClass = transaction.amount > 0 ? 'text-success' : 'text-danger';
            const amountSign = transaction.amount > 0 ? '+' : '';
            
            // 格式化日期
            const transactionDate = new Date(transaction.date);
            const formattedDate = transactionDate.toLocaleDateString('zh-CN', {
                year: 'numeric',
                month: '2-digit',
                day: '2-digit'
            });
            
            // 处理对手方信息，参考transactions.html的逻辑
            const counterparty = transaction.counterparty || '未知对手';
            
            // 处理描述信息，参考transactions.html的逻辑
            const description = transaction.description || '无描述';
            const shortDescription = description.length > 20 ? description.substring(0, 20) + '...' : description;
            
            html += `
                <div class="transaction-item">
                    <div class="transaction-info">
                        <div class="transaction-counterparty" title="${counterparty}">${counterparty}</div>
                        <div class="transaction-meta">
                            <span class="transaction-date">${formattedDate}</span>
                            <span class="transaction-description" title="${description}">${shortDescription}</span>
                        </div>
                    </div>
                    <div class="transaction-amount ${amountClass}">
                        ${amountSign}¥${Math.abs(transaction.amount).toLocaleString('zh-CN', {minimumFractionDigits: 2})}
                    </div>
                </div>
            `;
        });
        
        html += '</div>';
        container.innerHTML = html;
    }
}

 