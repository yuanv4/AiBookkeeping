/**
 * 收入分析页面JavaScript
 * 提供收入数据图表初始化和交互功能
 */

/**
 * 从CSS变量获取颜色值
 * @param {string} cssVar CSS变量名（包含--前缀）
 * @returns {string} 颜色值
 */
function getCSSColor(cssVar) {
    try {
        const value = getComputedStyle(document.documentElement).getPropertyValue(cssVar).trim();
        return value || '#000000'; // 默认黑色
    } catch (error) {
        console.warn(`无法获取CSS变量 ${cssVar}:`, error);
        return '#000000';
    }
}

/**
 * 收入分析模块
 */
const IncomeAnalysis = {
    // 数据存储
    data: {
        monthlyTrends: [],
        incomeSources: [],
        totalIncome: 0,
        avgMonthlyIncome: 0,
        growthRate: 0,
        transactionCount: 0
    },
    
    // 图表实例
    charts: {
        monthlyTrend: null,
        incomeSource: null
    },
    
    // 缓存配置
    cache: {
        enabled: true,
        key: 'income_analysis_data',
        expiry: 30 * 60 * 1000 // 30分钟
    },
    
    /**
     * 初始化收入分析模块
     * @param {Object} incomeData 收入数据
     */
    init: function(incomeData) {
        console.log('初始化收入分析模块', incomeData);
        
        // 存储数据
        this.data = { ...this.data, ...incomeData };
        
        // 缓存数据
        this.cacheData(incomeData);
        
        // 初始化图表
        this.initializeCharts();
        
        // 初始化交互功能
        this.initializeInteractions();
        
        console.log('收入分析模块初始化完成');
    },
    
    /**
     * 初始化所有图表
     */
    initializeCharts: function() {
        try {
            this.initMonthlyTrendChart();
            this.initIncomeSourceChart();
        } catch (error) {
            console.error('图表初始化失败:', error);
        }
    },
    
    /**
     * 初始化月度收入趋势图
     */
    initMonthlyTrendChart: function() {
        const canvas = document.getElementById('incomeMonthlyTrendChart');
        if (!canvas) {
            console.warn('月度趋势图画布未找到');
            return;
        }
        
        const ctx = canvas.getContext('2d');
        
        // 准备数据
        const labels = this.data.monthlyTrends.map(trend => trend.month || '未知');
        const amounts = this.data.monthlyTrends.map(trend => trend.amount || 0);
        
        // 创建渐变色
        const gradient = ctx.createLinearGradient(0, 0, 0, 400);
        gradient.addColorStop(0, 'rgba(40, 167, 69, 0.3)');
        gradient.addColorStop(1, 'rgba(40, 167, 69, 0.05)');
        
        this.charts.monthlyTrend = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: '月度收入',
                    data: amounts,
                    borderColor: getCSSColor('--success'),
                    backgroundColor: gradient,
                    borderWidth: 3,
                    fill: true,
                    tension: 0.4,
                    pointBackgroundColor: getCSSColor('--success'),
                    pointBorderColor: '#ffffff',
                    pointBorderWidth: 2,
                    pointRadius: 6,
                    pointHoverRadius: 8
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        titleColor: '#ffffff',
                        bodyColor: '#ffffff',
                        borderColor: getCSSColor('--success'),
                        borderWidth: 1,
                        callbacks: {
                            label: function(context) {
                                return `收入: ¥${context.parsed.y.toFixed(2)}`;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        grid: {
                            display: false
                        },
                        ticks: {
                            color: getCSSColor('--text-muted')
                        }
                    },
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: 'rgba(0, 0, 0, 0.1)'
                        },
                        ticks: {
                            color: getCSSColor('--text-muted'),
                            callback: function(value) {
                                return '¥' + value.toFixed(0);
                            }
                        }
                    }
                },
                interaction: {
                    intersect: false,
                    mode: 'index'
                }
            }
        });
    },
    
    /**
     * 初始化收入来源分析图
     */
    initIncomeSourceChart: function() {
        const canvas = document.getElementById('incomeSourceChart');
        if (!canvas) {
            console.warn('收入来源图画布未找到');
            return;
        }
        
        const ctx = canvas.getContext('2d');
        
        // 准备数据
        const sources = this.data.incomeSources || [];
        const labels = sources.map(source => source.source || '未分类');
        const amounts = sources.map(source => source.amount || 0);
        
        // 颜色配置
        const colors = [
            getCSSColor('--primary'),
            getCSSColor('--success'),
            getCSSColor('--info'),
            getCSSColor('--warning'),
            getCSSColor('--danger'),
            '#6f42c1', '#fd7e14', '#20c997'
        ];
        
        this.charts.incomeSource = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: labels,
                datasets: [{
                    data: amounts,
                    backgroundColor: colors.slice(0, labels.length),
                    borderColor: '#ffffff',
                    borderWidth: 2,
                    hoverBorderWidth: 3
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            padding: 20,
                            usePointStyle: true,
                            color: getCSSColor('--text-muted')
                        }
                    },
                    tooltip: {
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        titleColor: '#ffffff',
                        bodyColor: '#ffffff',
                        callbacks: {
                            label: function(context) {
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = ((context.parsed / total) * 100).toFixed(1);
                                return `${context.label}: ¥${context.parsed.toFixed(2)} (${percentage}%)`;
                            }
                        }
                    }
                },
                cutout: '60%'
            }
        });
    },
    
    /**
     * 初始化交互功能
     */
    initializeInteractions: function() {
        // 图表联动效果
        this.setupChartInteractions();
        
        // 数据刷新功能
        this.setupDataRefresh();
        
        // 响应式处理
        this.setupResponsiveHandling();
    },
    
    /**
     * 设置图表交互
     */
    setupChartInteractions: function() {
        // 月度趋势图点击事件
        if (this.charts.monthlyTrend) {
            this.charts.monthlyTrend.options.onClick = (event, elements) => {
                if (elements.length > 0) {
                    const index = elements[0].index;
                    const monthData = this.data.monthlyTrends[index];
                    console.log('点击月度数据:', monthData);
                    // 可以在这里添加详细信息显示逻辑
                }
            };
        }
        
        // 收入来源图点击事件
        if (this.charts.incomeSource) {
            this.charts.incomeSource.options.onClick = (event, elements) => {
                if (elements.length > 0) {
                    const index = elements[0].index;
                    const sourceData = this.data.incomeSources[index];
                    console.log('点击收入来源:', sourceData);
                    // 可以在这里添加来源详情显示逻辑
                }
            };
        }
    },
    
    /**
     * 设置数据刷新功能
     */
    setupDataRefresh: function() {
        // 可以添加定时刷新或手动刷新按钮
        console.log('数据刷新功能已设置');
    },
    
    /**
     * 设置响应式处理
     */
    setupResponsiveHandling: function() {
        window.addEventListener('resize', () => {
            // 延迟执行以避免频繁调用
            setTimeout(() => {
                if (this.charts.monthlyTrend) {
                    this.charts.monthlyTrend.resize();
                }
                if (this.charts.incomeSource) {
                    this.charts.incomeSource.resize();
                }
            }, 100);
        });
    },
    
    /**
     * 缓存数据
     * @param {Object} data 要缓存的数据
     */
    cacheData: function(data) {
        if (!this.cache.enabled) return;
        
        try {
            const cacheItem = {
                data: data,
                timestamp: Date.now()
            };
            localStorage.setItem(this.cache.key, JSON.stringify(cacheItem));
        } catch (error) {
            console.warn('数据缓存失败:', error);
        }
    },
    
    /**
     * 获取缓存数据
     * @returns {Object|null} 缓存的数据或null
     */
    getCachedData: function() {
        if (!this.cache.enabled) return null;
        
        try {
            const cached = localStorage.getItem(this.cache.key);
            if (!cached) return null;
            
            const cacheItem = JSON.parse(cached);
            const isExpired = Date.now() - cacheItem.timestamp > this.cache.expiry;
            
            if (isExpired) {
                localStorage.removeItem(this.cache.key);
                return null;
            }
            
            return cacheItem.data;
        } catch (error) {
            console.warn('获取缓存数据失败:', error);
            return null;
        }
    },
    
    /**
     * 销毁图表实例
     */
    destroy: function() {
        if (this.charts.monthlyTrend) {
            this.charts.monthlyTrend.destroy();
            this.charts.monthlyTrend = null;
        }
        if (this.charts.incomeSource) {
            this.charts.incomeSource.destroy();
            this.charts.incomeSource = null;
        }
        console.log('收入分析模块已销毁');
    }
};

