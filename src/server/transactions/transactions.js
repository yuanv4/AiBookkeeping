const { query } = require('../db');
const winston = require('winston');
const crypto = require('crypto');

// 获取日志记录器实例
const logger = winston.createLogger({
  level: process.env.LOG_LEVEL || 'info',
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.json()
  ),
  transports: [
    new winston.transports.File({ filename: '../logs/error.log', level: 'error' }),
    new winston.transports.File({ filename: '../logs/combined.log' })
  ]
});

// 加密交易记录敏感信息
function encryptData(data) {
  const cipher = crypto.createCipheriv('aes-256-gcm', process.env.AES_KEY, crypto.randomBytes(12));
  let encrypted = cipher.update(JSON.stringify(data), 'utf8', 'hex');
  encrypted += cipher.final('hex');
  const authTag = cipher.getAuthTag();
  return { encrypted, authTag: authTag.toString('hex') };
}

// 解密交易记录敏感信息
function decryptData(encrypted, authTag) {
  const decipher = crypto.createDecipheriv('aes-256-gcm', process.env.AES_KEY, crypto.randomBytes(12));
  decipher.setAuthTag(Buffer.from(authTag, 'hex'));
  let decrypted = decipher.update(encrypted, 'hex', 'utf8');
  decrypted += decipher.final('utf8');
  return JSON.parse(decrypted);
}

// 创建交易记录
async function createTransaction(userId, transactionData) {
  try {
    const { amount, category, transaction_date, memo, is_income } = transactionData;
    
    // 加密敏感信息
    const sensitiveData = { amount, memo };
    const { encrypted, authTag } = encryptData(sensitiveData);

    const result = await query(
      'INSERT INTO transactions (user_id, amount, category, transaction_date, memo, is_income, encrypted_data, auth_tag) VALUES ($1, $2, $3, $4, $5, $6, $7, $8) RETURNING id',
      [userId, amount, category, transaction_date, memo, is_income, encrypted, authTag]
    );

    return { success: true, transactionId: result.rows[0].id };
  } catch (error) {
    logger.error('创建交易记录失败:', error);
    return { success: false, error: '创建交易记录失败，请稍后重试' };
  }
}

// 获取交易记录列表
async function getTransactions(userId, filters = {}) {
  try {
    let queryText = 'SELECT * FROM transactions WHERE user_id = $1';
    const queryParams = [userId];

    // 添加过滤条件
    if (filters.startDate) {
      queryText += ' AND transaction_date >= $' + (queryParams.length + 1);
      queryParams.push(filters.startDate);
    }
    if (filters.endDate) {
      queryText += ' AND transaction_date <= $' + (queryParams.length + 1);
      queryParams.push(filters.endDate);
    }
    if (filters.category) {
      queryText += ' AND category = $' + (queryParams.length + 1);
      queryParams.push(filters.category);
    }
    if (typeof filters.is_income === 'boolean') {
      queryText += ' AND is_income = $' + (queryParams.length + 1);
      queryParams.push(filters.is_income);
    }

    queryText += ' ORDER BY transaction_date DESC';

    const result = await query(queryText, queryParams);
    return { success: true, transactions: result.rows };
  } catch (error) {
    logger.error('获取交易记录失败:', error);
    return { success: false, error: '获取交易记录失败，请稍后重试' };
  }
}

// 更新交易记录
async function updateTransaction(userId, transactionId, updateData) {
  try {
    // 验证交易记录所有权
    const ownership = await query('SELECT user_id FROM transactions WHERE id = $1', [transactionId]);
    if (ownership.rows.length === 0) {
      return { success: false, error: '交易记录不存在' };
    }
    if (ownership.rows[0].user_id !== userId) {
      return { success: false, error: '无权修改此交易记录' };
    }

    const { amount, category, transaction_date, memo, is_income } = updateData;
    
    // 加密更新后的敏感信息
    const sensitiveData = { amount, memo };
    const { encrypted, authTag } = encryptData(sensitiveData);

    const result = await query(
      'UPDATE transactions SET amount = $1, category = $2, transaction_date = $3, memo = $4, is_income = $5, encrypted_data = $6, auth_tag = $7, updated_at = CURRENT_TIMESTAMP WHERE id = $8 AND user_id = $9',
      [amount, category, transaction_date, memo, is_income, encrypted, authTag, transactionId, userId]
    );

    return { success: true };
  } catch (error) {
    logger.error('更新交易记录失败:', error);
    return { success: false, error: '更新交易记录失败，请稍后重试' };
  }
}

// 删除交易记录
async function deleteTransaction(userId, transactionId) {
  try {
    // 验证交易记录所有权
    const ownership = await query('SELECT user_id FROM transactions WHERE id = $1', [transactionId]);
    if (ownership.rows.length === 0) {
      return { success: false, error: '交易记录不存在' };
    }
    if (ownership.rows[0].user_id !== userId) {
      return { success: false, error: '无权删除此交易记录' };
    }

    await query('DELETE FROM transactions WHERE id = $1 AND user_id = $2', [transactionId, userId]);
    return { success: true };
  } catch (error) {
    logger.error('删除交易记录失败:', error);
    return { success: false, error: '删除交易记录失败，请稍后重试' };
  }
}

module.exports = {
  createTransaction,
  getTransactions,
  updateTransaction,
  deleteTransaction
};