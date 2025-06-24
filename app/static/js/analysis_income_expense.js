/**
 * 收支分析页面的JavaScript逻辑
 * 负责收支对比图表和净收支趋势图表渲染
 */

// 图表配置常量
const CHART_CONFIG = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
        legend: { 
            display: true,
            position: 'top'
        },
        tooltip: {
            backgroundColor: 'rgba(0, 0, 0, 0.8)',
            titleColor: '#ffffff',
            bodyColor: '#ffffff',
            borderWidth: 1,
            callbacks: {
                label: function(context) {
                    return `${context.dataset.label}: ¥${context.parsed.y.toFixed(2)}`;
                }
            }
        }
    },
    scales: {
        y: {
            beginAtZero: true,
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
    income: '#28a745',      // 收入 - 绿色
    expense: '#dc3545',     // 支出 - 红色
    net: '#007bff',         // 净收支 - 蓝色
    gradient: {
        income: 'rgba(40, 167, 69, 0.2)',
        expense: 'rgba(220, 53, 69, 0.2)',
        net: 'rgba(0, 123, 255, 0.2)'
    }
};

/**
 * 获取分析数据
 */
function getAnalysisData() {
    const dataElement = document.getElementById('analysis-data');
    if (!dataElement) {
        console.warn('未找到分析数据元素');
        return { 
            monthlyData: [], 
            totalIncome: 0, 
            totalExpense: 0 
        };
    }

    try {
        const monthlyData = dataElement.dataset.monthlyData ? 
            JSON.parse(dataElement.dataset.monthlyData) : [];
        const totalIncome = parseFloat(dataElement.dataset.totalIncome) || 0;
        const totalExpense = parseFloat(dataElement.dataset.totalExpense) || 0;
        
        return { monthlyData, totalIncome, totalExpense };
    } catch (error) {
        console.error('解析分析数据失败:', error);
        return { 
            monthlyData: [], 
            totalIncome: 0, 
            totalExpense: 0 
        };
    }
}

/**
 * 创建收支对比图表
 */
function createIncomeExpenseChart(canvas, data) {
    if (!canvas || canvas.tagName !== 'CANVAS') {
        console.warn('无效的Canvas元素');
        return null;
    }

    const ctx = canvas.getContext('2d');
    if (!ctx) {
        console.error('无法获取Canvas 2D上下文');
        return null;
    }

    // 处理数据
    const labels = data.monthlyData.map(item => item.month || '未知月份');
    const incomeData = data.monthlyData.map(item => Math.abs(item.income || 0));
    const expenseData = data.monthlyData.map(item => Math.abs(item.expense || 0));

    const chartConfig = {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [
                {
                    label: '收入',
                    data: incomeData,
                    backgroundColor: COLORS.gradient.income,
                    borderColor: COLORS.income,
                    borderWidth: 2
                },
                {
                    label: '支出',
                    data: expenseData,
                    backgroundColor: COLORS.gradient.expense,
                    borderColor: COLORS.expense,
                    borderWidth: 2
                }
            ]
        },
        options: CHART_CONFIG
    };

    try {
        return new Chart(ctx, chartConfig);
    } catch (error) {
        console.error('收支对比图表初始化失败:', error);
        return null;
    }
}

/**
 * 创建净收支趋势图表
 */
function createNetIncomeChart(canvas, data) {
    if (!canvas || canvas.tagName !== 'CANVAS') {
        console.warn('无效的Canvas元素');
        return null;
    }

    const ctx = canvas.getContext('2d');
    if (!ctx) {
        console.error('无法获取Canvas 2D上下文');
        return null;
    }

    // 处理数据
    const labels = data.monthlyData.map(item => item.month || '未知月份');
    const netData = data.monthlyData.map(item => 
        (item.income || 0) - Math.abs(item.expense || 0)
    );

    const chartConfig = {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: '净收支',
                data: netData,
                borderColor: COLORS.net,
                backgroundColor: COLORS.gradient.net,
                borderWidth: 3,
                fill: true,
                tension: 0.4,
                pointBackgroundColor: COLORS.net,
                pointBorderColor: '#ffffff',
                pointBorderWidth: 2,
                pointRadius: 6,
                pointHoverRadius: 8
            }]
        },
        options: {
            ...CHART_CONFIG,
            scales: {
                ...CHART_CONFIG.scales,
                y: {
                    ...CHART_CONFIG.scales.y,
                    beginAtZero: false
                }
            }
        }
    };

    try {
        return new Chart(ctx, chartConfig);
    } catch (error) {
        console.error('净收支趋势图表初始化失败:', error);
        return null;
    }
}

/**
 * 初始化收支分析页面
 */
function initIncomeExpenseAnalysis() {
    const incomeExpenseCanvas = document.getElementById('incomeExpenseChart');
    const netIncomeCanvas = document.getElementById('netIncomeChart');
    
    if (!incomeExpenseCanvas && !netIncomeCanvas) {
        return; // 不在收支分析页面
    }

    const data = getAnalysisData();
    const charts = [];
    
    if (incomeExpenseCanvas) {
        const chart1 = createIncomeExpenseChart(incomeExpenseCanvas, data);
        if (chart1) charts.push(chart1);
    }
    
    if (netIncomeCanvas) {
        const chart2 = createNetIncomeChart(netIncomeCanvas, data);
        if (chart2) charts.push(chart2);
    }
    
    if (charts.length > 0) {
        // 响应式处理
        window.addEventListener('resize', () => {
            charts.forEach(chart => chart.resize());
        });
        
        // 页面卸载时清理
        window.addEventListener('beforeunload', () => {
            charts.forEach(chart => chart.destroy());
        });
        
        console.log('收支分析页面初始化完成');
    }
}

// 自动初始化
document.addEventListener('DOMContentLoaded', initIncomeExpenseAnalysis); 