/**
 * 从HTML元素的data属性获取后端数据
 * @returns {Object|null} 收入数据对象或null
 */
function getIncomeDataFromHTML() {
    try {
        const dataElement = document.getElementById('income-data');
        if (!dataElement) {
            console.warn('未找到收入数据元素');
            return null;
        }
        
        const monthlyTrends = dataElement.dataset.monthlyTrends;
        const incomeSources = dataElement.dataset.incomeSources;
        const totalIncome = dataElement.dataset.totalIncome;
        const avgMonthlyIncome = dataElement.dataset.avgMonthlyIncome;
        const growthRate = dataElement.dataset.growthRate;
        const transactionCount = dataElement.dataset.transactionCount;
        
        return {
            monthlyTrends: monthlyTrends ? JSON.parse(monthlyTrends) : [],
            incomeSources: incomeSources ? JSON.parse(incomeSources) : [],
            totalIncome: parseFloat(totalIncome) || 0,
            avgMonthlyIncome: parseFloat(avgMonthlyIncome) || 0,
            growthRate: parseFloat(growthRate) || 0,
            transactionCount: parseInt(transactionCount) || 0
        };
    } catch (error) {
        console.error('解析收入数据失败:', error);
        return null;
    }
}

/**
 * 自动初始化收入分析模块
 */
function autoInitializeIncomeAnalysis() {
    // 检查是否在收入分析页面
    const incomeChartElements = document.querySelectorAll('#incomeMonthlyTrendChart, #incomeSourceChart');
    if (incomeChartElements.length === 0) {
        return; // 不在收入分析页面，不执行初始化
    }
    
    // 检查IncomeAnalysis模块是否可用
    if (typeof IncomeAnalysis === 'undefined') {
        console.error('IncomeAnalysis模块未定义');
        return;
    }
    
    // 获取数据
    const incomeData = getIncomeDataFromHTML();
    if (!incomeData) {
        console.error('无法获取收入数据，尝试使用空数据初始化');
        // 使用默认空数据初始化
        IncomeAnalysis.init({
            monthlyTrends: [],
            incomeSources: [],
            totalIncome: 0,
            avgMonthlyIncome: 0,
            growthRate: 0,
            transactionCount: 0
        });
        return;
    }
    
    // 初始化模块
    console.log('自动初始化收入分析模块', incomeData);
    IncomeAnalysis.init(incomeData);
}

// 自动初始化逻辑
document.addEventListener('DOMContentLoaded', function() {
    autoInitializeIncomeAnalysis();
});

// 页面卸载时清理资源
window.addEventListener('beforeunload', function() {
    if (typeof IncomeAnalysis !== 'undefined') {
        IncomeAnalysis.destroy();
    }
});