/**
 * AiBookkeeping - 图表主题和交互配置
 * 提供统一的图表样式、主题和交互功能
 */

// 图表主题配置
const ChartThemes = {
    // 默认主题 - 亮色
    default: {
        colors: {
            primary: '#4361ee',
            success: '#4cc9a6',
            danger: '#f25767',
            warning: '#ffaa46',
            info: '#3db0ef',
            neutral: ['#4361ee', '#6c84ca', '#8ea2d8', '#b0bfe5', '#d2dcf3'],
            category: ['#4361ee', '#4cc9a6', '#f25767', '#ffaa46', '#3db0ef', '#9b5de5', '#20c997', '#d63384']
        },
        fonts: {
            family: "'Noto Sans SC', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif",
            size: 12,
            color: '#334152'
        },
        elements: {
            line: {
                tension: 0.4,
                borderWidth: 2,
                fill: true,
                borderJoinStyle: 'round'
            },
            point: {
                radius: 4,
                hoverRadius: 6,
                borderWidth: 2,
                hoverBorderWidth: 2,
                hitRadius: 8
            },
            bar: {
                borderRadius: 4,
                borderWidth: 0,
                borderSkipped: false,
                maxBarThickness: 50
            },
            arc: {
                borderWidth: 1,
                borderColor: '#fff'
            }
        },
        grid: {
            color: 'rgba(0, 0, 0, 0.05)',
            borderColor: 'rgba(0, 0, 0, 0.05)',
            tickColor: 'rgba(0, 0, 0, 0.1)'
        },
        tooltip: {
            backgroundColor: 'rgba(0, 0, 0, 0.75)',
            titleColor: '#fff',
            bodyColor: '#fff',
            borderColor: 'rgba(255, 255, 255, 0.1)',
            borderWidth: 1
        },
        animation: {
            duration: 1000,
            easing: 'easeOutQuart'
        }
    },
    
    // 深色主题
    dark: {
        colors: {
            primary: '#6c8bfc',
            success: '#4cc9a6',
            danger: '#f25767',
            warning: '#ffaa46',
            info: '#3db0ef',
            neutral: ['#6c8bfc', '#8ba4fc', '#a8bcfd', '#c5d3fd', '#e2e9fe'],
            category: ['#6c8bfc', '#4cc9a6', '#f25767', '#ffaa46', '#3db0ef', '#9b5de5', '#20c997', '#d63384']
        },
        fonts: {
            family: "'Noto Sans SC', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif",
            size: 12,
            color: '#e2e8f0'
        },
        elements: {
            line: {
                tension: 0.4,
                borderWidth: 2,
                fill: true,
                borderJoinStyle: 'round'
            },
            point: {
                radius: 4,
                hoverRadius: 6,
                borderWidth: 2,
                hoverBorderWidth: 2,
                hitRadius: 8
            },
            bar: {
                borderRadius: 4,
                borderWidth: 0,
                borderSkipped: false,
                maxBarThickness: 50
            },
            arc: {
                borderWidth: 1,
                borderColor: '#1f2937'
            }
        },
        grid: {
            color: 'rgba(255, 255, 255, 0.07)',
            borderColor: 'rgba(255, 255, 255, 0.07)',
            tickColor: 'rgba(255, 255, 255, 0.12)'
        },
        tooltip: {
            backgroundColor: 'rgba(15, 23, 42, 0.9)',
            titleColor: '#fff',
            bodyColor: '#e2e8f0',
            borderColor: 'rgba(255, 255, 255, 0.1)',
            borderWidth: 1
        },
        animation: {
            duration: 1000,
            easing: 'easeOutQuart'
        }
    },
    
    // 打印主题 - 适合导出和打印
    print: {
        colors: {
            primary: '#000000',
            success: '#333333',
            danger: '#666666',
            warning: '#999999',
            info: '#555555',
            neutral: ['#000000', '#333333', '#666666', '#999999', '#cccccc'],
            category: ['#000000', '#333333', '#666666', '#999999', '#555555', '#777777', '#222222', '#444444']
        },
        fonts: {
            family: "'Noto Sans SC', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif",
            size: 10,
            color: '#000000'
        },
        elements: {
            line: {
                tension: 0,
                borderWidth: 1.5,
                fill: false,
                borderDash: [4, 4]
            },
            point: {
                radius: 3,
                hoverRadius: 3,
                borderWidth: 1,
                hoverBorderWidth: 1,
                hitRadius: 3
            },
            bar: {
                borderRadius: 0,
                borderWidth: 1,
                borderSkipped: false,
                maxBarThickness: 40
            },
            arc: {
                borderWidth: 1,
                borderColor: '#fff'
            }
        },
        grid: {
            color: 'rgba(0, 0, 0, 0.1)',
            borderColor: 'rgba(0, 0, 0, 0.1)',
            tickColor: 'rgba(0, 0, 0, 0.2)'
        },
        tooltip: {
            enabled: false
        },
        animation: {
            duration: 0
        }
    }
};

