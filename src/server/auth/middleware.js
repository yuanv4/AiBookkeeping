const jwt = require('jsonwebtoken');
const winston = require('winston');
const path = require('path');

// 获取日志记录器实例
const logger = winston.createLogger({
  level: process.env.LOG_LEVEL || 'info',
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.json()
  ),
  transports: [
    new winston.transports.File({ filename: path.join(__dirname, '../logs/error.log'), level: 'error' }),
    new winston.transports.File({ filename: path.join(__dirname, '../logs/combined.log') })
  ]
});

// 认证中间件
const authMiddleware = (req, res, next) => {
  // 如果认证被禁用，直接通过
  if (process.env.AUTH_ENABLED === 'false') {
    req.userId = 'dev-user-id';
    return next();
  }

  const authHeader = req.headers.authorization;
  if (!authHeader) {
    return res.status(401).json({ error: '未提供认证令牌' });
  }

  const token = authHeader.split(' ')[1];
  if (!token) {
    return res.status(401).json({ error: '无效的认证令牌格式' });
  }

  try {
    // 在测试环境中，允许使用测试token
    if (process.env.NODE_ENV === 'test' && token === 'test-token') {
      req.userId = 'test-user-id';
      return next();
    }

    const decoded = jwt.verify(token, process.env.JWT_SECRET);
    req.userId = decoded.userId;
    next();
  } catch (error) {
    logger.error('认证失败:', error);
    return res.status(401).json({ error: '无效的认证令牌' });
  }
};

// 资源所有者验证中间件
const ownershipMiddleware = (resourceType) => async (req, res, next) => {
  try {
    const userId = req.userId;
    const resourceId = req.params.id;

    if (!resourceId) {
      return res.status(400).json({ error: '未提供资源ID' });
    }

    // 根据资源类型查询所有权
    let query;
    switch (resourceType) {
      case 'transaction':
        query = 'SELECT user_id FROM transactions WHERE id = $1';
        break;
      case 'budget':
        query = 'SELECT user_id FROM budgets WHERE id = $1';
        break;
      case 'upload':
        query = 'SELECT user_id FROM uploads WHERE id = $1';
        break;
      default:
        return res.status(400).json({ error: '无效的资源类型' });
    }

    const result = await pool.query(query, [resourceId]);
    if (result.rows.length === 0) {
      return res.status(404).json({ error: '资源不存在' });
    }

    if (result.rows[0].user_id !== userId) {
      return res.status(403).json({ error: '无权访问此资源' });
    }

    next();
  } catch (error) {
    logger.error('所有权验证错误:', error);
    return res.status(500).json({ error: '所有权验证过程发生错误' });
  }
};

module.exports = {
  authMiddleware,
  ownershipMiddleware
};