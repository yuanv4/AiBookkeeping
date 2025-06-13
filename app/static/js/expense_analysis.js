/**
 * 支出分析页面JavaScript脚本
 * 负责初始化支出分析相关的图表和交互功能
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

// 等待DOM加载完成
document.addEventListener('DOMContentLoaded', function() {
    console.log('[EXPENSE_ANALYSIS] 页面已加载');
    
    // 初始化支出分析数据
    initExpenseAnalysisData();
    
    // 初始化图表
    initExpenseAnalysisCharts();
});

/**
 * 初始化支出分析数据
 * 从HTML模板中获取后端传递的数据并转换为JavaScript变量
 */
function initExpenseAnalysisData() {
    // 获取页面中的数据元素
    const categoryDataElement = document.getElementById('expense-category-data');
    const trendDataElement = document.getElementById('expense-trend-data');
    const patternDataElement = document.getElementById('spending-pattern-data');
    const anomalyDataElement = document.getElementById('anomaly-data');
    
    // 解析支出分类数据
    if (categoryDataElement) {
        try {
            window.expenseCategoryData = JSON.parse(categoryDataElement.textContent);
            console.log('[EXPENSE_ANALYSIS] 支出分类数据已加载:', window.expenseCategoryData);
        } catch (e) {
            console.error('[EXPENSE_ANALYSIS] 解析支出分类数据失败:', e);
            window.expenseCategoryData = null;
        }
    }
    
    // 解析支出趋势数据
    if (trendDataElement) {
        try {
            window.expenseTrendData = JSON.parse(trendDataElement.textContent);
            console.log('[EXPENSE_ANALYSIS] 支出趋势数据已加载:', window.expenseTrendData);
        } catch (e) {
            console.error('[EXPENSE_ANALYSIS] 解析支出趋势数据失败:', e);
            window.expenseTrendData = null;
        }
    }
    
    // 解析消费模式数据
    if (patternDataElement) {
        try {
            window.spendingPatternData = JSON.parse(patternDataElement.textContent);
            console.log('[EXPENSE_ANALYSIS] 消费模式数据已加载:', window.spendingPatternData);
        } catch (e) {
            console.error('[EXPENSE_ANALYSIS] 解析消费模式数据失败:', e);
            window.spendingPatternData = null;
        }
    }
    
    // 解析异常检测数据
    if (anomalyDataElement) {
        try {
            window.anomalyData = JSON.parse(anomalyDataElement.textContent);
            console.log('[EXPENSE_ANALYSIS] 异常检测数据已加载:', window.anomalyData);
        } catch (e) {
            console.error('[EXPENSE_ANALYSIS] 解析异常检测数据失败:', e);
            window.anomalyData = null;
        }
    }
    
    console.log('[EXPENSE_ANALYSIS] 所有数据初始化完成');
}

/**
 * 支出分析页面图表初始化脚本
 */
