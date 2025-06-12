/**
 * 共用JavaScript功能
 * 包含所有页面共享的功能
 */

// DOM加载完成后初始化通用功能
document.addEventListener('DOMContentLoaded', function() {
    console.log('[COMMON] DOM加载完成，初始化通用功能');
    
    // 初始化侧边栏切换功能
    initSidebarToggle();
    
    // 初始化卡片悬停效果
    initCardHoverEffects();
    
    // 初始化图标加载检测
    initIconLoadingDetection();
});

/**
 * 初始化侧边栏切换功能
 */
function initSidebarToggle() {
    const sidebarToggle = document.getElementById('sidebarToggle');
    const sidebar = document.querySelector('.sidebar');
    
    if (sidebarToggle && sidebar) {
        sidebarToggle.addEventListener('click', function() {
            sidebar.classList.toggle('show');
        });
        console.log('[COMMON] 侧边栏切换功能已初始化');
    }
}

/**
 * 初始化卡片悬停效果
 */
function initCardHoverEffects() {
    document.querySelectorAll('.card').forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-2px)';
        });
        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
        });
    });
    console.log('[COMMON] 卡片悬停效果已初始化');
}

/**
 * 初始化图标加载检测功能
 */
function initIconLoadingDetection() {
    // 检测Material Icons是否正常加载
    function checkIconsLoaded() {
        try {
            const testIcon = document.createElement('span');
            testIcon.className = 'material-icons-round';
            testIcon.textContent = 'check';
            testIcon.style.position = 'absolute';
            testIcon.style.opacity = '0';
            document.body.appendChild(testIcon);
            
            // 使用计算样式检查字体是否加载
            const computedStyle = window.getComputedStyle(testIcon);
            const fontFamily = computedStyle.getPropertyValue('font-family');
            const iconWidth = testIcon.offsetWidth > 0;
            
            document.body.removeChild(testIcon);
            
            const iconLoaded = iconWidth && fontFamily.includes('Material Icons');
            
            console.log('图标字体加载状态:', iconLoaded ? '成功' : '失败');
            
            if (!iconLoaded) {
                console.warn('Material Icons无法加载，使用备用图标');
                // 添加备用图标策略
                document.body.classList.add('icons-fallback');
                
                // 尝试多个备用图标源
                const iconSources = [
                    'https://cdn.jsdelivr.net/npm/@material-icons/font@1.0.29/material-icons-round.min.css',
                    'https://fonts.googleapis.com/icon?family=Material+Icons+Round&display=swap',
                    'https://fonts.loli.net/icon?family=Material+Icons+Round'
                ];
                
                // 尝试加载备用图标源
                loadBackupIcons(iconSources, 0);
                
                // 为所有图标添加文本备用方案
                document.querySelectorAll('.material-icons-round').forEach(icon => {
                    if (!icon.nextElementSibling || !icon.nextElementSibling.classList.contains('icon-text')) {
                        const textSpan = document.createElement('span');
                        textSpan.className = 'icon-text';
                        textSpan.textContent = icon.textContent;
                        icon.parentNode.insertBefore(textSpan, icon.nextSibling);
                    }
                });
            }
        } catch(err) {
            console.error('图标加载检测失败:', err);
            // 出错时也应用备用方案
            document.body.classList.add('icons-fallback');
        }
    }
    
    // 加载备用图标源
    function loadBackupIcons(sources, index) {
        if (index >= sources.length) return;
        
        const iconLink = document.createElement('link');
        iconLink.rel = 'stylesheet';
        iconLink.href = sources[index];
        
        iconLink.onload = function() {
            console.log('成功加载备用图标源:', sources[index]);
        };
        
        iconLink.onerror = function() {
            console.warn('备用图标源加载失败:', sources[index]);
            // 尝试下一个源
            loadBackupIcons(sources, index + 1);
        };
        
        document.head.appendChild(iconLink);
    }
    
    // 延迟执行检测，给图标字体加载留出时间
    setTimeout(checkIconsLoaded, 500);
    console.log('[COMMON] 图标加载检测功能已初始化');
}

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

