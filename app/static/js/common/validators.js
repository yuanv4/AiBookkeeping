/**
 * 验证工具函数模块
 * 提供各种数据验证功能
 */

/**
 * 验证邮箱格式
 * @param {string} email - 邮箱地址
 * @returns {boolean} 验证结果
 */
export function validateEmail(email) {
    if (!email || typeof email !== 'string') return false;
    
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

/**
 * 验证手机号格式（中国大陆）
 * @param {string} phone - 手机号
 * @returns {boolean} 验证结果
 */
export function validatePhone(phone) {
    if (!phone || typeof phone !== 'string') return false;
    
    const phoneRegex = /^1[3-9]\d{9}$/;
    return phoneRegex.test(phone);
}

/**
 * 验证日期格式 (YYYY-MM-DD)
 * @param {string} dateString - 日期字符串
 * @returns {boolean} 验证结果
 */
export function validateDate(dateString) {
    if (!dateString || typeof dateString !== 'string') return false;
    
    const dateRegex = /^\d{4}-\d{2}-\d{2}$/;
    if (!dateRegex.test(dateString)) return false;
    
    const date = new Date(dateString);
    return date instanceof Date && !isNaN(date);
}

/**
 * 验证金额格式
 * @param {string|number} amount - 金额
 * @returns {boolean} 验证结果
 */
export function validateAmount(amount) {
    if (amount === null || amount === undefined || amount === '') return false;
    
    const numAmount = Number(amount);
    return !isNaN(numAmount) && isFinite(numAmount);
}

/**
 * 验证必填字段
 * @param {any} value - 要验证的值
 * @returns {boolean} 验证结果
 */
export function validateRequired(value) {
    if (value === null || value === undefined) return false;
    if (typeof value === 'string') return value.trim().length > 0;
    if (Array.isArray(value)) return value.length > 0;
    return true;
}

/**
 * 验证字符串长度
 * @param {string} str - 要验证的字符串
 * @param {number} min - 最小长度
 * @param {number} max - 最大长度
 * @returns {boolean} 验证结果
 */
export function validateLength(str, min = 0, max = Infinity) {
    if (!str || typeof str !== 'string') return false;
    
    const length = str.trim().length;
    return length >= min && length <= max;
}

/**
 * 验证数字范围
 * @param {number} value - 要验证的数值
 * @param {number} min - 最小值
 * @param {number} max - 最大值
 * @returns {boolean} 验证结果
 */
export function validateRange(value, min = -Infinity, max = Infinity) {
    const numValue = Number(value);
    if (isNaN(numValue)) return false;
    
    return numValue >= min && numValue <= max;
}

/**
 * 验证银行卡号格式（简单验证）
 * @param {string} cardNumber - 银行卡号
 * @returns {boolean} 验证结果
 */
export function validateBankCard(cardNumber) {
    if (!cardNumber || typeof cardNumber !== 'string') return false;
    
    // 移除空格和连字符
    const cleaned = cardNumber.replace(/[\s-]/g, '');
    
    // 银行卡号通常为13-19位数字
    const cardRegex = /^\d{13,19}$/;
    return cardRegex.test(cleaned);
}

/**
 * 验证身份证号格式（中国大陆）
 * @param {string} idCard - 身份证号
 * @returns {boolean} 验证结果
 */
export function validateIdCard(idCard) {
    if (!idCard || typeof idCard !== 'string') return false;
    
    // 18位身份证号正则
    const idCardRegex = /^[1-9]\d{5}(18|19|20)\d{2}((0[1-9])|(1[0-2]))(([0-2][1-9])|10|20|30|31)\d{3}[0-9Xx]$/;
    return idCardRegex.test(idCard);
}

/**
 * 验证表单数据
 * @param {Object} data - 表单数据
 * @param {Object} rules - 验证规则
 * @returns {Object} 验证结果 {isValid: boolean, errors: Object}
 */
export function validateForm(data, rules) {
    const errors = {};
    let isValid = true;
    
    for (const [field, fieldRules] of Object.entries(rules)) {
        const value = data[field];
        const fieldErrors = [];
        
        for (const rule of fieldRules) {
            const { type, message, ...params } = rule;
            let valid = true;
            
            switch (type) {
                case 'required':
                    valid = validateRequired(value);
                    break;
                case 'email':
                    valid = !value || validateEmail(value);
                    break;
                case 'phone':
                    valid = !value || validatePhone(value);
                    break;
                case 'date':
                    valid = !value || validateDate(value);
                    break;
                case 'amount':
                    valid = !value || validateAmount(value);
                    break;
                case 'length':
                    valid = !value || validateLength(value, params.min, params.max);
                    break;
                case 'range':
                    valid = !value || validateRange(value, params.min, params.max);
                    break;
                default:
                    console.warn(`未知的验证规则类型: ${type}`);
            }
            
            if (!valid) {
                fieldErrors.push(message || `${field} 验证失败`);
                isValid = false;
            }
        }
        
        if (fieldErrors.length > 0) {
            errors[field] = fieldErrors;
        }
    }
    
    return { isValid, errors };
}
