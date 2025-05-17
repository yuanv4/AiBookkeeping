/**
 * 时间分析页面JavaScript
 * 提供按周、月、年的交易数据分析图表功能
 */

// 切换到月度标签并设置年份筛选
function switchToMonthlyTab(year) {
    // 保存年份到localStorage
    localStorage.setItem('selectedYearFilter', year);
    
    // 切换到月度标签
    const monthlyTab = document.getElementById('monthly-tab');
    if (monthlyTab) {
        const bsTab = new bootstrap.Tab(monthlyTab);
        bsTab.show();
    }
}

// 从HTML元素中读取图表数据
function getChartDataFromElement(elementId) {
    const element = document.getElementById(elementId);
    if (!element) return null;
    
    // 获取dataset属性
    const data = element.dataset;
    
    // 解析JSON数据
    const chartData = {};
    for (const key in data) {
        try {
            chartData[key] = JSON.parse(data[key]);
        } catch (e) {
            console.error(`无法解析${elementId}的${key}数据`, e);
            chartData[key] = [];
        }
    }
    
    return chartData;
}

// 初始化周分析图表
function initWeekdayChart() {
    const weekdayData = getChartDataFromElement('weekday-data');
    if (!document.getElementById('weekdayChart') || !weekdayData) return;
    
    const weekdayCtx = document.getElementById('weekdayChart').getContext('2d');
    
    // 周分析数据集
    const weekdayDatasets = [
        {
            label: '消费金额(元)',
            data: weekdayData.total,
            backgroundColor: app.colors.primary,
            borderColor: app.colors.primary,
            borderWidth: 1,
            order: 1
        },
        {
            label: '交易笔数',
            data: weekdayData.count,
            backgroundColor: app.colors.warning,
            borderColor: app.colors.warning,
            borderWidth: 1,
            order: 2,
            hidden: true
        },
        {
            label: '平均值(元/笔)',
            data: weekdayData.average,
            backgroundColor: app.colors.success,
            borderColor: app.colors.success,
            borderWidth: 1,
            order: 3,
            hidden: true
        }
    ];
    
    // 周分析图表特定配置
    const weekdayOptions = {
        scales: {
            x: {
                grid: {
                    display: false
                },
                ticks: {
                    font: {
                        family: app.chartConfig.fontFamily,
                        size: app.chartConfig.fontSize
                    }
                }
            },
            y: {
                beginAtZero: true,
                ticks: {
                    font: {
                        family: app.chartConfig.fontFamily,
                        size: app.chartConfig.fontSize
                    },
                    callback: function(value) {
                        return app.formatCurrency(value, 0);
                    }
                },
                title: {
                    display: true,
                    text: '金额 (元)',
                    font: {
                        family: app.chartConfig.fontFamily,
                        size: app.chartConfig.fontSize
                    }
                }
            }
        },
        plugins: {
            legend: {
                onClick: function(e, legendItem, legend) {
                    const index = legendItem.datasetIndex;
                    const ci = legend.chart;
                    const meta = ci.getDatasetMeta(index);
                    
                    // 更新数据集的可见性
                    meta.hidden = meta.hidden === null ? !ci.data.datasets[index].hidden : null;
                    
                    // 更新图表
                    ci.update();
                    
                    // 更新按钮状态
                    app.updateButtonStates(ci, '.toggle-dataset');
                }
            }
        }
    };
    
    // 创建周分析图表
    const weekdayChart = app.createChart(
        weekdayCtx, 
        'bar', 
        weekdayData.labels, 
        weekdayDatasets, 
        weekdayOptions
    );
    
    // 处理周分析图表切换按钮
    document.querySelectorAll('.toggle-dataset').forEach(button => {
        button.addEventListener('click', function() {
            const datasetIndex = parseInt(this.getAttribute('data-dataset'));
            const meta = weekdayChart.getDatasetMeta(datasetIndex);
            // 切换数据集可见性
            meta.hidden = !meta.hidden;
            weekdayChart.update();
            // 更新按钮状态
            app.updateButtonStates(weekdayChart, '.toggle-dataset');
        });
    });
    
    // 初始化周分析图表按钮状态
    app.updateButtonStates(weekdayChart, '.toggle-dataset');
}

