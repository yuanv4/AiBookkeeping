/**
 * 格式化工具函数模块
 * 提供各种数据格式化功能
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
 * 格式化货币金额
 * @param {number} amount - 金额
 * @param {string} currency - 货币符号，默认为 '¥'
 * @param {number} decimals - 小数位数，默认为 2
 * @returns {string} 格式化后的货币字符串
 */
export function formatCurrency(amount, currency = '¥', decimals = 2) {
    if (amount === null || amount === undefined || isNaN(amount)) {
        return `${currency}0.00`;
    }
    
    const formatted = Number(amount).toFixed(decimals);
    const parts = formatted.split('.');
    parts[0] = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, ',');
    
    return `${currency}${parts.join('.')}`;
}

/**
 * 格式化百分比
 * @param {number} value - 数值
 * @param {number} decimals - 小数位数，默认为 2
 * @returns {string} 格式化后的百分比字符串
 */
export function formatPercentage(value, decimals = 2) {
    if (value === null || value === undefined || isNaN(value)) {
        return '0.00%';
    }
    
    return `${(value * 100).toFixed(decimals)}%`;
}

/**
 * 格式化数字，添加千分位分隔符
 * @param {number} number - 要格式化的数字
 * @param {number} decimals - 小数位数，默认为 2
 * @returns {string} 格式化后的数字字符串
 */
export function formatNumber(number, decimals = 2) {
    if (number === null || number === undefined || isNaN(number)) {
        return '0';
    }
    
    const formatted = Number(number).toFixed(decimals);
    const parts = formatted.split('.');
    parts[0] = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, ',');
    
    return parts.join('.');
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