/**
 * 获取图表主题配色方案
 * @param {string} theme 主题名称，目前仅支持 'default'
 * @returns {object} 主题配色对象
 */
function getChartTheme(theme = 'default') {
    const themes = {
        default: {
            colors: {
                primary: getCSSColor('--primary'),
                secondary: getCSSColor('--secondary'),
                success: getCSSColor('--success'),
                danger: getCSSColor('--danger'),
                warning: getCSSColor('--warning'),
                info: getCSSColor('--info'),
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
                neutral: [
                    getCSSColor('--chart-neutral-1'),
                    getCSSColor('--chart-neutral-2'),
                    getCSSColor('--chart-neutral-3'),
                    getCSSColor('--chart-neutral-4'),
                    getCSSColor('--chart-neutral-5'),
                    getCSSColor('--chart-neutral-6')
                ],
                monochrome: [
                    getCSSColor('--chart-monochrome-1'),
                    getCSSColor('--chart-monochrome-2'),
                    getCSSColor('--chart-monochrome-3'),
                    getCSSColor('--chart-monochrome-4'),
                    getCSSColor('--chart-monochrome-5'),
                    getCSSColor('--chart-monochrome-6'),
                    getCSSColor('--chart-monochrome-7')
                ]
            },
            fonts: {
                family: getCSSColor('--chart-font-family'),
                size: parseInt(getCSSColor('--chart-font-size')) || 12,
                color: getCSSColor('--chart-font-color')
            },
            elements: {
                line: {
                    tension: parseFloat(getCSSColor('--chart-line-tension')) || 0.2,
                    borderWidth: parseInt(getCSSColor('--chart-line-border-width')) || 2,
                    fill: true,
                    borderJoinStyle: 'round'
                },
                point: {
                    radius: parseInt(getCSSColor('--chart-point-radius')) || 3,
                    hoverRadius: parseInt(getCSSColor('--chart-point-hover-radius')) || 5,
                    borderWidth: 2,
                    hoverBorderWidth: 2,
                    hitRadius: 8
                },
                bar: {
                    borderRadius: parseInt(getCSSColor('--chart-bar-border-radius')) || 2,
                    borderWidth: 0,
                    borderSkipped: false,
                    maxBarThickness: parseInt(getCSSColor('--chart-bar-max-thickness')) || 45
                },
                arc: {
                    borderWidth: 1,
                    borderColor: getCSSColor('--background')
                }
            },
            grid: {
                color: getCSSColor('--chart-grid-color'),
                borderColor: getCSSColor('--chart-grid-border-color'),
                tickColor: getCSSColor('--chart-grid-tick-color')
            },
            tooltip: {
                backgroundColor: getCSSColor('--chart-tooltip-bg'),
                titleColor: getCSSColor('--chart-tooltip-title-color'),
                bodyColor: getCSSColor('--chart-tooltip-body-color'),
                borderColor: getCSSColor('--chart-tooltip-border-color'),
                borderWidth: 1
            },
            animation: {
                duration: parseInt(getCSSColor('--chart-animation-duration')) || 800,
                easing: 'easeOutQuad'
            }
        }
    };
    
    return themes[theme] || themes.default;
}

/**
 * 应用图表主题
 * @param {object} chartInstance Chart.js实例
 * @param {string} theme 主题名称
 */
function applyChartTheme(chartInstance, theme = 'default') {
    if (!chartInstance || typeof Chart === 'undefined') {
        console.warn('Chart.js实例或Chart.js库不可用');
        return;
    }
    
    const themeConfig = getChartTheme(theme);
    
    // 应用主题到图表配置
    if (chartInstance.options) {
        // 字体配置
        if (themeConfig.fonts) {
            chartInstance.options.font = {
                family: themeConfig.fonts.family,
                size: themeConfig.fonts.size
            };
        }
        
        // 网格配置
        if (themeConfig.grid && chartInstance.options.scales) {
            Object.keys(chartInstance.options.scales).forEach(scaleKey => {
                const scale = chartInstance.options.scales[scaleKey];
                if (scale.grid) {
                    scale.grid.color = themeConfig.grid.color;
                    scale.grid.borderColor = themeConfig.grid.borderColor;
                }
                if (scale.ticks) {
                    scale.ticks.color = themeConfig.grid.tickColor;
                }
            });
        }
        
        // 工具提示配置
        if (themeConfig.tooltip && chartInstance.options.plugins && chartInstance.options.plugins.tooltip) {
            Object.assign(chartInstance.options.plugins.tooltip, themeConfig.tooltip);
        }
        
        // 动画配置
        if (themeConfig.animation) {
            chartInstance.options.animation = themeConfig.animation;
        }
    }
    
    // 更新图表
    chartInstance.update();
}

