/**
 * 支出分析页面
 * 提供智能的固定支出分析功能
 */

import BasePage from '../common/BasePage.js';
import { apiService } from '../common/utils.js';

class ExpenseAnalysisPage extends BasePage {
    constructor() {
        super();
        this.chart = null;
        this.data = null;
        this.largeExpensesLimit = 6; // 默认显示6个大额固定支出
        this.showingAllLarge = false;
        this.selectedMonth = null; // 当前选中的月份
        this.monthlyData = {}; // 按月份索引的数据
        this.expandedCategories = new Set(); // 展开的分类
    }

    /**
     * 显示Toast消息
     */
    showToast(message, type = 'info') {
        // 简单的toast实现
        const toast = document.createElement('div');
        toast.className = `alert alert-${type === 'error' ? 'danger' : type} position-fixed`;
        toast.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
        toast.textContent = message;

        document.body.appendChild(toast);

        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        }, 3000);
    }

    /**
     * 获取商户分类信息
     */
    getMerchantCategoryInfo(merchant) {
        const categoryMap = {
            '餐饮': { icon: 'coffee', color: 'primary' },
            '交通': { icon: 'car', color: 'info' },
            '通信': { icon: 'phone', color: 'success' },
            '医疗': { icon: 'heart', color: 'danger' },
            '日用购物': { icon: 'shopping-cart', color: 'warning' },
            '其他': { icon: 'more-horizontal', color: 'secondary' }
        };

        const category = merchant.category || '其他';
        return categoryMap[category] || categoryMap['其他'];
    }

    /**
     * 获取评分颜色
     */
    getScoreColor(score) {
        if (score >= 80) return 'success';
        if (score >= 60) return 'warning';
        return 'danger';
    }

    /**
     * 获取评分对应的文案
     */
    getScoreText(score) {
        if (score >= 90) return '极高固定性';
        if (score >= 80) return '高固定性';
        if (score >= 70) return '较高固定性';
        if (score >= 60) return '中等固定性';
        if (score >= 50) return '较低固定性';
        return '低固定性';
    }

    /**
     * 等待Chart.js加载完成
     */
    waitForChart() {
        return new Promise((resolve) => {
            let attempts = 0;
            const maxAttempts = 50; // 最多等待5秒

            function checkChart() {
                attempts++;
                console.log(`等待Chart.js加载，尝试 ${attempts}/${maxAttempts}`);

                if (typeof Chart !== 'undefined') {
                    console.log('Chart.js加载成功');
                    resolve();
                } else if (attempts >= maxAttempts) {
                    console.warn('Chart.js加载超时，继续执行');
                    resolve(); // 即使Chart.js未加载也继续执行
                } else {
                    setTimeout(checkChart, 100);
                }
            }

            checkChart();
        });
    }

    /**
     * 初始化页面
     */
    async init() {
        console.log('ExpenseAnalysisPage: 开始初始化');
        try {
            this.showLoading();

            console.log('ExpenseAnalysisPage: 等待Chart.js加载');
            await this.waitForChart();
            console.log('ExpenseAnalysisPage: Chart.js等待完成');

            console.log('ExpenseAnalysisPage: 开始加载数据');
            await this.loadData();
            console.log('ExpenseAnalysisPage: 数据加载完成，开始渲染');

            this.renderOverview();
            console.log('ExpenseAnalysisPage: 概览渲染完成');

            this.renderChart();
            console.log('ExpenseAnalysisPage: 图表渲染完成');

            this.renderExpenseDetails();
            console.log('ExpenseAnalysisPage: 详情渲染完成');

            this.hideLoading();
            console.log('ExpenseAnalysisPage: 初始化完成');
        } catch (error) {
            console.error('ExpenseAnalysisPage: 初始化失败', error);
            this.hideLoading(); // 确保即使出错也隐藏loading
            this.showError(error.message);
        }
    }

    /**
     * 加载数据
     */
    async loadData() {
        try {
            console.log('开始加载固定支出数据...');
            const fixedExpensesResponse = await fetch('/expense-analysis/api/fixed-expenses');
            const fixedExpensesData = await fixedExpensesResponse.json();
            console.log('固定支出API响应:', fixedExpensesData);

            if (!fixedExpensesData.success) {
                throw new Error(fixedExpensesData.error || '加载固定支出数据失败');
            }

            console.log('开始加载月度趋势数据...');
            const monthlyTrendResponse = await fetch('/expense-analysis/api/monthly-trend');
            const monthlyTrendData = await monthlyTrendResponse.json();
            console.log('月度趋势API响应:', monthlyTrendData);

            if (!monthlyTrendData.success) {
                throw new Error(monthlyTrendData.error || '加载月度趋势数据失败');
            }

            this.data = {
                fixedExpenses: fixedExpensesData.data,
                monthlyTrend: monthlyTrendData.data
            };

            console.log('数据加载完成:', this.data);
            console.log('固定支出数据:', this.data.fixedExpenses);
            console.log('月度趋势数据:', this.data.monthlyTrend);

        } catch (error) {
            console.error('Error loading data:', error);
            throw error;
        }
    }

    /**
     * 渲染概览卡片
     */
    renderOverview() {
        try {
            console.log('开始渲染概览，数据:', this.data);

            if (!this.data || !this.data.fixedExpenses) {
                throw new Error('固定支出数据不存在');
            }

            const { fixedExpenses } = this.data;
            console.log('固定支出数据:', fixedExpenses);

            // 检查数据结构
            console.log('检查数据结构...');
            console.log('fixedExpenses.daily_fixed_expenses:', fixedExpenses.daily_fixed_expenses);
            console.log('fixedExpenses.large_fixed_expenses:', fixedExpenses.large_fixed_expenses);

            if (!fixedExpenses.daily_fixed_expenses) {
                console.error('日常固定支出数据不存在，fixedExpenses:', fixedExpenses);
                throw new Error('日常固定支出数据不存在');
            }
            if (!fixedExpenses.large_fixed_expenses) {
                console.error('大额固定支出数据不存在，fixedExpenses:', fixedExpenses);
                throw new Error('大额固定支出数据不存在');
            }

            // 日常固定支出
            const dailyData = fixedExpenses.daily_fixed_expenses;
            console.log('日常固定支出数据:', dailyData);

            const dailyAvg = dailyData.monthly_average || 0;
            const dailyCount = (dailyData.merchants || []).length;
            document.getElementById('daily-fixed-amount').textContent = `¥${dailyAvg.toFixed(0)}`;
            document.getElementById('daily-fixed-merchants').textContent = `${dailyCount}个商户`;

            // 大额固定支出
            const largeData = fixedExpenses.large_fixed_expenses;
            console.log('大额固定支出数据:', largeData);

            const largeAvg = largeData.monthly_average || 0;
            const largeCount = (largeData.merchants || []).length;
            document.getElementById('large-fixed-amount').textContent = `¥${largeAvg.toFixed(0)}`;
            document.getElementById('large-fixed-merchants').textContent = `${largeCount}个商户`;

            // 总固定支出
            const totalAvg = dailyAvg + largeAvg;
            const totalCount = dailyCount + largeCount;
            document.getElementById('total-fixed-amount').textContent = `¥${totalAvg.toFixed(0)}`;
            document.getElementById('total-fixed-merchants').textContent = `${totalCount}个商户`;

            // 算法识别
            const { algorithm_summary } = fixedExpenses;
            if (algorithm_summary) {
                const accuracy = ((algorithm_summary.fixed_merchants_identified / algorithm_summary.total_merchants_analyzed) * 100).toFixed(1);
                document.getElementById('algorithm-accuracy').textContent = `${accuracy}%`;
                document.getElementById('analyzed-merchants').textContent = `${algorithm_summary.total_merchants_analyzed}个分析`;
            }

            console.log('概览渲染完成');
        } catch (error) {
            console.error('渲染概览时出错:', error);
            throw error;
        }
    }

    /**
     * 渲染月度趋势图表
     */
    renderChart() {
        try {
            console.log('开始渲染图表');
            console.log('当前数据状态:', this.data);
            const canvas = document.getElementById('monthly-trend-chart');
            if (!canvas) {
                console.error('图表canvas不存在');
                return;
            }

            console.log('Canvas元素找到:', canvas);
            const ctx = canvas.getContext('2d');
            const monthly_trend = this.data.monthlyTrend.monthly_trend;
            console.log('月度趋势数据:', monthly_trend);

            // 准备图表数据
            const labels = monthly_trend.map(item => item.month).reverse();
            const dailyData = monthly_trend.map(item => item.daily_fixed).reverse();
            const totalData = monthly_trend.map(item => item.total_fixed).reverse();

            console.log('图表数据准备完成:', { labels, dailyData, totalData });

            // 准备大额固定支出数据
            const largeData = monthly_trend.map(item => item.large_fixed).reverse();

            // 检查数据有效性
            if (!monthly_trend || !Array.isArray(monthly_trend) || monthly_trend.length === 0) {
                console.error('月度趋势数据无效:', monthly_trend);
                return;
            }

            // 检查Chart.js是否可用
            if (typeof Chart !== 'undefined' && Chart) {
                console.log('Chart.js可用，开始创建图表');
                this.chart = new Chart(ctx, {
                    type: 'bar',
                    data: {
                        labels: labels,
                        datasets: [
                            {
                                label: '日常固定支出',
                                data: dailyData,
                                backgroundColor: 'rgba(13, 110, 253, 0.8)',
                                borderColor: 'rgba(13, 110, 253, 1)',
                                borderWidth: 1,
                                borderRadius: 4,
                                borderSkipped: false,
                                stack: 'fixed-expenses'
                            },
                            {
                                label: '大额固定支出',
                                data: largeData,
                                backgroundColor: 'rgba(255, 193, 7, 0.8)',
                                borderColor: 'rgba(255, 193, 7, 1)',
                                borderWidth: 1,
                                borderRadius: 4,
                                borderSkipped: false,
                                stack: 'fixed-expenses'
                            }
                        ]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        scales: {
                            x: {
                                stacked: true,
                                grid: { display: false },
                                title: {
                                    display: true,
                                    text: '月份（点击柱状图查看详细数据）',
                                    color: '#6c757d',
                                    font: { size: 12 }
                                }
                            },
                            y: {
                                stacked: true,
                                beginAtZero: true,
                                title: {
                                    display: true,
                                    text: '金额（元）',
                                    color: '#6c757d'
                                },
                                ticks: {
                                    callback: function(value) {
                                        return '¥' + value.toLocaleString();
                                    }
                                }
                            }
                        },
                        plugins: {
                            legend: { position: 'top' },
                            tooltip: {
                                mode: 'index',
                                intersect: false,
                                callbacks: {
                                    label: function(context) {
                                        return context.dataset.label + ': ¥' + context.parsed.y.toLocaleString();
                                    },
                                    footer: function(tooltipItems) {
                                        let total = 0;
                                        tooltipItems.forEach(function(tooltipItem) {
                                            total += tooltipItem.parsed.y;
                                        });
                                        return '总计: ¥' + total.toLocaleString();
                                    },
                                    afterLabel: function(context) {
                                        return '点击查看该月份详细数据';
                                    }
                                }
                            }
                        },
                        onClick: (event, elements) => {
                            if (elements.length > 0) {
                                const clickedIndex = elements[0].index;
                                // 由于图表数据被reverse()，需要计算正确的原始数组索引
                                const originalIndex = monthly_trend.length - 1 - clickedIndex;
                                const monthData = monthly_trend[originalIndex];
                                console.log('点击图表月份 - 点击索引:', clickedIndex, '原始索引:', originalIndex, '月份数据:', monthData);
                                window.expenseAnalysisPage.selectMonth(monthData);
                            }
                        },
                        onHover: (event, elements) => {
                            event.native.target.style.cursor = elements.length > 0 ? 'pointer' : 'default';
                        }
                    }
                });
                console.log('图表创建成功');
            } else {
                console.warn('Chart.js未加载，显示文本信息');
                // 显示简单的文本信息
                const container = canvas.parentElement;
                container.innerHTML = `
                    <div class="text-center py-4">
                        <h6>月度固定支出趋势</h6>
                        <div class="row">
                            ${monthly_trend.map(item => `
                                <div class="col-md-2 mb-2">
                                    <div class="card">
                                        <div class="card-body p-2">
                                            <div class="small text-muted">${item.month}</div>
                                            <div class="fw-bold">¥${item.total_fixed.toFixed(0)}</div>
                                            <div class="small text-primary">日常: ¥${item.daily_fixed.toFixed(0)}</div>
                                            <div class="small text-warning">大额: ¥${item.large_fixed.toFixed(0)}</div>
                                        </div>
                                    </div>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                `;
            }
        } catch (error) {
            console.error('渲染图表时出错:', error);
        }
    }

    /**
     * 渲染支出详情列表
     */
    renderExpenseDetails() {
        this.renderDailyFixedExpenses();
        this.renderLargeFixedExpenses();
    }

    /**
     * 渲染日常固定支出列表 - 单列分类汇总卡片
     */
    renderDailyFixedExpenses() {
        const container = document.getElementById('daily-fixed-categories');
        const allMerchants = this.data.fixedExpenses.daily_fixed_expenses.merchants;

        // 根据选中月份筛选商户数据
        const merchants = this.getFilteredMerchantsByMonth(allMerchants);

        if (merchants.length === 0) {
            container.innerHTML = '<div class="text-muted text-center py-3">暂无日常固定支出数据</div>';
            return;
        }

        // 按display_category分组并计算汇总数据
        const categoryData = this.calculateCategoryData(merchants);

        // 按总金额排序
        const sortedCategories = Object.entries(categoryData).sort((a, b) => b[1].totalAmount - a[1].totalAmount);

        // 渲染分类汇总卡片
        container.innerHTML = sortedCategories.map(([categoryKey, data]) => {
            const categoryInfo = this.getCategoryInfo(categoryKey);
            const isExpanded = this.expandedCategories && this.expandedCategories.has(categoryKey);

            return `
                <div class="category-summary-card mb-3">
                    <div class="card border-0 shadow-sm">
                        <div class="card-body p-3 cursor-pointer" onclick="expenseAnalysisPage.toggleCategoryExpansion('${categoryKey}')">
                            <div class="d-flex align-items-center justify-content-between">
                                <div class="d-flex align-items-center">
                                    <div class="me-3 bg-${categoryInfo.color} bg-opacity-10 rounded-circle d-flex align-items-center justify-content-center" style="width: 2.5rem; height: 2.5rem;">
                                        ${this.getCategoryIcon(categoryKey, categoryInfo.color)}
                                    </div>
                                    <div>
                                        <h6 class="mb-1 fw-bold text-${categoryInfo.color}">${categoryInfo.name}</h6>
                                        <small class="text-muted">${data.merchantCount}个商户 • 月均¥${data.avgAmount.toFixed(0)}</small>
                                    </div>
                                </div>
                                <div class="d-flex align-items-center">
                                    <div class="text-end me-3">
                                        <div class="fw-bold text-${categoryInfo.color} fs-5">¥${data.totalAmount.toFixed(0)}</div>
                                        <small class="text-muted">总支出</small>
                                    </div>
                                    <div class="text-${categoryInfo.color}">
                                        ${isExpanded ?
                                            '<i data-lucide="chevron-up" style="width: 1.25rem; height: 1.25rem;"></i>' :
                                            '<i data-lucide="chevron-down" style="width: 1.25rem; height: 1.25rem;"></i>'
                                        }
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div class="category-details collapse ${isExpanded ? 'show' : ''}" id="category-${categoryKey}">
                            <div class="card-body pt-0">
                                <div id="merchants-${categoryKey}">
                                    ${isExpanded ? this.renderCategoryMerchantDetails(data.merchants) : ''}
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        }).join('');

        // 重新初始化Lucide图标
        if (typeof lucide !== 'undefined') {
            lucide.createIcons();
        }
    }

    /**
     * 计算分类汇总数据
     */
    calculateCategoryData(merchants) {
        const categoryData = {
            dining: { merchants: [], totalAmount: 0, merchantCount: 0, avgAmount: 0 },
            transport: { merchants: [], totalAmount: 0, merchantCount: 0, avgAmount: 0 },
            other: { merchants: [], totalAmount: 0, merchantCount: 0, avgAmount: 0 }
        };

        merchants.forEach(merchant => {
            const category = merchant.display_category || 'other';
            if (categoryData[category]) {
                categoryData[category].merchants.push(merchant);

                // 使用月度数据计算实际金额
                const monthlyTotal = this.calculateMerchantMonthlyTotal(merchant);
                categoryData[category].totalAmount += monthlyTotal;
                categoryData[category].merchantCount++;

                console.log('分类汇总 - 商户:', merchant.merchant, '分类:', category, '月度金额:', monthlyTotal);
            }
        });

        // 计算平均金额并按金额排序
        Object.keys(categoryData).forEach(category => {
            const data = categoryData[category];
            data.avgAmount = data.merchantCount > 0 ? data.totalAmount / data.merchantCount : 0;
            // 按月度金额排序而不是平均金额
            data.merchants.sort((a, b) => {
                const aMonthlyTotal = this.calculateMerchantMonthlyTotal(a);
                const bMonthlyTotal = this.calculateMerchantMonthlyTotal(b);
                return bMonthlyTotal - aMonthlyTotal;
            });
        });

        return categoryData;
    }

    /**
     * 获取分类信息
     */
    getCategoryInfo(categoryKey) {
        const categoryMap = {
            dining: { name: '餐饮支出', color: 'primary', description: '餐厅、咖啡、外卖等' },
            transport: { name: '交通支出', color: 'success', description: '地铁、打车、加油等' },
            other: { name: '其他支出', color: 'info', description: '通信、购物、服务等' }
        };
        return categoryMap[categoryKey] || categoryMap.other;
    }

    /**
     * 切换分类展开/收起状态
     */
    toggleCategoryExpansion(categoryKey) {
        const detailsElement = document.getElementById(`category-${categoryKey}`);
        const merchantsContainer = document.getElementById(`merchants-${categoryKey}`);

        if (!detailsElement) return;

        if (this.expandedCategories.has(categoryKey)) {
            // 收起
            this.expandedCategories.delete(categoryKey);
            detailsElement.classList.remove('show');
        } else {
            // 展开
            this.expandedCategories.add(categoryKey);
            detailsElement.classList.add('show');

            // 如果商户容器为空，则渲染商户详情
            if (merchantsContainer && merchantsContainer.innerHTML.trim() === '') {
                const allMerchants = this.data.fixedExpenses.daily_fixed_expenses.merchants;
                const merchants = this.getFilteredMerchantsByMonth(allMerchants);
                const categoryMerchants = merchants.filter(m => (m.display_category || 'other') === categoryKey);
                merchantsContainer.innerHTML = this.renderCategoryMerchantDetails(categoryMerchants);

                // 重新初始化Lucide图标
                if (typeof lucide !== 'undefined') {
                    lucide.createIcons();
                }
            }
        }
    }

    /**
     * 渲染分类商户详情 - 参照transactions.html的表格样式
     */
    renderCategoryMerchantDetails(merchants) {
        if (merchants.length === 0) {
            return '<div class="text-muted text-center py-3 small">暂无商户数据</div>';
        }

        // 按总金额从高到低排序
        const sortedMerchants = merchants.slice().sort((a, b) => {
            const totalAmountA = this.calculateMerchantMonthlyTotal(a);
            const totalAmountB = this.calculateMerchantMonthlyTotal(b);
            return totalAmountB - totalAmountA;
        });

        return `
            <div class="table-responsive">
                <table class="table table-hover table-sm mb-0">
                    <thead class="bg-light">
                        <tr>
                            <th class="px-3 py-3 fw-semibold text-muted small border-0">商户名称</th>
                            <th class="px-3 py-3 fw-semibold text-muted small border-0 text-end">总金额</th>
                            <th class="px-3 py-3 fw-semibold text-muted small border-0 text-center d-none d-md-table-cell">交易次数</th>
                            <th class="px-3 py-3 fw-semibold text-muted small border-0 text-center d-none d-lg-table-cell">平均间隔</th>
                            <th class="px-3 py-3 fw-semibold text-muted small border-0 text-center">操作</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${sortedMerchants.map(merchant => {
                            // 计算当月总金额
                            const totalAmount = this.calculateMerchantMonthlyTotal(merchant);

                            return `
                            <tr>
                                <td class="px-3 py-2">
                                    <span class="d-inline-block transaction-cell-truncate" title="${merchant.merchant}">
                                        ${merchant.merchant}
                                    </span>
                                    <div class="text-muted small d-md-none">
                                        ${merchant.transaction_count}次 • ${merchant.avg_interval}天间隔
                                    </div>
                                </td>
                                <td class="px-3 py-2 text-end">
                                    <span class="transaction-amount negative">${totalAmount.toFixed(2)}</span>
                                </td>
                                <td class="px-3 py-2 text-center d-none d-md-table-cell">
                                    <span class="badge bg-light text-dark small">${merchant.transaction_count}</span>
                                </td>
                                <td class="px-3 py-2 text-center d-none d-lg-table-cell">
                                    <span class="text-muted small">${merchant.avg_interval}天</span>
                                </td>
                                <td class="px-3 py-2 text-center">
                                    <button class="btn btn-sm btn-outline-primary" onclick="expenseAnalysisPage.showMerchantDetail('${merchant.merchant}')" title="查看详情">
                                        <i data-lucide="eye" style="width: 0.75rem; height: 0.75rem;"></i>
                                        <span class="d-none d-sm-inline ms-1 small">详情</span>
                                    </button>
                                </td>
                            </tr>
                        `;
                        }).join('')}
                    </tbody>
                </table>
            </div>
        `;
    }

    /**
     * 渲染大额固定支出列表 - 按金额从高到低排序
     */
    renderLargeFixedExpenses() {
        const container = document.getElementById('large-fixed-list');
        const moreButton = document.getElementById('large-fixed-more');
        const allMerchants = this.data.fixedExpenses.large_fixed_expenses.merchants;

        // 根据选中月份筛选商户数据
        let merchants = this.getFilteredMerchantsByMonth(allMerchants);

        if (merchants.length === 0) {
            container.innerHTML = '<div class="text-muted text-center py-3">暂无大额固定支出数据</div>';
            if (moreButton) moreButton.classList.add('d-none');
            return;
        }

        // 按月度金额从高到低排序
        merchants = merchants.sort((a, b) => {
            const aMonthlyTotal = this.calculateMerchantMonthlyTotal(a);
            const bMonthlyTotal = this.calculateMerchantMonthlyTotal(b);
            return bMonthlyTotal - aMonthlyTotal;
        });

        // 确定显示数量
        const displayCount = this.showingAllLarge ? merchants.length : this.largeExpensesLimit;
        const displayMerchants = merchants.slice(0, displayCount);

        // 渲染商户卡片
        container.innerHTML = displayMerchants.map(merchant => {
            // 计算当前月份的金额
            const monthlyAmount = this.calculateMerchantMonthlyTotal(merchant);
            // 获取评分文案
            const scoreText = this.getScoreText(merchant.total_score);
            const scoreColor = this.getScoreColor(merchant.total_score);

            return `
                <div class="merchant-card card border-0 shadow-sm mb-3" style="transition: all 0.2s ease;">
                    <div class="card-body p-3">
                        <div class="d-flex align-items-center">
                            <div class="me-3 flex-shrink-0">
                                <div class="merchant-icon bg-warning bg-opacity-10 rounded-circle d-flex align-items-center justify-content-center" style="width: 2.5rem; height: 2.5rem;">
                                    ${this.getCategoryIcon(merchant.category, 'warning')}
                                </div>
                            </div>
                            <div class="flex-grow-1 min-width-0">
                                <h6 class="merchant-name mb-1 fw-semibold text-truncate">${merchant.merchant}</h6>
                                <div class="merchant-meta small text-muted mb-2">
                                    <span class="badge bg-light text-dark me-1">${this.getCategoryName(merchant.category)}</span>
                                    <span>${merchant.transaction_count}次交易</span>
                                </div>
                                <div class="score-text mb-2">
                                    <span class="badge bg-${scoreColor} bg-opacity-10 text-${scoreColor}">${scoreText}</span>
                                </div>
                            </div>
                            <div class="text-end flex-shrink-0">
                                <div class="merchant-amount fw-bold text-warning">¥${monthlyAmount.toFixed(2)}</div>
                                <button class="btn btn-sm btn-outline-primary mt-2" onclick="expenseAnalysisPage.showMerchantDetail('${merchant.merchant}')">
                                    <i data-lucide="eye" class="me-1" style="width: 0.875rem; height: 0.875rem;"></i>详情
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        }).join('');

        // 控制"查看更多"按钮显示
        if (moreButton) {
            if (merchants.length > this.largeExpensesLimit && !this.showingAllLarge) {
                moreButton.classList.remove('d-none');
            } else {
                moreButton.classList.add('d-none');
            }
        }
    }

    /**
     * 选择月份进行数据筛选
     */
    selectMonth(monthData) {
        this.selectedMonth = monthData.month;
        console.log('选择月份:', monthData);

        // 重新渲染商户列表
        this.updateMerchantLists();

        // 高亮图表中的选中月份
        this.highlightChartMonth();
    }

    /**
     * 重置月份筛选，显示全部数据
     */
    resetMonthFilter() {
        this.selectedMonth = null;
        console.log('重置月份筛选');

        // 重新渲染商户列表
        this.updateMerchantLists();

        // 移除图表高亮
        this.removeChartHighlight();
    }



    /**
     * 更新商户列表显示
     */
    updateMerchantLists() {
        this.renderDailyFixedExpenses();
        this.renderLargeFixedExpenses();

        // 重新初始化Lucide图标
        if (typeof lucide !== 'undefined') {
            lucide.createIcons();
        }
    }

    /**
     * 高亮图表中的选中月份
     */
    highlightChartMonth() {
        if (this.chart && this.selectedMonth) {
            console.log('高亮图表月份:', this.selectedMonth);

            // 找到选中月份在图表中的索引
            const monthly_trend = this.data.monthlyTrend.monthly_trend;
            const labels = monthly_trend.map(item => item.month).reverse();
            const selectedIndex = labels.indexOf(this.selectedMonth);

            if (selectedIndex !== -1) {
                // 更新数据集的背景色，高亮选中的月份
                this.chart.data.datasets.forEach((dataset, datasetIndex) => {
                    const originalColors = datasetIndex === 0
                        ? 'rgba(13, 110, 253, 0.8)'  // 日常固定支出
                        : 'rgba(255, 193, 7, 0.8)';  // 大额固定支出

                    const highlightColors = datasetIndex === 0
                        ? 'rgba(13, 110, 253, 1.0)'  // 高亮日常固定支出
                        : 'rgba(255, 193, 7, 1.0)';  // 高亮大额固定支出

                    dataset.backgroundColor = labels.map((_, index) =>
                        index === selectedIndex ? highlightColors : originalColors
                    );
                });

                this.chart.update('none'); // 无动画更新
            }
        }
    }

    /**
     * 移除图表高亮
     */
    removeChartHighlight() {
        if (this.chart) {
            console.log('移除图表高亮');

            // 恢复原始颜色
            this.chart.data.datasets.forEach((dataset, datasetIndex) => {
                const originalColor = datasetIndex === 0
                    ? 'rgba(13, 110, 253, 0.8)'  // 日常固定支出
                    : 'rgba(255, 193, 7, 0.8)';  // 大额固定支出

                dataset.backgroundColor = originalColor;
            });

            this.chart.update('none'); // 无动画更新
        }
    }

    /**
     * 根据选中月份筛选商户数据
     */
    getFilteredMerchantsByMonth(merchants) {
        if (!this.selectedMonth || !merchants) {
            return merchants;
        }

        console.log('按月份筛选商户:', this.selectedMonth, '原始商户数量:', merchants.length);

        // 筛选在指定月份有交易的商户
        const filteredMerchants = merchants.filter(merchant => {
            // 检查商户是否有monthly_details数据
            if (!merchant.monthly_details || typeof merchant.monthly_details !== 'object') {
                console.warn('商户缺少monthly_details数据:', merchant.merchant);
                return false;
            }

            // 检查指定月份是否有数据
            const hasDataForMonth = this.selectedMonth in merchant.monthly_details;
            if (hasDataForMonth) {
                console.log('商户', merchant.merchant, '在', this.selectedMonth, '有交易数据');
            }

            return hasDataForMonth;
        });

        console.log('筛选后商户数量:', filteredMerchants.length);
        return filteredMerchants;
    }



    /**
     * 显示更多大额固定支出
     */
    showMoreLargeExpenses() {
        this.showingAllLarge = true;
        this.renderLargeFixedExpenses();
        // 重新初始化Lucide图标
        if (typeof lucide !== 'undefined') {
            lucide.createIcons();
        }
    }

    /**
     * 计算商户在当前选中月份的总金额
     */
    calculateMerchantMonthlyTotal(merchant) {
        // 如果没有选中月份，返回平均金额
        if (!this.selectedMonth) {
            return merchant.avg_amount;
        }

        // 使用新的monthly_details数据结构
        if (merchant.monthly_details && merchant.monthly_details[this.selectedMonth]) {
            const monthData = merchant.monthly_details[this.selectedMonth];
            console.log('使用月度明细数据计算金额:', merchant.merchant, this.selectedMonth, monthData.total_amount);
            return monthData.total_amount;
        }

        // 如果该月份没有数据，返回0（表示该月份没有交易）
        console.log('商户', merchant.merchant, '在', this.selectedMonth, '没有交易数据，返回0');
        return 0;
    }

    /**
     * 获取类别图标
     */
    getCategoryIcon(category, colorClass = null) {
        // 根据display_category或原始category确定图标
        let iconName = 'more-horizontal';

        if (category === 'dining' || category.includes('dining')) {
            iconName = 'utensils';
        } else if (category === 'transport' || category.includes('transport')) {
            iconName = 'car';
        } else if (category === 'daily_shopping') {
            iconName = 'shopping-cart';
        } else if (category === 'communication') {
            iconName = 'phone';
        } else if (category === 'medical') {
            iconName = 'heart';
        } else if (category === 'insurance') {
            iconName = 'shield';
        } else if (category.includes('transfer')) {
            iconName = 'credit-card';
        }

        const textColor = colorClass ? `text-${colorClass}` : 'text-muted';
        return `<i data-lucide="${iconName}" class="${textColor}"></i>`;
    }

    /**
     * 获取类别名称
     */
    getCategoryName(category) {
        const names = {
            'dining': '餐饮',
            'transport': '交通',
            'daily_shopping': '日用购物',
            'communication': '通信',
            'medical': '医疗',
            'insurance': '保险',
            'transfer': '转账',
            'transfer_rent': '房租转账',
            'transfer_living_expense': '生活费转账',
            'other': '其他'
        };
        return names[category] || '其他';
    }

    /**
     * 显示商户详情
     */
    async showMerchantDetail(merchantName) {
        try {
            const response = await fetch(`/expense-analysis/api/merchant-details/${encodeURIComponent(merchantName)}`);
            const data = await response.json();
            console.log('商户详情API响应:', data);

            if (!data.success) {
                throw new Error(data.error || '加载商户详情失败');
            }

            this.renderMerchantDetail(data.data);
            const modal = new bootstrap.Modal(document.getElementById('merchantDetailModal'));
            modal.show();

        } catch (error) {
            console.error('Error loading merchant detail:', error);
            this.showToast('加载商户详情失败', 'error');
        }
    }

    /**
     * 渲染商户详情
     */
    renderMerchantDetail(data) {
        const container = document.getElementById('merchant-detail-content');

        // 数据验证和默认值
        const statistics = data.statistics || {
            total_amount: 0,
            average_amount: 0,
            transaction_count: 0
        };
        const transactions = data.transactions || [];

        console.log('渲染商户详情，数据:', data);
        console.log('统计信息:', statistics);

        container.innerHTML = `
            <div class="row mb-3">
                <div class="col-md-4">
                    <div class="card bg-light">
                        <div class="card-body text-center">
                            <h5 class="card-title">总金额</h5>
                            <h3 class="text-primary">¥${statistics.total_amount.toFixed(2)}</h3>
                        </div>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="card bg-light">
                        <div class="card-body text-center">
                            <h5 class="card-title">平均金额</h5>
                            <h3 class="text-success">¥${statistics.average_amount.toFixed(2)}</h3>
                        </div>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="card bg-light">
                        <div class="card-body text-center">
                            <h5 class="card-title">交易次数</h5>
                            <h3 class="text-info">${statistics.transaction_count}次</h3>
                        </div>
                    </div>
                </div>
            </div>
            
            <h6>最近交易记录</h6>
            <div class="table-responsive">
                <table class="table table-sm">
                    <thead>
                        <tr>
                            <th>日期</th>
                            <th>金额</th>
                            <th>描述</th>
                            <th>账户</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${transactions.length > 0 ? transactions.map(t => `
                            <tr>
                                <td>${t.date || '--'}</td>
                                <td>¥${(t.amount || 0).toFixed(2)}</td>
                                <td>${t.description || '--'}</td>
                                <td>${t.account || '--'}</td>
                            </tr>
                        `).join('') : '<tr><td colspan="4" class="text-center text-muted">暂无交易记录</td></tr>'}
                    </tbody>
                </table>
            </div>
        `;
    }

    /**
     * 显示加载状态
     */
    showLoading() {
        document.getElementById('loading-state').style.display = 'block';
        document.getElementById('main-content').style.display = 'none';
        document.getElementById('error-state').style.display = 'none';
    }

    /**
     * 隐藏加载状态
     */
    hideLoading() {
        document.getElementById('loading-state').style.display = 'none';
        document.getElementById('main-content').style.display = 'block';
        document.getElementById('error-state').style.display = 'none';
        
        // 重新初始化Lucide图标
        if (typeof lucide !== 'undefined') {
            lucide.createIcons();
        }
    }

    /**
     * 显示错误状态
     */
    showError(message) {
        document.getElementById('loading-state').style.display = 'none';
        document.getElementById('main-content').style.display = 'none';
        document.getElementById('error-state').style.display = 'block';
        document.getElementById('error-message').textContent = message;
    }
}

// 初始化页面
document.addEventListener('DOMContentLoaded', () => {
    window.expenseAnalysisPage = new ExpenseAnalysisPage();
    window.expenseAnalysisPage.init();
});