// 初始化月度分析图表
function initMonthlyChart() {
    const monthlyData = getChartDataFromElement('monthly-data');
    if (!document.getElementById('monthlyChart') || !monthlyData) return;
    
    const monthlyCtx = document.getElementById('monthlyChart').getContext('2d');
    
    // 月度数据集
    const monthlyDatasets = [
        {
            label: '收入',
            data: monthlyData.income,
            backgroundColor: app.colors.success,
            borderColor: app.colors.success,
            borderWidth: 1,
            order: 1
        },
        {
            label: '支出',
            data: monthlyData.expense,
            backgroundColor: app.colors.danger,
            borderColor: app.colors.danger,
            borderWidth: 1,
            order: 2
        },
        {
            label: '净额',
            data: monthlyData.net,
            type: 'line',
            fill: false,
            borderColor: app.colors.primary,
            backgroundColor: app.colors.primary,
            pointBorderColor: app.colors.primary,
            pointBackgroundColor: '#fff',
            pointRadius: app.chartConfig.point.radius,
            pointHoverRadius: app.chartConfig.point.hoverRadius,
            borderWidth: 2,
            order: 0
        }
    ];
    
    // 月度图表特定配置
    const monthlyOptions = {
        scales: {
            x: {
                grid: {
                    display: false
                },
                ticks: {
                    font: {
                        family: app.chartConfig.fontFamily,
                        size: app.chartConfig.fontSize
                    }
                }
            },
            y: {
                beginAtZero: false,
                ticks: {
                    font: {
                        family: app.chartConfig.fontFamily,
                        size: app.chartConfig.fontSize
                    },
                    callback: function(value) {
                        return app.formatCurrency(value, 0);
                    }
                },
                title: {
                    display: true,
                    text: '金额 (元)',
                    font: {
                        family: app.chartConfig.fontFamily,
                        size: app.chartConfig.fontSize
                    }
                }
            }
        },
        plugins: {
            legend: {
                onClick: function(e, legendItem, legend) {
                    const index = legendItem.datasetIndex;
                    const ci = legend.chart;
                    const meta = ci.getDatasetMeta(index);
                    
                    // 更新数据集的可见性
                    meta.hidden = meta.hidden === null ? !ci.data.datasets[index].hidden : null;
                    
                    // 更新图表
                    ci.update();
                    
                    // 更新按钮状态
                    app.updateButtonStates(ci, '.monthly-toggle-dataset');
                }
            }
        }
    };
    
    // 创建月度图表
    const monthlyChart = app.createChart(
        monthlyCtx, 
        'bar', 
        monthlyData.labels, 
        monthlyDatasets, 
        monthlyOptions
    );
    
    // 处理月度图表切换按钮
    document.querySelectorAll('.monthly-toggle-dataset').forEach(button => {
        button.addEventListener('click', function() {
            const datasetIndex = parseInt(this.getAttribute('data-dataset'));
            const meta = monthlyChart.getDatasetMeta(datasetIndex);
            // 切换数据集可见性
            meta.hidden = !meta.hidden;
            monthlyChart.update();
            // 更新按钮状态
            app.updateButtonStates(monthlyChart, '.monthly-toggle-dataset');
        });
    });
    
    // 初始化月度图表按钮状态
    app.updateButtonStates(monthlyChart, '.monthly-toggle-dataset');
}

