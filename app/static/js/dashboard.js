/**
 * 仪表盘页面JavaScript
 * 提供数据图表初始化和交互功能
 */

document.addEventListener('DOMContentLoaded', function() {
    // 初始化动态样式
    applyDynamicStyles();

    // 初始化所有图表
    initializeCharts();
    
    // 添加其他交互功能
    initializeInteractions();
});

/**
 * 应用动态样式，代替HTML中的内联样式模板
 */
function applyDynamicStyles() {
    // 处理净收支图标样式
    const netAmount = parseFloat(document.getElementById('netAmount')?.textContent || '0');
    const netIcon = document.getElementById('netIcon');
    const netIconInner = document.getElementById('netIconInner');
    
    if (netIcon && netIconInner) {
        netIcon.style.backgroundColor = netAmount >= 0 ? 'rgba(71, 184, 129, 0.1)' : 'rgba(236, 76, 71, 0.1)';
        netIconInner.style.color = netAmount >= 0 ? 'var(--success)' : 'var(--danger)';
    }
    
    // 处理净现金流图标样式
    const cashFlowValue = document.getElementById('cashFlowValue');
    const cashFlowIcon = document.getElementById('cashFlowIcon');
    const cashFlowIconInner = document.getElementById('cashFlowIconInner');
    
    if (cashFlowValue && cashFlowIcon && cashFlowIconInner) {
        const cashFlowAmount = parseFloat(cashFlowValue.textContent || '0');
        cashFlowIcon.style.backgroundColor = cashFlowAmount >= 0 ? 'rgba(71, 184, 129, 0.1)' : 'rgba(236, 76, 71, 0.1)';
        cashFlowIconInner.style.color = cashFlowAmount >= 0 ? 'var(--success)' : 'var(--danger)';
    }
    
    // 处理储蓄率进度条样式
    const savingsRate = parseFloat(document.getElementById('savingsRate')?.textContent || '0');
    const savingsRateBar = document.getElementById('savingsRateBar');
    
    if (savingsRateBar) {
        // 设置宽度
        savingsRateBar.style.width = `${Math.min(savingsRate, 100)}%`;
        
        // 设置颜色类
        savingsRateBar.className = 'progress-bar';
        if (savingsRate >= 20) {
            savingsRateBar.classList.add('bg-success');
        } else if (savingsRate >= 10) {
            savingsRateBar.classList.add('bg-primary');
        } else if (savingsRate > 0) {
            savingsRateBar.classList.add('bg-warning');
        } else {
            savingsRateBar.classList.add('bg-danger');
        }
    }
}

/**
 * 初始化所有图表
 */
function initializeCharts() {
    // 初始化资金余额趋势图
    initBalanceHistoryChart();
}

/**
 * 初始化交互功能
 */
function initializeInteractions() {
    // 获取所有时间范围选择按钮
    const timeRangeButtons = document.querySelectorAll('[data-time-range]');
    if (timeRangeButtons.length > 0) {
        timeRangeButtons.forEach(btn => {
            btn.addEventListener('click', function() {
                // 移除所有按钮的活动状态
                timeRangeButtons.forEach(b => b.classList.remove('active'));
                
                // 添加当前按钮的活动状态
                this.classList.add('active');
                
                // 获取时间范围值
                const timeRange = this.getAttribute('data-time-range');
                
                // 跳转到新的URL
                window.location.href = `?time_range=${timeRange}`;
            });
        });
    }
    
    // 交易记录的过滤下拉框
    const transactionTypeFilter = document.getElementById('transactionTypeFilter');
    if (transactionTypeFilter) {
        // 初始化时应用当前选中的筛选条件
        filterTransactions(transactionTypeFilter.value);
        
        transactionTypeFilter.addEventListener('change', function() {
            filterTransactions(this.value);
        });
    }
    
    // 重置筛选条件按钮
    const resetFilterBtn = document.getElementById('reset-filter');
    if (resetFilterBtn) {
        resetFilterBtn.addEventListener('click', function() {
            const transactionTypeFilter = document.getElementById('transactionTypeFilter');
            if (transactionTypeFilter) {
                transactionTypeFilter.value = 'all';
                filterTransactions('all');
            }
        });
    }
}

