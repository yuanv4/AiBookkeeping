/**
 * 共用JavaScript功能
 * 包含所有页面共享的功能
 */

// 图表默认配置
function setupChartDefaults() {
    if (typeof Chart !== 'undefined') {
        // 配置图表主题样式
        Chart.defaults.color = '#334152';
        Chart.defaults.font.family = "'Noto Sans SC', sans-serif";
        Chart.defaults.elements.line.borderWidth = 2;
        Chart.defaults.elements.point.radius = 3;
        Chart.defaults.elements.point.hoverRadius = 5;
        
        // 注册Chart.js插件
        if (typeof ChartDataLabels !== 'undefined') {
            Chart.register(ChartDataLabels);
        }
    }
}

// 颜色配置
const colorPalette = {
    primary: '#4663ac',
    success: '#47b881',
    danger: '#ec4c47',
    warning: '#ffab00',
    info: '#1070ca',
    neutral: ['#4663ac', '#6c84ca', '#8ea2d8', '#b0bfe5', '#d2dcf3'],
    category: ['#4663ac', '#47b881', '#ec4c47', '#f7d154', '#1070ca', '#9c36b5', '#00bcd4', '#ff9800']
};

// 统一图表配置
const chartConfig = {
    // 全局字体设置
    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
    fontSize: 12,
    
    // 统一图表外观
    aspectRatio: 2.5,  // 宽高比
    responsive: true,
    maintainAspectRatio: false,
    
    // 全局动画设置
    animation: {
        duration: 1000,
        easing: 'easeOutQuart'
    },
    
    // 布局内边距
    padding: {
        top: 15,
        right: 25,
        bottom: 15,
        left: 15
    },
    
    // 图例设置
    legend: {
        position: 'top',
        align: 'center',
        labels: {
            boxWidth: 12,
            padding: 15,
            font: {
                family: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
                size: 12
            }
        }
    },
    
    // 数据点样式
    point: {
        radius: 4,
        hoverRadius: 6
    },
    
    // 工具提示样式
    tooltip: {
        cornerRadius: 4,
        caretSize: 6,
        caretPadding: 8,
        displayColors: true,
        titleFont: {
            size: 13,
            weight: 'bold'
        },
        bodyFont: {
            size: 12
        },
        callbacks: {
            label: function(context) {
                let label = context.dataset.label || '';
                if (label) {
                    label += ': ';
                }
                if (context.parsed.y !== null) {
                    label += new Intl.NumberFormat('zh-CN', { 
                        minimumFractionDigits: 2,
                        maximumFractionDigits: 2
                    }).format(context.parsed.y);
                }
                return label;
            }
        }
    }
};

// 通用图表创建函数
function createChart(ctx, type, labels, datasets, customOptions = {}) {
    // 默认选项
    const defaultOptions = {
        responsive: true,
        maintainAspectRatio: false,
        layout: {
            padding: {
                top: chartConfig.padding.top,
                right: chartConfig.padding.right,
                bottom: chartConfig.padding.bottom,
                left: chartConfig.padding.left
            }
        },
        plugins: {
            legend: {
                position: chartConfig.legend.position,
                align: chartConfig.legend.align,
                labels: chartConfig.legend.labels
            },
            tooltip: {
                mode: 'index',
                intersect: false,
                backgroundColor: 'rgba(0, 0, 0, 0.75)',
                titleColor: '#fff',
                bodyColor: '#fff',
                cornerRadius: chartConfig.tooltip.cornerRadius,
                callbacks: chartConfig.tooltip.callbacks
            }
        },
        animation: chartConfig.animation,
        interaction: {
            mode: 'index',
            intersect: false
        }
    };
    
    // 合并选项
    const options = {...defaultOptions, ...customOptions};
    
    // 创建图表
    return new Chart(ctx, {
        type: type,
        data: {
            labels: labels,
            datasets: datasets
        },
        options: options
    });
}

