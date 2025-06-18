/**
 * 支出分析页面的JavaScript逻辑
 * 负责图表渲染、数据加载和交互功能
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
                    return `支出: ¥${context.parsed.y.toFixed(2)}`;
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
    primary: '--primary-500',
    danger: '--danger-500',
    gradient: {
        start: 'rgba(220, 53, 69, 0.3)',
        end: 'rgba(220, 53, 69, 0.05)'
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
 * 创建支出趋势图表
 */
function createExpenseTrendChart(canvas, data) {
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

    const labels = data.map(item => item.month);
    const amounts = data.map(item => item.expense_amount);

    const chartConfig = {
        ...CHART_CONFIG,
        data: {
            labels: labels,
            datasets: [{
                label: '支出金额',
                data: amounts,
                borderColor: getCSSColor(COLORS.danger),
                backgroundColor: createGradient(ctx),
                borderWidth: DIMENSIONS.borderWidth,
                fill: true,
                tension: 0.4,
                pointBackgroundColor: getCSSColor(COLORS.danger),
                pointBorderColor: COLORS.white,
                pointBorderWidth: DIMENSIONS.pointBorderWidth,
                pointRadius: DIMENSIONS.pointRadius,
                pointHoverRadius: DIMENSIONS.pointHoverRadius
            }]
        }
    };

    // 设置tooltip边框颜色
    chartConfig.plugins.tooltip.borderColor = getCSSColor(COLORS.danger);

    try {
        return new Chart(ctx, chartConfig);
    } catch (error) {
        console.error('Chart.js初始化失败:', error);
        return null;
    }
}

/**
 * 获取支出分析数据
 */
function getExpenseAnalysisData() {
    const dataElement = document.getElementById('expense-analysis-data');
    if (!dataElement) {
        console.warn('未找到支出分析数据元素');
        return { trends: [], overview: {} };
    }

    try {
        const trends = dataElement.dataset.trends ? 
            JSON.parse(dataElement.dataset.trends) : [];
        const overview = dataElement.dataset.overview ? 
            JSON.parse(dataElement.dataset.overview) : {};
        
        return { trends, overview };
    } catch (error) {
        console.error('解析支出分析数据失败:', error);
        return { trends: [], overview: {} };
    }
}

/**
 * 加载支出分析数据
 */
async function loadExpenseAnalysisData() {
    try {
        // 加载概览数据
        const overviewResponse = await fetch('/expense-analysis/api/overview');
        const overviewData = await overviewResponse.json();
        
        // 加载趋势数据
        const trendsResponse = await fetch('/expense-analysis/api/trends?all_history=true');
        const trendsData = await trendsResponse.json();
        
        // 加载模式数据
        const patternsResponse = await fetch('/expense-analysis/api/patterns');
        const patternsData = await patternsResponse.json();
        
        // 加载分类数据
        const categoriesResponse = await fetch('/expense-analysis/api/categories');
        const categoriesData = await categoriesResponse.json();
        
        return {
            overview: overviewData,
            trends: trendsData,
            patterns: patternsData,
            categories: categoriesData
        };
    } catch (error) {
        console.error('加载支出分析数据失败:', error);
        throw error;
    }
}

/**
 * 更新页面数据
 */
function updatePageData(data) {
    // 更新概览卡片
    const totalExpenseElement = document.querySelector('[data-stat="total_expense"]');
    if (totalExpenseElement && data.overview.total_expense !== undefined) {
        totalExpenseElement.textContent = `¥${data.overview.total_expense.toFixed(2)}`;
    }
    
    const expenseCountElement = document.querySelector('[data-stat="expense_count"]');
    if (expenseCountElement && data.overview.expense_count !== undefined) {
        expenseCountElement.textContent = data.overview.expense_count;
    }
    
    const avgMonthlyElement = document.querySelector('[data-stat="avg_monthly_expense"]');
    if (avgMonthlyElement && data.overview.avg_monthly_expense !== undefined) {
        avgMonthlyElement.textContent = `¥${data.overview.avg_monthly_expense.toFixed(2)}`;
    }
    
    // 更新趋势图表
    const canvas = document.getElementById('expenseTrendChart');
    if (canvas && data.trends) {
        // 销毁现有图表
        if (window.expenseTrendChart) {
            window.expenseTrendChart.destroy();
        }
        
        // 创建新图表
        window.expenseTrendChart = createExpenseTrendChart(canvas, data.trends);
    }
    
    // 更新模式分析
    updatePatternsDisplay(data.patterns);
    
    // 更新分类表格
    updateCategoriesTable(data.categories, data.overview.total_expense);
}