// 图表交互增强
const ChartInteractions = {
    // 图表下载功能
    download: function(chart, filename = 'chart', format = 'png') {
        if (!chart) return false;
        
        try {
            // 创建一个链接元素来触发下载
            const link = document.createElement('a');
            link.href = chart.toBase64Image();
            link.download = filename + '.' + format;
            link.click();
            return true;
        } catch (error) {
            console.error('图表下载失败:', error);
            return false;
        }
    },
    
    // 图表全屏查看
    fullscreen: function(chartContainer) {
        if (!chartContainer) return false;
        
        try {
            if (!document.fullscreenElement) {
                // 进入全屏模式
                if (chartContainer.requestFullscreen) {
                    chartContainer.requestFullscreen();
                } else if (chartContainer.webkitRequestFullscreen) {
                    chartContainer.webkitRequestFullscreen();
                } else if (chartContainer.msRequestFullscreen) {
                    chartContainer.msRequestFullscreen();
                }
            } else {
                // 退出全屏模式
                if (document.exitFullscreen) {
                    document.exitFullscreen();
                } else if (document.webkitExitFullscreen) {
                    document.webkitExitFullscreen();
                } else if (document.msExitFullscreen) {
                    document.msExitFullscreen();
                }
            }
            return true;
        } catch (error) {
            console.error('图表全屏切换失败:', error);
            return false;
        }
    },
    
    // 图表缩放功能
    zoom: function(chart, resetZoom = false) {
        if (!chart || !chart.options.plugins.zoom) return false;
        
        try {
            if (resetZoom) {
                chart.resetZoom();
            } else {
                // 启用缩放插件
                chart.options.plugins.zoom.zoom.wheel.enabled = true;
                chart.options.plugins.zoom.zoom.pinch.enabled = true;
                chart.options.plugins.zoom.pan.enabled = true;
                chart.update();
            }
            return true;
        } catch (error) {
            console.error('图表缩放操作失败:', error);
            return false;
        }
    },
    
    // 图例交互增强
    enhanceLegend: function(chart) {
        if (!chart) return false;
        
        try {
            const originalLegendOnClick = Chart.defaults.plugins.legend.onClick;
            
            chart.options.plugins.legend.onClick = function(e, legendItem, legend) {
                // 显示点击效果
                const clickEffect = document.createElement('div');
                clickEffect.className = 'chart-legend-click-effect';
                clickEffect.style.left = e.offsetX + 'px';
                clickEffect.style.top = e.offsetY + 'px';
                e.target.appendChild(clickEffect);
                
                // 300ms后移除效果
                setTimeout(() => {
                    e.target.removeChild(clickEffect);
                }, 300);
                
                // 调用原始点击处理
                originalLegendOnClick.call(this, e, legendItem, legend);
            };
            
            chart.update();
            return true;
        } catch (error) {
            console.error('图例交互增强失败:', error);
            return false;
        }
    },
    
    // 数据点高亮功能
    highlightPoint: function(chart, datasetIndex, pointIndex) {
        if (!chart || !chart.data.datasets[datasetIndex]) return false;
        
        try {
            // 存储原始配置
            if (!chart._originalPointRadius) {
                chart._originalPointRadius = {};
                chart._originalBorderWidth = {};
            }
            
            // 重置所有点
            chart.data.datasets.forEach((dataset, i) => {
                if (chart._originalPointRadius[i]) {
                    dataset.pointRadius = chart._originalPointRadius[i];
                    dataset.pointBorderWidth = chart._originalBorderWidth[i];
                }
            });
            
            // 记住原始配置
            if (!chart._originalPointRadius[datasetIndex]) {
                chart._originalPointRadius[datasetIndex] = chart.data.datasets[datasetIndex].pointRadius;
                chart._originalBorderWidth[datasetIndex] = chart.data.datasets[datasetIndex].pointBorderWidth;
            }
            
            // 创建高亮点半径数组
            const pointRadiusArray = Array(chart.data.datasets[datasetIndex].data.length).fill(
                chart._originalPointRadius[datasetIndex]
            );
            const pointBorderWidthArray = Array(chart.data.datasets[datasetIndex].data.length).fill(
                chart._originalBorderWidth[datasetIndex]
            );
            
            // 设置高亮点
            pointRadiusArray[pointIndex] = pointRadiusArray[pointIndex] * 1.8;
            pointBorderWidthArray[pointIndex] = pointBorderWidthArray[pointIndex] * 1.5;
            
            // 应用新配置
            chart.data.datasets[datasetIndex].pointRadius = pointRadiusArray;
            chart.data.datasets[datasetIndex].pointBorderWidth = pointBorderWidthArray;
            
            chart.update();
            return true;
        } catch (error) {
            console.error('数据点高亮失败:', error);
            return false;
        }
    },
    
    // 初始化图表工具栏功能
    initToolbar: function() {
        document.addEventListener('click', function(event) {
            // 获取点击的工具栏按钮
            const toolbarBtn = event.target.closest('[data-chart-action]');
            if (!toolbarBtn) return;
            
            // 获取操作类型和图表ID
            const action = toolbarBtn.getAttribute('data-chart-action');
            const chartId = toolbarBtn.getAttribute('data-chart-id');
            
            // 获取图表实例
            const chartInstance = Chart.getChart(chartId);
            if (!chartInstance) return;
            
            // 获取图表容器
            const chartContainer = document.getElementById(chartId).closest('.chart-container');
            
            // 执行相应操作
            switch (action) {
                case 'download':
                    ChartInteractions.download(chartInstance);
                    break;
                case 'fullscreen':
                    ChartInteractions.fullscreen(chartContainer);
                    break;
                case 'zoom':
                    ChartInteractions.zoom(chartInstance);
                    break;
                case 'reset-zoom':
                    ChartInteractions.zoom(chartInstance, true);
                    break;
            }
        });
    }
};

