const express = require('express');
const dotenv = require('dotenv');
const path = require('path');
const winston = require('winston');
const { authMiddleware } = require('./auth/middleware');
const transactionsRouter = require('./transactions');
const uploadRouter = require('./upload');
const historyRouter = require('./routes/history');
const fs = require('fs');

// 加载环境变量配置
dotenv.config({ path: path.join(__dirname, '../../config/.env') });

// 配置日志记录器
const logger = winston.createLogger({
  level: process.env.LOG_LEVEL || 'info',
  format: winston.format.combine(
    winston.format.timestamp({
      format: 'YYYY-MM-DD HH:mm:ss'
    }),
    winston.format.printf(({ level, message, timestamp }) => {
      return `${timestamp} [${level.toUpperCase()}] ${message}`;
    })
  ),
  transports: [
    new winston.transports.File({ 
      filename: path.join(__dirname, 'logs/error.log'),
      level: 'error',
      maxsize: 5242880, // 5MB
      maxFiles: 5,
      tailable: true,
      options: { flags: 'a' } // 追加模式
    }),
    new winston.transports.File({ 
      filename: path.join(__dirname, 'logs/combined.log'),
      maxsize: 10485760, // 10MB
      maxFiles: 5,
      tailable: true,
      options: { flags: 'a' } // 追加模式
    }),
    new winston.transports.Console({
      format: winston.format.combine(
        winston.format.colorize(),
        winston.format.simple()
      )
    })
  ]
});

// 确保日志目录存在
const logDir = path.join(__dirname, 'logs');
if (!fs.existsSync(logDir)) {
  fs.mkdirSync(logDir, { recursive: true });
}

// 清空日志文件
const errorLogPath = path.join(logDir, 'error.log');
const combinedLogPath = path.join(logDir, 'combined.log');

fs.writeFileSync(errorLogPath, '');
fs.writeFileSync(combinedLogPath, '');

const app = express();

// 中间件配置
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// 静态文件服务
app.use(express.static(path.join(__dirname, '../../public')));

// API路由
app.use('/api/upload', uploadRouter);
app.use('/api/transactions', authMiddleware, transactionsRouter);
app.use('/api/history', historyRouter);

// 基础路由
app.get('/health', (req, res) => {
  res.json({ status: 'ok' });
});

// 前端路由处理
app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, '../../public/index.html'));
});

// 错误处理中间件
app.use((err, req, res, next) => {
  logger.error('应用错误:', err);
  res.status(500).json({ error: '服务器内部错误' });
});

// 仅在直接运行时启动服务器
if (require.main === module) {
  const port = process.env.PORT || 3000;
  app.listen(port, () => {
    logger.info(`服务器运行在端口 ${port}`);
  });
}

// 导出app实例供测试使用
module.exports = app;