/** * 过滤交易记录 */
function filterTransactions(filterType) {
    console.log('开始过滤交易记录，类型:', filterType);
    
    // 根据选择的类型过滤交易记录表
    const table = document.querySelector('.table');
    if (!table) {
        console.error('未找到表格元素');
        return;
    }
    
    const tableBody = table.querySelector('tbody');
    const rows = table.querySelectorAll('tbody tr');
    const noDataElement = document.getElementById('no-data');
    
    console.log('找到表格元素:', table);
    console.log('找到表格主体:', tableBody ? '是' : '否');
    console.log('找到行数:', rows.length);
    console.log('找到无数据提示元素:', noDataElement ? '是' : '否');
    
    // 默认状态：隐藏无数据提示，显示表格
    if (noDataElement) {
        noDataElement.style.display = 'none';
        // 确保不受其他CSS影响
        noDataElement.style.setProperty('display', 'none', 'important');
    }
    
    // 先显示表格主体
    if (tableBody) {
        tableBody.style.display = 'table-row-group';
    }
    
    let visibleRows = 0;
    
    rows.forEach((row, index) => {
        const typeCell = row.querySelector('td:nth-child(3)');
        if (!typeCell) {
            console.warn(`第${index+1}行没有找到类型单元格`);
            return;
        }
        
        const typeText = typeCell.textContent.trim().toLowerCase();
        let isVisible = false;
        
        switch(filterType) {
            case 'income':
                // 同时匹配英文和中文关键词
                isVisible = typeText.includes('income') || 
                           typeText.includes('refund') ||
                           typeText.includes('收入') || 
                           typeText.includes('退款') ||
                           typeText.includes('收款');
                break;
            case 'expense':
                // 同时匹配英文和中文关键词
                isVisible = typeText.includes('expense') || 
                           typeText.includes('payment') ||
                           typeText.includes('支出') || 
                           typeText.includes('消费') ||
                           typeText.includes('付款');
                break;
            default: // 'all'
                isVisible = true;
                break;
        }
        
        // 设置行的可见性
        row.style.display = isVisible ? 'table-row' : 'none';
        
        // 计算可见行数
        if (isVisible) {
            visibleRows++;
        }
    });
    
    console.log('过滤后可见行数:', visibleRows);
    
    // 根据可见行数决定是否显示"无数据"提示
    if (noDataElement) {
        if (visibleRows === 0) {
            // 没有可见行，显示"无数据"提示，隐藏表格主体
            console.log('没有匹配的行，显示无数据提示');
            noDataElement.style.setProperty('display', 'flex', 'important');
            if (tableBody) {
                tableBody.style.display = 'none';
            }
        } else {
            // 有可见行，隐藏"无数据"提示，显示表格主体
            console.log('有匹配的行，隐藏无数据提示');
            noDataElement.style.setProperty('display', 'none', 'important');
            if (tableBody) {
                tableBody.style.display = 'table-row-group';
            }
        }
    }
    
    // 检查最终状态
    console.log('过滤完成，表格主体显示状态:', tableBody ? tableBody.style.display : 'N/A');
    console.log('过滤完成，无数据提示显示状态:', noDataElement ? noDataElement.style.display : 'N/A');
}

/**
 * 初始化资金余额趋势图
 */
