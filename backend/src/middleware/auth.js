const jwt = require('jsonwebtoken');
const { PrismaClient } = require('@prisma/client');
const prisma = new PrismaClient();

/**
 * JWT 认证中间件
 * 验证请求头中的 JWT token
 */
const authenticate = async (req, res, next) => {
  try {
    // 从请求头获取 token
    const authHeader = req.headers.authorization;

    if (!authHeader || !authHeader.startsWith('Bearer ')) {
      return res.status(401).json({
        success: false,
        error: '未提供认证令牌'
      });
    }

    const token = authHeader.substring(7); // 移除 'Bearer ' 前缀

    // 验证 token
    const decoded = jwt.verify(token, process.env.JWT_SECRET);

    // 查询用户是否存在
    const user = await prisma.user.findUnique({
      where: { userId: decoded.userId },
      select: {
        userId: true,
        username: true,
        email: true,
        createdAt: true
      }
    });

    if (!user) {
      return res.status(401).json({
        success: false,
        error: '用户不存在'
      });
    }

    // 将用户信息附加到请求对象
    req.user = user;
    next();
  } catch (error) {
    if (error.name === 'JsonWebTokenError') {
      return res.status(401).json({
        success: false,
        error: '无效的认证令牌'
      });
    }
    if (error.name === 'TokenExpiredError') {
      return res.status(401).json({
        success: false,
        error: '认证令牌已过期'
      });
    }
    console.error('认证错误:', error);
    return res.status(500).json({
      success: false,
      error: '认证过程中发生错误'
    });
  }
};

/**
 * 可选认证中间件
 * 如果提供了 token 则验证,否则继续处理请求
 */
const optionalAuth = async (req, res, next) => {
  try {
    const authHeader = req.headers.authorization;

    if (!authHeader || !authHeader.startsWith('Bearer ')) {
      return next();
    }

    const token = authHeader.substring(7);
    const decoded = jwt.verify(token, process.env.JWT_SECRET);

    const user = await prisma.user.findUnique({
      where: { userId: decoded.userId },
      select: {
        userId: true,
        username: true,
        email: true,
        createdAt: true
      }
    });

    if (user) {
      req.user = user;
    }

    next();
  } catch (error) {
    // 忽略错误,继续处理请求
    next();
  }
};

module.exports = {
  authenticate,
  optionalAuth
};
