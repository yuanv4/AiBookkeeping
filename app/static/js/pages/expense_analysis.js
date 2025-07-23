/**
 * 支出分类分析页面 - 简化版本
 * 将原有的5个类合并为1个类，减少复杂度
 */

import BasePage from '../common/BasePage.js';
import { getProjectColors, getChartStyles, ChartRegistry } from '../common/utils.js';
import { formatCurrency } from '../common/formatters.js';
import { showNotification } from '../common/notifications.js';
import { apiService } from '../common/api-helpers.js';

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
        this.categoriesConfig = {};

        this.init();
    }

    async init() {
        try {
            console.log('支出分析页面初始化');
            window.expenseAnalysisPage = this;

            // 加载分类配置
            this.loadCategoriesConfig();

            await this.loadAvailableMonths();
            await this.loadInitialData();

        } catch (error) {
            console.error('页面初始化失败:', error);
        }
    }

    loadCategoriesConfig() {
        try {
            const pageDataElement = document.getElementById('page-data');
            if (pageDataElement) {
                const initialData = JSON.parse(pageDataElement.dataset.initialData);
                this.categoriesConfig = initialData.categories_config || {};
                console.log('加载分类配置:', this.categoriesConfig);
            }
        } catch (error) {
            console.error('加载分类配置失败:', error);
            this.categoriesConfig = {};
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

        const container = document.getElementById('monthly-trend-chart');
        if (!container) return;

        // 销毁现有图表
        if (this.chart) {
            ChartRegistry.destroy('monthly-trend-chart');
            this.chart = null;
        }

        // 构建图表数据
        const chartData = this.buildEChartsData();

        // 直接创建ECharts实例
        const chart = window.echarts.init(container);

        // 获取项目配置
        const colors = getProjectColors();
        const styles = getChartStyles();

        // 配置选项
        const option = {
            tooltip: {
                ...styles.tooltip,
                trigger: 'axis',
                axisPointer: { type: 'shadow' },
                formatter: (params) => {
                    if (params && params.length > 0) {
                        let result = `${params[0].name}<br/>`;
                        let total = 0;
                        params.forEach(param => {
                            total += param.value;
                            result += `${param.marker}${param.seriesName}: ${formatCurrency(param.value)}<br/>`;
                        });
                        result += `<strong>总计: ${formatCurrency(total)}</strong>`;
                        return result;
                    }
                    return '';
                }
            },
            legend: {
                show: true,
                top: 'top',
                textStyle: { color: colors.bodyColor }
            },
            grid: styles.grid,
            xAxis: {
                type: 'category',
                data: chartData.labels,
                ...styles.axisStyle
            },
            yAxis: {
                type: 'value',
                ...styles.axisStyle,
                axisLabel: {
                    ...styles.axisStyle.axisLabel,
                    formatter: (value) => formatCurrency(value, true)
                }
            },
            series: chartData.series
        };

        // 设置配置
        chart.setOption(option);

        // 注册到管理器
        ChartRegistry.register('monthly-trend-chart', chart);

        // 添加点击事件
        chart.on('click', (params) => {
            if (params.componentType === 'series') {
                const clickedMonth = params.name;
                this.selectMonth(clickedMonth);
            }
        });

        // 保存引用
        this.chart = chart;
    }

    buildSeriesFromConfig(labels, monthlyDataMap, colors) {
        const series = [];
        const colorKeys = ['primary', 'success', 'info', 'warning', 'danger', 'secondary'];
        let colorIndex = 0;

        // 如果有分类配置，使用配置构建系列
        if (this.categoriesConfig && Object.keys(this.categoriesConfig).length > 0) {
            for (const [categoryCode, categoryInfo] of Object.entries(this.categoriesConfig)) {
                const colorKey = colorKeys[colorIndex % colorKeys.length];
                const isLast = colorIndex === Object.keys(this.categoriesConfig).length - 1;

                series.push({
                    name: categoryInfo.name,
                    type: 'bar',
                    stack: 'expenses',
                    data: labels.map(month => monthlyDataMap[month]?.[categoryCode] || 0),
                    itemStyle: {
                        color: colors[colorKey] + 'CC', // 80% 透明度
                        borderRadius: isLast ? [2, 2, 0, 0] : [0, 0, 0, 0] // 最后一个系列顶部圆角
                    },
                    emphasis: {
                        itemStyle: { color: colors[colorKey] }
                    }
                });

                colorIndex++;
            }
        } else {
            // 如果没有配置，显示空数据
            console.warn('没有分类配置，无法构建图表系列');
        }

        return series;
    }

    buildEChartsData() {
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

        // 获取项目颜色配置
        const colors = getProjectColors();

        // 构建ECharts系列数据 - 使用配置驱动
        const series = this.buildSeriesFromConfig(labels, monthlyDataMap, colors);

        return {
            labels: labels,
            series: series
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
                                    <button class="btn btn-sm btn-outline-primary" onclick="window.expenseAnalysisPage.navigateToMerchantTransactions('${merchant.name}')" title="查看交易">
                                        <i data-lucide="external-link" style="width: 0.75rem; height: 0.75rem;"></i>
                                        <span class="d-none d-sm-inline ms-1 small">查看交易</span>
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

    // 跳转到商户交易列表
    navigateToMerchantTransactions(merchantName) {
        try {
            // 构建跳转URL
            const baseUrl = '/transactions/';
            const params = new URLSearchParams();

            // 添加商户筛选参数
            params.append('counterparty', merchantName);

            // 添加月份筛选参数
            if (this.selectedMonth) {
                const { startDate, endDate } = this.convertMonthToDateRange(this.selectedMonth);
                params.append('start_date', startDate);
                params.append('end_date', endDate);
            }

            // 构建完整URL并跳转
            const fullUrl = `${baseUrl}?${params.toString()}`;
            window.location.href = fullUrl;

        } catch (error) {
            console.error('跳转到商户交易列表失败:', error);
        }
    }

    // 将月份转换为日期范围
    convertMonthToDateRange(monthStr) {
        try {
            // monthStr 格式: "YYYY-MM"
            const [year, month] = monthStr.split('-');
            const yearNum = parseInt(year);
            const monthNum = parseInt(month);

            // 计算月份的第一天
            const startDate = `${year}-${month.padStart(2, '0')}-01`;

            // 计算月份的最后一天
            const lastDay = new Date(yearNum, monthNum, 0).getDate();
            const endDate = `${year}-${month.padStart(2, '0')}-${lastDay.toString().padStart(2, '0')}`;

            return { startDate, endDate };

        } catch (error) {
            console.error('月份转换失败:', error);
            // 返回默认值
            const now = new Date();
            const year = now.getFullYear();
            const month = (now.getMonth() + 1).toString().padStart(2, '0');
            const lastDay = new Date(year, now.getMonth() + 1, 0).getDate();

            return {
                startDate: `${year}-${month}-01`,
                endDate: `${year}-${month}-${lastDay.toString().padStart(2, '0')}`
            };
        }
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
