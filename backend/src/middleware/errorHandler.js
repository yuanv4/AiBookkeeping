/**
 * 全局错误处理中间件
 */

/**
 * Prisma 错误码映射
 */
const PRISMA_ERROR_MAP = {
  P2002: '数据已存在',
  P2025: '记录不存在',
  P2003: '外键约束失败',
  P2014: '关联数据存在'
};

/**
 * 错误处理中间件
 */
const errorHandler = (err, req, res, next) => {
  console.error('错误:', err);

  // Prisma 错误
  if (err.code && err.code.startsWith('P')) {
    const message = PRISMA_ERROR_MAP[err.code] || '数据库操作失败';
    return res.status(400).json({
      success: false,
      error: message,
      code: err.code
    });
  }

  // JWT 错误
  if (err.name === 'JsonWebTokenError') {
    return res.status(401).json({
      success: false,
      error: '无效的认证令牌'
    });
  }

  if (err.name === 'TokenExpiredError') {
    return res.status(401).json({
      success: false,
      error: '认证令牌已过期'
    });
  }

  // 验证错误
  if (err.name === 'ValidationError') {
    return res.status(400).json({
      success: false,
      error: err.message,
      details: err.details
    });
  }

  // 默认错误
  res.status(500).json({
    success: false,
    error: process.env.NODE_ENV === 'production'
      ? '服务器内部错误'
      : err.message
  });
};

/**
 * 404 处理中间件
 */
const notFoundHandler = (req, res) => {
  res.status(404).json({
    success: false,
    error: '请求的资源不存在'
  });
});

/**
 * 异步错误包装器
 * 用于捕获异步路由中的错误
 */
const asyncHandler = (fn) => (req, res, next) => {
  Promise.resolve(fn(req, res, next)).catch(next);
};

module.exports = {
  errorHandler,
  notFoundHandler,
  asyncHandler
};
