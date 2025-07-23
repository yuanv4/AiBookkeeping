/**
 * 通知系统模块
 * 提供统一的消息通知功能
 */

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
 * 显示成功通知
 * @param {string} message - 通知消息
 * @param {number} duration - 显示时长（毫秒），默认3000ms
 */
export function showSuccess(message, duration = 3000) {
    return showNotification(message, 'success', duration);
}

/**
 * 显示错误通知
 * @param {string} message - 通知消息
 * @param {number} duration - 显示时长（毫秒），默认5000ms
 */
export function showError(message, duration = 5000) {
    return showNotification(message, 'error', duration);
}

/**
 * 显示警告通知
 * @param {string} message - 通知消息
 * @param {number} duration - 显示时长（毫秒），默认4000ms
 */
export function showWarning(message, duration = 4000) {
    return showNotification(message, 'warning', duration);
}

/**
 * 显示信息通知
 * @param {string} message - 通知消息
 * @param {number} duration - 显示时长（毫秒），默认3000ms
 */
export function showInfo(message, duration = 3000) {
    return showNotification(message, 'info', duration);
}

/**
 * 清除所有通知
 */
export function clearAllNotifications() {
    const container = document.getElementById('notification-container');
    if (container) {
        container.innerHTML = '';
    }
}

/**
 * 显示确认对话框
 * @param {string} message - 确认消息
 * @param {string} title - 对话框标题，默认为"确认"
 * @returns {Promise<boolean>} 用户选择结果
 */
export function showConfirm(message, title = '确认') {
    return new Promise((resolve) => {
        // 创建模态框HTML
        const modalHtml = `
            <div class="modal fade" id="confirmModal" tabindex="-1" aria-hidden="true">
                <div class="modal-dialog">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">${escapeHtml(title)}</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                        </div>
                        <div class="modal-body">
                            <p>${escapeHtml(message)}</p>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">取消</button>
                            <button type="button" class="btn btn-primary" id="confirmBtn">确认</button>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // 添加到页面
        document.body.insertAdjacentHTML('beforeend', modalHtml);
        
        const modalElement = document.getElementById('confirmModal');
        const modal = new bootstrap.Modal(modalElement);
        
        // 绑定事件
        const confirmBtn = document.getElementById('confirmBtn');
        confirmBtn.addEventListener('click', () => {
            modal.hide();
            resolve(true);
        });
        
        modalElement.addEventListener('hidden.bs.modal', () => {
            modalElement.remove();
            resolve(false);
        });
        
        modal.show();
    });
}

/**
 * 显示加载提示
 * @param {string} message - 加载消息，默认为"加载中..."
 * @returns {Function} 关闭加载提示的函数
 */
export function showLoading(message = '加载中...') {
    const loadingHtml = `
        <div class="modal fade" id="loadingModal" tabindex="-1" aria-hidden="true" data-bs-backdrop="static">
            <div class="modal-dialog modal-dialog-centered">
                <div class="modal-content">
                    <div class="modal-body text-center py-4">
                        <div class="spinner-border text-primary mb-3" role="status">
                            <span class="visually-hidden">Loading...</span>
                        </div>
                        <p class="mb-0">${escapeHtml(message)}</p>
                    </div>
                </div>
            </div>
        </div>
    `;

    document.body.insertAdjacentHTML('beforeend', loadingHtml);
    
    const modalElement = document.getElementById('loadingModal');
    const modal = new bootstrap.Modal(modalElement);
    modal.show();

    // 返回关闭函数
    return () => {
        modal.hide();
        modalElement.addEventListener('hidden.bs.modal', () => {
            modalElement.remove();
        });
    };
}
