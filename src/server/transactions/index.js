const express = require('express');
const crypto = require('crypto');
const { query } = require('../db');
const { authMiddleware } = require('../auth');
const winston = require('winston');

const router = express.Router();

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

// 加密函数
const encrypt = (text) => {
  const iv = crypto.randomBytes(12);
  const cipher = crypto.createCipheriv('aes-256-gcm', Buffer.from(process.env.AES_KEY, 'hex'), iv);
  let encrypted = cipher.update(text, 'utf8', 'hex');
  encrypted += cipher.final('hex');
  const authTag = cipher.getAuthTag();
  return { encrypted, iv: iv.toString('hex'), authTag: authTag.toString('hex') };
};

// 解密函数
const decrypt = (encrypted, iv, authTag) => {
  const decipher = crypto.createDecipheriv(
    'aes-256-gcm',
    Buffer.from(process.env.AES_KEY, 'hex'),
    Buffer.from(iv, 'hex')
  );
  decipher.setAuthTag(Buffer.from(authTag, 'hex'));
  let decrypted = decipher.update(encrypted, 'hex', 'utf8');
  decrypted += decipher.final('utf8');
  return decrypted;
};

// 创建交易记录
router.post('/', authMiddleware, async (req, res) => {
  try {
    const { amount, category, transaction_date, memo, is_income } = req.body;
    
    // 加密敏感信息
    const encryptedMemo = encrypt(memo);
    
    const result = await query(
      'INSERT INTO transactions (user_id, amount, category, transaction_date, memo, memo_iv, memo_auth_tag, is_income) VALUES ($1, $2, $3, $4, $5, $6, $7, $8) RETURNING id',
      [req.userId, amount, category, transaction_date, encryptedMemo.encrypted, encryptedMemo.iv, encryptedMemo.authTag, is_income]
    );
    
    res.status(201).json({ id: result.rows[0].id });
  } catch (error) {
    logger.error('创建交易记录失败:', error);
    res.status(500).json({ error: '创建交易记录失败' });
  }
});

// 获取交易记录列表
router.get('/', authMiddleware, async (req, res) => {
  try {
    const { startDate, endDate, category } = req.query;
    let queryText = 'SELECT * FROM transactions WHERE user_id = $1';
    const queryParams = [req.userId];
    
    if (startDate && endDate) {
      queryText += ' AND transaction_date BETWEEN $2 AND $3';
      queryParams.push(startDate, endDate);
    }
    if (category) {
      queryText += ' AND category = $' + (queryParams.length + 1);
      queryParams.push(category);
    }
    
    const result = await query(queryText, queryParams);
    
    // 解密备注信息
    const transactions = result.rows.map(transaction => ({
      ...transaction,
      memo: decrypt(transaction.memo, transaction.memo_iv, transaction.memo_auth_tag)
    }));
    
    res.json(transactions);
  } catch (error) {
    logger.error('获取交易记录失败:', error);
    res.status(500).json({ error: '获取交易记录失败' });
  }
});

// 更新交易记录
router.put('/:id', authMiddleware, async (req, res) => {
  try {
    const { amount, category, transaction_date, memo, is_income } = req.body;
    const transactionId = req.params.id;
    
    // 验证记录所有权
    const checkOwnership = await query(
      'SELECT id FROM transactions WHERE id = $1 AND user_id = $2',
      [transactionId, req.userId]
    );
    
    if (checkOwnership.rows.length === 0) {
      return res.status(403).json({ error: '无权限修改此记录' });
    }
    
    // 加密新的备注信息
    const encryptedMemo = encrypt(memo);
    
    await query(
      'UPDATE transactions SET amount = $1, category = $2, transaction_date = $3, memo = $4, memo_iv = $5, memo_auth_tag = $6, is_income = $7 WHERE id = $8 AND user_id = $9',
      [amount, category, transaction_date, encryptedMemo.encrypted, encryptedMemo.iv, encryptedMemo.authTag, is_income, transactionId, req.userId]
    );
    
    res.json({ message: '更新成功' });
  } catch (error) {
    logger.error('更新交易记录失败:', error);
    res.status(500).json({ error: '更新交易记录失败' });
  }
});

// 删除交易记录
router.delete('/:id', authMiddleware, async (req, res) => {
  try {
    const transactionId = req.params.id;
    
    // 验证记录所有权
    const checkOwnership = await query(
      'SELECT id FROM transactions WHERE id = $1 AND user_id = $2',
      [transactionId, req.userId]
    );
    
    if (checkOwnership.rows.length === 0) {
      return res.status(403).json({ error: '无权限删除此记录' });
    }
    
    await query('DELETE FROM transactions WHERE id = $1 AND user_id = $2', [transactionId, req.userId]);
    
    res.json({ message: '删除成功' });
  } catch (error) {
    logger.error('删除交易记录失败:', error);
    res.status(500).json({ error: '删除交易记录失败' });
  }
});

module.exports = router;