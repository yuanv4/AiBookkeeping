/**
 * 仪表盘页面的JavaScript逻辑
 * 负责余额趋势图表渲染
 */

// 图表配置常量
const CHART_CONFIG = {
    type: 'line',
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
        legend: { display: false },
        tooltip: {
            backgroundColor: 'rgba(0, 0, 0, 0.8)',
            titleColor: '#ffffff',
            bodyColor: '#ffffff',
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
            grid: { color: 'rgba(0, 0, 0, 0.05)' },
            ticks: {
                callback: function(value) {
                    return '¥' + value.toLocaleString();
                }
            }
        },
        x: {
            grid: { display: false }
        }
    }
};

// 颜色配置
const COLORS = {
    primary: '--primary-500',
    gradient: {
        start: 'rgba(0, 123, 255, 0.3)',
        end: 'rgba(0, 123, 255, 0.05)'
    },
    white: '#ffffff'
};

// 尺寸配置
const DIMENSIONS = {
    maxHeight: 280,
    borderWidth: 3,
    pointRadius: 6,
    pointHoverRadius: 8,
    pointBorderWidth: 2
};

/**
 * 从CSS变量获取颜色值
 */
function getCSSColor(cssVar) {
    try {
        const value = getComputedStyle(document.documentElement).getPropertyValue(cssVar).trim();
        return value || '#000000';
    } catch (error) {
        console.warn(`无法获取CSS变量 ${cssVar}:`, error);
        return '#000000';
    }
}

/**
 * 设置Canvas尺寸
 */
function setupCanvas(canvas) {
    const container = canvas.parentElement;
    if (container) {
        const rect = container.getBoundingClientRect();
        canvas.width = rect.width;
        canvas.height = Math.min(rect.height, DIMENSIONS.maxHeight);
    }
}

/**
 * 创建渐变色
 */
function createGradient(ctx) {
    const gradient = ctx.createLinearGradient(0, 0, 0, 400);
    gradient.addColorStop(0, COLORS.gradient.start);
    gradient.addColorStop(1, COLORS.gradient.end);
    return gradient;
}

/**
 * 创建余额趋势图表
 */
function createBalanceChart(canvas, data) {
    if (!canvas || canvas.tagName !== 'CANVAS') {
        console.warn('无效的Canvas元素');
        return null;
    }

    const ctx = canvas.getContext('2d');
    if (!ctx) {
        console.error('无法获取Canvas 2D上下文');
        return null;
    }

    setupCanvas(canvas);

    const labels = data.monthlyTrends.map(trend => trend.month);
    const amounts = data.monthlyTrends.map(trend => trend.balance);

    const chartConfig = {
        ...CHART_CONFIG,
        data: {
            labels: labels,
            datasets: [{
                label: '账户余额',
                data: amounts,
                borderColor: getCSSColor(COLORS.primary),
                backgroundColor: createGradient(ctx),
                borderWidth: DIMENSIONS.borderWidth,
                fill: true,
                tension: 0.4,
                pointBackgroundColor: getCSSColor(COLORS.primary),
                pointBorderColor: COLORS.white,
                pointBorderWidth: DIMENSIONS.pointBorderWidth,
                pointRadius: DIMENSIONS.pointRadius,
                pointHoverRadius: DIMENSIONS.pointHoverRadius
            }]
        }
    };

    // 设置tooltip边框颜色
    chartConfig.plugins.tooltip.borderColor = getCSSColor(COLORS.primary);

    try {
        return new Chart(ctx, chartConfig);
    } catch (error) {
        console.error('Chart.js初始化失败:', error);
        return null;
    }
}

/**
 * 获取仪表盘数据
 */
function getDashboardData() {
    const dataElement = document.getElementById('dashboard-data');
    if (!dataElement) {
        console.warn('未找到仪表盘数据元素');
        return { balance: 0, monthlyTrends: [] };
    }

    try {
        const balance = parseFloat(dataElement.dataset.balance) || 0;
        const monthlyTrends = dataElement.dataset.monthlyTrends ? 
            JSON.parse(dataElement.dataset.monthlyTrends) : [];
        
        return { balance, monthlyTrends };
    } catch (error) {
        console.error('解析仪表盘数据失败:', error);
        return { balance: 0, monthlyTrends: [] };
    }
}

/**
 * 初始化仪表盘
 */
function initDashboard() {
    const canvas = document.getElementById('balanceTrendChart');
    if (!canvas) return; // 不在仪表盘页面

    const data = getDashboardData();
    const chart = createBalanceChart(canvas, data);
    
    if (chart) {
        // 响应式处理
        window.addEventListener('resize', () => chart.resize());
        
        // 页面卸载时清理
        window.addEventListener('beforeunload', () => {
            chart.destroy();
        });
        
        console.log('仪表盘初始化完成');
    }
}

// 自动初始化
document.addEventListener('DOMContentLoaded', initDashboard); 