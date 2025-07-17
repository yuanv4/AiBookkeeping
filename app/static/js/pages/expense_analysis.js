/**
 * 支出分类分析页面
 * 提供基于商户类型的智能支出分类与统计分析功能
 */

import BasePage from '../common/BasePage.js';
import { ChartHelper, apiService, StandardTableGenerator } from '../common/utils.js';

/**
 * 状态管理系统
 * 管理应用的全局状态和数据缓存
 */
class ExpenseAnalysisState {
    constructor() {
        this.selectedMonth = null;
        this.availableMonths = [];
        this.categoryData = {};
        this.loading = false;
        this.error = null;
        this.dataCache = new Map();
        this.subscribers = [];

        console.log('状态管理系统初始化完成');
    }

    /**
     * 订阅状态变更
     */
    subscribe(callback) {
        this.subscribers.push(callback);
    }

    /**
     * 取消订阅
     */
    unsubscribe(callback) {
        this.subscribers = this.subscribers.filter(sub => sub !== callback);
    }

    /**
     * 通知所有订阅者状态变更
     */
    notifyStateChange() {
        const state = this.getState();
        this.subscribers.forEach(callback => {
            try {
                callback(state);
            } catch (error) {
                console.error('状态变更通知失败:', error);
            }
        });
    }

    /**
     * 获取当前状态
     */
    getState() {
        return {
            selectedMonth: this.selectedMonth,
            availableMonths: this.availableMonths,
            categoryData: this.categoryData,
            loading: this.loading,
            error: this.error
        };
    }

    /**
     * 设置选中月份
     */
    setSelectedMonth(month) {
        if (this.selectedMonth !== month) {
            this.selectedMonth = month;
            console.log('选中月份变更:', month);
            this.notifyStateChange();
        }
    }

    /**
     * 设置可用月份列表
     */
    setAvailableMonths(months) {
        this.availableMonths = months;
        this.notifyStateChange();
    }

    /**
     * 设置分类数据
     */
    setCategoryData(data) {
        this.categoryData = data;
        this.notifyStateChange();
    }

    /**
     * 设置加载状态
     */
    setLoading(loading) {
        this.loading = loading;
        this.notifyStateChange();
    }

    /**
     * 设置错误状态
     */
    setError(error) {
        this.error = error;
        this.notifyStateChange();
    }

    /**
     * 缓存数据
     */
    cacheData(key, data) {
        this.dataCache.set(key, {
            data: data,
            timestamp: Date.now()
        });
    }

    /**
     * 获取缓存数据
     */
    getCachedData(key, maxAge = 5 * 60 * 1000) { // 默认5分钟缓存
        const cached = this.dataCache.get(key);
        if (cached && (Date.now() - cached.timestamp) < maxAge) {
            return cached.data;
        }
        return null;
    }

    /**
     * 清理过期缓存
     */
    cleanExpiredCache() {
        const now = Date.now();
        const maxAge = 10 * 60 * 1000; // 10分钟

        for (const [key, value] of this.dataCache.entries()) {
            if (now - value.timestamp > maxAge) {
                this.dataCache.delete(key);
            }
        }
    }

    /**
     * 清除缓存
     */
    clearCache() {
        this.dataCache.clear();
    }
}

/**
 * 数据加载组件
 * 负责API数据获取、缓存和预加载
 */
class DataLoader {
    constructor(state) {
        this.state = state;
    }

    /**
     * 加载可用月份数据
     */
    async loadAvailableMonths() {
        try {
            console.log('开始加载可用月份数据...');

            // 检查缓存
            const cached = this.state.getCachedData('available-months');
            if (cached) {
                console.log('使用缓存的月份数据');
                this.state.setAvailableMonths(cached);
                return cached;
            }

            const result = await apiService.standardPost('/expense-analysis/api/available-months', {}, {
                method: 'GET'
            });

            if (!result.success) {
                throw new Error(result.error || '获取可用月份失败');
            }

            // 缓存数据
            this.state.cacheData('available-months', result.data);
            this.state.setAvailableMonths(result.data);

            console.log('可用月份数据加载完成:', result.data);
            return result.data;

        } catch (error) {
            console.error('加载可用月份失败:', error);
            const errorMessage = error.message || '网络连接异常，请检查网络后重试';
            this.state.setError('加载可用月份失败: ' + errorMessage);

            // 提供默认的空数据，避免页面完全无法使用
            const fallbackData = {
                months: [],
                latest_month: null,
                total_months: 0,
                month_stats: {}
            };
            this.state.setAvailableMonths(fallbackData);
            throw error;
        }
    }

