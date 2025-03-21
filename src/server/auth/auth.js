const jwt = require('jsonwebtoken');
const crypto = require('crypto');
const { query } = require('../db');
const winston = require('winston');

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
async function register(username, password, email) {
  try {
    // 检查用户名是否已存在
    const existingUser = await query('SELECT id FROM users WHERE username = $1', [username]);
    if (existingUser.rows.length > 0) {
      return { success: false, error: '用户名已存在' };
    }

    // 生成密码盐和哈希
    const salt = crypto.randomBytes(16).toString('hex');
    const hash = crypto.pbkdf2Sync(password, salt, 1000, 64, 'sha512').toString('hex');

    // 插入新用户记录
    const result = await query(
      'INSERT INTO users (username, password_hash, password_salt, email) VALUES ($1, $2, $3, $4) RETURNING id',
      [username, hash, salt, email]
    );

    const userId = result.rows[0].id;
    const tokens = generateTokens(userId);

    return { success: true, userId, ...tokens };
  } catch (error) {
    logger.error('用户注册失败:', error);
    return { success: false, error: '注册失败，请稍后重试' };
  }
}

// 用户登录
async function login(username, password) {
  try {
    // 查询用户信息
    const result = await query(
      'SELECT id, password_hash, password_salt FROM users WHERE username = $1',
      [username]
    );

    if (result.rows.length === 0) {
      return { success: false, error: '用户名或密码错误' };
    }

    const user = result.rows[0];
    const hash = crypto.pbkdf2Sync(password, user.password_salt, 1000, 64, 'sha512').toString('hex');

    if (hash !== user.password_hash) {
      return { success: false, error: '用户名或密码错误' };
    }

    const tokens = generateTokens(user.id);
    return { success: true, userId: user.id, ...tokens };
  } catch (error) {
    logger.error('用户登录失败:', error);
    return { success: false, error: '登录失败，请稍后重试' };
  }
}

// 生成访问令牌和刷新令牌
function generateTokens(userId) {
  const accessToken = jwt.sign({ userId }, process.env.JWT_SECRET, { expiresIn: '1h' });
  const refreshToken = jwt.sign({ userId }, process.env.JWT_SECRET, { expiresIn: '7d' });
  return { accessToken, refreshToken };
}

// 刷新访问令牌
function refreshAccessToken(refreshToken) {
  try {
    const decoded = jwt.verify(refreshToken, process.env.JWT_SECRET);
    const accessToken = jwt.sign({ userId: decoded.userId }, process.env.JWT_SECRET, { expiresIn: '1h' });
    return { success: true, accessToken };
  } catch (error) {
    logger.error('刷新令牌失败:', error);
    return { success: false, error: '无效的刷新令牌' };
  }
}

// 验证访问令牌
function verifyAccessToken(token) {
  try {
    const decoded = jwt.verify(token, process.env.JWT_SECRET);
    return { valid: true, userId: decoded.userId };
  } catch (error) {
    logger.error('访问令牌验证失败:', error);
    return { valid: false, error: error.message };
  }
}

module.exports = {
  register,
  login,
  refreshAccessToken,
  verifyAccessToken
};