// 通用按钮状态更新函数
function updateButtonStates(chart, selector) {
    document.querySelectorAll(selector).forEach(button => {
        const datasetIndex = parseInt(button.getAttribute('data-dataset'));
        const meta = chart.getDatasetMeta(datasetIndex);
        
        if (meta.hidden) {
            if (selector === '.toggle-dataset') {
                button.classList.remove('btn-primary', 'btn-warning', 'btn-success');
                button.classList.add('btn-outline-' + (datasetIndex === 0 ? 'primary' : datasetIndex === 1 ? 'warning' : 'success'));
            } else {
                if (datasetIndex === 0) {
                    button.classList.remove('btn-success');
                    button.classList.add('btn-outline-success');
                } else if (datasetIndex === 1) {
                    button.classList.remove('btn-danger');
                    button.classList.add('btn-outline-danger');
                } else {
                    button.classList.remove('btn-primary');
                    button.classList.add('btn-outline-primary');
                }
            }
        } else {
            if (selector === '.toggle-dataset') {
                button.classList.remove('btn-outline-primary', 'btn-outline-warning', 'btn-outline-success');
                button.classList.add('btn-' + (datasetIndex === 0 ? 'primary' : datasetIndex === 1 ? 'warning' : 'success'));
            } else {
                if (datasetIndex === 0) {
                    button.classList.remove('btn-outline-success');
                    button.classList.add('btn-success');
                } else if (datasetIndex === 1) {
                    button.classList.remove('btn-outline-danger');
                    button.classList.add('btn-danger');
                } else {
                    button.classList.remove('btn-outline-primary');
                    button.classList.add('btn-primary');
                }
            }
        }
    });
}

// 数字格式化
function formatCurrency(value, decimals = 2) {
    return new Intl.NumberFormat('zh-CN', { 
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals 
    }).format(value);
}

// 格式化大数字，如果大于10000，显示为万单位
function formatLargeNumber(value) {
    if (Math.abs(value) >= 10000) {
        return (value / 10000).toFixed(1) + '万';
    }
    return value.toFixed(0);
}

// 格式化日期
function formatDate(dateString) {
    if (!dateString) return '';
    const date = new Date(dateString);
    return `${date.getFullYear()}-${(date.getMonth()+1).toString().padStart(2, '0')}-${date.getDate().toString().padStart(2, '0')}`;
}

// 重定向到URL
function redirectTo(url) {
    window.location.href = url;
}

// 从URL中获取查询参数
function getQueryParam(name) {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get(name);
}

// 添加URL查询参数
function addQueryParam(name, value) {
    const urlParams = new URLSearchParams(window.location.search);
    urlParams.set(name, value);
    return window.location.pathname + '?' + urlParams.toString();
}

// 显示通知
function showNotification(message, type = 'info') {
    // 如果页面上没有通知容器，创建一个
    let notificationContainer = document.getElementById('notification-container');
    if (!notificationContainer) {
        notificationContainer = document.createElement('div');
        notificationContainer.id = 'notification-container';
        notificationContainer.style.position = 'fixed';
        notificationContainer.style.top = '20px';
        notificationContainer.style.right = '20px';
        notificationContainer.style.zIndex = '9999';
        document.body.appendChild(notificationContainer);
    }
    
    // 创建通知元素
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} shadow-sm`;
    notification.style.minWidth = '250px';
    notification.style.marginBottom = '10px';
    notification.innerHTML = `
        <div class="d-flex align-items-center">
            <i class="material-icons-round me-2" style="font-size: 20px;">
                ${type === 'success' ? 'check_circle' : type === 'danger' ? 'error' : 'info'}
            </i>
            <span>${message}</span>
            <button type="button" class="btn-close ms-auto" data-bs-dismiss="alert" aria-label="关闭"></button>
        </div>
    `;
    
    // 添加到容器
    notificationContainer.appendChild(notification);
    
    // 3秒后自动关闭
    setTimeout(() => {
        notification.classList.add('fade');
        setTimeout(() => {
            notification.remove();
        }, 300);
    }, 3000);
}

// 初始化所有工具提示
function initTooltips() {
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

// 文档加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    // 设置图表默认配置
    setupChartDefaults();
    
    // 初始化所有工具提示
    initTooltips();
    
    // 初始化侧边栏
    initSidebar();
    
    // 添加消息提示自动关闭功能
    initAlertAutoDismiss();
});

/**
 * 初始化侧边栏交互
 */
function initSidebar() {
    // 移动设备下的侧边栏切换
    const sidebarToggle = document.getElementById('sidebarToggle');
    if (sidebarToggle) {
        sidebarToggle.addEventListener('click', function() {
            document.querySelector('.sidebar').classList.toggle('show');
        });
    }
    
    // 在窗口大小变化时处理响应式布局
    window.addEventListener('resize', function() {
        if (window.innerWidth > 992) {
            const sidebar = document.querySelector('.sidebar');
            if (sidebar) {
                sidebar.classList.remove('show');
            }
        }
    });
}

/**
 * 设置提示消息自动关闭
 */
function initAlertAutoDismiss() {
    const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
    alerts.forEach(alert => {
        // 5秒后自动关闭提示
        setTimeout(() => {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });
}

// 导出公共函数
window.app = {
    formatCurrency,
    formatLargeNumber,
    formatDate,
    redirectTo,
    getQueryParam,
    addQueryParam,
    showNotification,
    colors: colorPalette,
    chartConfig,
    createChart,
    updateButtonStates
}; 