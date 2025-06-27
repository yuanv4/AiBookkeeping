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
        return value || '#000000';
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
    return date.toISOString().split('T')[0];
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