    /**
     * 加载指定月份的分析数据
     */
    async loadMonthData(month) {
        try {
            console.log('开始加载月份数据:', month);

            // 检查缓存
            const cacheKey = `month-data-${month}`;
            const cached = this.state.getCachedData(cacheKey);
            if (cached) {
                console.log('使用缓存的月份数据:', month, cached);
                console.log('缓存数据的target_month:', cached.target_month);
                console.log('缓存数据的总支出:', cached.summary?.total_expense);
                console.log('缓存数据的分析期间:', cached.summary?.analyzed_period);

                // 验证缓存数据是否匹配请求的月份
                if (cached.target_month !== month) {
                    console.error('缓存数据月份不匹配！请求:', month, '缓存:', cached.target_month);
                    console.log('清除错误的缓存数据');
                    this.state.clearCachedData(cacheKey);
                } else {
                    this.state.setCategoryData(cached);
                    return cached;
                }
            }

            this.state.setLoading(true);

            const params = new URLSearchParams();
            params.append('month', month);

            const url = `/expense-analysis/api/merchant-analysis?${params.toString()}`;
            console.log('=== API调用开始 ===');
            console.log('请求URL:', url);
            console.log('请求月份:', month);

            const result = await apiService.standardPost(url, {}, {
                method: 'GET'
            });
            console.log('API响应数据:', result);

            if (!result.success) {
                throw new Error(result.error || '加载月份数据失败');
            }

            // 缓存数据
            this.state.cacheData(cacheKey, result.data);
            this.state.setCategoryData(result.data);
            this.state.setLoading(false);

            console.log('月份数据加载完成:', month, result.data);

            // 确保主要内容显示
            setTimeout(() => {
                const mainPage = window.expenseAnalysisPage;
                if (mainPage && mainPage.showMainContent) {
                    mainPage.showMainContent();

                }
            }, 100);

            return result.data;

        } catch (error) {
            console.error('加载月份数据失败:', error);
            this.state.setLoading(false);

            // 根据错误类型提供不同的错误信息
            let errorMessage = '加载数据失败';
            if (error.name === 'TypeError' && error.message.includes('fetch')) {
                errorMessage = '网络连接失败，请检查网络连接后重试';
            } else if (error.message.includes('404')) {
                errorMessage = '请求的数据不存在，请联系管理员';
            } else if (error.message.includes('500')) {
                errorMessage = '服务器内部错误，请稍后重试';
            } else {
                errorMessage = error.message || '未知错误，请重试';
            }

            this.state.setError(errorMessage);
            throw error;
        }
    }

    /**
     * 预加载相邻月份数据
     */
    async preloadAdjacentMonths(currentMonth, availableMonths) {
        try {
            const currentIndex = availableMonths.indexOf(currentMonth);
            const toPreload = [];

            // 预加载前一个月
            if (currentIndex > 0) {
                toPreload.push(availableMonths[currentIndex - 1]);
            }

            // 预加载后一个月
            if (currentIndex < availableMonths.length - 1) {
                toPreload.push(availableMonths[currentIndex + 1]);
            }

            // 异步预加载，不阻塞主流程
            toPreload.forEach(month => {
                const cacheKey = `month-data-${month}`;
                if (!this.state.getCachedData(cacheKey)) {
                    setTimeout(() => {
                        this.loadMonthData(month).catch(error => {
                            console.log('预加载月份数据失败:', month, error.message);
                        });
                    }, 1000); // 延迟1秒预加载
                }
            });

        } catch (error) {
            console.log('预加载相邻月份失败:', error);
        }
    }
}

/**
 * 月份选择组件
 * 负责月份选择、图表展示和点击事件处理
 */
class MonthSelector {
    constructor(state, dataLoader) {
        this.state = state;
        this.dataLoader = dataLoader;
        this.chart = null;
        this.lastRenderedMonth = null; // 记录上次渲染的月份

        // 订阅状态变更
        this.state.subscribe((state) => this.onStateChange(state));
    }

    /**
     * 状态变更处理
     */
    onStateChange(state) {
        if (state.categoryData && state.selectedMonth &&
            state.categoryData.categories &&
            Object.keys(state.categoryData.categories).length > 0) {

            // 避免重复渲染同一个月份的图表
            if (this.lastRenderedMonth !== state.selectedMonth) {
                console.log('图表需要重新渲染，从', this.lastRenderedMonth, '到', state.selectedMonth);
                this.renderChart(state.categoryData, state.selectedMonth);
                this.lastRenderedMonth = state.selectedMonth;
            } else {
                console.log('跳过图表重复渲染，月份未变化:', state.selectedMonth);
            }
        }
    }

    /**
     * 初始化月份选择器
     */
    async initialize() {
        try {
            // 加载可用月份
            const monthsData = await this.dataLoader.loadAvailableMonths();

            // 检查URL参数中的月份
            const urlParams = new URLSearchParams(window.location.search);
            const urlMonth = urlParams.get('month');

            let selectedMonth = monthsData.latest_month;

            // 如果URL中有月份参数且在可用月份中，使用URL参数
            if (urlMonth && monthsData.months && monthsData.months.includes(urlMonth)) {
                selectedMonth = urlMonth;
                console.log('使用URL参数中的月份:', urlMonth);
            } else if (urlMonth) {
                console.warn('URL参数中的月份不在可用月份中:', urlMonth, '可用月份:', monthsData.months);
            }

            // 设置选中月份
            if (selectedMonth) {
                await this.selectMonth(selectedMonth);
            }

        } catch (error) {
            console.error('月份选择器初始化失败:', error);
        }
    }



