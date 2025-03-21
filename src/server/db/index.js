const { Pool } = require('pg');
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

// 数据库连接配置
const pool = new Pool({
  host: process.env.DB_HOST || 'localhost',
  port: process.env.DB_PORT || 5432,
  database: process.env.DB_NAME || 'ai_bookkeeping',
  user: process.env.DB_USER || 'postgres',
  password: process.env.DB_PASSWORD || 'postgres',
});

// 测试数据库连接
pool.connect()
  .then(() => {
    logger.info('数据库连接成功');
  })
  .catch(err => {
    logger.error('数据库连接失败:', err);
  });

// 查询包装函数
const query = async (text, params) => {
  try {
    const start = Date.now();
    const res = await pool.query(text, params);
    const duration = Date.now() - start;
    logger.debug('执行查询', { text, duration, rows: res.rowCount });
    return res;
  } catch (err) {
    logger.error('查询执行失败:', err);
    throw err;
  }
};

module.exports = {
  query,
  pool
};