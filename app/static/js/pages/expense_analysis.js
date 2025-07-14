/**
 * 支出分类分析页面
 * 提供基于商户类型的智能支出分类与统计分析功能
 */

class ExpenseAnalysisPage {
    constructor() {
        this.chart = null;
        this.data = null;
        this.selectedCategory = null; // 当前选中的分类
        this.expandedCategories = new Set(); // 展开的分类
        this.activeFilters = {
            category: null,
            month: null,
            search: '',
            dateRange: { start: null, end: null }
        }; // 活跃的筛选条件

        // 绑定事件
        this.bindEvents();

        // 页面加载完成后初始化
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.init());
        } else {
            this.init();
        }
    }

    /**
     * 绑定事件处理器
     */
    bindEvents() {
        // 页面可见性变化事件
        document.addEventListener('visibilitychange', () => {
            if (!document.hidden && this.data) {
                this.refreshData();
            }
        });

        // 窗口大小变化事件
        window.addEventListener('resize', () => {
            if (this.chart) {
                this.chart.resize();
            }
        });

        // 筛选相关事件绑定（延迟到DOM加载后）
        document.addEventListener('DOMContentLoaded', () => {
            this.bindFilterEvents();
        });
    }

    /**
     * 绑定筛选相关事件
     */
    bindFilterEvents() {
        // 搜索框事件
        const searchInput = document.getElementById('merchant-search-input');
        if (searchInput) {
            let searchTimeout;
            searchInput.addEventListener('input', (e) => {
                clearTimeout(searchTimeout);
                searchTimeout = setTimeout(() => {
                    this.handleSearchInput(e.target.value);
                }, 300); // 300ms防抖
            });
        }

        // 筛选按钮事件
        const applyBtn = document.getElementById('apply-filters-btn');
        if (applyBtn) {
            applyBtn.addEventListener('click', () => this.applyDateRangeFilter());
        }

        // 清除筛选按钮事件
        const clearBtn = document.getElementById('clear-filters-btn');
        if (clearBtn) {
            clearBtn.addEventListener('click', () => this.clearAllFilters());
        }
    }

    /**
     * 初始化页面
     */
    async init() {
        try {
            console.log('支出分类分析页面初始化开始');
            
            // 设置全局引用
            window.expenseAnalysisPage = this;
            
            await this.loadData();
            this.render();
            
            console.log('支出分类分析页面初始化完成');
        } catch (error) {
            console.error('页面初始化失败:', error);
            this.showError(error.message);
        }
    }

    /**
     * 加载数据
     */
    async loadData() {
        try {
            console.log('开始加载商户分类支出数据...');

            // 构建查询参数
            const params = new URLSearchParams();
            if (this.activeFilters.dateRange.start) {
                params.append('start_date', this.activeFilters.dateRange.start);
            }
            if (this.activeFilters.dateRange.end) {
                params.append('end_date', this.activeFilters.dateRange.end);
            }

            const url = `/expense-analysis/api/merchant-analysis${params.toString() ? '?' + params.toString() : ''}`;
            const merchantAnalysisResponse = await fetch(url);
            const merchantAnalysisData = await merchantAnalysisResponse.json();
            console.log('商户分析API响应:', merchantAnalysisData);

            if (!merchantAnalysisData.success) {
                throw new Error(merchantAnalysisData.error || '加载商户分析数据失败');
            }

            this.data = merchantAnalysisData.data;
            console.log('数据加载成功:', this.data);

        } catch (error) {
            console.error('加载数据失败:', error);
            this.showToast('加载数据失败: ' + error.message, 'error');
            throw error;
        }
    }

    /**
     * 渲染页面内容
     */
    render() {
        this.hideLoading();
        this.renderOverview();
        this.renderChart();
        this.renderExpenseDetails();
        this.updateFilterStatus();
        this.updateCategoryCardStates();
        this.showMainContent();
    }

    /**
     * 渲染概览卡片
     */
    renderOverview() {
        try {
            console.log('开始渲染概览，数据:', this.data);

            if (!this.data || !this.data.categories) {
                throw new Error('商户分类数据不存在');
            }

            const { categories, summary } = this.data;
            console.log('分类数据:', categories);
            console.log('汇总数据:', summary);

            // 计算各类别金额
            let diningAmount = 0;
            let transportAmount = 0;
            let shoppingAmount = 0;
            let diningMerchants = 0;
            let transportMerchants = 0;
            let shoppingMerchants = 0;

            // 遍历所有分类
            Object.keys(categories).forEach(categoryKey => {
                const categoryData = categories[categoryKey];
                const merchantCount = Object.keys(categoryData.merchants || {}).length;
                
                if (categoryKey === 'dining') {
                    diningAmount = categoryData.total_amount || 0;
                    diningMerchants = merchantCount;
                } else if (categoryKey === 'transport') {
                    transportAmount = categoryData.total_amount || 0;
                    transportMerchants = merchantCount;
                } else if (categoryKey === 'shopping') {
                    shoppingAmount = categoryData.total_amount || 0;
                    shoppingMerchants = merchantCount;
                }
            });

            // 更新KPI卡片
            document.getElementById('dining-amount').textContent = `¥${diningAmount.toFixed(0)}`;
            document.getElementById('dining-merchants').textContent = `${diningMerchants}个商户`;

            document.getElementById('transport-amount').textContent = `¥${transportAmount.toFixed(0)}`;
            document.getElementById('transport-merchants').textContent = `${transportMerchants}个商户`;

            document.getElementById('shopping-amount').textContent = `¥${shoppingAmount.toFixed(0)}`;
            document.getElementById('shopping-merchants').textContent = `${shoppingMerchants}个商户`;

            document.getElementById('total-expense-amount').textContent = `¥${(summary.total_expense || 0).toFixed(0)}`;
            document.getElementById('total-merchants').textContent = `${summary.total_merchants || 0}个商户`;

            console.log('概览渲染完成');
        } catch (error) {
            console.error('渲染概览失败:', error);
            this.showToast('渲染概览失败: ' + error.message, 'error');
        }
    }

    /**
     * 渲染月度趋势图表
     */
    renderChart() {
        try {
            console.log('开始渲染图表');
            const canvas = document.getElementById('monthly-trend-chart');
            if (!canvas) {
                console.error('图表canvas不存在');
                return;
            }

            const ctx = canvas.getContext('2d');
            
            // 从各分类的月度数据中构建图表数据
            const monthlyDataMap = {};
            const { categories } = this.data;
            
            // 收集所有月份的数据
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
            const months = Object.keys(monthlyDataMap).sort();
            const labels = months.slice(-12); // 最近12个月
            
            // 为主要分类准备数据集
            const datasets = [
                {
                    label: '餐饮支出',
                    data: labels.map(month => monthlyDataMap[month]?.dining || 0),
                    backgroundColor: 'rgba(13, 110, 253, 0.8)',
                    borderColor: 'rgba(13, 110, 253, 1)',
                    borderWidth: 1,
                    borderRadius: 4,
                    stack: 'expenses'
                },
                {
                    label: '交通支出',
                    data: labels.map(month => monthlyDataMap[month]?.transport || 0),
                    backgroundColor: 'rgba(25, 135, 84, 0.8)',
                    borderColor: 'rgba(25, 135, 84, 1)',
                    borderWidth: 1,
                    borderRadius: 4,
                    stack: 'expenses'
                },
                {
                    label: '购物支出',
                    data: labels.map(month => monthlyDataMap[month]?.shopping || 0),
                    backgroundColor: 'rgba(13, 202, 240, 0.8)',
                    borderColor: 'rgba(13, 202, 240, 1)',
                    borderWidth: 1,
                    borderRadius: 4,
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
                    borderRadius: 4,
                    stack: 'expenses'
                }
            ];

            console.log('图表数据准备完成:', { labels, datasets });

            // 检查Chart.js是否可用
            if (typeof Chart !== 'undefined' && Chart) {
                console.log('Chart.js可用，开始创建图表');
                this.chart = new Chart(ctx, {
                    type: 'bar',
                    data: {
                        labels: labels,
                        datasets: datasets
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        interaction: {
                            mode: 'index',
                            intersect: false,
                        },
                        plugins: {
                            legend: {
                                position: 'top',
                            },
                            tooltip: {
                                mode: 'index',
                                intersect: false,
                                callbacks: {
                                    label: function(context) {
                                        return context.dataset.label + ': ¥' + context.parsed.y.toFixed(2);
                                    }
                                }
                            }
                        },
                        onClick: (event, elements) => {
                            if (elements.length > 0) {
                                const clickedIndex = elements[0].index;
                                const selectedMonth = labels[clickedIndex];
                                console.log('点击图表月份:', selectedMonth);
                                // 调用月份筛选功能
                                this.filterByMonth(selectedMonth);
                            }
                        },
                        scales: {
                            x: {
                                stacked: true,
                                grid: {
                                    display: false
                                }
                            },
                            y: {
                                stacked: true,
                                beginAtZero: true,
                                ticks: {
                                    callback: function(value) {
                                        return '¥' + value.toFixed(0);
                                    }
                                }
                            }
                        }
                    }
                });
                console.log('图表创建成功');
            } else {
                console.error('Chart.js不可用');
            }
        } catch (error) {
            console.error('渲染图表失败:', error);
        }
    }

    /**
     * 渲染支出详情列表
     */
    renderExpenseDetails() {
        this.renderCategoryExpenses();
    }

    /**
     * 渲染分类支出列表
     */
    renderCategoryExpenses() {
        const container = document.getElementById('expense-categories');
        const { categories } = this.data;

        if (!categories || Object.keys(categories).length === 0) {
            container.innerHTML = '<div class="text-muted text-center py-3">暂无支出分类数据</div>';
            return;
        }

        // 按总金额排序分类
        let sortedCategories = Object.entries(categories).sort((a, b) => b[1].total_amount - a[1].total_amount);

        // 应用分类筛选
        if (this.activeFilters.category) {
            sortedCategories = sortedCategories.filter(([categoryKey]) => categoryKey === this.activeFilters.category);
        }

        // 渲染分类汇总卡片
        container.innerHTML = sortedCategories.map(([categoryKey, categoryData]) => {
            const isExpanded = this.expandedCategories.has(categoryKey);
            const merchantCount = Object.keys(categoryData.merchants || {}).length;

            return `
                <div class="category-summary-card mb-3">
                    <div class="card border-0 shadow-sm">
                        <div class="card-body p-3 cursor-pointer" onclick="expenseAnalysisPage.toggleCategoryExpansion('${categoryKey}')">
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
                                <div id="merchants-${categoryKey}">
                                    ${isExpanded ? this.renderCategoryMerchantDetails(categoryData.merchants) : ''}
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
     * 渲染分类商户详情 - 参照transactions.html的表格样式
     */
    renderCategoryMerchantDetails(merchants) {
        if (!merchants || Object.keys(merchants).length === 0) {
            return '<div class="text-muted text-center py-3 small">暂无商户数据</div>';
        }

        // 转换为数组并按总金额排序
        let merchantArray = Object.entries(merchants).map(([merchantName, merchantData]) => ({
            name: merchantName,
            ...merchantData
        })).sort((a, b) => b.total_amount - a.total_amount);

        // 应用搜索筛选
        if (this.activeFilters.search) {
            const searchTerm = this.activeFilters.search.toLowerCase();
            merchantArray = merchantArray.filter(merchant =>
                merchant.name.toLowerCase().includes(searchTerm)
            );
        }

        // 如果筛选后没有结果
        if (merchantArray.length === 0) {
            return '<div class="text-muted text-center py-3 small">没有找到匹配的商户</div>';
        }

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
                        ${merchantArray.map(merchant => {
                            // 高亮搜索结果
                            const highlightedName = this.highlightSearchTerm(merchant.name, this.activeFilters.search);

                            return `
                            <tr>
                                <td class="px-3 py-2">
                                    <span class="d-inline-block transaction-cell-truncate" title="${merchant.name}">
                                        ${highlightedName}
                                    </span>
                                    <div class="text-muted small d-md-none">
                                        ${merchant.transaction_count}次 • 平均¥${merchant.avg_amount.toFixed(0)}
                                    </div>
                                </td>
                                <td class="px-3 py-2 text-end">
                                    <span class="transaction-amount negative">¥${merchant.total_amount.toFixed(2)}</span>
                                </td>
                                <td class="px-3 py-2 text-center d-none d-md-table-cell">
                                    <span class="badge bg-light text-dark small">${merchant.transaction_count}</span>
                                </td>
                                <td class="px-3 py-2 text-center d-none d-lg-table-cell">
                                    <span class="text-muted small">¥${merchant.avg_amount.toFixed(0)}</span>
                                </td>
                                <td class="px-3 py-2 text-center">
                                    <button class="btn btn-sm btn-outline-primary" onclick="expenseAnalysisPage.showMerchantDetail('${merchant.name}')" title="查看详情">
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
                const categoryData = this.data.categories[categoryKey];
                if (categoryData && categoryData.merchants) {
                    merchantsContainer.innerHTML = this.renderCategoryMerchantDetails(categoryData.merchants);

                    // 重新初始化Lucide图标
                    if (typeof lucide !== 'undefined') {
                        lucide.createIcons();
                    }
                }
            }
        }
    }

    /**
     * 显示商户详情
     */
    async showMerchantDetail(merchantName) {
        try {
            console.log('显示商户详情:', merchantName);

            // 显示模态框
            const modal = new bootstrap.Modal(document.getElementById('merchantDetailModal'));
            modal.show();

            // 加载商户详情数据
            const response = await fetch(`/expense-analysis/api/merchant-details/${encodeURIComponent(merchantName)}`);
            const data = await response.json();

            if (data.success) {
                this.renderMerchantDetailModal(data.data);
            } else {
                throw new Error(data.error || '获取商户详情失败');
            }

        } catch (error) {
            console.error('显示商户详情失败:', error);
            this.showToast('获取商户详情失败: ' + error.message, 'error');
        }
    }

    /**
     * 渲染商户详情模态框内容
     */
    renderMerchantDetailModal(merchantData) {
        const container = document.getElementById('merchant-detail-content');
        const { merchant_name, category_info, transactions, statistics } = merchantData;

        container.innerHTML = `
            <div class="merchant-detail-header mb-4">
                <div class="d-flex align-items-center">
                    <div class="me-3 bg-${category_info.color} bg-opacity-10 rounded-circle d-flex align-items-center justify-content-center" style="width: 3rem; height: 3rem;">
                        <i data-lucide="${category_info.icon}" class="text-${category_info.color}" style="width: 1.5rem; height: 1.5rem;"></i>
                    </div>
                    <div>
                        <h5 class="mb-1">${merchant_name}</h5>
                        <span class="badge bg-${category_info.color} bg-opacity-10 text-${category_info.color}">${category_info.name}</span>
                    </div>
                </div>
            </div>

            <div class="merchant-statistics mb-4">
                <div class="row g-3">
                    <div class="col-4">
                        <div class="text-center">
                            <div class="fw-bold text-danger fs-5">¥${statistics.total_amount.toFixed(2)}</div>
                            <small class="text-muted">总支出</small>
                        </div>
                    </div>
                    <div class="col-4">
                        <div class="text-center">
                            <div class="fw-bold fs-5">${statistics.transaction_count}</div>
                            <small class="text-muted">交易次数</small>
                        </div>
                    </div>
                    <div class="col-4">
                        <div class="text-center">
                            <div class="fw-bold fs-5">¥${statistics.average_amount.toFixed(0)}</div>
                            <small class="text-muted">平均金额</small>
                        </div>
                    </div>
                </div>
            </div>

            <div class="merchant-transactions">
                <h6 class="mb-3">最近交易记录</h6>
                <div class="table-responsive">
                    <table class="table table-sm">
                        <thead class="bg-light">
                            <tr>
                                <th class="border-0">日期</th>
                                <th class="border-0 text-end">金额</th>
                                <th class="border-0 d-none d-md-table-cell">描述</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${transactions.map(transaction => `
                                <tr>
                                    <td>${transaction.date}</td>
                                    <td class="text-end">
                                        <span class="transaction-amount negative">¥${transaction.amount.toFixed(2)}</span>
                                    </td>
                                    <td class="d-none d-md-table-cell">
                                        <span class="text-muted small">${transaction.description || '-'}</span>
                                    </td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
            </div>
        `;

        // 重新初始化Lucide图标
        if (typeof lucide !== 'undefined') {
            lucide.createIcons();
        }
    }

    /**
     * 刷新数据
     */
    async refreshData() {
        try {
            await this.loadData();
            this.render();
            this.showToast('数据已刷新', 'success');
        } catch (error) {
            console.error('刷新数据失败:', error);
            this.showToast('刷新数据失败: ' + error.message, 'error');
        }
    }

    // ==================== 筛选功能方法 ====================

    /**
     * 按分类筛选
     */
    filterByCategory(categoryKey) {
        console.log('按分类筛选:', categoryKey);

        // 更新筛选状态
        this.activeFilters.category = this.activeFilters.category === categoryKey ? null : categoryKey;

        // 更新UI状态
        this.updateFilterStatus();
        this.updateCategoryCardStates();
        this.renderCategoryExpenses();
    }

    /**
     * 按月份筛选
     */
    filterByMonth(selectedMonth) {
        console.log('按月份筛选:', selectedMonth);

        // 更新筛选状态
        this.activeFilters.month = this.activeFilters.month === selectedMonth ? null : selectedMonth;

        // 更新UI状态
        this.updateFilterStatus();
        this.renderCategoryExpenses();
    }

    /**
     * 处理搜索输入
     */
    handleSearchInput(searchTerm) {
        console.log('搜索商户:', searchTerm);

        // 更新筛选状态
        this.activeFilters.search = searchTerm.trim();

        // 更新UI状态
        this.updateFilterStatus();
        this.renderCategoryExpenses();
    }

    /**
     * 应用日期范围筛选
     */
    applyDateRangeFilter() {
        const startDate = document.getElementById('start-date-input')?.value;
        const endDate = document.getElementById('end-date-input')?.value;

        if (startDate || endDate) {
            this.activeFilters.dateRange = { start: startDate, end: endDate };
            console.log('应用日期范围筛选:', this.activeFilters.dateRange);

            // 重新加载数据
            this.loadData();
        }
    }

    /**
     * 清除所有筛选条件
     */
    clearAllFilters() {
        console.log('清除所有筛选条件');

        // 重置筛选状态
        this.activeFilters = {
            category: null,
            month: null,
            search: '',
            dateRange: { start: null, end: null }
        };

        // 清除输入框
        const searchInput = document.getElementById('merchant-search-input');
        if (searchInput) searchInput.value = '';

        const startDateInput = document.getElementById('start-date-input');
        if (startDateInput) startDateInput.value = '';

        const endDateInput = document.getElementById('end-date-input');
        if (endDateInput) endDateInput.value = '';

        // 更新UI
        this.updateFilterStatus();
        this.updateCategoryCardStates();
        this.renderCategoryExpenses();

        // 如果有日期筛选，重新加载数据
        this.loadData();
    }

    /**
     * 更新筛选状态显示
     */
    updateFilterStatus() {
        const statusContainer = document.getElementById('filter-status');
        const activeFiltersContainer = document.getElementById('active-filters');

        if (!statusContainer || !activeFiltersContainer) return;

        const activeFilterTags = [];

        // 分类筛选标签
        if (this.activeFilters.category) {
            const categoryData = this.data?.categories?.[this.activeFilters.category];
            if (categoryData) {
                activeFilterTags.push(`
                    <span class="badge bg-primary bg-opacity-10 text-primary">
                        分类: ${categoryData.name}
                        <button type="button" class="btn-close btn-close-sm ms-1"
                                onclick="expenseAnalysisPage.filterByCategory('${this.activeFilters.category}')"
                                aria-label="移除筛选"></button>
                    </span>
                `);
            }
        }

        // 月份筛选标签
        if (this.activeFilters.month) {
            activeFilterTags.push(`
                <span class="badge bg-success bg-opacity-10 text-success">
                    月份: ${this.activeFilters.month}
                    <button type="button" class="btn-close btn-close-sm ms-1"
                            onclick="expenseAnalysisPage.filterByMonth('${this.activeFilters.month}')"
                            aria-label="移除筛选"></button>
                </span>
            `);
        }

        // 搜索筛选标签
        if (this.activeFilters.search) {
            activeFilterTags.push(`
                <span class="badge bg-info bg-opacity-10 text-info">
                    搜索: ${this.activeFilters.search}
                    <button type="button" class="btn-close btn-close-sm ms-1"
                            onclick="expenseAnalysisPage.handleSearchInput('')"
                            aria-label="移除筛选"></button>
                </span>
            `);
        }

        // 日期范围筛选标签
        if (this.activeFilters.dateRange.start || this.activeFilters.dateRange.end) {
            const dateText = `${this.activeFilters.dateRange.start || '开始'} ~ ${this.activeFilters.dateRange.end || '结束'}`;
            activeFilterTags.push(`
                <span class="badge bg-warning bg-opacity-10 text-warning">
                    日期: ${dateText}
                    <button type="button" class="btn-close btn-close-sm ms-1"
                            onclick="expenseAnalysisPage.clearDateRangeFilter()"
                            aria-label="移除筛选"></button>
                </span>
            `);
        }

        // 显示或隐藏筛选状态
        if (activeFilterTags.length > 0) {
            activeFiltersContainer.innerHTML = activeFilterTags.join('');
            statusContainer.style.display = 'block';
        } else {
            statusContainer.style.display = 'none';
        }
    }

    /**
     * 清除日期范围筛选
     */
    clearDateRangeFilter() {
        this.activeFilters.dateRange = { start: null, end: null };

        // 清除输入框
        const startDateInput = document.getElementById('start-date-input');
        if (startDateInput) startDateInput.value = '';

        const endDateInput = document.getElementById('end-date-input');
        if (endDateInput) endDateInput.value = '';

        // 更新UI并重新加载数据
        this.updateFilterStatus();
        this.loadData();
    }

    /**
     * 更新分类卡片的选中状态
     */
    updateCategoryCardStates() {
        // 更新KPI卡片的视觉状态
        const categoryCards = ['dining', 'transport', 'shopping'];
        categoryCards.forEach(category => {
            const cardElement = document.querySelector(`[onclick*="filterByCategory('${category}')"]`);
            if (cardElement) {
                if (this.activeFilters.category === category) {
                    cardElement.classList.add('active-filter');
                } else {
                    cardElement.classList.remove('active-filter');
                }
            }
        });
    }

    // ==================== 工具方法 ====================

    /**
     * 高亮搜索词
     */
    highlightSearchTerm(text, searchTerm) {
        if (!searchTerm || !text) return text;

        const regex = new RegExp(`(${searchTerm.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi');
        return text.replace(regex, '<mark class="bg-warning bg-opacity-25">$1</mark>');
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
    }

    /**
     * 显示主要内容
     */
    showMainContent() {
        document.getElementById('main-content').style.display = 'block';
        document.getElementById('error-state').style.display = 'none';
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

    /**
     * 显示提示消息
     */
    showToast(message, type = 'info') {
        // 这里可以集成Toast组件
        console.log(`[${type.toUpperCase()}] ${message}`);

        // 简单的alert实现，可以后续替换为更好的Toast组件
        if (type === 'error') {
            alert('错误: ' + message);
        }
    }
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    new ExpenseAnalysisPage();
});