/**
 * 应用统一颜色主题到所有图表
 * 使用CSS变量替代chart-themes.js
 */
function applyUnifiedColorTheme() {
    // 确保Chart.js已加载
    if (typeof Chart === 'undefined') {
        console.warn('Chart.js未加载，无法应用图表主题');
        return;
    }
    
    try {
        // 应用基础样式（从CSS变量获取）
        Chart.defaults.color = getCSSColor('--text-secondary');
        Chart.defaults.font.family = getCSSColor('--font-family-system');
        Chart.defaults.font.size = 12;
        
        // 应用元素样式
        Chart.defaults.elements.line.borderWidth = 2;
        Chart.defaults.elements.line.tension = 0.4;
        Chart.defaults.elements.point.radius = 4;
        Chart.defaults.elements.point.hoverRadius = 6;
        Chart.defaults.elements.bar.borderRadius = 4;
        Chart.defaults.elements.arc.borderWidth = 0;
        
        // 应用网格样式
        Chart.defaults.scale.grid.color = getCSSColor('--gray-200');
        Chart.defaults.scale.grid.borderColor = getCSSColor('--gray-300');
        Chart.defaults.scale.ticks.color = getCSSColor('--text-secondary');
        
        // 应用工具提示样式
        Object.assign(Chart.defaults.plugins.tooltip, {
            backgroundColor: 'rgba(0, 0, 0, 0.8)',
            titleColor: '#ffffff',
            bodyColor: '#ffffff',
            borderColor: getCSSColor('--gray-300'),
            borderWidth: 1,
            cornerRadius: 8,
            caretSize: 6
        });
        
        // 应用动画设置
        Chart.defaults.animation = {
            duration: 750,
            easing: 'easeOutQuart'
        };
        
        // 创建统一的颜色配置对象，从CSS变量获取
        window.defaultColors = {
            // 基础颜色系统
            primary: getCSSColor('--primary'),
            secondary: getCSSColor('--secondary'),
            success: getCSSColor('--success'),
            danger: getCSSColor('--danger'),
            warning: getCSSColor('--warning'),
            info: getCSSColor('--info'),
            
            // 图表专用颜色
            income: getCSSColor('--chart-income'),
            expense: getCSSColor('--chart-expense'),
            savings: getCSSColor('--chart-savings'),
            balance: getCSSColor('--chart-balance'),
            neutral: getCSSColor('--chart-neutral'),
            
            // 图表分类颜色
            category: [
                getCSSColor('--chart-category-1'),
                getCSSColor('--chart-category-2'),
                getCSSColor('--chart-category-3'),
                getCSSColor('--chart-category-4'),
                getCSSColor('--chart-category-5'),
                getCSSColor('--chart-category-6')
            ],
            
            // 透明度变体
            primaryLight: getCSSColor('--primary-10'),
            successLight: getCSSColor('--success-10'),
            dangerLight: getCSSColor('--danger-10'),
            warningLight: getCSSColor('--warning-10'),
            infoLight: getCSSColor('--info-10'),
            
            // Hover状态颜色
            primaryHover: getCSSColor('--primary-hover'),
            successHover: getCSSColor('--success-hover'),
            dangerHover: getCSSColor('--danger-hover'),
            warningHover: getCSSColor('--warning-hover'),
            infoHover: getCSSColor('--info-hover'),
            
            // 单色系列（用于渐变图表）
            monochrome: [
                getCSSColor('--primary'),
                getCSSColor('--primary-600'),
                getCSSColor('--primary-700'),
                getCSSColor('--gray-600'),
                getCSSColor('--gray-700')
            ]
        };
        
        console.log('已成功应用统一颜色主题到所有图表');
        return true;
    } catch (error) {
        console.error('应用统一颜色主题失败:', error);
        
        // 降级处理：如果CSS变量获取失败，尝试使用ChartThemes（向后兼容）
        if (typeof ChartThemes !== 'undefined') {
            console.log('降级使用ChartThemes配置');
            return applyLegacyTheme();
        }
        
        return false;
    }
}

