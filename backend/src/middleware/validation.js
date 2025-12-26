/**
 * 请求体验证中间件
 */

/**
 * 验证交易记录数据
 */
const validateTransaction = (req, res, next) => {
  const { transactionId, amount, timestamp, description, platform, category } = req.body;

  const errors = [];

  // 必填字段验证
  if (!transactionId || typeof transactionId !== 'string') {
    errors.push('transactionId 是必填字段,且必须是字符串');
  }

  if (amount === undefined || typeof amount !== 'number') {
    errors.push('amount 是必填字段,且必须是数字');
  }

  if (!timestamp || !Date.parse(timestamp)) {
    errors.push('timestamp 是必填字段,且必须是有效的日期时间');
  }

  if (!description || typeof description !== 'string') {
    errors.push('description 是必填字段,且必须是字符串');
  }

  if (!platform || typeof platform !== 'string') {
    errors.push('platform 是必填字段,且必须是字符串');
  }

  // 字段长度验证
  if (transactionId && transactionId.length > 255) {
    errors.push('transactionId 长度不能超过 255 个字符');
  }

  if (description && description.length > 1000) {
    errors.push('description 长度不能超过 1000 个字符');
  }

  // 平台枚举验证
  const validPlatforms = ['alipay', 'wechat', 'ccb', 'cmb', 'other'];
  if (platform && !validPlatforms.includes(platform)) {
    errors.push(`platform 必须是以下值之一: ${validPlatforms.join(', ')}`);
  }

  if (errors.length > 0) {
    return res.status(400).json({
      success: false,
      error: '数据验证失败',
      details: errors
    });
  }

  next();
};

/**
 * 验证分类数据
 */
const validateCategory = (req, res, next) => {
  const { name, type, parentId } = req.body;

  const errors = [];

  // 必填字段验证
  if (!name || typeof name !== 'string') {
    errors.push('name 是必填字段,且必须是字符串');
  }

  if (!type || typeof type !== 'string') {
    errors.push('type 是必填字段,且必须是字符串');
  }

  // 字段长度验证
  if (name && name.length > 100) {
    errors.push('name 长度不能超过 100 个字符');
  }

  // 类型枚举验证
  const validTypes = ['expense', 'income'];
  if (type && !validTypes.includes(type)) {
    errors.push(`type 必须是以下值之一: ${validTypes.join(', ')}`);
  }

  if (errors.length > 0) {
    return res.status(400).json({
      success: false,
      error: '数据验证失败',
      details: errors
    });
  }

  next();
};

/**
 * 验证用户注册数据
 */
const validateRegistration = (req, res, next) => {
  const { username, password, email } = req.body;

  const errors = [];

  // 用户名验证
  if (!username || typeof username !== 'string') {
    errors.push('username 是必填字段');
  } else if (username.length < 3 || username.length > 20) {
    errors.push('username 长度必须在 3-20 个字符之间');
  } else if (!/^[a-zA-Z0-9_]+$/.test(username)) {
    errors.push('username 只能包含字母、数字和下划线');
  }

  // 密码验证
  if (!password || typeof password !== 'string') {
    errors.push('password 是必填字段');
  } else if (password.length < 6) {
    errors.push('password 长度不能少于 6 个字符');
  }

  // 邮箱验证(可选)
  if (email && typeof email === 'string') {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
      errors.push('email 格式不正确');
    }
  }

  if (errors.length > 0) {
    return res.status(400).json({
      success: false,
      error: '数据验证失败',
      details: errors
    });
  }

  next();
};

/**
 * 验证用户登录数据
 */
const validateLogin = (req, res, next) => {
  const { username, password } = req.body;

  const errors = [];

  if (!username || typeof username !== 'string') {
    errors.push('username 是必填字段');
  }

  if (!password || typeof password !== 'string') {
    errors.push('password 是必填字段');
  }

  if (errors.length > 0) {
    return res.status(400).json({
      success: false,
      error: '数据验证失败',
      details: errors
    });
  }

  next();
};

module.exports = {
  validateTransaction,
  validateCategory,
  validateRegistration,
  validateLogin
};
