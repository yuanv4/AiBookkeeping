/**
 * 支出分类分析页面 - 简化版本
 * 将原有的5个类合并为1个类，减少复杂度
 */

import BasePage from '../common/BasePage.js';
import { ChartHelper, showNotification, apiService } from '../common/utils.js';

class ExpenseAnalysisPage extends BasePage {
    constructor() {
        super();
        
        // 简化的状态管理 - 直接使用属性而不是复杂的状态管理器
        this.selectedMonth = null;
        this.availableMonths = [];
        this.categoryData = {};
        this.loading = false;
        this.chart = null;
        this.expandedCategories = new Set();

        this.init();
    }

    async init() {
        try {
            console.log('支出分析页面初始化');
            window.expenseAnalysisPage = this;

            await this.loadAvailableMonths();
            await this.loadInitialData();
            
        } catch (error) {
            console.error('页面初始化失败:', error);
        }
    }

    // 数据加载方法
    async loadAvailableMonths() {
        try {
            const response = await fetch('/expense-analysis/api/available-months');
            const result = await response.json();
            
            if (result.success) {
                this.availableMonths = result.data.months || [];
                
                // 确定初始月份
                const urlParams = new URLSearchParams(window.location.search);
                const urlMonth = urlParams.get('month');
                
                this.selectedMonth = (urlMonth && this.availableMonths.includes(urlMonth)) 
                    ? urlMonth 
                    : result.data.latest_month;
                    
            } else {
                throw new Error(result.error || '获取可用月份失败');
            }
        } catch (error) {
            console.error('加载可用月份失败:', error);
        }
    }

    async loadInitialData() {
        if (!this.selectedMonth) return;

        await this.loadMonthData(this.selectedMonth);
        this.renderChart();
        this.renderCategories();
    }

    async loadMonthData(month) {
        try {
            this.setLoading(true);

            const response = await fetch(`/expense-analysis/api/merchant-analysis?month=${month}`);
            const result = await response.json();

            if (result.success) {
                this.categoryData = result.data;
                this.selectedMonth = month;
            } else {
                throw new Error(result.error || '加载数据失败');
            }

        } catch (error) {
            console.error('加载月份数据失败:', error);
        } finally {
            this.setLoading(false);
        }
    }

    // 月份选择
    async selectMonth(month) {
        if (this.selectedMonth === month) return;
        
        await this.loadMonthData(month);
        this.renderChart();
        this.renderCategories();
    }

    // 渲染方法
    renderChart() {
        if (!this.categoryData.categories) return;
        
        const canvas = document.getElementById('monthly-trend-chart');
        if (!canvas) return;
        
        // 销毁现有图表
        if (this.chart) {
            this.chart.destroy();
            this.chart = null;
        }
        
        // 构建图表数据
        const chartData = this.buildChartData();
        
        this.chart = ChartHelper.createBarChart('monthly-trend-chart', {
            data: chartData,
            options: this.getChartOptions()
        });
    }