function initExpenseAnalysisCharts() {
    // 如果base.html中未注册插件，这里再次尝试注册
    if (typeof Chart !== 'undefined' && typeof ChartDataLabels !== 'undefined' && 
        !Chart.registry.plugins.get('datalabels')) {
        Chart.register(ChartDataLabels);
    }
    
    // 定义常用颜色，直接从CSS变量获取
    const colors = {
        // 使用财务专业版主题颜色
        expense: getCSSColor('--danger'),
        necessary: getCSSColor('--warning'),
        discretionary: getCSSColor('--info'),
        savings: getCSSColor('--success'),
        primary: getCSSColor('--primary'),
        secondary: getCSSColor('--secondary'),
        success: getCSSColor('--success'),
        danger: getCSSColor('--danger'),
        warning: getCSSColor('--warning'),
        info: getCSSColor('--info'),
        // 图表分类颜色
        category: [
            getCSSColor('--chart-category-1'),
            getCSSColor('--chart-category-2'),
            getCSSColor('--chart-category-3'),
            getCSSColor('--chart-category-4'),
            getCSSColor('--chart-category-5'),
            getCSSColor('--chart-category-6'),
            getCSSColor('--chart-category-7'),
            getCSSColor('--chart-category-8')
        ],
        neutral: getCSSColor('--secondary'),
        // 将颜色转换为半透明版本的辅助函数
        getAlpha: function(color, alpha = 0.8) {
            // 处理十六进制颜色
            if (color.startsWith('#')) {
                const r = parseInt(color.slice(1, 3), 16);
                const g = parseInt(color.slice(3, 5), 16);
                const b = parseInt(color.slice(5, 7), 16);
                return `rgba(${r}, ${g}, ${b}, ${alpha})`;
            }
            // 处理rgba颜色
            if (color.startsWith('rgba')) {
                return color.replace(/rgba\((.+?), .+?\)/, `rgba($1, ${alpha})`);
            }
            // 处理rgb颜色
            if (color.startsWith('rgb')) {
                return color.replace(/rgb\((.+?)\)/, `rgba($1, ${alpha})`);
            }
            return color;
        }
    };
    
    /**
     * 通用货币格式化函数
     * @param {number} value - 需要格式化的数值
     * @returns {string} 格式化后的字符串
     */
    function formatCurrencyForChart(value) {
        if (value === null || typeof value === 'undefined') {
            return '¥0.00';
        }
        const absValue = Math.abs(value);
        let sign = value < 0 ? '-' : '';
        
        if (absValue >= 100000000) {
            return sign + '¥' + (absValue / 100000000).toFixed(2) + '亿';
        } else if (absValue >= 10000) {
            return sign + '¥' + (absValue / 10000).toFixed(2) + '万';
        }
        return sign + '¥' + absValue.toFixed(2);
    }
    
    /**
     * 显示无数据消息
     * @param {HTMLElement} ctx - Canvas元素
     * @param {string} message - 消息内容
     */
    function displayNoDataMessage(ctx, message) {
        const parent = ctx.parentElement;
        parent.innerHTML = `<div class="text-center py-4"><div class="text-muted">${message}</div></div>`;
    }
    
    // 初始化各个图表
    initExpenseCategoryChart();
    initExpenseTrendChart();
    initMonthlyExpenseChart();
    initAnomalyDetectionChart();
    
    /**
     * 初始化支出分类饼图
     */
    function initExpenseCategoryChart() {
        const ctx = document.getElementById('expenseCategoryChart');
        if (!ctx) return;
        
        // 从后端数据获取支出分类数据
        let categoryData;
        if (window.expenseCategoryData && window.expenseCategoryData.categories) {
            const categories = window.expenseCategoryData.categories;
            categoryData = {
                labels: categories.map(cat => cat.name || cat.category),
                amounts: categories.map(cat => cat.amount || 0),
                percentages: categories.map(cat => cat.percentage || 0)
            };
        } else {
            // 如果没有数据，显示无数据消息
            displayNoDataMessage(ctx, '暂无支出分类数据');
            return;
        }
        
        new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: categoryData.labels,
                datasets: [{
                    data: categoryData.amounts,
                    backgroundColor: colors.category,
                    borderWidth: 2,
                    borderColor: '#ffffff'
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
                            usePointStyle: true
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const label = context.label || '';
                                const value = formatCurrencyForChart(context.parsed);
                                const percentage = categoryData.percentages[context.dataIndex];
                                return `${label}: ${value} (${percentage}%)`;
                            }
                        }
                    },
                    datalabels: {
                        display: true,
                        formatter: function(value, context) {
                            const percentage = categoryData.percentages[context.dataIndex];
                            return percentage >= 5 ? `${percentage}%` : '';
                        },
                        color: '#ffffff',
                        font: {
                            weight: 'bold'
                        }
                    }
                }
            }
        });
    }
    
    /**
     * 初始化支出趋势折线图
     */
    function initExpenseTrendChart() {
        const ctx = document.getElementById('expenseTrendChart');
        if (!ctx) return;
        
        // 从后端数据获取支出趋势数据
        let trendData;
        if (window.expenseTrendData && window.expenseTrendData.monthly_data) {
            const monthlyData = window.expenseTrendData.monthly_data;
            trendData = {
                labels: monthlyData.map(data => `${data.month}月`),
                totalExpense: monthlyData.map(data => data.total_expense || 0),
                necessaryExpense: monthlyData.map(data => data.necessary_expense || 0),
                discretionaryExpense: monthlyData.map(data => data.discretionary_expense || 0)
            };
        } else {
            // 如果没有数据，显示无数据消息
            displayNoDataMessage(ctx, '暂无支出趋势数据');
            return;
        }
        
        new Chart(ctx, {
            type: 'line',
            data: {
                labels: trendData.labels,
                datasets: [
                    {
                        label: '总支出',
                        data: trendData.totalExpense,
                        borderColor: colors.expense,
                        backgroundColor: colors.getAlpha(colors.expense, 0.1),
                        borderWidth: 3,
                        fill: true,
                        tension: 0.4
                    },
                    {
                        label: '必要支出',
                        data: trendData.necessaryExpense,
                        borderColor: colors.necessary,
                        backgroundColor: colors.getAlpha(colors.necessary, 0.1),
                        borderWidth: 2,
                        fill: false,
                        tension: 0.4
                    },
                    {
                        label: '非必要支出',
                        data: trendData.discretionaryExpense,
                        borderColor: colors.discretionary,
                        backgroundColor: colors.getAlpha(colors.discretionary, 0.1),
                        borderWidth: 2,
                        fill: false,
                        tension: 0.4
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'top'
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false,
                        callbacks: {
                            label: function(context) {
                                const label = context.dataset.label || '';
                                const value = formatCurrencyForChart(context.parsed.y);
                                return `${label}: ${value}`;
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: function(value) {
                                return formatCurrencyForChart(value);
                            }
                        }
                    }
                },
                interaction: {
                    mode: 'index',
                    intersect: false
                }
            }
        });
    }
    
    /**
     * 初始化月度支出趋势图表
     */
    function initMonthlyExpenseChart() {
        const ctx = document.getElementById('monthlyExpenseChart');
        if (!ctx) return;
        
        // 从后端数据获取月度支出数据
        let monthlyData;
        if (window.spendingPatternData && window.spendingPatternData.monthly_trends) {
            const trends = window.spendingPatternData.monthly_trends;
            monthlyData = {
                labels: trends.map(data => `${data.month}月`),
                totalExpense: trends.map(data => data.total_expense || 0),
                necessaryExpense: trends.map(data => data.necessary_expense || 0),
                discretionaryExpense: trends.map(data => data.discretionary_expense || 0)
            };
        } else {
            // 如果没有数据，显示无数据消息
            displayNoDataMessage(ctx, '暂无月度支出数据');
            return;
        }
        
        new Chart(ctx, {
            type: 'bar',
            data: {
                labels: monthlyData.labels,
                datasets: [
                    {
                        label: '总支出',
                        data: monthlyData.totalExpense,
                        backgroundColor: colors.getAlpha(colors.expense, 0.8),
                        borderColor: colors.expense,
                        borderWidth: 1
                    },
                    {
                        label: '必要支出',
                        data: monthlyData.necessaryExpense,
                        backgroundColor: colors.getAlpha(colors.necessary, 0.8),
                        borderColor: colors.necessary,
                        borderWidth: 1
                    },
                    {
                        label: '非必要支出',
                        data: monthlyData.discretionaryExpense,
                        backgroundColor: colors.getAlpha(colors.discretionary, 0.8),
                        borderColor: colors.discretionary,
                        borderWidth: 1
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'top'
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false,
                        callbacks: {
                            label: function(context) {
                                const label = context.dataset.label || '';
                                const value = formatCurrencyForChart(context.parsed.y);
                                return `${label}: ${value}`;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        stacked: false
                    },
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: function(value) {
                                return formatCurrencyForChart(value);
                            }
                        }
                    }
                }
            }
        });
    }
    
    /**
     * 初始化异常支出检测图表
     */
    function initAnomalyDetectionChart() {
        const ctx = document.getElementById('anomalyDetectionChart');
        if (!ctx) return;
        
        // 从后端数据获取异常检测数据
        let anomalyData;
        if (window.anomalyData && window.anomalyData.monthly_data) {
            const monthlyData = window.anomalyData.monthly_data;
            const anomalies = window.anomalyData.anomalies || [];
            
            anomalyData = {
                labels: monthlyData.map(data => `${data.month}月`),
                normalExpense: monthlyData.map(data => data.normal_expense || 0),
                anomalies: anomalies
            };
        } else {
            // 如果没有数据，显示无数据消息
            displayNoDataMessage(ctx, '暂无异常检测数据');
            return;
        }
        
        // 创建异常点数据
        const anomalyPoints = anomalyData.labels.map((label, index) => {
            const anomaly = anomalyData.anomalies.find(a => `${a.month}月` === label);
            return anomaly ? anomaly.amount : null;
        });
        
        new Chart(ctx, {
            type: 'line',
            data: {
                labels: anomalyData.labels,
                datasets: [
                    {
                        label: '正常支出',
                        data: anomalyData.normalExpense,
                        borderColor: colors.primary,
                        backgroundColor: colors.getAlpha(colors.primary, 0.1),
                        borderWidth: 2,
                        fill: true,
                        tension: 0.4
                    },
                    {
                        label: '异常支出',
                        data: anomalyPoints,
                        borderColor: colors.danger,
                        backgroundColor: colors.danger,
                        borderWidth: 0,
                        pointRadius: 8,
                        pointHoverRadius: 10,
                        showLine: false,
                        fill: false
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'top'
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const label = context.dataset.label || '';
                                const value = formatCurrencyForChart(context.parsed.y);
                                if (context.dataset.label === '异常支出' && context.parsed.y) {
                                    const anomaly = anomalyData.anomalies.find(a => a.month === context.label);
                                    return `${label}: ${value} (${anomaly ? anomaly.type : ''})`;
                                }
                                return `${label}: ${value}`;
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: function(value) {
                                return formatCurrencyForChart(value);
                            }
                        }
                    }
                }
            }
        });
    }
}