/**
 * 图表交互功能对象
 * 替代chart-themes.js中的ChartInteractions
 */
const ChartInteractions = {
    /**
     * 下载图表为图片
     */
    downloadChart: function(chartInstance, filename = 'chart') {
        if (!chartInstance) return;
        
        const url = chartInstance.toBase64Image();
        const link = document.createElement('a');
        link.download = `${filename}.png`;
        link.href = url;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    },
    
    /**
     * 全屏显示图表
     */
    toggleFullscreen: function(chartContainer) {
        if (!chartContainer) return;
        
        if (!document.fullscreenElement) {
            chartContainer.requestFullscreen().catch(err => {
                console.warn('无法进入全屏模式:', err);
            });
        } else {
            document.exitFullscreen();
        }
    },
    
    /**
     * 重置图表缩放
     */
    resetZoom: function(chartInstance) {
        if (chartInstance && chartInstance.resetZoom) {
            chartInstance.resetZoom();
        }
    },
    
    /**
     * 图例交互增强
     */
    enhanceLegendInteraction: function(chartInstance) {
        if (!chartInstance) return;
        
        const originalLegendClickHandler = chartInstance.options.plugins.legend.onClick;
        
        chartInstance.options.plugins.legend.onClick = function(e, legendItem, legend) {
            // 调用原始处理器
            if (originalLegendClickHandler) {
                originalLegendClickHandler.call(this, e, legendItem, legend);
            }
            
            // 添加自定义交互效果
            const chart = legend.chart;
            const datasets = chart.data.datasets;
            
            // 双击图例项时，只显示该项，隐藏其他项
            if (e.detail === 2) {
                datasets.forEach((dataset, index) => {
                    dataset.hidden = index !== legendItem.datasetIndex;
                });
                chart.update();
            }
        };
    },
    
    /**
     * 数据点高亮
     */
    highlightDataPoint: function(chartInstance, datasetIndex, pointIndex) {
        if (!chartInstance || !chartInstance.data.datasets[datasetIndex]) return;
        
        const dataset = chartInstance.data.datasets[datasetIndex];
        const meta = chartInstance.getDatasetMeta(datasetIndex);
        
        // 重置所有点的样式
        meta.data.forEach(point => {
            point.options.backgroundColor = dataset.backgroundColor;
            point.options.borderColor = dataset.borderColor;
            point.options.radius = 3;
        });
        
        // 高亮指定点
        if (meta.data[pointIndex]) {
            meta.data[pointIndex].options.backgroundColor = getCSSColor('--warning');
            meta.data[pointIndex].options.borderColor = getCSSColor('--warning');
            meta.data[pointIndex].options.radius = 6;
        }
        
        chartInstance.update('none');
    },
    
    /**
     * 初始化图表工具栏
     */
    initializeToolbar: function(chartContainer, chartInstance) {
        if (!chartContainer || !chartInstance) return;
        
        // 检查是否已存在工具栏
        if (chartContainer.querySelector('.chart-toolbar')) return;
        
        const toolbar = document.createElement('div');
        toolbar.className = 'chart-toolbar';
        toolbar.innerHTML = `
            <button class="btn btn-sm btn-outline-secondary" data-action="download" title="下载图表">
                <i class="fas fa-download"></i>
            </button>
            <button class="btn btn-sm btn-outline-secondary" data-action="fullscreen" title="全屏">
                <i class="fas fa-expand"></i>
            </button>
            <button class="btn btn-sm btn-outline-secondary" data-action="reset" title="重置缩放">
                <i class="fas fa-undo"></i>
            </button>
        `;
        
        // 添加工具栏样式
        toolbar.style.cssText = `
            position: absolute;
            top: 10px;
            right: 10px;
            z-index: 1000;
            display: flex;
            gap: 5px;
            opacity: 0;
            transition: opacity 0.3s ease;
        `;
        
        // 事件监听
        toolbar.addEventListener('click', (e) => {
            const action = e.target.closest('[data-action]')?.dataset.action;
            switch (action) {
                case 'download':
                    this.downloadChart(chartInstance, 'chart');
                    break;
                case 'fullscreen':
                    this.toggleFullscreen(chartContainer);
                    break;
                case 'reset':
                    this.resetZoom(chartInstance);
                    break;
            }
        });
        
        // 鼠标悬停显示工具栏
        chartContainer.addEventListener('mouseenter', () => {
            toolbar.style.opacity = '1';
        });
        
        chartContainer.addEventListener('mouseleave', () => {
            toolbar.style.opacity = '0';
        });
        
        chartContainer.style.position = 'relative';
        chartContainer.appendChild(toolbar);
    }
};

