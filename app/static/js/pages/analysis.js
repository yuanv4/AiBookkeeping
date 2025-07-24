/**
 * 财务分析页面 - 合并仪表盘和支出分析功能
 * 
 * 提供现金流健康监控与支出分类分析的统一界面
 */

import BasePage from '../common/BasePage.js';
import { getChartStyles, ChartRegistry, getCSSColorValue } from '../common/utils.js';
import { getCSSColor } from '../common/dom-utils.js';
import { formatCurrency } from '../common/formatters.js';
import { showNotification } from '../common/notifications.js';
import { apiService } from '../common/api-helpers.js';

export default class AnalysisPage extends BasePage {
    constructor() {
        super();

        // 仪表盘相关状态
        this.dashboardData = {};
        this.charts = {};

        // 支出分析相关状态  
        this.selectedMonth = null;
        this.availableMonths = [];
        this.categoryData = {};
        this.categoriesConfig = {};
        this.expandedCategories = new Set();
        this.loading = false;

        this.init();
    }

    async init() {
        try {
            console.log('财务分析页面初始化');
            window.analysisPage = this;

            // 加载初始数据
            this.loadInitialData();

            // 初始化图表
            this.initializeCharts();

            // 更新仪表盘数据（确保图表有数据）
            this.updateDashboard(this.dashboardData);

            // 加载支出分析数据
            await this.loadExpenseAnalysisData();

        } catch (error) {
            console.error('页面初始化失败:', error);
            this.showErrorState('页面初始化失败');
        }
    }

    loadInitialData() {
        try {
            const dataContainer = document.getElementById('analysis-data');
            if (dataContainer) {
                // 加载仪表盘数据
                this.dashboardData = JSON.parse(dataContainer.dataset.dashboardData);
                
                // 加载分类配置
                this.categoriesConfig = JSON.parse(dataContainer.dataset.categoriesConfig);
                
                console.log('加载初始数据:', {
                    dashboard: this.dashboardData,
                    categories: this.categoriesConfig
                });
                
                // 更新仪表盘显示
                this.updateDashboard(this.dashboardData);
            }
        } catch (error) {
            console.error('加载初始数据失败:', error);
            this.categoriesConfig = {};
            this.dashboardData = {};
        }
    }

    initializeCharts() {
        // 初始化净现金趋势图 (来自仪表盘)
        this.initializeNetWorthChart();
        
        // 初始化月度支出趋势图 (来自支出分析)
        this.initializeMonthlyTrendChart();
    }

