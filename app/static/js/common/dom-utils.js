/**
 * DOM操作工具函数模块
 * 提供统一的DOM操作和UI组件功能
 */

import { escapeHtml } from './notifications.js';

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
 * 简化的DOM操作函数
 */

/**
 * 根据ID获取元素
 * @param {string} id - 元素ID
 * @returns {Element|null} DOM元素
 */
export function getElementById(id) {
    return document.getElementById(id);
}

/**
 * 根据选择器获取元素
 * @param {string} selector - CSS选择器
 * @returns {Element|null} DOM元素
 */
export function querySelector(selector) {
    return document.querySelector(selector);
}

/**
 * 根据选择器获取所有匹配元素
 * @param {string} selector - CSS选择器
 * @returns {NodeList} DOM元素列表
 */
export function querySelectorAll(selector) {
    return document.querySelectorAll(selector);
}

/**
 * 添加事件监听器
 * @param {Element} element - DOM元素
 * @param {string} event - 事件类型
 * @param {Function} handler - 事件处理函数
 * @param {Object} options - 事件选项
 */
export function addEventListener(element, event, handler, options = {}) {
    if (element && typeof element.addEventListener === 'function') {
        element.addEventListener(event, handler, options);
    }
}

/**
 * 移除事件监听器
 * @param {Element} element - DOM元素
 * @param {string} event - 事件类型
 * @param {Function} handler - 事件处理函数
 */
export function removeEventListener(element, event, handler) {
    if (element && typeof element.removeEventListener === 'function') {
        element.removeEventListener(event, handler);
    }
}