// 应用主题到图表
function applyChartTheme(chart, themeName = 'default') {
    if (!chart || !ChartThemes[themeName]) return false;
    
    try {
        const theme = ChartThemes[themeName];
        
        // 应用颜色
        Chart.defaults.color = theme.fonts.color;
        
        // 应用字体
        Chart.defaults.font.family = theme.fonts.family;
        Chart.defaults.font.size = theme.fonts.size;
        
        // 应用元素样式
        Object.assign(Chart.defaults.elements.line, theme.elements.line);
        Object.assign(Chart.defaults.elements.point, theme.elements.point);
        Object.assign(Chart.defaults.elements.bar, theme.elements.bar);
        Object.assign(Chart.defaults.elements.arc, theme.elements.arc);
        
        // 应用网格样式
        Chart.defaults.scale.grid.color = theme.grid.color;
        Chart.defaults.scale.grid.borderColor = theme.grid.borderColor;
        Chart.defaults.scale.ticks.color = theme.fonts.color;
        
        // 应用工具提示样式
        Object.assign(Chart.defaults.plugins.tooltip, {
            backgroundColor: theme.tooltip.backgroundColor,
            titleColor: theme.tooltip.titleColor,
            bodyColor: theme.tooltip.bodyColor,
            borderColor: theme.tooltip.borderColor,
            borderWidth: theme.tooltip.borderWidth
        });
        
        // 应用动画设置
        Chart.defaults.animation = theme.animation;
        
        // 更新图表
        chart.update();
        return true;
    } catch (error) {
        console.error('应用图表主题失败:', error);
        return false;
    }
}

// 初始化图表交互
document.addEventListener('DOMContentLoaded', function() {
    // 初始化图表工具栏功能
    ChartInteractions.initToolbar();
    
    // 添加全局样式到文档
    const style = document.createElement('style');
    style.textContent = `
        .chart-legend-click-effect {
            position: absolute;
            width: 30px;
            height: 30px;
            border-radius: 50%;
            background-color: rgba(0, 0, 0, 0.1);
            transform: translate(-50%, -50%);
            animation: chart-legend-click-ripple 0.3s ease-out;
            pointer-events: none;
        }
        
        @keyframes chart-legend-click-ripple {
            0% {
                opacity: 1;
                transform: translate(-50%, -50%) scale(0);
            }
            100% {
                opacity: 0;
                transform: translate(-50%, -50%) scale(1.5);
            }
        }
    `;
    document.head.appendChild(style);
}); 