// 初始化年度分析图表
function initYearlyChart() {
    const yearlyData = getChartDataFromElement('yearly-data');
    if (!document.getElementById('yearlyChart') || !yearlyData) return;
    
    const yearlyCtx = document.getElementById('yearlyChart').getContext('2d');
    
    // 年度数据集
    const yearlyDatasets = [
        {
            label: '收入',
            data: yearlyData.income,
            backgroundColor: app.colors.success,
            borderColor: app.colors.success,
            borderWidth: 1,
            order: 1
        },
        {
            label: '支出',
            data: yearlyData.expense,
            backgroundColor: app.colors.danger,
            borderColor: app.colors.danger,
            borderWidth: 1,
            order: 2
        },
        {
            label: '净额',
            data: yearlyData.net,
            type: 'line',
            fill: false,
            borderColor: app.colors.primary,
            backgroundColor: app.colors.primary,
            pointBorderColor: app.colors.primary,
            pointBackgroundColor: '#fff',
            pointRadius: app.chartConfig.point.radius,
            pointHoverRadius: app.chartConfig.point.hoverRadius,
            borderWidth: 2,
            order: 0
        }
    ];
    
    // 年度图表特定配置
    const yearlyOptions = {
        scales: {
            x: {
                grid: {
                    display: false
                },
                ticks: {
                    font: {
                        family: app.chartConfig.fontFamily,
                        size: app.chartConfig.fontSize
                    }
                }
            },
            y: {
                beginAtZero: true,
                ticks: {
                    font: {
                        family: app.chartConfig.fontFamily,
                        size: app.chartConfig.fontSize
                    },
                    callback: function(value) {
                        return app.formatCurrency(value, 0);
                    }
                },
                title: {
                    display: true,
                    text: '金额 (元)',
                    font: {
                        family: app.chartConfig.fontFamily,
                        size: app.chartConfig.fontSize
                    }
                }
            }
        },
        plugins: {
            legend: {
                onClick: function(e, legendItem, legend) {
                    const index = legendItem.datasetIndex;
                    const ci = legend.chart;
                    const meta = ci.getDatasetMeta(index);
                    
                    // 更新数据集的可见性
                    meta.hidden = meta.hidden === null ? !ci.data.datasets[index].hidden : null;
                    
                    // 更新图表
                    ci.update();
                    
                    // 更新按钮状态
                    app.updateButtonStates(ci, '.yearly-toggle-dataset');
                }
            }
        }
    };
    
    // 创建年度图表
    const yearlyChart = app.createChart(
        yearlyCtx, 
        'bar', 
        yearlyData.labels, 
        yearlyDatasets, 
        yearlyOptions
    );
    
    // 处理年度图表切换按钮
    document.querySelectorAll('.yearly-toggle-dataset').forEach(button => {
        button.addEventListener('click', function() {
            const datasetIndex = parseInt(this.getAttribute('data-dataset'));
            const meta = yearlyChart.getDatasetMeta(datasetIndex);
            // 切换数据集可见性
            meta.hidden = !meta.hidden;
            yearlyChart.update();
            // 更新按钮状态
            app.updateButtonStates(yearlyChart, '.yearly-toggle-dataset');
        });
    });
    
    // 初始化年度图表按钮状态
    app.updateButtonStates(yearlyChart, '.yearly-toggle-dataset');
}

// 文档加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    // 进度条初始化
    document.querySelectorAll('.progress-bar[data-width]').forEach(progressBar => {
        const width = progressBar.getAttribute('data-width');
        progressBar.style.width = width + '%';
    });
    
    // 检查本地存储中是否有保存的选项卡
    const activeTab = localStorage.getItem('activeTimeAnalysisTab');
    if (activeTab) {
        // 激活保存的选项卡
        const tab = document.querySelector(activeTab);
        if (tab) {
            const bsTab = new bootstrap.Tab(tab);
            bsTab.show();
        }
    }
    
    // 为选项卡添加事件监听器，保存选择的选项卡
    const tabs = document.querySelectorAll('button[data-bs-toggle="tab"]');
    tabs.forEach(tab => {
        tab.addEventListener('shown.bs.tab', function(event) {
            localStorage.setItem('activeTimeAnalysisTab', '#' + event.target.id);
        });
    });
    
    // 检查是否有年份筛选参数
    if (localStorage.getItem('selectedYearFilter')) {
        const year = localStorage.getItem('selectedYearFilter');
        // 在月度标签内处理年份筛选
        if (activeTab === '#monthly-tab') {
            // 重定向到带有年份筛选的URL
            window.location.href = `/time_analysis?year=${year}`;
        }
        // 清除localStorage中的年份筛选
        localStorage.removeItem('selectedYearFilter');
    }
    
    // 初始化图表
    initWeekdayChart();
    initMonthlyChart();
    initYearlyChart();
    
    // 如果周分析数据为空，但其他数据不为空，自动切换到有数据的选项卡
    const hasWeekdayData = !!document.getElementById('weekday-data');
    const hasMonthlyData = !!document.getElementById('monthly-data');
    const hasYearlyData = !!document.getElementById('yearly-data');
    
    if (!hasWeekdayData && (hasMonthlyData || hasYearlyData)) {
        if (hasMonthlyData) {
            document.getElementById('monthly-tab').click();
        } else if (hasYearlyData) {
            document.getElementById('yearly-tab').click();
        }
    }
}); 