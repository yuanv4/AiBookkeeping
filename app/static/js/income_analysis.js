// 收入分析页面的JavaScript逻辑

// 等待DOM加载完成
document.addEventListener('DOMContentLoaded', function() {
    console.log('[INCOME_ANALYSIS] 页面已加载');
    
    // 初始化收入分析数据
    initIncomeAnalysisData();
});

/**
 * 初始化收入分析数据
 * 从HTML模板中获取后端传递的数据并转换为JavaScript变量
 */
function initIncomeAnalysisData() {
    // 获取页面中的数据元素
    const balanceDataElement = document.getElementById('balance-data');
    const stabilityDataElement = document.getElementById('stability-data');
    const sourceDataElement = document.getElementById('source-data');
    const cashflowDataElement = document.getElementById('cashflow-data');
    const growthDataElement = document.getElementById('growth-data');
    
    // 解析收支平衡数据
    if (balanceDataElement) {
        try {
            window.balanceData = JSON.parse(balanceDataElement.textContent);
            console.log('[INCOME_ANALYSIS] 收支平衡数据已加载:', window.balanceData);
        } catch (e) {
            console.error('[INCOME_ANALYSIS] 解析收支平衡数据失败:', e);
            window.balanceData = null;
        }
    }
    
    // 解析收入稳定性数据
    if (stabilityDataElement) {
        try {
            window.stabilityData = JSON.parse(stabilityDataElement.textContent);
            console.log('[INCOME_ANALYSIS] 收入稳定性数据已加载:', window.stabilityData);
        } catch (e) {
            console.error('[INCOME_ANALYSIS] 解析收入稳定性数据失败:', e);
            window.stabilityData = null;
        }
    }
    
    // 解析收入来源分布数据
    if (sourceDataElement) {
        try {
            window.sourceData = JSON.parse(sourceDataElement.textContent);
            console.log('[INCOME_ANALYSIS] 收入来源分布数据已加载:', window.sourceData);
        } catch (e) {
            console.error('[INCOME_ANALYSIS] 解析收入来源分布数据失败:', e);
            window.sourceData = null;
        }
    }
    
    // 解析现金流数据
    if (cashflowDataElement) {
        try {
            window.cashflowData = JSON.parse(cashflowDataElement.textContent);
            console.log('[INCOME_ANALYSIS] 现金流数据已加载:', window.cashflowData);
        } catch (e) {
            console.error('[INCOME_ANALYSIS] 解析现金流数据失败:', e);
            window.cashflowData = null;
        }
    }
    
    // 解析收入增长数据
    if (growthDataElement) {
        try {
            window.growthData = JSON.parse(growthDataElement.textContent);
            console.log('[INCOME_ANALYSIS] 收入增长数据已加载:', window.growthData);
        } catch (e) {
            console.error('[INCOME_ANALYSIS] 解析收入增长数据失败:', e);
            window.growthData = null;
        }
    }
    
    console.log('[INCOME_ANALYSIS] 所有数据初始化完成');
}

/**
 * 收入分析页面图表初始化脚本
 */