    buildChartData() {
        const { categories } = this.categoryData;
        const monthlyDataMap = {};
        
        // 收集月度数据
        Object.keys(categories).forEach(categoryKey => {
            const categoryData = categories[categoryKey];
            if (categoryData.monthly_data) {
                Object.keys(categoryData.monthly_data).forEach(month => {
                    if (!monthlyDataMap[month]) {
                        monthlyDataMap[month] = {};
                    }
                    monthlyDataMap[month][categoryKey] = categoryData.monthly_data[month];
                });
            }
        });
        
        // 准备图表数据
        const allMonths = Object.keys(monthlyDataMap).sort();
        const selectedIndex = allMonths.indexOf(this.selectedMonth);
        
        let labels;
        if (selectedIndex >= 0) {
            const endIndex = selectedIndex + 1;
            const startIndex = Math.max(0, endIndex - 5);
            labels = allMonths.slice(startIndex, endIndex);
        } else {
            labels = allMonths.slice(-5);
        }
        
        return {
            labels: labels,
            datasets: [
                {
                    label: '餐饮支出',
                    data: labels.map(month => monthlyDataMap[month]?.dining || 0),
                    backgroundColor: 'rgba(13, 110, 253, 0.8)',
                    borderColor: 'rgba(13, 110, 253, 1)',
                    borderWidth: 1,
                    stack: 'expenses'
                },
                {
                    label: '交通支出',
                    data: labels.map(month => monthlyDataMap[month]?.transport || 0),
                    backgroundColor: 'rgba(25, 135, 84, 0.8)',
                    borderColor: 'rgba(25, 135, 84, 1)',
                    borderWidth: 1,
                    stack: 'expenses'
                },
                {
                    label: '购物支出',
                    data: labels.map(month => monthlyDataMap[month]?.shopping || 0),
                    backgroundColor: 'rgba(13, 202, 240, 0.8)',
                    borderColor: 'rgba(13, 202, 240, 1)',
                    borderWidth: 1,
                    stack: 'expenses'
                },
                {
                    label: '其他支出',
                    data: labels.map(month => {
                        const monthData = monthlyDataMap[month] || {};
                        return (monthData.services || 0) + (monthData.healthcare || 0) +
                               (monthData.finance || 0) + (monthData.other || 0);
                    }),
                    backgroundColor: 'rgba(108, 117, 125, 0.8)',
                    borderColor: 'rgba(108, 117, 125, 1)',
                    borderWidth: 1,
                    stack: 'expenses'
                }
            ]
        };
    }

    getChartOptions() {
        return {
            responsive: true,
            plugins: {
                legend: { position: 'top' },
                tooltip: {
                    callbacks: {
                        label: (context) => context.dataset.label + ': ¥' + context.parsed.y.toFixed(2)
                    }
                }
            },
            onClick: (_, elements) => {
                if (elements.length > 0) {
                    const clickedIndex = elements[0].index;
                    const labels = this.chart.data.labels;
                    const clickedMonth = labels[clickedIndex];
                    this.selectMonth(clickedMonth);
                }
            },
            scales: {
                x: { stacked: true },
                y: { 
                    stacked: true,
                    beginAtZero: true,
                    ticks: {
                        callback: (value) => '¥' + value.toFixed(0)
                    }
                }
            }
        };
    }

    // 分类渲染
    renderCategories() {
        const container = document.getElementById('expense-categories');
        if (!container || !this.categoryData.categories) return;

        const categories = Object.entries(this.categoryData.categories)
            .sort((a, b) => b[1].total_amount - a[1].total_amount);

        container.innerHTML = categories.map(([categoryKey, categoryData]) => {
            const isExpanded = this.expandedCategories.has(categoryKey);
            const merchantCount = Object.keys(categoryData.merchants || {}).length;

            return `
                <div class="category-summary-card mb-3">
                    <div class="card border-0 shadow-sm">
                        <div class="card-body p-3 cursor-pointer" onclick="window.expenseAnalysisPage.toggleCategory('${categoryKey}')">
                            <div class="d-flex align-items-center justify-content-between">
                                <div class="d-flex align-items-center">
                                    <div class="me-3 bg-${categoryData.color} bg-opacity-10 rounded-circle d-flex align-items-center justify-content-center" style="width: 2.5rem; height: 2.5rem;">
                                        <i data-lucide="${categoryData.icon}" class="text-${categoryData.color}" style="width: 1.25rem; height: 1.25rem;"></i>
                                    </div>
                                    <div>
                                        <h6 class="mb-1 fw-bold text-${categoryData.color}">${categoryData.name}</h6>
                                        <small class="text-muted">${merchantCount}个商户 • ${categoryData.percentage.toFixed(1)}%</small>
                                    </div>
                                </div>
                                <div class="d-flex align-items-center">
                                    <div class="text-end me-3">
                                        <div class="fw-bold text-${categoryData.color} fs-5">¥${categoryData.total_amount.toFixed(0)}</div>
                                        <small class="text-muted">总支出</small>
                                    </div>
                                    <div class="text-${categoryData.color}">
                                        <i data-lucide="${isExpanded ? 'chevron-up' : 'chevron-down'}" style="width: 1.25rem; height: 1.25rem;"></i>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div class="category-details collapse ${isExpanded ? 'show' : ''}" id="category-${categoryKey}">
                            <div class="card-body pt-0">
                                ${isExpanded ? this.renderMerchants(categoryData.merchants) : ''}
                            </div>
                        </div>
                    </div>
                </div>
            `;
        }).join('');

        // 重新初始化图标
        this.initializeIcons();
    }