function initBalanceHistoryChart() {
    const balanceHistoryCanvas = document.getElementById('balanceHistoryChart');
    if (!balanceHistoryCanvas) return;
    
    try {
        // 从隐藏元素中获取数据
        const chartDataElement = document.getElementById('balance-history-data');
        if (!chartDataElement) return;
        
        const chartData = JSON.parse(chartDataElement.getAttribute('data-chart'));
        if (!chartData || !chartData.labels || !chartData.values) return;
        
        new Chart(balanceHistoryCanvas, {
            type: 'line',
            data: {
                labels: chartData.labels,
                datasets: [{
                    label: '账户余额',
                    data: chartData.values,
                    borderColor: '#4663ac',
                    backgroundColor: 'rgba(70, 99, 172, 0.1)',
                    borderWidth: 2,
                    pointRadius: 3,
                    pointBackgroundColor: '#4663ac',
                    tension: 0.4,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: false,
                        grid: {
                            display: true,
                            color: 'rgba(0,0,0,0.05)'
                        }
                    },
                    x: {
                        grid: {
                            display: false
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        backgroundColor: 'rgba(0,0,0,0.7)',
                        padding: 10,
                        cornerRadius: 4,
                        callbacks: {
                            label: function(context) {
                                return `余额: ${context.raw.toFixed(2)}`;
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
    } catch (error) {
        console.error('初始化余额趋势图失败:', error);
    }
}

/**
 * 初始化收支对比图
 */
function initIncomeExpenseChart() {
    const incomeExpenseCanvas = document.getElementById('incomeExpenseChart');
    if (!incomeExpenseCanvas) return;
    
    try {
        // 从隐藏元素中获取数据
        const chartDataElement = document.getElementById('income-expense-data');
        if (!chartDataElement) return;
        
        const chartData = JSON.parse(chartDataElement.getAttribute('data-chart'));
        if (!chartData || !chartData.labels || !chartData.income || !chartData.expense) return;
        
        new Chart(incomeExpenseCanvas, {
            type: 'bar',
            data: {
                labels: chartData.labels,
                datasets: [
                    {
                        label: '收入',
                        data: chartData.income,
                        backgroundColor: 'rgba(71, 184, 129, 0.7)',
                        borderColor: 'rgba(71, 184, 129, 1)',
                        borderWidth: 1
                    },
                    {
                        label: '支出',
                        data: chartData.expense.map(val => Math.abs(val)), // 取绝对值，使支出显示为正数
                        backgroundColor: 'rgba(236, 76, 71, 0.7)',
                        borderColor: 'rgba(236, 76, 71, 1)',
                        borderWidth: 1
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: {
                            display: true,
                            color: 'rgba(0,0,0,0.05)'
                        }
                    },
                    x: {
                        grid: {
                            display: false
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: true,
                        position: 'top'
                    },
                    tooltip: {
                        backgroundColor: 'rgba(0,0,0,0.7)',
                        padding: 10,
                        cornerRadius: 4,
                        callbacks: {
                            label: function(context) {
                                const label = context.dataset.label || '';
                                const value = context.raw.toFixed(2);
                                return `${label}: ${value}`;
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
    } catch (error) {
        console.error('初始化收支对比图失败:', error);
    }
}

/**
 * 初始化收入来源图
 */
function initIncomeSourceChart() {
    const incomeSourceCanvas = document.getElementById('incomeSourceChart');
    if (!incomeSourceCanvas) return;
    
    try {
        // 从隐藏元素中获取数据
        const chartDataElement = document.getElementById('income-source-data');
        if (!chartDataElement) return;
        
        const chartData = JSON.parse(chartDataElement.getAttribute('data-chart'));
        if (!chartData || !chartData.labels || !chartData.values) return;
        
        // 生成随机颜色数组，但收入相关的颜色应该是绿色系
        const backgroundColors = chartData.labels.map(() => {
            // 绿色系随机颜色
            const r = Math.floor(Math.random() * 100) + 50;
            const g = Math.floor(Math.random() * 100) + 150;
            const b = Math.floor(Math.random() * 100) + 50;
            return `rgba(${r}, ${g}, ${b}, 0.7)`;
        });
        
        new Chart(incomeSourceCanvas, {
            type: 'doughnut',
            data: {
                labels: chartData.labels,
                datasets: [{
                    data: chartData.values,
                    backgroundColor: backgroundColors,
                    borderColor: 'rgba(255, 255, 255, 0.8)',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: true,
                        position: 'bottom',
                        labels: {
                            boxWidth: 15,
                            padding: 10
                        }
                    },
                    tooltip: {
                        backgroundColor: 'rgba(0,0,0,0.7)',
                        padding: 10,
                        cornerRadius: 4,
                        callbacks: {
                            label: function(context) {
                                const label = context.label || '';
                                const value = context.raw.toFixed(2);
                                const total = context.chart.data.datasets[0].data.reduce((a, b) => a + b, 0);
                                const percentage = Math.round((context.raw / total) * 100);
                                return `${label}: ${value} (${percentage}%)`;
                            }
                        }
                    }
                }
            }
        });
    } catch (error) {
        console.error('初始化收入来源图失败:', error);
    }
}

/**
 * 初始化支出类别图
 */
function initExpenseCategoryChart() {
    const expenseCategoryCanvas = document.getElementById('expenseCategoryChart');
    if (!expenseCategoryCanvas) return;
    
    try {
        // 从隐藏元素中获取数据
        const chartDataElement = document.getElementById('expense-category-data');
        if (!chartDataElement) return;
        
        const chartData = JSON.parse(chartDataElement.getAttribute('data-chart'));
        if (!chartData || !chartData.labels || !chartData.values) return;
        
        // 生成随机颜色数组，但支出相关的颜色应该是红色系
        const backgroundColors = chartData.labels.map(() => {
            // 红色系随机颜色
            const r = Math.floor(Math.random() * 100) + 150;
            const g = Math.floor(Math.random() * 100) + 50;
            const b = Math.floor(Math.random() * 100) + 50;
            return `rgba(${r}, ${g}, ${b}, 0.7)`;
        });
        
        new Chart(expenseCategoryCanvas, {
            type: 'doughnut',
            data: {
                labels: chartData.labels,
                datasets: [{
                    data: chartData.values.map(val => Math.abs(val)), // 取绝对值，使支出显示为正数
                    backgroundColor: backgroundColors,
                    borderColor: 'rgba(255, 255, 255, 0.8)',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: true,
                        position: 'bottom',
                        labels: {
                            boxWidth: 15,
                            padding: 10
                        }
                    },
                    tooltip: {
                        backgroundColor: 'rgba(0,0,0,0.7)',
                        padding: 10,
                        cornerRadius: 4,
                        callbacks: {
                            label: function(context) {
                                const label = context.label || '';
                                const value = context.raw.toFixed(2);
                                const total = context.chart.data.datasets[0].data.reduce((a, b) => a + b, 0);
                                const percentage = Math.round((context.raw / total) * 100);
                                return `${label}: ${value} (${percentage}%)`;
                            }
                        }
                    }
                }
            }
        });
    } catch (error) {
        console.error('初始化支出类别图失败:', error);
    }
}

/**
 * 初始化月度趋势图
 */
function initMonthlyTrendChart() {
    const monthlyTrendCanvas = document.getElementById('monthlyTrendChart');
    if (!monthlyTrendCanvas) return;
    
    try {
        // 从隐藏元素中获取数据
        const chartDataElement = document.getElementById('monthly-trend-data');
        if (!chartDataElement) return;
        
        const chartData = JSON.parse(chartDataElement.getAttribute('data-chart'));
        if (!chartData || !chartData.labels || !chartData.income || !chartData.expense || !chartData.net) return;
        
        new Chart(monthlyTrendCanvas, {
            type: 'line',
            data: {
                labels: chartData.labels,
                datasets: [
                    {
                        label: '净收支',
                        data: chartData.net,
                        borderColor: '#4663ac',
                        backgroundColor: 'rgba(70, 99, 172, 0.1)',
                        borderWidth: 2,
                        pointRadius: 3,
                        pointBackgroundColor: '#4663ac',
                        tension: 0.4,
                        fill: false
                    },
                    {
                        label: '收入',
                        data: chartData.income,
                        borderColor: 'rgba(71, 184, 129, 1)',
                        backgroundColor: 'rgba(71, 184, 129, 0.1)',
                        borderWidth: 2,
                        pointRadius: 3,
                        pointBackgroundColor: 'rgba(71, 184, 129, 1)',
                        tension: 0.4,
                        fill: false
                    },
                    {
                        label: '支出',
                        data: chartData.expense.map(val => Math.abs(val)), // 取绝对值，使支出显示为正数
                        borderColor: 'rgba(236, 76, 71, 1)',
                        backgroundColor: 'rgba(236, 76, 71, 0.1)',
                        borderWidth: 2,
                        pointRadius: 3,
                        pointBackgroundColor: 'rgba(236, 76, 71, 1)',
                        tension: 0.4,
                        fill: false
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: false,
                        grid: {
                            display: true,
                            color: 'rgba(0,0,0,0.05)'
                        }
                    },
                    x: {
                        grid: {
                            display: false
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: true,
                        position: 'top'
                    },
                    tooltip: {
                        backgroundColor: 'rgba(0,0,0,0.7)',
                        padding: 10,
                        cornerRadius: 4,
                        callbacks: {
                            label: function(context) {
                                const label = context.dataset.label || '';
                                const value = context.raw.toFixed(2);
                                return `${label}: ${value}`;
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
    } catch (error) {
        console.error('初始化月度趋势图失败:', error);
    }
} 