/**
 * 更新模式分析显示
 */
function updatePatternsDisplay(patterns) {
    // 更新固定支出
    const fixedContainer = document.getElementById('fixed-expenses-container');
    if (fixedContainer && patterns.fixed_expenses) {
        if (patterns.fixed_expenses.length > 0) {
            const html = patterns.fixed_expenses.slice(0, 5).map(expense => `
                <div class="list-group-item d-flex justify-content-between align-items-center">
                    <div>
                        <h6 class="mb-1">${expense.counterparty}</h6>
                        <small class="text-muted">频率: ${expense.frequency}次</small>
                    </div>
                    <span class="badge bg-primary rounded-pill">¥${expense.amount.toFixed(2)}</span>
                </div>
            `).join('');
            fixedContainer.innerHTML = html;
        } else {
            fixedContainer.innerHTML = `
                <div class="text-center text-muted py-4">
                    <i class="fas fa-info-circle fa-2x mb-2"></i>
                    <p>暂无固定支出模式</p>
                </div>
            `;
        }
    }
    
    // 更新异常支出
    const abnormalContainer = document.getElementById('abnormal-expenses-container');
    if (abnormalContainer && patterns.abnormal_expenses) {
        if (patterns.abnormal_expenses.length > 0) {
            const html = patterns.abnormal_expenses.slice(0, 5).map(expense => `
                <div class="list-group-item">
                    <div class="d-flex justify-content-between align-items-start">
                        <div>
                            <h6 class="mb-1">${expense.counterparty}</h6>
                            <small class="text-muted">${expense.date}</small>
                            ${expense.description ? `<br><small class="text-muted">${expense.description}</small>` : ''}
                        </div>
                        <span class="badge bg-danger">¥${expense.amount.toFixed(2)}</span>
                    </div>
                </div>
            `).join('');
            abnormalContainer.innerHTML = html;
        } else {
            abnormalContainer.innerHTML = `
                <div class="text-center text-muted py-4">
                    <i class="fas fa-check-circle fa-2x mb-2"></i>
                    <p>未发现异常支出</p>
                </div>
            `;
        }
    }
}

/**
 * 更新分类表格
 */
function updateCategoriesTable(categories, totalExpense) {
    const tbody = document.querySelector('#expense-categories-table tbody');
    if (tbody && categories) {
        const html = categories.map((category, index) => {
            const percentage = totalExpense > 0 ? (category.total_amount / totalExpense * 100) : 0;
            return `
                <tr>
                    <td>${index + 1}</td>
                    <td>${category.counterparty}</td>
                    <td class="text-danger">¥${category.total_amount.toFixed(2)}</td>
                    <td>${category.transaction_count}</td>
                    <td>¥${category.avg_amount.toFixed(2)}</td>
                    <td>
                        <div class="progress" style="height: 20px;">
                            <div class="progress-bar bg-danger" 
                                 style="width: ${percentage}%">
                                ${percentage.toFixed(1)}%
                            </div>
                        </div>
                    </td>
                </tr>
            `;
        }).join('');
        tbody.innerHTML = html;
    }
}

/**
 * 显示错误消息
 */
function showErrorMessage(message) {
    // 创建错误提示
    const alertDiv = document.createElement('div');
    alertDiv.className = 'alert alert-danger alert-dismissible fade show';
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    // 插入到页面顶部
    const container = document.querySelector('.page-container');
    if (container) {
        container.insertBefore(alertDiv, container.firstChild);
        
        // 3秒后自动移除
        setTimeout(() => {
            if (alertDiv.parentNode) {
                alertDiv.remove();
            }
        }, 3000);
    }
}

/**
 * 初始化支出分析页面
 */
function initExpenseAnalysis() {
    const canvas = document.getElementById('expenseTrendChart');
    if (!canvas) return; // 不在支出分析页面

    // 获取初始数据
    const data = getExpenseAnalysisData();
    
    // 创建趋势图表
    if (data.trends && data.trends.length > 0) {
        window.expenseTrendChart = createExpenseTrendChart(canvas, data.trends);
    }
    
    // 响应式处理
    window.addEventListener('resize', () => {
        if (window.expenseTrendChart) {
            window.expenseTrendChart.resize();
        }
    });
    
    // 页面卸载时清理
    window.addEventListener('beforeunload', () => {
        if (window.expenseTrendChart) {
            window.expenseTrendChart.destroy();
        }
    });
    
    console.log('支出分析页面初始化完成');
}

// 自动初始化
document.addEventListener('DOMContentLoaded', initExpenseAnalysis); 