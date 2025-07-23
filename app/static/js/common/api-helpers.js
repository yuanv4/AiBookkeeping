/**
 * API请求辅助函数模块
 * 提供统一的API请求处理功能
 */

import { showNotification } from './notifications.js';

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
 * 简化的API请求函数
 */

/**
 * 发送GET请求（简化版）
 * @param {string} url - 请求URL
 * @param {boolean} showLoading - 是否显示加载状态，默认true
 * @returns {Promise} 请求Promise
 */
export async function get(url, showLoading = true) {
    return await apiService.get(url, { showLoading });
}

/**
 * 发送POST请求（简化版）
 * @param {string} url - 请求URL
 * @param {FormData|Object} data - 请求数据
 * @param {boolean} showLoading - 是否显示加载状态，默认true
 * @returns {Promise} 请求Promise
 */
export async function post(url, data, showLoading = true) {
    return await apiService.post(url, data, { showLoading });
}

/**
 * 发送文件上传请求
 * @param {string} url - 请求URL
 * @param {FormData} formData - 表单数据
 * @param {Function} progressCallback - 进度回调函数
 * @returns {Promise} 请求Promise
 */
export async function uploadFile(url, formData, progressCallback = null) {
    return new Promise((resolve, reject) => {
        const xhr = new XMLHttpRequest();
        
        // 监听上传进度
        if (progressCallback && typeof progressCallback === 'function') {
            xhr.upload.addEventListener('progress', (event) => {
                if (event.lengthComputable) {
                    const percentComplete = (event.loaded / event.total) * 100;
                    progressCallback(percentComplete);
                }
            });
        }
        
        // 监听请求完成
        xhr.addEventListener('load', () => {
            if (xhr.status >= 200 && xhr.status < 300) {
                try {
                    const response = JSON.parse(xhr.responseText);
                    resolve({ success: true, data: response });
                } catch (error) {
                    resolve({ success: true, data: xhr.responseText });
                }
            } else {
                reject(new Error(`HTTP ${xhr.status}: ${xhr.statusText}`));
            }
        });
        
        // 监听请求错误
        xhr.addEventListener('error', () => {
            reject(new Error('网络请求失败'));
        });
        
        // 发送请求
        xhr.open('POST', url);
        xhr.send(formData);
    });
}
