/**
 * 仪表盘页面的JavaScript逻辑
 * 仅负责初次加载时的账户余额展示和趋势图表渲染
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
 * 仪表盘模块
 */
const Dashboard = {
    // 数据存储
    data: {
        balance: 0,
        monthlyTrends: [],
        lastUpdated: null
    },
    
    // 图表实例
    charts: {
        balanceTrend: null
    },
    
    /**
     * 初始化仪表盘模块
     * @param {Object} dashboardData 仪表盘数据
     */
    init: function(dashboardData) {
        console.log('初始化仪表盘模块', dashboardData);
        // 存储数据
        this.data = { ...this.data, ...dashboardData };
        // 初始化图表
        this.initializeCharts();
        // 初始化交互功能
        this.initializeInteractions();
        console.log('仪表盘模块初始化完成');
    },
    
    /**
     * 初始化图表
     */
    initializeCharts: function() {
        try {
            this.initBalanceTrendChart();
        } catch (error) {
            console.error('图表初始化失败:', error);
        }
    },
    
    /**
     * 初始化余额趋势图
     */
    initBalanceTrendChart: function() {
        const canvas = document.getElementById('balanceTrendChart');
        if (!canvas) {
            console.warn('余额趋势图画布未找到');
            return;
        }
        const ctx = canvas.getContext('2d');
        // 准备数据
        const labels = this.data.monthlyTrends.map(trend => trend.month);
        const amounts = this.data.monthlyTrends.map(trend => trend.balance);
        // 创建渐变色
        const gradient = ctx.createLinearGradient(0, 0, 0, 400);
        gradient.addColorStop(0, 'rgba(0, 123, 255, 0.3)');
        gradient.addColorStop(1, 'rgba(0, 123, 255, 0.05)');
        this.charts.balanceTrend = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: '账户余额',
                    data: amounts,
                    borderColor: getCSSColor('--primary-500'),
                    backgroundColor: gradient,
                    borderWidth: 3,
                    fill: true,
                    tension: 0.4,
                    pointBackgroundColor: getCSSColor('--primary-500'),
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
                        borderColor: getCSSColor('--primary-500'),
                        borderWidth: 1,
                        callbacks: {
                            label: function(context) {
                                return `余额: ¥${context.parsed.y.toFixed(2)}`;
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: false,
                        grid: {
                            color: 'rgba(0, 0, 0, 0.05)'
                        },
                        ticks: {
                            callback: function(value) {
                                return '¥' + value.toLocaleString();
                            }
                        }
                    },
                    x: {
                        grid: {
                            display: false
                        }
                    }
                }
            }
        });
    },
    
    /**
     * 初始化交互功能（仅响应式处理）
     */
    initializeInteractions: function() {
        // 响应式处理
        window.addEventListener('resize', () => {
            if (this.charts.balanceTrend) {
                this.charts.balanceTrend.resize();
            }
        });
    },
    
    /**
     * 销毁图表实例
     */
    destroy: function() {
        if (this.charts.balanceTrend) {
            this.charts.balanceTrend.destroy();
            this.charts.balanceTrend = null;
        }
        console.log('仪表盘模块已销毁');
    }
};

/**
 * 从HTML元素的data属性获取后端数据
 * @returns {Object|null} 仪表盘数据对象或null
 */
function getDashboardDataFromHTML() {
    try {
        const dataElement = document.getElementById('dashboard-data');
        if (!dataElement) {
            console.warn('未找到仪表盘数据元素');
            return null;
        }
        const balance = dataElement.dataset.balance;
        const monthlyTrends = dataElement.dataset.monthlyTrends;
        const lastUpdated = dataElement.dataset.lastUpdated;
        return {
            balance: parseFloat(balance) || 0,
            monthlyTrends: monthlyTrends ? JSON.parse(monthlyTrends) : [],
            lastUpdated: lastUpdated || null
        };
    } catch (error) {
        console.error('解析仪表盘数据失败:', error);
        return null;
    }
}

/**
 * 自动初始化仪表盘模块
 */
function autoInitializeDashboard() {
    // 检查是否在仪表盘页面
    const dashboardChartElement = document.getElementById('balanceTrendChart');
    if (!dashboardChartElement) {
        return; // 不在仪表盘页面，不执行初始化
    }
    // 检查Dashboard模块是否可用
    if (typeof Dashboard === 'undefined') {
        console.error('Dashboard模块未定义');
        return;
    }
    // 获取数据
    const dashboardData = getDashboardDataFromHTML();
    if (!dashboardData) {
        console.error('无法获取仪表盘数据，尝试使用空数据初始化');
        // 使用默认空数据初始化
        Dashboard.init({
            balance: 0,
            monthlyTrends: [],
            lastUpdated: null
        });
        return;
    }
    // 初始化模块
    console.log('自动初始化仪表盘模块', dashboardData);
    Dashboard.init(dashboardData);
}

// 自动初始化逻辑
document.addEventListener('DOMContentLoaded', function() {
    autoInitializeDashboard();
});

// 页面卸载时清理资源
window.addEventListener('beforeunload', function() {
    if (typeof Dashboard !== 'undefined') {
        Dashboard.destroy();
    }
}); 