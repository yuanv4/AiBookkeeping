const express = require('express');
const { hashPassword, verifyPassword, generateToken } = require('./index');
const { query } = require('../db');
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

// 用户注册
router.post('/register', async (req, res) => {
  try {
    const { username, password, email } = req.body;

    // 检查用户名是否已存在
    const existingUser = await query('SELECT id FROM users WHERE username = $1', [username]);
    if (existingUser.rows.length > 0) {
      return res.status(400).json({ error: '用户名已存在' });
    }

    // 加密密码
    const { salt, hash } = hashPassword(password);

    // 创建用户记录
    const result = await query(
      'INSERT INTO users (username, password_hash, password_salt, email) VALUES ($1, $2, $3, $4) RETURNING id',
      [username, hash, salt, email]
    );

    // 生成JWT令牌
    const { token, refreshToken } = generateToken(result.rows[0].id);

    res.status(201).json({
      userId: result.rows[0].id,
      token,
      refreshToken
    });
  } catch (error) {
    logger.error('用户注册失败:', error);
    res.status(500).json({ error: '注册失败，请稍后重试' });
  }
});

// 用户登录
router.post('/login', async (req, res) => {
  try {
    const { username, password } = req.body;

    // 查找用户
    const result = await query(
      'SELECT id, password_hash, password_salt FROM users WHERE username = $1',
      [username]
    );

    if (result.rows.length === 0) {
      return res.status(401).json({ error: '用户名或密码错误' });
    }

    const user = result.rows[0];

    // 验证密码
    if (!verifyPassword(password, user.password_hash, user.password_salt)) {
      return res.status(401).json({ error: '用户名或密码错误' });
    }

    // 生成新的JWT令牌
    const { token, refreshToken } = generateToken(user.id);

    res.json({
      userId: user.id,
      token,
      refreshToken
    });
  } catch (error) {
    logger.error('用户登录失败:', error);
    res.status(500).json({ error: '登录失败，请稍后重试' });
  }
});

// 刷新令牌
router.post('/refresh-token', async (req, res) => {
  try {
    const { refreshToken } = req.body;
    const { valid, userId } = verifyToken(refreshToken);

    if (!valid) {
      return res.status(401).json({ error: '无效的刷新令牌' });
    }

    // 生成新的访问令牌
    const tokens = generateToken(userId);

    res.json(tokens);
  } catch (error) {
    logger.error('令牌刷新失败:', error);
    res.status(500).json({ error: '令牌刷新失败' });
  }
});

module.exports = router;