    renderMerchants(merchants) {
        if (!merchants || Object.keys(merchants).length === 0) {
            return '<div class="text-muted text-center py-3 small">暂无商户数据</div>';
        }

        const merchantArray = Object.entries(merchants)
            .map(([name, data]) => ({ name, ...data }))
            .sort((a, b) => b.total_amount - a.total_amount);

        return `
            <div class="table-responsive">
                <table class="table table-hover table-sm mb-0">
                    <thead class="bg-light">
                        <tr>
                            <th class="px-3 py-3 fw-semibold text-muted small border-0">商户名称</th>
                            <th class="px-3 py-3 fw-semibold text-muted small border-0 text-end">总金额</th>
                            <th class="px-3 py-3 fw-semibold text-muted small border-0 text-center d-none d-md-table-cell">交易次数</th>
                            <th class="px-3 py-3 fw-semibold text-muted small border-0 text-center d-none d-lg-table-cell">平均金额</th>
                            <th class="px-3 py-3 fw-semibold text-muted small border-0 text-center">操作</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${merchantArray.map(merchant => `
                            <tr>
                                <td class="px-3 py-2">
                                    <span class="d-inline-block" title="${merchant.name}">${merchant.name}</span>
                                    <div class="text-muted small d-md-none">
                                        ${merchant.transaction_count}次 • 平均¥${merchant.avg_amount.toFixed(0)}
                                    </div>
                                </td>
                                <td class="px-3 py-2 text-end">
                                    <span class="text-danger">¥${merchant.total_amount.toFixed(2)}</span>
                                </td>
                                <td class="px-3 py-2 text-center d-none d-md-table-cell">
                                    <span class="badge bg-light text-dark small">${merchant.transaction_count}</span>
                                </td>
                                <td class="px-3 py-2 text-center d-none d-lg-table-cell">
                                    <span class="text-muted small">¥${merchant.avg_amount.toFixed(0)}</span>
                                </td>
                                <td class="px-3 py-2 text-center">
                                    <button class="btn btn-sm btn-outline-primary" onclick="window.expenseAnalysisPage.showMerchantDetail('${merchant.name}')" title="查看详情">
                                        <i data-lucide="eye" style="width: 0.75rem; height: 0.75rem;"></i>
                                        <span class="d-none d-sm-inline ms-1 small">详情</span>
                                    </button>
                                </td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        `;
    }

    // 分类展开/收起
    toggleCategory(categoryKey) {
        const detailsElement = document.getElementById(`category-${categoryKey}`);
        if (!detailsElement) return;

        if (this.expandedCategories.has(categoryKey)) {
            this.expandedCategories.delete(categoryKey);
            detailsElement.classList.remove('show');
        } else {
            this.expandedCategories.add(categoryKey);
            detailsElement.classList.add('show');

            // 如果内容为空，则渲染商户详情
            const cardBody = detailsElement.querySelector('.card-body');
            if (cardBody && cardBody.innerHTML.trim() === '') {
                const categoryData = this.categoryData.categories[categoryKey];
                if (categoryData && categoryData.merchants) {
                    cardBody.innerHTML = this.renderMerchants(categoryData.merchants);
                    this.initializeIcons();
                }
            }
        }
    }

    // 商户详情
    async showMerchantDetail(merchantName) {
        try {
            // 显示模态框
            const modal = new bootstrap.Modal(document.getElementById('merchantDetailModal'));
            modal.show();

            // 显示加载状态
            const container = document.getElementById('merchant-detail-content');
            if (container) {
                container.innerHTML = `
                    <div class="text-center py-4">
                        <div class="spinner-border text-primary" role="status">
                            <span class="visually-hidden">加载中...</span>
                        </div>
                        <div class="mt-3 text-muted">正在加载商户详情...</div>
                    </div>
                `;
            }

            // 构建API URL
            let apiUrl = `/expense-analysis/api/merchant-details/${encodeURIComponent(merchantName)}`;
            if (this.selectedMonth) {
                apiUrl += `?month=${encodeURIComponent(this.selectedMonth)}`;
            }

            // 加载数据
            const response = await fetch(apiUrl);
            const data = await response.json();

            if (data.success) {
                this.renderMerchantModal(data.data);
            } else {
                throw new Error(data.error || '获取商户详情失败');
            }

        } catch (error) {
            console.error('显示商户详情失败:', error);
        }
    }

    renderMerchantModal(merchantData) {
        const container = document.getElementById('merchant-detail-content');
        const { merchant_name, category_info, transactions, statistics, filter_info } = merchantData;

        // 更新模态框标题
        const modalTitle = document.getElementById('merchantDetailModalLabel');
        if (modalTitle && filter_info) {
            const periodText = filter_info.period_info || '所有时间';
            modalTitle.innerHTML = `
                <i data-lucide="store" class="me-2"></i>
                商户详情 - ${merchant_name}
                <small class="text-muted ms-2">(${periodText})</small>
            `;
        }

        container.innerHTML = `
            <div class="merchant-overview mb-4">
                <div class="d-flex align-items-center mb-3">
                    <div class="me-3 bg-${category_info.color} bg-opacity-10 rounded-circle d-flex align-items-center justify-content-center" style="width: 3rem; height: 3rem;">
                        <i data-lucide="${category_info.icon}" class="text-${category_info.color}" style="width: 1.5rem; height: 1.5rem;"></i>
                    </div>
                    <div>
                        <h4 class="mb-1">${merchant_name}</h4>
                        <span class="badge bg-${category_info.color} bg-opacity-10 text-${category_info.color}">${category_info.name}</span>
                    </div>
                </div>

                <div class="row g-3">
                    <div class="col-md-4">
                        <div class="text-center p-3 bg-light rounded">
                            <div class="h4 text-danger mb-1">¥${statistics.total_amount.toFixed(2)}</div>
                            <small class="text-muted">总支出</small>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="text-center p-3 bg-light rounded">
                            <div class="h4 text-primary mb-1">${statistics.transaction_count}</div>
                            <small class="text-muted">交易次数</small>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="text-center p-3 bg-light rounded">
                            <div class="h4 text-success mb-1">¥${statistics.average_amount.toFixed(0)}</div>
                            <small class="text-muted">平均金额</small>
                        </div>
                    </div>
                </div>
            </div>

            <div class="transactions-section">
                <h6 class="mb-3">交易记录</h6>
                <div class="table-responsive">
                    <table class="table table-hover table-sm">
                        <thead class="bg-light">
                            <tr>
                                <th class="px-3 py-2">日期</th>
                                <th class="px-3 py-2 text-end">金额</th>
                                <th class="px-3 py-2 d-none d-md-table-cell">账户</th>
                                <th class="px-3 py-2 d-none d-lg-table-cell">描述</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${transactions.map(transaction => `
                                <tr>
                                    <td class="px-3 py-2">${transaction.date}</td>
                                    <td class="px-3 py-2 text-end">
                                        <span class="text-danger">¥${transaction.amount.toFixed(2)}</span>
                                    </td>
                                    <td class="px-3 py-2 d-none d-md-table-cell">
                                        <span class="text-muted small">${transaction.account || '-'}</span>
                                    </td>
                                    <td class="px-3 py-2 d-none d-lg-table-cell">
                                        <span class="text-muted small">${transaction.description || '-'}</span>
                                    </td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
            </div>
        `;

        this.initializeIcons();
    }

    // 工具方法
    setLoading(loading) {
        this.loading = loading;
        if (loading) {
            apiService.showLoading(true);
        } else {
            apiService.showLoading(false);
        }
    }
}

// 导出类
export default ExpenseAnalysisPage;

// 页面加载完成后初始化
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => new ExpenseAnalysisPage());
} else {
    new ExpenseAnalysisPage();
}
