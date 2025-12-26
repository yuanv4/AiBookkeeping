const jwt = require('jsonwebtoken');
const bcrypt = require('bcrypt');
const { PrismaClient } = require('@prisma/client');
const prisma = new PrismaClient();

/**
 * 生成 JWT token
 */
const generateToken = (userId) => {
  return jwt.sign(
    { userId },
    process.env.JWT_SECRET,
    { expiresIn: process.env.JWT_EXPIRES_IN || '7d' }
  );
};

/**
 * 用户注册
 */
const register = async (username, password, email = null) => {
  // 检查用户名是否已存在
  const existingUser = await prisma.user.findUnique({
    where: { username }
  });

  if (existingUser) {
    throw new Error('用户名已存在');
  }

  // 检查邮箱是否已存在
  if (email) {
    const existingEmail = await prisma.user.findUnique({
      where: { email }
    });

    if (existingEmail) {
      throw new Error('邮箱已被使用');
    }
  }

  // 加密密码
  const hashedPassword = await bcrypt.hash(password, 10);

  // 创建用户
  const user = await prisma.user.create({
    data: {
      username,
      password: hashedPassword,
      email
    },
    select: {
      userId: true,
      username: true,
      email: true,
      createdAt: true
    }
  });

  // 生成 token
  const token = generateToken(user.userId);

  return {
    user,
    token
  };
};

/**
 * 用户登录
 */
const login = async (username, password) => {
  // 查找用户
  const user = await prisma.user.findUnique({
    where: { username }
  });

  if (!user) {
    throw new Error('用户名或密码错误');
  }

  // 验证密码
  const isPasswordValid = await bcrypt.compare(password, user.password);

  if (!isPasswordValid) {
    throw new Error('用户名或密码错误');
  }

  // 生成 token
  const token = generateToken(user.userId);

  // 返回用户信息(不包含密码)
  const { password: _, ...userWithoutPassword } = user;

  return {
    user: userWithoutPassword,
    token
  };
};

/**
 * 验证 token
 */
const verifyToken = (token) => {
  try {
    const decoded = jwt.verify(token, process.env.JWT_SECRET);
    return decoded;
  } catch (error) {
    throw new Error('无效的 token');
  }
};

/**
 * 获取用户信息
 */
const getUserById = async (userId) => {
  const user = await prisma.user.findUnique({
    where: { userId },
    select: {
      userId: true,
      username: true,
      email: true,
      createdAt: true
    }
  });

  if (!user) {
    throw new Error('用户不存在');
  }

  return user;
};

module.exports = {
  register,
  login,
  verifyToken,
  getUserById,
  generateToken
};