    /**
     * 选择月份
     */
    async selectMonth(month) {
        try {
            console.log('=== MonthSelector.selectMonth ===');
            console.log('选择月份:', month);
            console.log('当前状态中的选中月份:', this.state.selectedMonth);

            // 更新状态
            this.state.setSelectedMonth(month);
            console.log('状态已更新，新的选中月份:', this.state.selectedMonth);

            // 加载月份数据
            console.log('开始加载月份数据...');
            await this.dataLoader.loadMonthData(month);
            console.log('月份数据加载完成');

            // 预加载相邻月份
            const availableMonths = this.state.availableMonths;
            if (availableMonths.length > 0) {
                this.dataLoader.preloadAdjacentMonths(month, availableMonths);
            }

        } catch (error) {
            console.error('选择月份失败:', error);
        }
    }

    /**
     * 渲染图表
     */
    renderChart(data, selectedMonth) {
        try {
            console.log('开始渲染图表，选中月份:', selectedMonth);
            const canvas = document.getElementById('monthly-trend-chart');
            if (!canvas) {
                console.error('图表canvas不存在');
                return;
            }

            // 保存当前实例的引用，用于图表点击事件
            const monthSelectorInstance = this;

            // 销毁现有图表
            if (this.chart) {
                console.log('销毁现有图表');
                try {
                    // 彻底销毁图表和所有相关资源
                    this.chart.destroy();
                } catch (error) {
                    console.warn('销毁图表时出现警告:', error);
                }
                this.chart = null;
                console.log('图表已销毁');
            }

            // 从各分类的月度数据中构建图表数据
            const monthlyDataMap = {};
            const { categories } = data;

            // 数据验证
            if (!categories || typeof categories !== 'object') {
                console.error('图表数据无效:', data);
                return;
            }

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

            console.log('月度数据映射:', monthlyDataMap);

            // 准备图表数据 - 显示选中月份及前4个月（总共5个月）
            const allMonths = Object.keys(monthlyDataMap).sort();
            console.log('所有月份:', allMonths);
            console.log('选中月份:', selectedMonth);

            const selectedIndex = allMonths.indexOf(selectedMonth);
            console.log('选中月份索引:', selectedIndex);

            let labels;
            if (selectedIndex >= 0) {
                // 确保始终显示5个月，以选中月份为结束点
                const endIndex = selectedIndex + 1;
                const startIndex = Math.max(0, endIndex - 5);
                labels = allMonths.slice(startIndex, endIndex);

                // 如果不足5个月，从最早的月份开始显示
                if (labels.length < 5 && allMonths.length >= 5) {
                    labels = allMonths.slice(0, 5);
                }

                console.log('计算的标签范围:', startIndex, 'to', endIndex, '结果:', labels, '长度:', labels.length);
            } else {
                // 如果选中月份不在数据中，显示最近5个月
                labels = allMonths.slice(-5);
                console.log('使用最近5个月:', labels);
            }

            // 为主要分类准备数据集
            const datasets = [
                {
                    label: '餐饮支出',
                    data: labels.map(month => monthlyDataMap[month]?.dining || 0),
                    backgroundColor: labels.map(month =>
                        month === selectedMonth ? 'rgba(13, 110, 253, 1)' : 'rgba(13, 110, 253, 0.8)'
                    ),
                    borderColor: 'rgba(13, 110, 253, 1)',
                    borderWidth: labels.map(month => month === selectedMonth ? 3 : 1),
                    borderRadius: 4,
                    stack: 'expenses'
                },
                {
                    label: '交通支出',
                    data: labels.map(month => monthlyDataMap[month]?.transport || 0),
                    backgroundColor: labels.map(month =>
                        month === selectedMonth ? 'rgba(25, 135, 84, 1)' : 'rgba(25, 135, 84, 0.8)'
                    ),
                    borderColor: 'rgba(25, 135, 84, 1)',
                    borderWidth: labels.map(month => month === selectedMonth ? 3 : 1),
                    borderRadius: 4,
                    stack: 'expenses'
                },
                {
                    label: '购物支出',
                    data: labels.map(month => monthlyDataMap[month]?.shopping || 0),
                    backgroundColor: labels.map(month =>
                        month === selectedMonth ? 'rgba(13, 202, 240, 1)' : 'rgba(13, 202, 240, 0.8)'
                    ),
                    borderColor: 'rgba(13, 202, 240, 1)',
                    borderWidth: labels.map(month => month === selectedMonth ? 3 : 1),
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
                    backgroundColor: labels.map(month =>
                        month === selectedMonth ? 'rgba(108, 117, 125, 1)' : 'rgba(108, 117, 125, 0.8)'
                    ),
                    borderColor: 'rgba(108, 117, 125, 1)',
                    borderWidth: labels.map(month => month === selectedMonth ? 3 : 1),
                    borderRadius: 4,
                    stack: 'expenses'
                }
            ];

            console.log('图表数据准备完成:', { labels, datasets });

            // 使用ChartHelper创建图表
            console.log('使用ChartHelper创建图表');
            const chartOptions = {
                data: {
                    labels: labels,
                    datasets: datasets
                },
                options: {
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
                    onClick: (_, elements) => {
                        if (elements.length > 0) {
                            const clickedIndex = elements[0].index;
                            const clickedMonth = labels[clickedIndex];
                            console.log('=== 图表点击事件 ===');
                            console.log('点击的月份:', clickedMonth);
                            console.log('点击的索引:', clickedIndex);
                            console.log('当前标签:', labels);
                            // 使用保存的实例引用
                            monthSelectorInstance.selectMonth(clickedMonth);
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
            };

            this.chart = ChartHelper.createBarChart('monthly-trend-chart', chartOptions);

            if (this.chart) {
                console.log('图表创建成功');
            } else {
                console.error('图表创建失败');
            }
        } catch (error) {
            console.error('渲染图表失败:', error);
        }
    }
}

/**
 * 分类详情组件
 * 负责分类详情展示，响应月份状态变化
 */
class CategoryDetails {
    constructor(state) {
        this.state = state;
        this.expandedCategories = new Set();
        this.activeFilters = {
            category: null,
            search: ''
        };

        // 订阅状态变更
        this.state.subscribe((state) => this.onStateChange(state));
    }

    /**
     * 状态变更处理
     */
    onStateChange(state) {
        console.log('CategoryDetails状态变更:', {
            selectedMonth: state.selectedMonth,
            hasCategoryData: !!state.categoryData,
            hasCategories: !!(state.categoryData && state.categoryData.categories),
            categoriesCount: state.categoryData && state.categoryData.categories ? Object.keys(state.categoryData.categories).length : 0
        });

        if (state.categoryData && state.selectedMonth &&
            state.categoryData.categories &&
            Object.keys(state.categoryData.categories).length > 0) {
            console.log('开始渲染分类详情，月份:', state.selectedMonth);
            console.log('传递给renderCategoryExpenses的数据:', state.categoryData);
            console.log('数据中的target_month:', state.categoryData.target_month);
            this.renderCategoryExpenses(state.categoryData);
        } else {
            console.log('跳过分类详情渲染，条件不满足');
        }
    }

    /**
     * 渲染分类支出列表
     */
    renderCategoryExpenses(data) {
        console.log('=== renderCategoryExpenses 开始 ===');
        console.log('传入的数据:', data);

        const container = document.getElementById('expense-categories');
        if (!container) {
            console.error('分类详情容器不存在');
            return;
        }

        // 数据验证
        if (!data || typeof data !== 'object') {
            console.error('无效的数据格式:', data);
            container.innerHTML = '<div class="text-danger text-center py-3">数据格式错误，请刷新页面重试</div>';
            return;
        }

        const { categories } = data;
        console.log('提取的分类数据:', categories);

        if (!categories || typeof categories !== 'object' || Object.keys(categories).length === 0) {
            container.innerHTML = `
                <div class="text-center py-5">
                    <div class="text-muted mb-3">
                        <i data-lucide="inbox" style="width: 3rem; height: 3rem; opacity: 0.5;"></i>
                    </div>
                    <h6 class="text-muted">暂无支出分类数据</h6>
                    <p class="text-muted small mb-0">当前月份没有找到支出记录</p>
                </div>
            `;
            // 重新初始化图标
            this.initializeIcons();
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
                <div class="category-summary-card card-hover-effect-subtle mb-3">
                    <div class="card border-0 shadow-sm">
                        <div class="card-body p-3 cursor-pointer" onclick="window.expenseAnalysisPage.categoryDetails.toggleCategoryExpansion('${categoryKey}')">
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
        this.initializeIcons();

        console.log('=== renderCategoryExpenses 完成 ===');
        console.log('已渲染分类数量:', sortedCategories.length);
        console.log('容器HTML长度:', container.innerHTML.length);
        console.log('前3个分类的金额:', sortedCategories.slice(0, 3).map(([_, data]) => ({
            name: data.name,
            amount: data.total_amount,
            percentage: data.percentage
        })));

        // 详细输出所有分类的关键数据
        console.log('所有分类详细数据:');
        sortedCategories.forEach(([_, data], index) => {
            console.log(`${index + 1}. ${data.name}: ¥${data.total_amount} (${data.percentage}%)`);
        });
    }

    /**
     * 渲染分类商户详情
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

        // 使用StandardTableGenerator生成标准表格
        return StandardTableGenerator.generateTable({
            id: 'category-merchant-details-table',
            headers: [
                '商户名称',
                '<span class="text-end">总金额</span>',
                '<span class="text-center d-none d-md-inline">交易次数</span>',
                '<span class="text-center d-none d-lg-inline">平均金额</span>',
                '<span class="text-center">操作</span>'
            ],
            data: merchantArray,
            rowRenderer: (merchant) => {
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
                            <button class="btn btn-sm btn-outline-primary" onclick="window.expenseAnalysisPage.showMerchantDetail('${merchant.name}')" title="查看详情">
                                <i data-lucide="eye" style="width: 0.75rem; height: 0.75rem;"></i>
                                <span class="d-none d-sm-inline ms-1 small">详情</span>
                            </button>
                        </td>
                    </tr>
                `;
            },
            noDataMessage: "没有找到匹配的商户"
        });
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
                const currentData = this.state.getState().categoryData;
                if (currentData && currentData.categories && currentData.categories[categoryKey]) {
                    const categoryData = currentData.categories[categoryKey];
                    if (categoryData.merchants) {
                        merchantsContainer.innerHTML = this.renderCategoryMerchantDetails(categoryData.merchants);

                        // 重新初始化Lucide图标
                        this.initializeIcons();
                    }
                }
            }
        }
    }

    /**
     * 高亮搜索词
     */
    highlightSearchTerm(text, searchTerm) {
        if (!searchTerm || !text) return text;

        const regex = new RegExp(`(${searchTerm.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi');
        return text.replace(regex, '<mark class="bg-warning bg-opacity-25">$1</mark>');
    }

    /**
     * 设置搜索筛选
     */
    setSearchFilter(searchTerm) {
        this.activeFilters.search = searchTerm.trim();
        // 重新渲染当前数据
        const currentData = this.state.getState().categoryData;
        if (currentData) {
            this.renderCategoryExpenses(currentData);
        }
    }

    /**
     * 设置分类筛选
     */
    setCategoryFilter(categoryKey) {
        this.activeFilters.category = this.activeFilters.category === categoryKey ? null : categoryKey;
        // 重新渲染当前数据
        const currentData = this.state.getState().categoryData;
        if (currentData) {
            this.renderCategoryExpenses(currentData);
        }
    }
}

class ExpenseAnalysisPage extends BasePage {
    constructor() {
        super();
        this.chart = null;
        this.data = null;
        this.expandedCategories = new Set(); // 展开的分类
        this.activeFilters = {
            category: null,
            search: ''
        }; // 活跃的筛选条件（简化版，月份由状态管理）

        // 商户详情模态框状态跟踪
        this.merchantModalState = {
            isOpen: false,
            currentMerchant: null,
            lastMonth: null
        };

        // 初始化状态管理系统
        this.state = new ExpenseAnalysisState();

        // 初始化组件
        this.dataLoader = new DataLoader(this.state);
        this.monthSelector = new MonthSelector(this.state, this.dataLoader);
        this.categoryDetails = new CategoryDetails(this.state);

        // 订阅状态变更
        this.state.subscribe((state) => this.onStateChange(state));

        // 定期清理缓存
        this.setupCacheCleanup();

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
     * 状态变更处理器
     */
    onStateChange(state) {
        console.log('状态变更:', state);

        // 更新本地数据引用
        if (state.categoryData) {
            this.data = state.categoryData;
        }

        // 检查月份变更并处理模态框刷新
        if (state.selectedMonth && this.merchantModalState.lastMonth !== state.selectedMonth) {
            this.handleMonthChangeForModal(state.selectedMonth);
            this.merchantModalState.lastMonth = state.selectedMonth;
        }

        // 处理加载状态
        if (state.loading) {
            this.showLoading();
            this.addDataUpdatingClass();
        } else {
            this.hideLoading();
            this.removeDataUpdatingClass();

            // 数据加载完成后显示主要内容
            if (state.categoryData && state.selectedMonth) {
                this.showMainContent();
            }
        }

        // 处理错误状态
        if (state.error) {
            this.showError(state.error);
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


    }

    /**
     * 处理月份变更对模态框的影响
     */
    handleMonthChangeForModal(newMonth) {
        // 检查商户详情模态框是否打开
        if (this.merchantModalState.isOpen && this.merchantModalState.currentMerchant) {
            console.log('检测到月份变更，模态框已打开，准备刷新商户详情:', {
                merchant: this.merchantModalState.currentMerchant,
                oldMonth: this.merchantModalState.lastMonth,
                newMonth: newMonth
            });

            // 自动刷新商户详情数据
            this.refreshMerchantDetailModal(this.merchantModalState.currentMerchant);
        }
    }

    /**
     * 刷新商户详情模态框数据
     */
    async refreshMerchantDetailModal(merchantName) {
        try {
            console.log('刷新商户详情模态框数据:', merchantName);

            // 获取当前选中月份
            const selectedMonth = this.state.selectedMonth;

            // 构建API URL
            let apiUrl = `/expense-analysis/api/merchant-details/${encodeURIComponent(merchantName)}`;
            if (selectedMonth) {
                apiUrl += `?month=${encodeURIComponent(selectedMonth)}`;
            }

            // 显示加载状态
            const container = document.getElementById('merchant-detail-content');
            if (container) {
                container.innerHTML = `
                    <div class="text-center py-3">
                        <div class="spinner-border text-primary" role="status">
                            <span class="visually-hidden">加载中...</span>
                        </div>
                        <div class="mt-2 text-muted small">正在更新数据...</div>
                    </div>
                `;
            }

            // 检查缓存（刷新时使用较短的缓存时间）
            const cacheKey = `merchant-detail-${merchantName}-${selectedMonth || 'all'}`;
            const cachedData = this.state.getCachedData(cacheKey, 30 * 1000); // 30秒缓存

            if (cachedData) {
                console.log('使用缓存的商户详情数据进行刷新:', cachedData);
                this.renderMerchantDetailModal(cachedData);
                return;
            }

            // 加载新数据
            const data = await apiService.standardPost(apiUrl, {}, {
                method: 'GET'
            });

            if (data.success) {
                // 缓存数据
                this.state.cacheData(cacheKey, data.data);
                this.renderMerchantDetailModal(data.data);
            } else {
                throw new Error(data.error || '刷新商户详情失败');
            }

        } catch (error) {
            console.error('刷新商户详情模态框失败:', error);

            // 显示错误状态
            const container = document.getElementById('merchant-detail-content');
            if (container) {
                container.innerHTML = `
                    <div class="text-center py-3 text-danger">
                        <i data-lucide="alert-circle" style="width: 2rem; height: 2rem;"></i>
                        <div class="mt-2">刷新失败: ${error.message}</div>
                        <button class="btn btn-sm btn-outline-primary mt-2" onclick="window.expenseAnalysisPage.refreshMerchantDetailModal('${this.merchantModalState.currentMerchant}')">
                            重试
                        </button>
                    </div>
                `;

                // 重新初始化图标
                this.initializeIcons();
            }
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

            // 初始化月份选择器（会自动加载数据）
            await this.monthSelector.initialize();

            console.log('支出分类分析页面初始化完成');
        } catch (error) {
            console.error('页面初始化失败:', error);
            this.showError(error.message);
        }
    }



    /**
     * 渲染页面内容
     */
    render() {
        this.hideLoading();

        this.showMainContent();
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
     * 显示商户详情
     */
    async showMerchantDetail(merchantName) {
        try {
            console.log('显示商户详情:', merchantName);

            // 获取当前选中月份
            const selectedMonth = this.state.selectedMonth;
            console.log('当前选中月份:', selectedMonth);

            // 更新模态框状态跟踪
            this.merchantModalState.isOpen = true;
            this.merchantModalState.currentMerchant = merchantName;
            this.merchantModalState.lastMonth = selectedMonth;

            // 显示模态框
            const modal = new bootstrap.Modal(document.getElementById('merchantDetailModal'));

            // 监听模态框关闭事件
            const modalElement = document.getElementById('merchantDetailModal');
            modalElement.addEventListener('hidden.bs.modal', () => {
                this.merchantModalState.isOpen = false;
                this.merchantModalState.currentMerchant = null;
                console.log('商户详情模态框已关闭，状态已清理');
            }, { once: true });

            modal.show();

            // 显示初始加载状态
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

            // 构建API URL，包含月份参数
            let apiUrl = `/expense-analysis/api/merchant-details/${encodeURIComponent(merchantName)}`;
            if (selectedMonth) {
                apiUrl += `?month=${encodeURIComponent(selectedMonth)}`;
                console.log('API URL包含月份参数:', apiUrl);
            } else {
                console.log('未选择月份，显示所有交易数据');
            }

            // 检查缓存
            const cacheKey = `merchant-detail-${merchantName}-${selectedMonth || 'all'}`;
            const cachedData = this.state.getCachedData(cacheKey, 2 * 60 * 1000); // 2分钟缓存

            if (cachedData) {
                console.log('使用缓存的商户详情数据:', cachedData);
                this.renderMerchantDetailModal(cachedData);
                return;
            }

            // 加载商户详情数据
            const data = await apiService.standardPost(apiUrl, {}, {
                method: 'GET'
            });

            if (data.success) {
                console.log('商户详情数据加载成功:', data.data);

                // 缓存数据
                this.state.cacheData(cacheKey, data.data);

                this.renderMerchantDetailModal(data.data);
            } else {
                throw new Error(data.error || '获取商户详情失败');
            }

        } catch (error) {
            console.error('显示商户详情失败:', error);

            // 在模态框中显示错误状态
            const container = document.getElementById('merchant-detail-content');
            if (container) {
                container.innerHTML = `
                    <div class="text-center py-4">
                        <div class="text-danger mb-3">
                            <i data-lucide="alert-circle" style="width: 3rem; height: 3rem;"></i>
                        </div>
                        <h6 class="text-danger">加载失败</h6>
                        <p class="text-muted mb-3">${error.message}</p>
                        <button class="btn btn-primary btn-sm" onclick="window.expenseAnalysisPage.showMerchantDetail('${merchantName}')">
                            <i data-lucide="refresh-cw" class="me-1" style="width: 1rem; height: 1rem;"></i>
                            重新加载
                        </button>
                    </div>
                `;

                // 重新初始化图标
                this.initializeIcons();
            }

            this.showToast('获取商户详情失败: ' + error.message, 'error');
        }
    }

    /**
     * 渲染商户详情模态框内容 - 渐进式信息展示
     */
    renderMerchantDetailModal(merchantData) {
        const container = document.getElementById('merchant-detail-content');
        const { merchant_name, category_info, transactions, statistics, filter_info } = merchantData;

        // 更新模态框标题以包含月份信息
        const modalTitle = document.getElementById('merchantDetailModalLabel');
        if (modalTitle && filter_info) {
            const periodText = filter_info.period_info || '所有时间';
            modalTitle.innerHTML = `
                <i data-lucide="store" class="me-2"></i>
                商户详情 - ${merchant_name}
                <small class="text-muted ms-2">(${periodText})</small>
            `;
        }

        // 渲染简化的两层展示结构
        const overviewHtml = this.renderMerchantOverview(merchantData);
        const transactionsHtml = this.renderMerchantTransactions(merchantData);

        container.innerHTML = `
            ${overviewHtml}
            ${transactionsHtml}
        `;

        // 初始化交互事件
        this.initializeMerchantModalInteractions();

        // 重新初始化Lucide图标
        this.initializeIcons();
    }

    /**
     * 渲染商户概览区域（基础层）
     */
    renderMerchantOverview(merchantData) {
        const { merchant_name, category_info, statistics, filter_info } = merchantData;
        const periodInfo = filter_info ? filter_info.period_info : '所有时间';

        return `
            <div class="merchant-overview-section">
                <div class="merchant-header-enhanced">
                    <div class="d-flex align-items-center justify-content-between">
                        <div class="d-flex align-items-center">
                            <div class="merchant-avatar-lg me-3">
                                <i data-lucide="${category_info.icon}" class="text-${category_info.color}" style="width: 2rem; height: 2rem;"></i>
                            </div>
                            <div>
                                <h4 class="merchant-name-primary">${merchant_name}</h4>
                                <div class="merchant-meta-row">
                                    <span class="category-badge-enhanced bg-${category_info.color} bg-opacity-10 text-${category_info.color}">${category_info.name}</span>
                                    <span class="period-indicator">${periodInfo}</span>
                                </div>
                            </div>
                        </div>
                        <div class="merchant-actions">
                            <button class="btn btn-primary btn-sm expand-toggle-btn card-hover-effect-subtle"
                                    data-bs-toggle="collapse"
                                    data-bs-target="#merchantTransactionsCollapse"
                                    aria-expanded="false">
                                <i data-lucide="list" class="me-1" style="width: 1rem; height: 1rem;"></i>
                                查看交易记录
                            </button>
                        </div>
                    </div>
                </div>

                <div class="merchant-stats-grid row g-3">
                    <div class="col-md-4">
                        <div class="stat-card card-hover-effect" data-stat="total">
                            <div class="stat-value text-danger">¥${statistics.total_amount.toFixed(2)}</div>
                            <div class="stat-label">总支出</div>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="stat-card card-hover-effect" data-stat="count">
                            <div class="stat-value text-primary">${statistics.transaction_count}</div>
                            <div class="stat-label">交易次数</div>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="stat-card card-hover-effect" data-stat="average">
                            <div class="stat-value text-success">¥${statistics.average_amount.toFixed(0)}</div>
                            <div class="stat-label">平均金额</div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }



    /**
     * 渲染交易记录区域（详情层）
     */
    renderMerchantTransactions(merchantData) {
        const { transactions, filter_info } = merchantData;
        const hasTransactions = transactions && transactions.length > 0;
        const periodInfo = filter_info ? filter_info.period_info : '所有时间';

        return `
            <div class="merchant-transactions-section collapse" id="merchantTransactionsCollapse">
                <div class="d-flex justify-content-between align-items-center mb-3">
                    <h6 class="mb-0">
                        <i data-lucide="list" class="me-2 text-primary" style="width: 1.25rem; height: 1.25rem;"></i>
                        交易记录
                    </h6>
                    <button class="btn btn-outline-secondary btn-sm expand-toggle-btn card-hover-effect-subtle"
                            data-bs-toggle="collapse"
                            data-bs-target="#merchantTransactionsCollapse"
                            aria-expanded="true">
                        <i data-lucide="chevron-up" class="me-1" style="width: 1rem; height: 1rem;"></i>
                        收起
                    </button>
                </div>

                ${hasTransactions ? `
                    <div class="transactions-table-container">
                        <div class="table-responsive">
                            <table class="table table-hover table-sm mb-0">
                                <thead class="table-light">
                                    <tr>
                                        <th class="border-0 px-3 py-3 fw-semibold text-muted small">日期</th>
                                        <th class="border-0 px-3 py-3 fw-semibold text-muted small d-none d-md-table-cell">账户</th>
                                        <th class="border-0 px-3 py-3 fw-semibold text-muted small text-end">金额</th>
                                        <th class="border-0 px-3 py-3 fw-semibold text-muted small text-end d-none d-lg-table-cell">余额</th>
                                        <th class="border-0 px-3 py-3 fw-semibold text-muted small d-none d-md-table-cell">对手信息</th>
                                        <th class="border-0 px-3 py-3 fw-semibold text-muted small d-none d-lg-table-cell">摘要</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    ${transactions.map(transaction => `
                                        <tr>
                                            <td class="px-3 py-2">${transaction.date}</td>
                                            <td class="px-3 py-2 d-none d-md-table-cell">
                                                <span class="text-muted small">${transaction.account || '-'}</span>
                                            </td>
                                            <td class="px-3 py-2 text-end">
                                                <span class="transaction-amount negative">¥${transaction.amount.toFixed(2)}</span>
                                            </td>
                                            <td class="px-3 py-2 text-end d-none d-lg-table-cell">
                                                <span class="text-muted small">-</span>
                                            </td>
                                            <td class="px-3 py-2 d-none d-md-table-cell">
                                                <span class="text-muted small">${merchantData.merchant_name}</span>
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
                ` : `
                    <div class="text-center py-5">
                        <div class="text-muted mb-3">
                            <i data-lucide="inbox" style="width: 3rem; height: 3rem; opacity: 0.5;"></i>
                        </div>
                        <h6 class="text-muted">暂无交易记录</h6>
                        <p class="text-muted small mb-3">
                            ${filter_info && filter_info.filtered_month ?
                                `${periodInfo}没有找到该商户的交易记录` :
                                '该商户暂无交易记录'
                            }
                        </p>
                        ${filter_info && filter_info.filtered_month ?
                            '<small class="text-muted">提示：您可以通过点击月度趋势图表切换到其他月份查看数据</small>' :
                            ''
                        }
                    </div>
                `}
            </div>
        `;
    }

    /**
     * 初始化商户模态框交互事件 - 简化版两层展示
     */
    initializeMerchantModalInteractions() {
        // 统计卡片点击直接展开交易记录
        document.querySelectorAll('.stat-card').forEach(card => {
            card.addEventListener('click', () => {
                const transactionsCollapse = document.getElementById('merchantTransactionsCollapse');
                if (transactionsCollapse && !transactionsCollapse.classList.contains('show')) {
                    const bsCollapse = new bootstrap.Collapse(transactionsCollapse);
                    bsCollapse.show();

                    // 更新按钮状态
                    const toggleBtn = document.querySelector('[data-bs-target="#merchantTransactionsCollapse"]');
                    if (toggleBtn) {
                        toggleBtn.setAttribute('aria-expanded', 'true');
                        const icon = toggleBtn.querySelector('i[data-lucide]');
                        if (icon) {
                            icon.setAttribute('data-lucide', 'chevron-up');
                            this.initializeIcons();
                        }
                    }
                }
            });
        });

        // 展开/折叠按钮图标切换
        document.querySelectorAll('.expand-toggle-btn').forEach(btn => {
            btn.addEventListener('click', function() {
                const icon = this.querySelector('i[data-lucide]');
                const target = this.getAttribute('data-bs-target');

                // 切换图标
                setTimeout(() => {
                    if (icon && target) {
                        const targetElement = document.querySelector(target);
                        const isShown = targetElement && targetElement.classList.contains('show');

                        if (target === '#merchantTransactionsCollapse') {
                            const newIcon = isShown ? 'chevron-down' : 'chevron-up';
                            const newText = isShown ? '查看交易记录' : '收起';

                            icon.setAttribute('data-lucide', newIcon);

                            // 更新按钮文本（如果有文本节点）
                            const textNode = Array.from(this.childNodes).find(node => node.nodeType === Node.TEXT_NODE);
                            if (textNode && this.classList.contains('btn-primary')) {
                                // 这是基础层的按钮
                                textNode.textContent = isShown ? '查看交易记录' : '查看交易记录';
                            } else if (textNode) {
                                // 这是交易记录层的收起按钮
                                textNode.textContent = newText;
                            }

                            this.initializeIcons();
                        }
                    }
                }, 150);
            });
        });
    }

    /**
     * 刷新数据
     */
    async refreshData() {
        try {
            // 使用新的组件化架构重新加载当前月份数据
            const currentMonth = this.state.selectedMonth;
            if (currentMonth) {
                await this.dataLoader.loadMonthData(currentMonth);
                this.showToast('数据已刷新', 'success');
            } else {
                // 重新初始化月份选择器
                await this.monthSelector.initialize();
                this.showToast('数据已刷新', 'success');
            }
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

        // 使用CategoryDetails组件的分类筛选功能
        this.categoryDetails.setCategoryFilter(categoryKey);


    }

    /**
     * 按月份筛选（已由MonthSelector组件处理）
     */
    filterByMonth(selectedMonth) {
        console.log('按月份筛选（通过MonthSelector组件）:', selectedMonth);

        // 使用MonthSelector组件的月份选择功能
        this.monthSelector.selectMonth(selectedMonth);
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
        console.log('显示主要内容');
        const mainContent = document.getElementById('main-content');
        const errorState = document.getElementById('error-state');

        if (mainContent) {
            mainContent.style.display = 'block';
            console.log('主要内容已显示');
        } else {
            console.error('主要内容元素不存在');
        }

        if (errorState) {
            errorState.style.display = 'none';
        }
    }

    /**
     * 显示错误状态
     */
    showError(message) {
        document.getElementById('loading-state').style.display = 'none';
        document.getElementById('main-content').style.display = 'none';
        document.getElementById('error-state').style.display = 'block';

        // 更新错误消息 - 适配error_state宏的结构
        const errorTitle = document.querySelector('#error-state .error-title');
        const errorDescription = document.querySelector('#error-state .error-description');

        if (errorTitle) {
            errorTitle.textContent = message;
        }
        if (errorDescription) {
            errorDescription.textContent = "请稍后重试或联系管理员";
        }
    }

    /**
     * 添加数据更新样式
     */
    addDataUpdatingClass() {
        const container = document.getElementById('expense-categories');
        if (container) {
            container.classList.add('data-updating');
        }
    }

    /**
     * 移除数据更新样式
     */
    removeDataUpdatingClass() {
        const container = document.getElementById('expense-categories');
        if (container) {
            container.classList.remove('data-updating');
            // 添加月份切换动画
            container.classList.add('month-transition');
            setTimeout(() => {
                container.classList.remove('month-transition');
            }, 300);
        }
    }

    /**
     * 设置缓存清理
     */
    setupCacheCleanup() {
        // 每5分钟清理一次过期缓存
        setInterval(() => {
            this.state.cleanExpiredCache();
            console.log('缓存清理完成');
        }, 5 * 60 * 1000);

        // 页面隐藏时清理缓存
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                this.state.cleanExpiredCache();
            }
        });
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

// 图标初始化现在使用继承自BasePage的initializeIcons()方法

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    new ExpenseAnalysisPage();
});