    initializeNetWorthChart() {
        const container = document.getElementById('netWorthChart');
        if (!container) {
            console.warn('找不到图表容器 #netWorthChart');
            return;
        }

        // 初始化ECharts实例
        const chart = window.echarts.init(container);

        // 获取项目配置
        const styles = getChartStyles();
        const primaryColor = getCSSColorValue('primary');

        // 配置选项
        const option = {
            tooltip: {
                trigger: 'axis',
                formatter: function(params) {
                    const data = params[0];
                    return `${data.name}<br/>净现金: ¥${data.value.toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
                }
            },
            grid: {
                left: '3%',
                right: '4%',
                bottom: '3%',
                containLabel: true
            },
            xAxis: {
                type: 'category',
                boundaryGap: false,
                data: [],
                axisLine: {
                    lineStyle: {
                        color: styles.axisColor
                    }
                },
                axisLabel: {
                    color: styles.textColor
                }
            },
            yAxis: {
                type: 'value',
                axisLine: {
                    lineStyle: {
                        color: styles.axisColor
                    }
                },
                axisLabel: {
                    color: styles.textColor,
                    formatter: function(value) {
                        return '¥' + value.toLocaleString('zh-CN');
                    }
                },
                splitLine: {
                    lineStyle: {
                        color: styles.gridColor
                    }
                }
            },
            series: [{
                name: '净现金',
                type: 'line',
                smooth: true,
                symbol: 'circle',
                symbolSize: 6,
                lineStyle: {
                    color: primaryColor,
                    width: 3
                },
                itemStyle: {
                    color: primaryColor
                },
                areaStyle: {
                    color: {
                        type: 'linear',
                        x: 0, y: 0, x2: 0, y2: 1,
                        colorStops: [
                            { offset: 0, color: primaryColor + '40' },
                            { offset: 1, color: primaryColor + '10' }
                        ]
                    }
                },
                data: []
            }]
        };

        // 设置配置
        chart.setOption(option);

        // 注册到管理器
        ChartRegistry.register('netWorthChart', chart);

        // 保存引用
        this.charts.netWorth = chart;
    }

    initializeMonthlyTrendChart() {
        const container = document.getElementById('monthly-trend-chart');
        if (!container) {
            console.warn('找不到图表容器 #monthly-trend-chart');
            return;
        }

        // 初始化ECharts实例
        const chart = window.echarts.init(container);

        // 获取项目配置
        const styles = getChartStyles();

        // 配置选项
        const option = {
            tooltip: {
                trigger: 'axis',
                formatter: function(params) {
                    let result = `${params[0].name}<br/>`;
                    params.forEach(param => {
                        result += `${param.seriesName}: ¥${Math.abs(param.value).toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}<br/>`;
                    });
                    return result;
                }
            },
            legend: {
                data: [],
                textStyle: {
                    color: styles.textColor
                }
            },
            grid: {
                left: '3%',
                right: '4%',
                bottom: '3%',
                containLabel: true
            },
            xAxis: {
                type: 'category',
                data: [],
                axisLine: {
                    lineStyle: {
                        color: styles.axisColor
                    }
                },
                axisLabel: {
                    color: styles.textColor
                }
            },
            yAxis: {
                type: 'value',
                axisLine: {
                    lineStyle: {
                        color: styles.axisColor
                    }
                },
                axisLabel: {
                    color: styles.textColor,
                    formatter: function(value) {
                        return '¥' + Math.abs(value).toLocaleString('zh-CN');
                    }
                },
                splitLine: {
                    lineStyle: {
                        color: styles.gridColor
                    }
                }
            },
            series: []
        };

        // 设置配置
        chart.setOption(option);

        // 注册到管理器
        ChartRegistry.register('monthlyTrendChart', chart);

        // 保存引用
        this.charts.monthlyTrend = chart;
    }

    updateDashboard(data) {
        if (!data) return;
        this.updateCoreMetrics(data.core_metrics);
        this.updateNetWorthChart(data.net_worth_trend);
    }

    updateCoreMetrics(metrics) {
        if (!metrics) return;
        
        const currentAssetsEl = document.getElementById('currentAssets');
        const netIncomeEl = document.getElementById('netIncome');
        const emergencyReserveEl = document.getElementById('emergencyReserveMonths');
        
        if (currentAssetsEl) {
            currentAssetsEl.textContent = `¥${metrics.current_total_assets.toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
        }
        
        if (netIncomeEl) {
            netIncomeEl.textContent = `¥${metrics.net_income.toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
        }
        
        if (emergencyReserveEl) {
            this.updateEmergencyReserveMonths(metrics.emergency_reserve_months);
        }
    }

    updateEmergencyReserveMonths(months) {
        const element = document.getElementById('emergencyReserveMonths');
        if (!element) return;
        
        if (months < 0) {
            element.textContent = '无限';
        } else {
            element.textContent = `${months.toFixed(1)}个月`;
        }
    }

    updateNetWorthChart(trendData) {
        if (!trendData || !this.charts.netWorth) return;

        try {
            const labels = trendData.map(d => d.date);
            const data = trendData.map(d => d.value);

            // 直接使用ECharts API更新数据
            this.charts.netWorth.setOption({
                xAxis: { data: labels },
                series: [{ data: data }]
            });
        } catch (error) {
            console.error('更新净现金趋势图失败:', error);
        }
    }

    // 支出分析相关方法
    async loadExpenseAnalysisData() {
        try {
            await this.loadAvailableMonths();
            await this.loadInitialExpenseData();
        } catch (error) {
            console.error('加载支出分析数据失败:', error);
        }
    }

    async loadAvailableMonths() {
        try {
            const response = await fetch('/analysis/api/available-months');
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

    async loadInitialExpenseData() {
        if (!this.selectedMonth) return;

        await this.loadMonthData(this.selectedMonth);
        this.renderMonthlyTrendChart();
        this.renderCategories();
    }

    async loadMonthData(month) {
        try {
            this.setLoading(true);

            const response = await fetch(`/analysis/api/merchant-analysis?month=${month}`);
            const result = await response.json();

            if (result.success) {
                this.categoryData = result.data;
                console.log('加载月度数据成功:', this.categoryData);
            } else {
                throw new Error(result.error || '获取月度数据失败');
            }
        } catch (error) {
            console.error('加载月度数据失败:', error);
            this.showErrorState('数据加载失败');
        } finally {
            this.setLoading(false);
        }
    }

    setLoading(loading) {
        this.loading = loading;
        const overlay = document.getElementById('loadingOverlay');
        if (overlay) {
            overlay.style.display = loading ? 'flex' : 'none';
        }
    }

    showErrorState(message) {
        const errorState = document.getElementById('error-state');
        const errorMessage = document.getElementById('error-message');
        const mainContent = document.getElementById('main-content');
        
        if (errorState && errorMessage) {
            errorMessage.textContent = message;
            errorState.style.display = 'block';
        }
        
        if (mainContent) {
            mainContent.style.display = 'none';
        }
    }

    renderMonthlyTrendChart() {
        // 实现月度趋势图渲染逻辑
        if (!this.categoryData.categories || !this.charts.monthlyTrend) return;

        try {
            // 从分类数据中提取月度数据
            const categories = Object.keys(this.categoryData.categories);
            if (categories.length === 0) return;

            // 获取所有月份（从第一个分类的月度数据中）
            const firstCategory = this.categoryData.categories[categories[0]];
            if (!firstCategory.monthly_data) return;

            const months = Object.keys(firstCategory.monthly_data).sort();

            // 准备图表数据
            const series = categories.map(categoryCode => {
                const categoryData = this.categoryData.categories[categoryCode];
                const categoryInfo = this.categoriesConfig[categoryCode] || { name: categoryCode };

                return {
                    name: categoryInfo.name,
                    type: 'line',
                    smooth: true,
                    data: months.map(month => Math.abs(categoryData.monthly_data[month] || 0))
                };
            });

            // 更新图表
            this.charts.monthlyTrend.setOption({
                xAxis: { data: months },
                legend: { data: categories.map(code => (this.categoriesConfig[code] || {name: code}).name) },
                series: series
            });
        } catch (error) {
            console.error('渲染月度趋势图失败:', error);
        }
    }

    renderCategories() {
        // 实现分类详情渲染逻辑
        const container = document.getElementById('expense-categories');
        if (!container || !this.categoryData.categories) return;

        try {
            container.innerHTML = '';
            
            Object.entries(this.categoryData.categories).forEach(([categoryCode, categoryData]) => {
                const categoryInfo = this.categoriesConfig[categoryCode] || { name: categoryCode, icon: 'more-horizontal', color: 'secondary' };
                
                const categoryCard = this.createCategoryCard(categoryCode, categoryInfo, categoryData);
                container.appendChild(categoryCard);
            });
        } catch (error) {
            console.error('渲染分类详情失败:', error);
        }
    }

    createCategoryCard(categoryCode, categoryInfo, categoryData) {
        // 创建分类卡片的DOM元素
        const card = document.createElement('div');
        card.className = 'card mb-3 category-card';
        card.dataset.category = categoryCode;

        // 卡片头部
        card.innerHTML = `
            <div class="card-body">
                <div class="d-flex justify-content-between align-items-center">
                    <div class="d-flex align-items-center">
                        <div class="me-3 bg-${categoryInfo.color} bg-opacity-10 rounded-3 d-flex align-items-center justify-content-center" style="width: 2.5rem; height: 2.5rem;">
                            <i data-lucide="${categoryInfo.icon}" class="text-${categoryInfo.color}"></i>
                        </div>
                        <div>
                            <h6 class="mb-1">${categoryInfo.name}</h6>
                            <small class="text-muted">${Object.keys(categoryData.merchants || {}).length} 个商户</small>
                        </div>
                    </div>
                    <div class="text-end">
                        <div class="fs-5 fw-bold text-danger">¥${Math.abs(categoryData.total_amount).toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</div>
                        <small class="text-muted">${(categoryData.percentage || 0).toFixed(1)}%</small>
                    </div>
                </div>
            </div>
        `;

        // 添加商户详情区域（默认隐藏）
        const detailsContainer = document.createElement('div');
        detailsContainer.className = 'category-details collapse';
        detailsContainer.id = `category-details-${categoryCode}`;

        // 创建商户列表
        if (categoryData.merchants && Object.keys(categoryData.merchants).length > 0) {
            const merchantsTable = document.createElement('table');
            merchantsTable.className = 'table table-sm table-hover mb-0';

            // 表头
            merchantsTable.innerHTML = `
                <thead>
                    <tr>
                        <th>商户名称</th>
                        <th class="text-end">交易次数</th>
                        <th class="text-end">支出金额</th>
                        <th class="text-end">占比</th>
                    </tr>
                </thead>
                <tbody></tbody>
            `;

            // 添加商户行
            const tbody = merchantsTable.querySelector('tbody');
            Object.entries(categoryData.merchants).forEach(([merchantName, merchantData]) => {
                // 计算商户在该分类中的占比
                const merchantPercentage = categoryData.total_amount > 0
                    ? (Math.abs(merchantData.total_amount) / Math.abs(categoryData.total_amount)) * 100
                    : 0;

                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${merchantName}</td>
                    <td class="text-end">${merchantData.transaction_count}次</td>
                    <td class="text-end merchant-amount">¥${Math.abs(merchantData.total_amount).toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</td>
                    <td class="text-end">${merchantPercentage.toFixed(1)}%</td>
                `;
                tbody.appendChild(row);
            });

            detailsContainer.appendChild(merchantsTable);
        } else {
            detailsContainer.innerHTML = '<div class="p-3 text-center text-muted">暂无商户数据</div>';
        }

        card.appendChild(detailsContainer);

        // 添加点击事件
        card.addEventListener('click', () => {
            // 切换详情区域的显示/隐藏
            const details = card.querySelector('.category-details');
            if (details) {
                details.classList.toggle('show');
            }
        });

        // 重新初始化图标
        if (typeof lucide !== 'undefined' && lucide.createIcons) {
            lucide.createIcons();
        }

        return card;
    }
}

// 初始化页面
document.addEventListener('DOMContentLoaded', () => {
    const page = new AnalysisPage();
});
