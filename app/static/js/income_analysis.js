/**
 * 收入分析页面图表初始化脚本
 */
function initIncomeAnalysisCharts() {
    // 设置图表全局配置
    Chart.defaults.font.family = "'Noto Sans SC', 'sans-serif'";
    Chart.defaults.color = '#505A66';
    Chart.defaults.plugins.tooltip.backgroundColor = 'rgba(25, 30, 56, 0.9)';
    Chart.defaults.plugins.tooltip.padding = 10;
    Chart.defaults.plugins.tooltip.cornerRadius = 3;
    Chart.defaults.plugins.legend.position = 'top';
    
    // 定义常用颜色
    const colors = {
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
                plugins: {
                    title: {
                        display: true,
                        text: '月度收支与储蓄率趋势'
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
                                    label += '¥' + context.parsed.y.toFixed(2);
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
                    }
                },
                scales: {
                    x: {
                        stacked: false,
                        grid: {
                            display: false
                        }
                    },
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: '金额 (¥)'
                        }
                    },
                    y1: {
                        position: 'right',
                        beginAtZero: true,
                        max: 100,
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
                        text: '月度收入波动分析'
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
                                label += '¥' + context.parsed.y.toFixed(2);
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
                    }
                },
                scales: {
                    x: {
                        grid: {
                            display: false
                        }
                    },
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: '收入金额 (¥)'
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
                                return `¥${value.toFixed(2)} (${percentage}%)`;
                            }
                        }
                    },
                    datalabels: {
                        formatter: (value, ctx) => {
                            const total = ctx.dataset.data.reduce((acc, val) => acc + val, 0);
                            const percentage = ((value / total) * 100).toFixed(1);
                            return percentage + '%';
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
        
        const labels = monthlySourcesData.map(item => item.month);
        const data = monthlySourcesData.map(item => item.source_count);
        
        new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: '收入来源数量',
                    data: data,
                    backgroundColor: colors.info,
                    borderColor: colors.info,
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: '月度收入来源数量'
                    }
                },
                scales: {
                    x: {
                        grid: {
                            display: false
                        }
                    },
                    y: {
                        beginAtZero: true,
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
                        tension: 0.4
                    },
                    {
                        label: '收入',
                        data: incomeData,
                        borderColor: colors.income,
                        borderWidth: 2,
                        pointRadius: 3,
                        fill: false
                    },
                    {
                        label: '支出',
                        data: expenseData.map(v => Math.abs(v)), // 取绝对值显示
                        borderColor: colors.expense,
                        borderWidth: 2,
                        pointRadius: 3,
                        fill: false
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: '月度现金流趋势'
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
                                label += '¥' + context.parsed.y.toFixed(2);
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
                            text: '金额 (¥)'
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
                        text: '年度收入增长趋势'
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
                                    label += '¥' + context.parsed.y.toFixed(2);
                                }
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
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: '收入金额 (¥)'
                        }
                    },
                    y1: {
                        position: 'right',
                        title: {
                            display: true,
                            text: '增长率 (%)'
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
        
        if (!incomeGrowthData.inflation || incomeGrowthData.inflation.length === 0) return;
        
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
} 