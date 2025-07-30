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
