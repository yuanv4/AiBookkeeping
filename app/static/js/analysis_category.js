/**
 * 分类洞察页面的JavaScript逻辑
 * 负责分类饼图渲染和交互功能
 */

// 图表配置常量
const PIE_CHART_CONFIG = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
        legend: { 
            display: true,
            position: 'bottom',
            labels: {
                padding: 20,
                usePointStyle: true
            }
        },
        tooltip: {
            backgroundColor: 'rgba(0, 0, 0, 0.8)',
            titleColor: '#ffffff',
            bodyColor: '#ffffff',
            borderWidth: 1,
            callbacks: {
                label: function(context) {
                    const label = context.label || '未分类';
                    const value = context.parsed;
                    const total = context.dataset.data.reduce((a, b) => a + b, 0);
                    const percentage = ((value / total) * 100).toFixed(1);
                    return `${label}: ¥${value.toFixed(2)} (${percentage}%)`;
                }
            }
        }
    }
};

// 颜色配置 - 为不同分类提供丰富的颜色选择
const CATEGORY_COLORS = [
    '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF',
    '#FF9F40', '#FF6384', '#C9CBCF', '#4BC0C0', '#FF6384',
    '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF', '#FF9F40'
];

/**
 * 获取分类数据
 */
function getCategoryData() {
    const dataElement = document.getElementById('category-data');
    if (!dataElement) {
        console.warn('未找到分类数据元素');
        return { 
            categoryBreakdown: [], 
            topCategories: [], 
            totalExpense: 0 
        };
    }

    try {
        const categoryBreakdown = dataElement.dataset.categoryBreakdown ? 
            JSON.parse(dataElement.dataset.categoryBreakdown) : [];
        const topCategories = dataElement.dataset.topCategories ? 
            JSON.parse(dataElement.dataset.topCategories) : [];
        const totalExpense = parseFloat(dataElement.dataset.totalExpense) || 0;
        
        return { categoryBreakdown, topCategories, totalExpense };
    } catch (error) {
        console.error('解析分类数据失败:', error);
        return { 
            categoryBreakdown: [], 
            topCategories: [], 
            totalExpense: 0 
        };
    }
}

/**
 * 创建分类饼图
 */
function createCategoryPieChart(canvas, data) {
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
    const labels = data.categoryBreakdown.map(item => item.name || '未分类');
    const amounts = data.categoryBreakdown.map(item => Math.abs(item.amount || 0));
    const colors = CATEGORY_COLORS.slice(0, labels.length);

    // 如果没有数据，显示占位图表
    if (labels.length === 0) {
        const emptyChartConfig = {
            type: 'doughnut',
            data: {
                labels: ['暂无数据'],
                datasets: [{
                    data: [1],
                    backgroundColor: ['#e9ecef'],
                    borderWidth: 0
                }]
            },
            options: {
                ...PIE_CHART_CONFIG,
                plugins: {
                    ...PIE_CHART_CONFIG.plugins,
                    tooltip: {
                        enabled: false
                    }
                }
            }
        };

        try {
            return new Chart(ctx, emptyChartConfig);
        } catch (error) {
            console.error('空饼图初始化失败:', error);
            return null;
        }
    }

    const chartConfig = {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: amounts,
                backgroundColor: colors,
                borderColor: colors.map(color => color + '80'), // 添加透明度
                borderWidth: 2,
                hoverBorderWidth: 3
            }]
        },
        options: PIE_CHART_CONFIG
    };

    try {
        return new Chart(ctx, chartConfig);
    } catch (error) {
        console.error('分类饼图初始化失败:', error);
        return null;
    }
}

/**
 * 更新排行榜显示
 */
function updateCategoryRanking(data) {
    const rankingElement = document.getElementById('categoryRanking');
    if (!rankingElement) return;

    if (data.topCategories.length === 0) {
        rankingElement.innerHTML = `
            <div class="text-center text-muted py-4">
                <i data-lucide="inbox" class="mb-2"></i>
                <p class="mt-2">暂无分类数据</p>
            </div>
        `;
        // 重新初始化图标
        if (typeof lucide !== 'undefined') {
            lucide.createIcons();
        }
        return;
    }

    const rankingHTML = data.topCategories.map((category, index) => `
        <div class="ranking-item">
            <div class="ranking-number">${index + 1}</div>
            <div class="ranking-content">
                <div class="category-name">${category.name || '未分类'}</div>
                <div class="category-amount">¥${(category.amount || 0).toFixed(2)}</div>
            </div>
        </div>
    `).join('');

    rankingElement.innerHTML = rankingHTML;
}

/**
 * 更新分类数据表格
 */
function updateCategoryTable(data) {
    const tableBody = document.getElementById('categoryTableBody');
    if (!tableBody) return;

    if (data.categoryBreakdown.length === 0) {
        tableBody.innerHTML = `
            <tr>
                <td colspan="4" class="text-center text-muted py-4">暂无数据</td>
            </tr>
        `;
        return;
    }

    const tableHTML = data.categoryBreakdown.map(category => `
        <tr>
            <td>${category.name || '未分类'}</td>
            <td class="text-danger">¥${(category.amount || 0).toFixed(2)}</td>
            <td>${(category.percentage || 0).toFixed(1)}%</td>
            <td>${category.count || 0}</td>
        </tr>
    `).join('');

    tableBody.innerHTML = tableHTML;
}

/**
 * 初始化分类洞察页面
 */
function initCategoryAnalysis() {
    const pieCanvas = document.getElementById('categoryPieChart');
    
    if (!pieCanvas) {
        return; // 不在分类洞察页面
    }

    const data = getCategoryData();
    
    // 创建饼图
    const pieChart = createCategoryPieChart(pieCanvas, data);
    
    // 更新排行榜和表格
    updateCategoryRanking(data);
    updateCategoryTable(data);
    
    if (pieChart) {
        // 响应式处理
        window.addEventListener('resize', () => {
            pieChart.resize();
        });
        
        // 页面卸载时清理
        window.addEventListener('beforeunload', () => {
            pieChart.destroy();
        });
        
        console.log('分类洞察页面初始化完成');
    }
}

// 自动初始化
document.addEventListener('DOMContentLoaded', initCategoryAnalysis); 