function initIncomeAnalysisCharts() {
    // 如果base.html中未注册插件，这里再次尝试注册
    if (typeof Chart !== 'undefined' && typeof ChartDataLabels !== 'undefined' && 
        !Chart.registry.plugins.get('datalabels')) {
        Chart.register(ChartDataLabels);
    }
    
    // 检查并使用全局财务主题颜色
    const useFinanceTheme = typeof window.defaultColors !== 'undefined';
    
    // 定义常用颜色，优先使用全局财务主题颜色
    const colors = useFinanceTheme ? {
        // 使用财务专业版主题颜色
        income: window.defaultColors.success,
        expense: window.defaultColors.danger,
        savings: window.defaultColors.warning,
        ratio: window.defaultColors.info,
        primary: window.defaultColors.primary,
        secondary: window.defaultColors.secondary,
        success: window.defaultColors.success,
        danger: window.defaultColors.danger,
        warning: window.defaultColors.warning,
        info: window.defaultColors.info,
        // 图表分类颜色
        category: window.defaultColors.category,
        neutral: window.defaultColors.neutral,
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
    } : {
        // 保留原有颜色作为后备方案
        income: 'rgba(70, 99, 172, 0.8)',
        expense: 'rgba(236, 76, 71, 0.8)',
        savings: 'rgba(71, 184, 129, 0.8)',
        ratio: 'rgba(255, 171, 0, 0.8)',
        primary: '#4663ac',
        danger: '#ec4c47',
        success: '#47b881',
        warning: '#ffab00',
        info: '#1070ca'
    };
    
    /**
     * 通用货币格式化函数
     * @param {number} value - 需要格式化的数值
     * @returns {string} 格式化后的字符串
     */
    function formatCurrencyForChart(value) {
        if (value === null || typeof value === 'undefined') {
            return '¥0.00'; // 或 'N/A'
        }
        const absValue = Math.abs(value);
        let sign = value < 0 ? '-' : ''; // 保留符号，以防支出为负（理论上不会，但防御性处理）
        
        if (absValue >= 100000000) {
            return sign + '¥' + (absValue / 100000000).toFixed(2) + '亿';
        } else if (absValue >= 10000) {
            return sign + '¥' + (absValue / 10000).toFixed(2) + '万';
        }
        return sign + '¥' + absValue.toFixed(2);
    }
    
    // 为图表准备数据
    initIncomeExpenseChart();
    initIncomeStabilityChart();
    initIncomeSourcesChart();
    initMonthlySourcesChart();
    initCashFlowChart();
    initIncomeGrowthChart();
    initIncomeVsInflationChart();
    initBreakEvenChart();
    
    /**
     * 初始化收入支出平衡分析图表
     */
    function initIncomeExpenseChart() {
        const ctx = document.getElementById('incomeExpenseChart');
        if (!ctx) return;
        
        // 确保数据存在
        if (!incomeExpenseData || incomeExpenseData.length === 0) {
            displayNoDataMessage(ctx, '暂无收入支出数据');
            return;
        }
        
        const labels = incomeExpenseData.map(item => item.month);
        const incomeData = incomeExpenseData.map(item => item.income);
        const expenseData = incomeExpenseData.map(item => item.expense);
        const savingRateData = incomeExpenseData.map(item => item.saving_rate * 100);
        
        new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: '收入',
                        data: incomeData,
                        backgroundColor: colors.income,
                        order: 2
                    },
                    {
                        label: '支出',
                        data: expenseData,
                        backgroundColor: colors.expense,
                        order: 3
                    },
                    {
                        label: '储蓄率(%)',
                        data: savingRateData,
                        type: 'line',
                        borderColor: colors.savings,
                        borderWidth: 2,
                        pointBackgroundColor: colors.savings,
                        fill: false,
                        yAxisID: 'y1',
                        order: 1
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                layout: {
                    padding: {
                        top: 10
                    }
                },
                plugins: {
                    title: {
                        display: true,
                        text: labels.length > 24 ? '月度收支与储蓄率趋势 (可缩放平移查看更多)' : '月度收支与储蓄率趋势'
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false,
                        callbacks: {
                            label: function(context) {
                                let label = context.dataset.label || '';
                                if (label) {
                                    label += ': ';
                                }
                                if (context.dataset.yAxisID === 'y1') {
                                    label += context.parsed.y.toFixed(1) + '%';
                                } else {
                                    label += formatCurrencyForChart(context.parsed.y);
                                }
                                return label;
                            }
                        }
                    },
                    zoom: {
                        zoom: {
                            wheel: {
                                enabled: true
                            },
                            pinch: {
                                enabled: true
                            },
                            mode: 'xy'
                        },
                        pan: {
                            enabled: true,
                            mode: 'xy'
                        }
                    },
                    datalabels: {
                        display: function(context) {
                            return context.dataset.label === '储蓄率(%)';
                        },
                        formatter: function(value, context) {
                            if (context.dataset.label === '储蓄率(%)') {
                                if (value === null || typeof value === 'undefined') return '';
                                return value.toFixed(1) + '%';
                            }
                            return null;
                        },
                        color: colors.savings,
                        align: function(context) {
                            if (context.dataset.label === '储蓄率(%)') {
                                const y1Scale = context.chart.scales['y1'];
                                const value = context.dataset.data[context.dataIndex];
                                if (y1Scale && value !== null && typeof value !== 'undefined') {
                                    if (value > (y1Scale.max * 0.85)) {
                                        return 'bottom';
                                    }
                                }
                            }
                            return 'top';
                        },
                        anchor: 'end',
                        offset: function(context) {
                            if (context.dataset.label === '储蓄率(%)') {
                                const y1Scale = context.chart.scales['y1'];
                                const value = context.dataset.data[context.dataIndex];
                                if (y1Scale && value !== null && typeof value !== 'undefined') {
                                    if (value > (y1Scale.max * 0.85)) {
                                        return 8;
                                    }
                                }
                            }
                            return 6;
                        },
                        font: {
                            size: 10,
                            weight: '500'
                        },
                        clamp: true
                    }
                },
                scales: {
                    x: {
                        stacked: false,
                        grid: {
                            display: false
                        },
                        ticks: {
                            autoSkip: true,
                            maxRotation: 45,
                            minRotation: 0,
                            padding: 10
                        }
                    },
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: '金额 (¥)'
                        },
                        ticks: {
                            callback: function(value, index, values) {
                                return formatCurrencyForChart(value);
                            }
                        }
                    },
                    y1: {
                        position: 'right',
                        beginAtZero: true,
                        grace: '8%',
                        title: {
                            display: true,
                            text: '储蓄率 (%)'
                        }
                    }
                }
            }
        });
    }
    
    /**
     * 初始化收入稳定性分析图表
     */
    function initIncomeStabilityChart() {
        const ctx = document.getElementById('incomeStabilityChart');
        if (!ctx) return;
        
        // 确保数据存在
        if (!incomeStabilityData || incomeStabilityData.length === 0) {
            displayNoDataMessage(ctx, '暂无收入稳定性数据');
            return;
        }
        
        const labels = incomeStabilityData.map(item => item.month);
        const incomeData = incomeStabilityData.map(item => item.income);
        
        // 计算移动平均线
        const movingAverage = [];
        const window = 3; // 3个月移动平均
        
        for (let i = 0; i < incomeData.length; i++) {
            if (i < window - 1) {
                movingAverage.push(null);
            } else {
                let sum = 0;
                for (let j = 0; j < window; j++) {
                    sum += incomeData[i - j];
                }
                movingAverage.push(sum / window);
            }
        }
        
        new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: '月收入',
                        data: incomeData,
                        backgroundColor: colors.income,
                        order: 2
                    },
                    {
                        label: '3个月移动平均',
                        data: movingAverage,
                        type: 'line',
                        borderColor: colors.warning,
                        borderWidth: 2,
                        pointBackgroundColor: colors.warning,
                        fill: false,
                        order: 1
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: labels.length > 24 ? '月度收入波动分析 (可缩放平移查看更多)' : '月度收入波动分析'
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false,
                        callbacks: {
                            label: function(context) {
                                let label = context.dataset.label || '';
                                if (label) {
                                    label += ': ';
                                }
                                label += formatCurrencyForChart(context.parsed.y);
                                return label;
                            }
                        }
                    },
                    zoom: {
                        zoom: {
                            wheel: {
                                enabled: true
                            },
                            pinch: {
                                enabled: true
                            },
                            mode: 'xy'
                        },
                        pan: {
                            enabled: true,
                            mode: 'xy'
                        }
                    },
                    datalabels: {
                        display: function(context) {
                            // 只为"3个月移动平均"折线显示数据标签
                            return context.dataset.label === '3个月移动平均';
                        },
                        formatter: function(value, context) {
                            if (context.dataset.label === '3个月移动平均') {
                                if (value === null || typeof value === 'undefined') return ''; // 空值不显示标签
                                return formatCurrencyForChart(value);
                            }
                            return null;
                        },
                        color: colors.warning, // 与线条颜色一致，或选择如 '#555' 的深色以保证对比度
                        align: function(context) {
                            if (context.dataset.label === '3个月移动平均') {
                                const yScale = context.chart.scales['y']; 
                                const value = context.dataset.data[context.dataIndex];
                                if (yScale && value !== null && typeof value !== 'undefined') {
                                    // 如果图表只有y轴，或者能确保yScale.max是正确的比较对象
                                    // 检查yScale.max是否已定义且大于0，避免除以0或NaN
                                    if (yScale.max && yScale.max > 0 && value > (yScale.max * 0.85)) { 
                                        return 'bottom';
                                    }
                                }
                            }
                            return 'top'; 
                        },
                        offset: function(context) {
                            if (context.dataset.label === '3个月移动平均') {
                                const yScale = context.chart.scales['y'];
                                const value = context.dataset.data[context.dataIndex];
                                if (yScale && value !== null && typeof value !== 'undefined') {
                                    if (yScale.max && yScale.max > 0 && value > (yScale.max * 0.85)) {
                                        return 8; // 向下的偏移量
                                    }
                                }
                            }
                            return 6; // 默认向上的偏移量
                        },
                        font: {
                            size: 10,
                            weight: '500'
                        },
                        clamp: true // 尝试将标签限制在图表区域内
                    }
                },
                scales: {
                    x: {
                        grid: {
                            display: false
                        },
                        ticks: {
                            autoSkip: true,
                            maxRotation: 45,
                            minRotation: 0,
                            padding: 10
                        }
                    },
                    y: {
                        beginAtZero: true,
                        grace: '8%', // 为Y轴添加呼吸空间
                        title: {
                            display: true,
                            text: '收入金额 (¥)'
                        },
                        ticks: {
                            callback: function(value, index, values) {
                                return formatCurrencyForChart(value);
                            }
                        }
                    }
                }
            }
        });
    }
    
    /**
     * 初始化收入来源分布饼图
     */
    function initIncomeSourcesChart() {
        const ctx = document.getElementById('incomeSourcesPieChart');
        if (!ctx) return;
        
        // 确保数据存在
        if (!incomeSourcesData || incomeSourcesData.length === 0) {
            displayNoDataMessage(ctx, '暂无收入来源数据');
            return;
        }
        
        const labels = incomeSourcesData.map(item => item.source);
        const data = incomeSourcesData.map(item => item.amount);
        
        // 生成随机颜色
        const backgroundColors = generateColors(labels.length);
        
        new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: labels,
                datasets: [{
                    data: data,
                    backgroundColor: backgroundColors,
                    borderColor: 'white',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: '收入来源分布'
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const value = context.raw;
                                const total = context.dataset.data.reduce((acc, val) => acc + val, 0);
                                const percentage = ((value / total) * 100).toFixed(1);
                                return `${formatCurrencyForChart(value)} (${percentage}%)`;
                            }
                        }
                    },
                    datalabels: {
                        formatter: (value, ctx) => {
                            const total = ctx.dataset.data.reduce((acc, val) => acc + val, 0);
                            const percentage = ((value / total) * 100).toFixed(1);
                            return percentage + '%';
                        },
                        color: '#444',
                        font: {
                            weight: 'bold'
                        },
                        display: function(context) {
                            const total = context.dataset.data.reduce((acc, val) => acc + val, 0);
                            const value = context.dataset.data[context.dataIndex];
                            return (value / total) * 100 >= 5; // 只显示占比5%以上的标签
                        }
                    },
                    legend: {
                        position: 'right',
                        labels: {
                            boxWidth: 12,
                            padding: 15
                        }
                    }
                },
                layout: {
                    padding: {
                        top: 10,
                        bottom: 10
                    }
                }
            }
        });
    }
    
    /**
     * 初始化月度收入来源数量图表
     */
    function initMonthlySourcesChart() {
        const ctx = document.getElementById('monthlySourcesChart');
        if (!ctx) return;
        
        // 确保数据存在
        if (!monthlySourcesData || monthlySourcesData.length === 0) {
            displayNoDataMessage(ctx, '暂无月度收入来源数据');
            return;
        }
        
        const labels = monthlySourcesData.map(item => item.month);
        const data = monthlySourcesData.map(item => item.source_count);
        
        new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: '收入来源数量',
                    data: data,
                    backgroundColor: colors.income,
                    borderColor: colors.income,
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: labels.length > 24 ? '月度收入来源数量 (可缩放平移查看更多)' : '月度收入来源数量'
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                let label = context.dataset.label || '';
                                if (label) {
                                    label += ': ';
                                }
                                label += context.parsed.y; // 数量是整数，直接显示
                                return label;
                            }
                        }
                    },
                    zoom: {
                        zoom: {
                            wheel: { enabled: true },
                            pinch: { enabled: true },
                            mode: 'xy'
                        },
                        pan: {
                            enabled: true,
                            mode: 'xy'
                        }
                    },
                    datalabels: {
                        display: function(context) {
                            return context.dataset.data[context.dataIndex] > 0; // 只为大于0的值显示标签
                        },
                        formatter: function(value, context) {
                            return value; // 直接显示数量值
                        },
                        anchor: 'start',  // 修改为start
                        align: 'top',     // 保持 top
                        offset: 8,        // 增加offset以提供更好的间距
                        rotation: 0,      // 保持 rotation
                        padding: 0,       // 保持 padding: 0
                        color: '#555',
                        font: { size: 10 },
                        clamp: true       // 添加clamp属性确保标签在图表区域内
                    }
                },
                scales: {
                    x: {
                        grid: {
                            display: false
                        },
                        ticks: {
                            autoSkip: true,
                            maxRotation: 45,
                            minRotation: 0,
                            padding: 10
                        }
                    },
                    y: {
                        beginAtZero: true,
                        grace: '20%', // Y轴呼吸空间
                        title: {
                            display: true,
                            text: '来源数量'
                        },
                        ticks: {
                            stepSize: 1
                        }
                    }
                }
            }
        });
    }
    
    /**
     * 初始化现金流趋势图表
     */
    function initCashFlowChart() {
        const ctx = document.getElementById('cashFlowChart');
        if (!ctx) return;
        
        // 确保数据存在
        if (!cashFlowData || cashFlowData.length === 0) {
            displayNoDataMessage(ctx, '暂无现金流数据');
            return;
        }
        
        const labels = cashFlowData.map(item => item.month);
        const netFlowData = cashFlowData.map(item => item.net_flow);
        const incomeData = cashFlowData.map(item => item.income);
        const expenseData = cashFlowData.map(item => item.expense);
        
        new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: '净现金流',
                        data: netFlowData,
                        borderColor: colors.success,
                        backgroundColor: 'rgba(71, 184, 129, 0.1)',
                        borderWidth: 2,
                        fill: true,
                        tension: 0.4,
                        pointRadius: 4,
                        pointHoverRadius: 6,
                        yAxisID: 'y1'  // 使用右侧Y轴
                    },
                    {
                        label: '收入',
                        data: incomeData,
                        borderColor: colors.income,
                        borderWidth: 2,
                        pointRadius: 3,
                        pointHoverRadius: 5,
                        fill: false,
                        yAxisID: 'y'   // 使用左侧Y轴
                    },
                    {
                        label: '支出',
                        data: expenseData.map(v => Math.abs(v)), // 取绝对值显示
                        borderColor: colors.expense,
                        borderWidth: 2,
                        pointRadius: 3,
                        pointHoverRadius: 5,
                        fill: false,
                        yAxisID: 'y'   // 使用左侧Y轴
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: labels.length > 24 ? '月度现金流趋势 (可缩放平移查看更多)' : '月度现金流趋势'
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false,
                        callbacks: {
                            label: function(context) {
                                let label = context.dataset.label || '';
                                if (label) {
                                    label += ': ';
                                }
                                // 统一使用formatCurrencyForChart格式化
                                label += formatCurrencyForChart(context.parsed.y);
                                return label;
                            }
                        }
                    },
                    zoom: {
                        zoom: {
                            wheel: {
                                enabled: true
                            },
                            pinch: {
                                enabled: true
                            },
                            mode: 'xy'
                        },
                        pan: {
                            enabled: true,
                            mode: 'xy'
                        }
                    },
                    datalabels: {
                        display: function(context) {
                            // 只在净现金流线上显示数据标签，避免图表过于拥挤
                            return context.dataset.label === '净现金流' && 
                                   // 根据数据点索引控制显示密度，避免标签重叠
                                   context.dataIndex % (context.dataset.data.length > 12 ? 3 : 2) === 0;
                        },
                        formatter: function(value, context) {
                            return formatCurrencyForChart(value);
                        },
                        color: colors.success,
                        align: function(context) {
                            const value = context.dataset.data[context.dataIndex];
                            // 正值在上方显示，负值在下方显示
                            return value >= 0 ? 'top' : 'bottom';
                        },
                        anchor: 'center',
                        offset: 8,
                        font: {
                            size: 10,
                            weight: '500'
                        },
                        clamp: true
                    }
                },
                scales: {
                    x: {
                        grid: {
                            display: false
                        },
                        ticks: {
                            autoSkip: true,
                            maxRotation: 45,
                            minRotation: 0,
                            padding: 10
                        }
                    },
                    y: {
                        beginAtZero: true,
                        grace: '5%', // 为Y轴添加呼吸空间
                        title: {
                            display: true,
                            text: '收入/支出金额 (¥)'
                        },
                        ticks: {
                            callback: function(value, index, values) {
                                return formatCurrencyForChart(value);
                            }
                        }
                    },
                    y1: {
                        position: 'right',
                        beginAtZero: true,
                        grace: '10%', // 为右侧Y轴添加更多呼吸空间
                        title: {
                            display: true,
                            text: '净现金流金额 (¥)'
                        },
                        ticks: {
                            callback: function(value, index, values) {
                                return formatCurrencyForChart(value);
                            }
                        },
                        grid: {
                            drawOnChartArea: false // 不显示右侧Y轴的网格线，避免图表过于复杂
                        }
                    }
                }
            }
        });
    }
    
    /**
     * 初始化收入增长图表
     */
    function initIncomeGrowthChart() {
        const ctx = document.getElementById('incomeGrowthChart');
        if (!ctx) return;
        
        // 确保数据存在
        if (!incomeGrowthData || !incomeGrowthData.yearly || incomeGrowthData.yearly.length === 0) {
            displayNoDataMessage(ctx, '暂无收入增长数据');
            return;
        }
        
        const labels = incomeGrowthData.yearly.map(item => item.year);
        const incomeData = incomeGrowthData.yearly.map(item => item.income);
        
        // 计算同比增长率
        const growthRateData = [];
        for (let i = 1; i < incomeData.length; i++) {
            if (incomeData[i-1] > 0) {
                const rate = (incomeData[i] - incomeData[i-1]) / incomeData[i-1] * 100;
                growthRateData.push(rate);
            } else {
                growthRateData.push(null);
            }
        }
        // 第一年没有增长率
        growthRateData.unshift(null);
        
        new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: '年收入',
                        data: incomeData,
                        backgroundColor: colors.income,
                        borderColor: colors.income,
                        borderWidth: 1,
                        order: 2
                    },
                    {
                        label: '同比增长率(%)',
                        data: growthRateData,
                        type: 'line',
                        borderColor: colors.success,
                        backgroundColor: 'transparent',
                        borderWidth: 2,
                        pointBackgroundColor: colors.success,
                        pointRadius: 4,
                        pointHoverRadius: 6,
                        yAxisID: 'y1',
                        order: 1
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: labels.length > 12 ? '年度收入增长趋势 (可缩放平移查看更多)' : '年度收入增长趋势'
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false,
                        callbacks: {
                            label: function(context) {
                                let label = context.dataset.label || '';
                                if (label) {
                                    label += ': ';
                                }
                                if (context.dataset.yAxisID === 'y1') {
                                    if (context.parsed.y !== null) {
                                        label += context.parsed.y.toFixed(1) + '%';
                                    } else {
                                        label += '无数据';
                                    }
                                } else {
                                    label += formatCurrencyForChart(context.parsed.y);
                                }
                                return label;
                            }
                        }
                    },
                    zoom: {
                        zoom: {
                            wheel: {
                                enabled: true
                            },
                            pinch: {
                                enabled: true
                            },
                            mode: 'xy'
                        },
                        pan: {
                            enabled: true,
                            mode: 'xy'
                        }
                    },
                    datalabels: {
                        // 简化数据标签配置，只在年收入上显示
                        display: function(context) {
                            // 只在年收入柱上显示标签，且根据数据量控制密度
                            return context.dataset.label === '年收入' && 
                                  (context.dataset.data.length <= 6 || context.dataIndex % 2 === 0);
                        },
                        formatter: function(value) {
                            return formatCurrencyForChart(value);
                        },
                        color: '#505A66',
                        anchor: 'end',
                        align: 'top',
                        offset: 6,
                        font: {
                            size: 10,
                            weight: '500'
                        },
                        clamp: true
                    }
                },
                scales: {
                    x: {
                        grid: {
                            display: false
                        },
                        ticks: {
                            autoSkip: true,
                            maxRotation: 45,
                            minRotation: 0,
                            padding: 10
                        }
                    },
                    y: {
                        beginAtZero: true,
                        grace: '5%', // 为Y轴添加呼吸空间
                        title: {
                            display: true,
                            text: '收入金额 (¥)'
                        },
                        ticks: {
                            callback: function(value, index, values) {
                                return formatCurrencyForChart(value);
                            }
                        }
                    },
                    y1: {
                        position: 'right',
                        beginAtZero: true,
                        grace: '10%', // 为增长率Y轴添加更多呼吸空间
                        title: {
                            display: true,
                            text: '增长率 (%)'
                        },
                        grid: {
                            drawOnChartArea: false // 不显示右侧Y轴的网格线，避免图表过于复杂
                        }
                    }
                }
            }
        });
    }
    
    /**
     * 初始化收入vs通胀图表
     */
    function initIncomeVsInflationChart() {
        const ctx = document.getElementById('incomeVsInflationChart');
        if (!ctx) return;
        
        // 确保数据存在
        if (!incomeGrowthData || !incomeGrowthData.inflation || incomeGrowthData.inflation.length === 0) {
            displayNoDataMessage(ctx, '暂无收入vs通胀数据');
            return;
        }
        
        const labels = incomeGrowthData.inflation.map(item => item.year);
        const incomeGrowthData2 = incomeGrowthData.inflation.map(item => item.income_growth * 100);
        const inflationData = incomeGrowthData.inflation.map(item => item.inflation * 100);
        const realGrowthData = incomeGrowthData.inflation.map(item => item.real_growth * 100);
        
        new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: '名义收入增长率',
                        data: incomeGrowthData2,
                        backgroundColor: colors.income,
                        order: 2
                    },
                    {
                        label: '通货膨胀率',
                        data: inflationData,
                        backgroundColor: colors.expense,
                        order: 3
                    },
                    {
                        label: '实际收入增长率',
                        data: realGrowthData,
                        type: 'line',
                        borderColor: colors.success,
                        backgroundColor: 'transparent',
                        borderWidth: 2,
                        pointBackgroundColor: colors.success,
                        order: 1
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: '收入增长vs通胀'
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false,
                        callbacks: {
                            label: function(context) {
                                let label = context.dataset.label || '';
                                if (label) {
                                    label += ': ';
                                }
                                label += context.parsed.y.toFixed(1) + '%';
                                return label;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        grid: {
                            display: false
                        }
                    },
                    y: {
                        title: {
                            display: true,
                            text: '百分比 (%)'
                        }
                    }
                }
            }
        });
    }
    
    /**
     * 初始化收支平衡点分析图表
     */
    function initBreakEvenChart() {
        const ctx = document.getElementById('breakEvenAnalysisChart');
        if (!ctx) return;
        
        // 确保数据存在
        if (!breakEvenData || typeof breakEvenData.fixed_expense_ratio === 'undefined' || 
            typeof breakEvenData.variable_expense_ratio === 'undefined') {
            displayNoDataMessage(ctx, '暂无收支平衡数据');
            return;
        }
        
        // 创建固定和变动支出的饼图
        new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['固定支出', '变动支出'],
                datasets: [{
                    data: [
                        breakEvenData.fixed_expense_ratio * 100,
                        breakEvenData.variable_expense_ratio * 100
                    ],
                    backgroundColor: [colors.warning, colors.expense],
                    borderColor: 'white',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: '支出结构分析'
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const value = context.raw;
                                return `${context.label}: ${value.toFixed(1)}%`;
                            }
                        }
                    },
                    datalabels: {
                        formatter: (value) => {
                            return value.toFixed(1) + '%';
                        },
                        color: '#fff',
                        font: {
                            weight: 'bold'
                        },
                        display: function(context) {
                            const total = context.dataset.data.reduce((acc, val) => acc + val, 0);
                            const value = context.dataset.data[context.dataIndex];
                            return (value / total) * 100 >= 5; // 只显示占比5%以上的标签
                        }
                    },
                    subtitle: {
                        display: true,
                        text: `收支平衡点: ¥${breakEvenData.break_even_point.toFixed(2)}`,
                        padding: {
                            top: 10,
                            bottom: 0
                        }
                    }
                }
            }
        });
    }
    
    /**
     * 生成随机颜色数组
     */
    function generateColors(count) {
        const baseColors = [
            '#4663ac', '#ec4c47', '#47b881', '#ffab00', '#1070ca',
            '#735dd0', '#00b8d9', '#ff5630', '#36b37e', '#00a3bf'
        ];
        
        // 如果数量小于基础颜色数量，直接返回部分基础颜色
        if (count <= baseColors.length) {
            return baseColors.slice(0, count);
        }
        
        // 否则生成随机颜色
        const result = [...baseColors];
        
        for (let i = baseColors.length; i < count; i++) {
            const hue = Math.floor(Math.random() * 360);
            const saturation = 70 + Math.floor(Math.random() * 30);
            const lightness = 50 + Math.floor(Math.random() * 10);
            
            result.push(`hsl(${hue}, ${saturation}%, ${lightness}%)`);
        }
        
        return result;
    }

    /**
     * 显示无数据消息
     */
    function displayNoDataMessage(canvas, message) {
        const ctx = canvas.getContext('2d');
        const width = canvas.width;
        const height = canvas.height;
        
        // 清除画布
        ctx.clearRect(0, 0, width, height);
        
        // 设置文本样式
        ctx.font = '14px "Noto Sans SC", sans-serif';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillStyle = '#8492a6';
        
        // 绘制消息
        ctx.fillText(message || '暂无数据', width / 2, height / 2);
    }
} 

// 页面加载完成后初始化图表
document.addEventListener('DOMContentLoaded', function() {
    console.log('初始化收入分析图表...');
    initIncomeAnalysisCharts();
});