/**
 * 降级主题应用函数（向后兼容）
 * 当CSS变量不可用时使用ChartThemes
 */
function applyLegacyTheme() {
    try {
        const theme = ChartThemes.default;
        
        // 应用ChartThemes配置
        Chart.defaults.color = theme.fonts.color;
        Chart.defaults.font.family = theme.fonts.family;
        Chart.defaults.font.size = theme.fonts.size;
        
        Object.assign(Chart.defaults.elements.line, theme.elements.line);
        Object.assign(Chart.defaults.elements.point, theme.elements.point);
        Object.assign(Chart.defaults.elements.bar, theme.elements.bar);
        Object.assign(Chart.defaults.elements.arc, theme.elements.arc);
        
        Chart.defaults.scale.grid.color = theme.grid.color;
        Chart.defaults.scale.grid.borderColor = theme.grid.borderColor;
        Chart.defaults.scale.ticks.color = theme.fonts.color;
        
        Object.assign(Chart.defaults.plugins.tooltip, {
            backgroundColor: theme.tooltip.backgroundColor,
            titleColor: theme.tooltip.titleColor,
            bodyColor: theme.tooltip.bodyColor,
            borderColor: theme.tooltip.borderColor,
            borderWidth: theme.tooltip.borderWidth
        });
        
        Chart.defaults.animation = theme.animation;
        
        window.defaultColors = {
            primary: theme.colors.primary,
            secondary: theme.colors.secondary,
            success: theme.colors.success,
            danger: theme.colors.danger,
            warning: theme.colors.warning,
            info: theme.colors.info,
            neutral: theme.colors.neutral,
            category: theme.colors.category,
            monochrome: theme.colors.monochrome,
            income: theme.colors.success,
            expense: theme.colors.danger,
            savings: theme.colors.warning,
            balance: theme.colors.primary
        };
        
        console.log('已成功应用降级主题配置');
        return true;
    } catch (error) {
        console.error('降级主题应用失败:', error);
        return false;
    }
}

// 保持向后兼容的别名
const applyFinanceThemeToAllCharts = applyUnifiedColorTheme;

// 在文档加载完成后自动应用统一颜色主题
document.addEventListener('DOMContentLoaded', function() {
    // 立即应用统一颜色主题
    applyUnifiedColorTheme();
    
    // 更新所有Chart实例以应用新主题
    setTimeout(function() {
        if (typeof Chart !== 'undefined') {
            const allCharts = Object.values(Chart.instances);
            allCharts.forEach(chart => {
                if (chart && typeof chart.update === 'function') {
                    chart.update();
                }
            });
            console.log(`已更新${allCharts.length}个图表实例以应用新主题`);
        }
    }, 100);
    
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
    colors: window.defaultColors,
    chartConfig,
    createChart,
    updateButtonStates
};