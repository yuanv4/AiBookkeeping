/**
 * 应用程序共享工具函数
 * 提供通用的辅助函数和工具方法
 */

/**
 * 格式化文件大小
 * @param {number} bytes - 字节数
 * @returns {string} 格式化后的文件大小字符串
 */
export function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

/**
 * HTML转义，防止XSS攻击
 * @param {string} text - 需要转义的文本
 * @returns {string} 转义后的HTML安全文本
 */
export function escapeHtml(text) {
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return text.replace(/[&<>"']/g, function(m) { return map[m]; });
}

/**
 * 显示非阻塞式通知
 * @param {string} message - 通知消息
 * @param {string} type - 通知类型 ('success', 'error', 'warning', 'info')
 * @param {number} duration - 显示时长（毫秒），默认5000ms
 */
export function showNotification(message, type = 'info', duration = 5000) {
    // 创建通知容器（如果不存在）
    let container = document.getElementById('notification-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'notification-container';
        container.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 9999;
            max-width: 400px;
        `;
        document.body.appendChild(container);
    }

    // 创建通知元素
    const notification = document.createElement('div');
    const typeClass = {
        'success': 'alert-success',
        'error': 'alert-danger',
        'warning': 'alert-warning',
        'info': 'alert-info'
    }[type] || 'alert-info';

    const iconClass = {
        'success': 'fas fa-check-circle',
        'error': 'fas fa-exclamation-triangle',
        'warning': 'fas fa-exclamation-circle',
        'info': 'fas fa-info-circle'
    }[type] || 'fas fa-info-circle';

    notification.className = `alert ${typeClass} alert-dismissible fade show mb-2`;
    notification.style.cssText = `
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        border: none;
    `;
    
    notification.innerHTML = `
        <div class="d-flex align-items-center">
            <i class="${iconClass} me-2"></i>
            <div class="flex-grow-1">${escapeHtml(message)}</div>
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;

    // 添加到容器
    container.appendChild(notification);

    // 自动移除
    setTimeout(() => {
        if (notification.parentNode) {
            notification.classList.remove('show');
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
            }, 150);
        }
    }, duration);

    return notification;
}

/**
 * 从CSS变量获取颜色值
 * @param {string} cssVar - CSS变量名（如 '--primary-500'）
 * @returns {string} 颜色值
 */
export function getCSSColor(cssVar) {
    try {
        const value = getComputedStyle(document.documentElement).getPropertyValue(cssVar).trim();
        return value;
    } catch (error) {
        console.warn(`无法获取CSS变量 ${cssVar}:`, error);
        return '#000000';
    }
}

/**
 * 防抖函数
 * @param {Function} func - 要防抖的函数
 * @param {number} wait - 等待时间（毫秒）
 * @returns {Function} 防抖后的函数
 */
export function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

/**
 * 节流函数
 * @param {Function} func - 要节流的函数
 * @param {number} limit - 时间间隔（毫秒）
 * @returns {Function} 节流后的函数
 */
export function throttle(func, limit) {
    let inThrottle;
    return function(...args) {
        if (!inThrottle) {
            func.apply(this, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

/**
 * 格式化日期为 YYYY-MM-DD 格式
 * @param {Date} date - 要格式化的日期对象
 * @returns {string} 格式化后的日期字符串
 */
export function formatDate(date) {
    if (!(date instanceof Date)) {
        console.warn('formatDate: 参数必须是 Date 对象');
        return '';
    }
    // return date.toISOString().split('T')[0]; // 旧方法，会导致时区问题

    const year = date.getFullYear();
    const month = (date.getMonth() + 1).toString().padStart(2, '0');
    const day = date.getDate().toString().padStart(2, '0');
    
    return `${year}-${month}-${day}`;
}

/**
 * URL 处理工具
 */
export const urlHandler = {
    /**
     * 获取URL查询参数值
     * @param {string} param - 参数名
     * @returns {string|null} 参数值
     */
    get(param) {
        const urlParams = new URLSearchParams(window.location.search);
        return urlParams.get(param);
    },

    /**
     * 设置URL查询参数
     * @param {string} param - 参数名
     * @param {string} value - 参数值
     * @param {boolean} reload - 是否重新加载页面，默认true
     */
    set(param, value, reload = true) {
        const url = new URL(window.location);
        url.searchParams.set(param, value);
        
        if (reload) {
            window.location.href = url.toString();
        } else {
            window.history.pushState({}, '', url.toString());
        }
    },

    /**
     * 移除URL查询参数
     * @param {string} param - 参数名
     * @param {boolean} reload - 是否重新加载页面，默认true
     */
    remove(param, reload = true) {
        const url = new URL(window.location);
        url.searchParams.delete(param);
        
        if (reload) {
            window.location.href = url.toString();
        } else {
            window.history.pushState({}, '', url.toString());
        }
    },

    /**
     * 批量设置URL查询参数
     * @param {Object} params - 参数对象
     * @param {boolean} reload - 是否重新加载页面，默认true
     */
    setMultiple(params, reload = true) {
        const url = new URL(window.location);
        
        Object.entries(params).forEach(([key, value]) => {
            if (value !== null && value !== undefined && value !== '') {
                url.searchParams.set(key, value);
            } else {
                url.searchParams.delete(key);
            }
        });
        
        if (reload) {
            window.location.href = url.toString();
        } else {
            window.history.pushState({}, '', url.toString());
        }
    },

    /**
     * 获取当前所有查询参数
     * @returns {Object} 参数对象
     */
    getAll() {
        const urlParams = new URLSearchParams(window.location.search);
        const params = {};
        for (const [key, value] of urlParams) {
            params[key] = value;
        }
        return params;
    }
};

/**
 * API 服务相关功能
 */
export const apiService = {
    /**
     * 显示加载状态
     * @param {boolean} show - 是否显示加载状态
     */
    showLoading(show) {
        let overlay = document.getElementById('loadingOverlay');
        if (!overlay && show) {
            // 创建加载遮罩层
            overlay = document.createElement('div');
            overlay.id = 'loadingOverlay';
            overlay.style.cssText = `
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(255, 255, 255, 0.8);
                display: flex;
                justify-content: center;
                align-items: center;
                z-index: 9999;
            `;
            overlay.innerHTML = `
                <div class="text-center">
                    <div class="spinner-border text-primary" role="status">
                        <span class="visually-hidden">加载中...</span>
                    </div>
                    <div class="mt-2">加载中...</div>
                </div>
            `;
            document.body.appendChild(overlay);
        }
        
        if (overlay) {
            overlay.style.display = show ? 'flex' : 'none';
        }
    },

    /**
     * 发送GET请求
     * @param {string} url - 请求URL
     * @param {Object} options - 请求选项
     * @param {boolean} options.showLoading - 是否显示加载状态，默认true
     * @returns {Promise} 请求Promise
     */
    async get(url, options = {}) {
        const { showLoading = true } = options;
        
        if (showLoading) {
            this.showLoading(true);
        }
        
        try {
            const response = await fetch(url, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                }
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            return { success: true, data };
            
        } catch (error) {
            console.error('API GET请求失败:', error);
            showNotification(`请求失败: ${error.message}`, 'error');
            return { success: false, error: error.message };
        } finally {
            if (showLoading) {
                this.showLoading(false);
            }
        }
    },

    /**
     * 发送POST请求
     * @param {string} url - 请求URL
     * @param {FormData|Object} data - 请求数据
     * @param {Object} options - 请求选项
     * @param {boolean} options.showLoading - 是否显示加载状态，默认true
     * @param {boolean} options.isFormData - 数据是否为FormData，默认自动检测
     * @returns {Promise} 请求Promise
     */
    async post(url, data, options = {}) {
        const { showLoading = true, isFormData = data instanceof FormData } = options;
        
        if (showLoading) {
            this.showLoading(true);
        }
        
        try {
            const requestOptions = {
                method: 'POST',
                body: isFormData ? data : JSON.stringify(data)
            };
            
            if (!isFormData) {
                requestOptions.headers = {
                    'Content-Type': 'application/json',
                };
            }
            
            const response = await fetch(url, requestOptions);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            // 尝试解析JSON，如果失败则返回文本
            const responseText = await response.text();
            let responseData;
            try {
                responseData = JSON.parse(responseText);
            } catch {
                responseData = responseText;
            }
            
            return { success: true, data: responseData };
            
        } catch (error) {
            console.error('API POST请求失败:', error);
            showNotification(`请求失败: ${error.message}`, 'error');
            return { success: false, error: error.message };
        } finally {
            if (showLoading) {
                this.showLoading(false);
            }
        }
    },

    /**
     * 标准化的POST请求方法
     * 统一处理加载状态、错误处理和成功回调
     * @param {string} url - 请求URL
     * @param {Object|FormData} data - 请求数据
     * @param {Object} options - 配置选项
     * @param {boolean} options.showLoading - 是否显示加载状态，默认true
     * @param {string} options.errorHandler - 错误处理方式，'default'|'silent'|'custom'
     * @param {Function} options.successCallback - 成功回调函数
     * @param {Function} options.errorCallback - 自定义错误回调函数
     * @returns {Promise<Object>} API响应结果
     */
    async standardPost(url, data, options = {}) {
        const {
            showLoading = true,
            errorHandler = 'default',
            successCallback = null,
            errorCallback = null
        } = options;

        try {
            // 调用原有的post方法
            const result = await this.post(url, data, { showLoading });

            // 处理成功响应
            if (result.success) {
                if (successCallback && typeof successCallback === 'function') {
                    successCallback(result);
                }
                return result;
            } else {
                // 处理业务逻辑错误
                const errorMessage = result.error || '操作失败';
                this.handleStandardError(errorMessage, errorHandler, errorCallback);
                return result;
            }
        } catch (error) {
            // 处理网络或其他异常
            const errorMessage = error.message || '网络请求失败';
            this.handleStandardError(errorMessage, errorHandler, errorCallback);
            return { success: false, error: errorMessage };
        }
    },

    /**
     * 统一的错误处理方法
     * @param {string} errorMessage - 错误消息
     * @param {string} errorHandler - 错误处理方式
     * @param {Function} errorCallback - 自定义错误回调
     */
    handleStandardError(errorMessage, errorHandler, errorCallback) {
        switch (errorHandler) {
            case 'silent':
                // 静默处理，不显示错误
                console.error('API错误 (静默):', errorMessage);
                break;
            case 'custom':
                // 使用自定义错误处理
                if (errorCallback && typeof errorCallback === 'function') {
                    errorCallback(errorMessage);
                } else {
                    console.warn('自定义错误处理器未定义，使用默认处理');
                    showNotification(`错误: ${errorMessage}`, 'error');
                }
                break;
            case 'default':
            default:
                // 默认错误处理：显示通知
                showNotification(`错误: ${errorMessage}`, 'error');
                break;
        }
    }
};

/**
 * UI 组件相关功能
 */
export const ui = {
    /**
     * 从HTML字符串创建DOM元素
     * @param {string} htmlString - HTML字符串
     * @returns {Element|null} 创建的DOM元素
     */
    createDOMElement(htmlString) {
        if (typeof htmlString !== 'string') {
            console.warn('createDOMElement: 参数必须是字符串');
            return null;
        }
        
        const template = document.createElement('template');
        template.innerHTML = htmlString.trim();
        return template.content.firstElementChild;
    },

    /**
     * 渲染Bootstrap分页组件
     * @param {Object} options - 分页配置选项
     * @param {number} options.currentPage - 当前页码
     * @param {number} options.totalPages - 总页数
     * @param {Function} options.onPageClick - 页码点击回调函数
     * @param {string} options.containerId - 分页容器ID
     * @returns {void}
     */
    renderPagination(options) {
        const { currentPage, totalPages, onPageClick, containerId } = options;
        const container = document.getElementById(containerId);
        
        if (!container) {
            console.warn(`renderPagination: 找不到容器 #${containerId}`);
            return;
        }
        
        container.innerHTML = '';
        
        if (totalPages <= 1) return;
        
        // 确保当前页在有效范围内
        const safePage = Math.max(1, Math.min(currentPage, totalPages));
        
        const pagination = document.createElement('ul');
        pagination.className = 'pagination justify-content-center';
        
        // 上一页按钮
        const prevLi = document.createElement('li');
        prevLi.className = `page-item ${safePage === 1 ? 'disabled' : ''}`;
        const prevLink = document.createElement('a');
        prevLink.className = 'page-link';
        prevLink.href = '#';
        prevLink.innerHTML = '<i class="fas fa-chevron-left"></i>';
        prevLink.addEventListener('click', (e) => {
            e.preventDefault();
            if (safePage > 1 && onPageClick) {
                onPageClick(safePage - 1);
            }
        });
        prevLi.appendChild(prevLink);
        pagination.appendChild(prevLi);
        
        // 页码按钮
        const startPage = Math.max(1, safePage - 2);
        const endPage = Math.min(totalPages, safePage + 2);
        
        // 如果开始页不是1，显示第一页和省略号
        if (startPage > 1) {
            this._createPageButton(pagination, 1, safePage, onPageClick);
            if (startPage > 2) {
                this._createEllipsis(pagination);
            }
        }
        
        // 显示当前页前后的页码
        for (let i = startPage; i <= endPage; i++) {
            this._createPageButton(pagination, i, safePage, onPageClick);
        }
        
        // 如果结束页不是最后一页，显示省略号和最后一页
        if (endPage < totalPages) {
            if (endPage < totalPages - 1) {
                this._createEllipsis(pagination);
            }
            this._createPageButton(pagination, totalPages, safePage, onPageClick);
        }
        
        // 下一页按钮
        const nextLi = document.createElement('li');
        nextLi.className = `page-item ${safePage === totalPages ? 'disabled' : ''}`;
        const nextLink = document.createElement('a');
        nextLink.className = 'page-link';
        nextLink.href = '#';
        nextLink.innerHTML = '<i class="fas fa-chevron-right"></i>';
        nextLink.addEventListener('click', (e) => {
            e.preventDefault();
            if (safePage < totalPages && onPageClick) {
                onPageClick(safePage + 1);
            }
        });
        nextLi.appendChild(nextLink);
        pagination.appendChild(nextLi);
        
        container.appendChild(pagination);
    },

    /**
     * 创建页码按钮
     * @private
     */
    _createPageButton(pagination, pageNumber, currentPage, onPageClick) {
        const li = document.createElement('li');
        li.className = `page-item ${pageNumber === currentPage ? 'active' : ''}`;
        
        const link = document.createElement('a');
        link.className = 'page-link';
        link.href = '#';
        link.textContent = pageNumber;
        
        link.addEventListener('click', (e) => {
            e.preventDefault();
            if (pageNumber !== currentPage && onPageClick) {
                onPageClick(pageNumber);
            }
        });
        
        li.appendChild(link);
        pagination.appendChild(li);
    },

    /**
     * 创建省略号
     * @private
     */
    _createEllipsis(pagination) {
        const li = document.createElement('li');
        li.className = 'page-item disabled';
        
        const span = document.createElement('span');
        span.className = 'page-link';
        span.textContent = '...';
        
        li.appendChild(span);
        pagination.appendChild(li);
    },

    /**
     * 显示确认对话框
     * @param {Object} options - 配置选项
     * @returns {Promise<boolean>} 用户选择结果
     */
    async showConfirmationModal(options = {}) {
        const {
            title = '确认操作',
            message = '您确定要执行此操作吗？',
            confirmText = '确认',
            cancelText = '取消',
            type = 'warning'
        } = options;

        return new Promise((resolve) => {
            // 创建模态框HTML
            const modalHtml = `
                <div class="modal fade" id="confirmationModal" tabindex="-1" aria-hidden="true">
                    <div class="modal-dialog">
                        <div class="modal-content">
                            <div class="modal-header">
                                <h5 class="modal-title">${escapeHtml(title)}</h5>
                                <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                            </div>
                            <div class="modal-body">
                                <div class="d-flex align-items-center">
                                    <i class="fas fa-exclamation-triangle text-warning me-3 fs-3"></i>
                                    <div>${escapeHtml(message)}</div>
                                </div>
                            </div>
                            <div class="modal-footer">
                                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">${escapeHtml(cancelText)}</button>
                                <button type="button" class="btn btn-${type === 'danger' ? 'danger' : 'primary'}" id="confirmBtn">${escapeHtml(confirmText)}</button>
                            </div>
                        </div>
                    </div>
                </div>
            `;

            // 创建并添加模态框到页面
            const modalElement = this.createDOMElement(modalHtml);
            document.body.appendChild(modalElement);

            // 初始化Bootstrap模态框
            const modal = new bootstrap.Modal(modalElement);
            
            // 绑定事件
            const confirmBtn = modalElement.querySelector('#confirmBtn');
            const handleConfirm = () => {
                modal.hide();
                resolve(true);
            };
            
            const handleCancel = () => {
                modal.hide();
                resolve(false);
            };

            confirmBtn.addEventListener('click', handleConfirm);
            
            // 监听模态框关闭事件，清理DOM
            modalElement.addEventListener('hidden.bs.modal', () => {
                document.body.removeChild(modalElement);
            });

            // 监听取消事件
            modalElement.addEventListener('hidden.bs.modal', (e) => {
                if (e.target === modalElement) {
                    resolve(false);
                }
            });

            // 显示模态框
            modal.show();
        });
    }
};

/**
 * ECharts 轻量级工具函数
 * 提供项目统一的图表配置和工具函数，不封装ECharts API
 */

/**
 * 获取项目颜色配置
 * @returns {Object} 颜色配置对象
 */
export function getProjectColors() {
    return {
        primary: getCSSColor('--bs-primary') || '#0d6efd',
        success: getCSSColor('--bs-success') || '#198754',
        info: getCSSColor('--bs-info') || '#0dcaf0',
        warning: getCSSColor('--bs-warning') || '#ffc107',
        danger: getCSSColor('--bs-danger') || '#dc3545',
        secondary: getCSSColor('--bs-secondary') || '#6c757d',
        bodyColor: getCSSColor('--bs-body-color') || '#212529',
        borderColor: getCSSColor('--bs-border-color') || '#dee2e6',
        borderColorTranslucent: getCSSColor('--bs-border-color-translucent') || 'rgba(0,0,0,.125)'
    };
}

/**
 * 格式化货币显示
 * @param {number} value - 数值
 * @param {boolean} compact - 是否使用紧凑格式
 * @returns {string} 格式化后的字符串
 */
export function formatCurrency(value, compact = false) {
    const options = compact
        ? { notation: 'compact', minimumFractionDigits: 0, maximumFractionDigits: 1 }
        : { minimumFractionDigits: 2, maximumFractionDigits: 2 };

    return '¥' + value.toLocaleString('zh-CN', options);
}

/**
 * 获取通用的图表样式配置
 * @returns {Object} 样式配置对象
 */
export function getChartStyles() {
    const colors = getProjectColors();

    return {
        tooltip: {
            backgroundColor: 'rgba(255, 255, 255, 0.95)',
            borderColor: colors.borderColor,
            borderWidth: 1,
            textStyle: {
                color: colors.bodyColor,
                fontSize: 12
            }
        },
        grid: {
            left: '3%',
            right: '4%',
            bottom: '3%',
            containLabel: true
        },
        axisStyle: {
            axisLine: {
                lineStyle: { color: colors.borderColor }
            },
            axisLabel: {
                color: colors.secondary,
                fontSize: 11
            },
            splitLine: {
                lineStyle: { color: colors.borderColorTranslucent }
            }
        }
    };
}

/**
 * 简单的图表实例管理器（防止内存泄漏）
 */
export const ChartRegistry = {
    charts: new Map(),

    /**
     * 注册图表实例
     * @param {string} id - 图表ID
     * @param {Object} chart - ECharts实例
     */
    register(id, chart) {
        // 先销毁现有实例
        this.destroy(id);

        // 注册新实例
        this.charts.set(id, chart);

        // 添加响应式支持
        const resizeHandler = () => {
            if (chart && !chart.isDisposed()) {
                chart.resize();
            }
        };
        window.addEventListener('resize', resizeHandler);
        chart._resizeHandler = resizeHandler;
    },

    /**
     * 销毁图表实例
     * @param {string} id - 图表ID
     */
    destroy(id) {
        const chart = this.charts.get(id);
        if (chart && !chart.isDisposed()) {
            // 移除resize监听器
            if (chart._resizeHandler) {
                window.removeEventListener('resize', chart._resizeHandler);
            }
            chart.dispose();
            this.charts.delete(id);
        }
    },

    /**
     * 获取图表实例
     * @param {string} id - 图表ID
     * @returns {Object|null} ECharts实例
     */
    get(id) {
        return this.charts.get(id) || null;
    },

    /**
     * 销毁所有图表实例
     */
    destroyAll() {
        this.charts.forEach((chart, id) => {
            this.destroy(id);
        });
    }
};

// 页面卸载时清理所有图表实例
window.addEventListener('beforeunload', () => {
    ChartRegistry.destroyAll();
});

/**
 * Tabulator 表格工具函数
 * 提供项目统一的表格配置和工具函数
 */

/**
 * 获取Tabulator中文本地化配置
 * @returns {Object} 中文本地化配置
 */
export function getTabulatorLocale() {
    return {
        "zh-cn": {
            "pagination": {
                "page_size": "每页显示",
                "page_title": "显示页面",
                "first": "首页",
                "first_title": "首页",
                "last": "末页",
                "last_title": "末页",
                "prev": "上一页",
                "prev_title": "上一页",
                "next": "下一页",
                "next_title": "下一页",
                "all": "全部"
            },
            "headerFilters": {
                "default": "筛选...",
                "columns": {
                    "name": "按名称筛选..."
                }
            },
            "groups": {
                "item": "项目",
                "items": "项目"
            },
            "sort": {
                "sortAsc": "升序排列",
                "sortDesc": "降序排列"
            },
            "columns": {
                "name": "名称"
            },
            "data": {
                "loading": "加载中...",
                "error": "错误"
            }
        }
    };
}

/**
 * 获取Tabulator通用配置
 * @returns {Object} 通用配置对象
 */
export function getTabulatorCommonConfig() {
    const colors = getProjectColors();

    return {
        layout: "fitColumns",
        responsiveLayout: "hide",
        pagination: "local",
        paginationSize: 20,
        paginationSizeSelector: [10, 20, 50, 100],
        movableColumns: true,
        resizableRows: true,
        selectable: true,
        locale: "zh-cn",
        langs: getTabulatorLocale(),
        headerFilterPlaceholder: "筛选...",
        placeholder: "没有找到匹配的记录",
        // 样式配置
        rowHeight: 45,
        headerHeight: 50,
        // 主题样式
        cssClass: "table-bootstrap5"
    };
}

/**
 * 获取财务数据专用的列格式化器
 * @returns {Object} 格式化器对象
 */
export function getTabulatorFormatters() {
    return {
        // 货币格式化器
        currency: function(cell) {
            const value = cell.getValue();
            if (value === null || value === undefined || value === '') return '';

            const formatted = formatCurrency(Math.abs(value));

            if (value > 0) {
                return `<span class="text-success fw-semibold">+${formatted}</span>`;
            } else if (value < 0) {
                return `<span class="text-danger fw-semibold">-${formatted}</span>`;
            } else {
                return `<span class="text-muted">${formatted}</span>`;
            }
        },

        // 余额格式化器
        balance: function(cell) {
            const value = cell.getValue();
            if (value === null || value === undefined || value === '') return '';

            return `<span class="fw-semibold">${formatCurrency(value)}</span>`;
        },

        // 日期格式化器
        dateFormat: function(cell) {
            const value = cell.getValue();
            if (!value) return '';

            const date = new Date(value);
            return date.toLocaleDateString('zh-CN', {
                year: 'numeric',
                month: '2-digit',
                day: '2-digit'
            });
        },

        // 文本截断格式化器
        textTruncate: function(cell, formatterParams) {
            const value = cell.getValue();
            if (!value) return '';

            const maxLength = formatterParams.maxLength || 20;
            const truncated = value.length > maxLength
                ? value.substring(0, maxLength) + '...'
                : value;

            return `<span title="${value}" class="text-truncate d-inline-block" style="max-width: 100%;">${truncated}</span>`;
        }
    };
}

// ==================== 分类相关工具函数 ====================



/**
 * 创建分类列的格式化器
 * @param {Object} categoriesConfig - 分类配置信息
 * @returns {Function} 格式化器函数
 */
function createCategoryFormatter(categoriesConfig) {
    return function(cell) {
        const category = cell.getValue();

        // 使用传入的分类配置
        let categoryInfo;
        if (categoriesConfig && categoriesConfig[category]) {
            categoryInfo = categoriesConfig[category];
        } else {
            // 配置缺失时使用最小化的通用默认值
            categoryInfo = {
                name: '未知分类',
                icon: 'help-circle',
                color: 'secondary'
            };
        }

        return `<span class="category-badge d-flex align-items-center">
            <i data-lucide="${categoryInfo.icon}" class="text-${categoryInfo.color}" style="width: 1rem; height: 1rem;"></i>
            <span class="ms-2 small">${categoryInfo.name}</span>
        </span>`;
    };
}

/**
 * 创建分类筛选器选项
 * @param {Object} categoriesConfig - 分类配置信息
 * @returns {Object} 筛选器参数
 */
function createCategoryFilterParams(categoriesConfig) {
    const filterOptions = { '': '全部分类' };

    // 使用分类配置构建筛选选项
    if (categoriesConfig && Object.keys(categoriesConfig).length > 0) {
        for (const [code, info] of Object.entries(categoriesConfig)) {
            filterOptions[code] = info.name;
        }
    }
    // 如果没有配置，筛选器将只有"全部分类"选项

    return {
        values: filterOptions,
        clearable: true,
        placeholder: "选择分类"
    };
}

/**
 * 获取财务表格专用的列配置
 * @param {Object} categoriesConfig - 分类配置信息
 * @returns {Object} 列配置对象
 */
export function getFinancialTableColumns(categoriesConfig = {}) {
    const formatters = getTabulatorFormatters();

    return {
        // 交易记录表格列配置（优化后的列顺序）
        transactions: [
            {
                title: "日期",
                field: "date",
                sorter: "string",
                headerFilter: "input",
                headerFilterPlaceholder: "筛选日期",
                width: 120,
                formatter: formatters.dateFormat,
                responsive: 0 // 最高优先级，始终显示
            },
            {
                title: "分类",
                field: "category",
                headerFilter: "select",
                headerFilterParams: createCategoryFilterParams(categoriesConfig),
                width: 100,
                formatter: createCategoryFormatter(categoriesConfig),
                sorter: "string",
                responsive: 1 // 高优先级
            },
            {
                title: "对手信息",
                field: "counterparty",
                headerFilter: "input",
                headerFilterPlaceholder: "筛选对手",
                width: 150,
                formatter: formatters.textTruncate,
                formatterParams: { maxLength: 15 },
                responsive: 2 // 中等优先级
            },
            {
                title: "金额",
                field: "amount",
                sorter: "number",
                headerFilter: "number",
                headerFilterPlaceholder: "筛选金额",
                width: 120,
                formatter: formatters.currency,
                hozAlign: "right",
                responsive: 0 // 最高优先级，始终显示
            },
            {
                title: "账户",
                field: "account",
                headerFilter: "input",
                headerFilterPlaceholder: "筛选账户",
                width: 150,
                formatter: formatters.textTruncate,
                formatterParams: { maxLength: 15 },
                responsive: 4 // 较低优先级
            },
            {
                title: "摘要",
                field: "description",
                headerFilter: "input",
                headerFilterPlaceholder: "筛选摘要",
                minWidth: 200,
                formatter: formatters.textTruncate,
                formatterParams: { maxLength: 25 },
                responsive: 5 // 最低优先级，小屏幕隐藏
            }
        ]
    };
}

/**
 * Tabulator实例管理器（类似ChartRegistry）
 */
export const TableRegistry = {
    tables: new Map(),

    /**
     * 注册表格实例
     * @param {string} id - 表格ID
     * @param {Object} table - Tabulator实例
     */
    register(id, table) {
        // 先销毁现有实例
        this.destroy(id);

        // 注册新实例
        this.tables.set(id, table);

        // 添加响应式支持
        const resizeHandler = () => {
            if (table && !table.destroyed) {
                table.redraw();
            }
        };
        window.addEventListener('resize', resizeHandler);
        table._resizeHandler = resizeHandler;
    },

    /**
     * 销毁表格实例
     * @param {string} id - 表格ID
     */
    destroy(id) {
        const table = this.tables.get(id);
        if (table && !table.destroyed) {
            // 移除resize监听器
            if (table._resizeHandler) {
                window.removeEventListener('resize', table._resizeHandler);
            }
            table.destroy();
            this.tables.delete(id);
        }
    },

    /**
     * 获取表格实例
     * @param {string} id - 表格ID
     * @returns {Object|null} Tabulator实例
     */
    get(id) {
        return this.tables.get(id) || null;
    },

    /**
     * 销毁所有表格实例
     */
    destroyAll() {
        this.tables.forEach((table, id) => {
            this.destroy(id);
        });
    }
};

/**
 * 创建交易记录表格
 * @param {string} containerId - 容器ID
 * @param {Array} data - 表格数据
 * @param {Object} options - 额外配置选项
 * @param {Object} categoriesConfig - 分类配置信息
 * @returns {Object} Tabulator实例
 */
export function createTransactionsTable(containerId, data = [], options = {}, categoriesConfig = {}) {
    const commonConfig = getTabulatorCommonConfig();
    const columns = getFinancialTableColumns(categoriesConfig).transactions;

    // 合并配置
    const config = {
        ...commonConfig,
        data: data,
        columns: columns,
        // 交易记录特定配置
        initialSort: [
            { column: "date", dir: "desc" }
        ],
        // 行样式配置
        rowFormatter: function(row) {
            const data = row.getData();
            const element = row.getElement();

            // 根据金额大小添加样式
            if (data.amount > 1000) {
                element.style.backgroundColor = "#e8f5e8";
            } else if (data.amount < -1000) {
                element.style.backgroundColor = "#ffeaea";
            }
        },
        ...options
    };

    // 创建表格实例
    const table = new window.Tabulator(`#${containerId}`, config);

    // 添加表格渲染完成后的回调，初始化图标
    table.on("tableBuilt", function(){
        // 初始化Lucide图标
        if (typeof lucide !== 'undefined' && lucide.createIcons) {
            lucide.createIcons();
        }
    });

    table.on("renderComplete", function(){
        // 每次重新渲染后都初始化图标
        if (typeof lucide !== 'undefined' && lucide.createIcons) {
            lucide.createIcons();
        }
    });

    // 注册到管理器
    TableRegistry.register(containerId, table);

    return table;
}

/**
 * 更新表格汇总信息（用于交易记录）
 * @param {Object} table - Tabulator实例
 * @param {Object} summaryElements - 汇总元素对象
 */
export function updateTransactionsSummary(table, summaryElements) {
    if (!table || !summaryElements) return;

    try {
        const data = table.getData();

        let totalIncome = 0;
        let totalExpense = 0;
        let incomeCount = 0;
        let expenseCount = 0;
        let latestBalance = 0;

        data.forEach(row => {
            const amount = parseFloat(row.amount) || 0;
            const balance = parseFloat(row.balance) || 0;

            if (amount > 0) {
                totalIncome += amount;
                incomeCount++;
            } else if (amount < 0) {
                totalExpense += Math.abs(amount);
                expenseCount++;
            }

            // 假设数据按日期排序，取最新的余额
            latestBalance = balance;
        });

        // 更新DOM元素
        if (summaryElements.totalIncome) {
            summaryElements.totalIncome.textContent = formatCurrency(totalIncome);
        }
        if (summaryElements.totalExpense) {
            summaryElements.totalExpense.textContent = formatCurrency(totalExpense);
        }
        if (summaryElements.incomeCount) {
            summaryElements.incomeCount.textContent = incomeCount;
        }
        if (summaryElements.expenseCount) {
            summaryElements.expenseCount.textContent = expenseCount;
        }
        if (summaryElements.latestBalance) {
            summaryElements.latestBalance.textContent = formatCurrency(latestBalance);
        }

    } catch (error) {
        console.error('更新交易汇总信息失败:', error);
    }
}

// 页面卸载时清理所有表格实例
window.addEventListener('beforeunload', () => {
    TableRegistry.destroyAll();
});

