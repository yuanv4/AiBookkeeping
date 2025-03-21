const express = require('express');
// 移除数据库引用
// const { query, pool } = require('../db');
const { authMiddleware } = require('../auth/middleware');
const winston = require('winston');
const fs = require('fs').promises;
const path = require('path');

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

// 获取所有上传记录
router.get('/uploads', async (req, res) => {
  try {
    // 获取用户ID，如果已登录
    const userId = req.user ? req.user.id : null;
    
    // 读取所有上传记录文件
    const uploadsDir = path.join(__dirname, '../../../database/uploads');
    
    // 确保目录存在
    try {
      await fs.access(uploadsDir);
    } catch (error) {
      // 如果目录不存在，创建它
      await fs.mkdir(uploadsDir, { recursive: true });
    }
    
    let files = [];
    try {
      files = await fs.readdir(uploadsDir);
    } catch (error) {
      logger.error('读取上传目录失败:', error);
      return res.json({ uploads: [] });
    }
    
    const uploads = [];
    
    // 读取每个上传记录文件
    for (const file of files) {
      if (!file.endsWith('.json')) continue;
      
      try {
        const fileContent = await fs.readFile(path.join(uploadsDir, file), 'utf-8');
        const uploadRecord = JSON.parse(fileContent);
        
        // 如果指定了用户ID，只返回该用户的记录
        if (userId && uploadRecord.userId !== userId) {
          continue;
        }
        
        uploads.push({
          id: uploadRecord.id,
          filename: uploadRecord.originalName,
          uploadDate: uploadRecord.createdAt,
          size: formatFileSize(uploadRecord.size),
          transactionCount: uploadRecord.summary.transactionCount,
          totalIncome: uploadRecord.summary.totalIncome,
          totalExpense: uploadRecord.summary.totalExpense,
          balance: uploadRecord.summary.balance
        });
      } catch (error) {
        logger.error(`解析上传记录文件 ${file} 失败:`, error);
        // 跳过无法解析的文件
        continue;
      }
    }
    
    // 按上传日期降序排序
    uploads.sort((a, b) => new Date(b.uploadDate) - new Date(a.uploadDate));
    
    res.json({ uploads });
  } catch (error) {
    logger.error('获取上传记录失败:', error);
    res.status(500).json({ error: '获取上传记录失败', message: error.message });
  }
});

// 获取特定上传的交易记录
router.get('/uploads/:uploadId/transactions', async (req, res) => {
  try {
    const { uploadId } = req.params;
    const userId = req.user ? req.user.id : null;
    
    // 首先验证上传记录是否存在并属于该用户
    const uploadsDir = path.join(__dirname, '../../../database/uploads');
    const transactionsDir = path.join(__dirname, '../../../database/transactions');
    
    // 确保目录存在
    try {
      await fs.access(uploadsDir);
      await fs.access(transactionsDir);
    } catch (error) {
      return res.status(404).json({ error: '上传记录不存在' });
    }
    
    // 读取上传记录
    try {
      const uploadFilePath = path.join(uploadsDir, `${uploadId}.json`);
      const uploadContent = await fs.readFile(uploadFilePath, 'utf-8');
      const uploadRecord = JSON.parse(uploadContent);
      
      // 如果指定了用户ID，验证记录所有权
      if (userId && uploadRecord.userId !== userId) {
        return res.status(403).json({ error: '无权访问此记录' });
      }
      
      // 读取交易记录
      const transactionsFilePath = path.join(transactionsDir, `${uploadId}.json`);
      const transactionsContent = await fs.readFile(transactionsFilePath, 'utf-8');
      const transactions = JSON.parse(transactionsContent);
      
      res.json({ transactions });
    } catch (error) {
      if (error.code === 'ENOENT') {
        return res.status(404).json({ error: '上传记录不存在' });
      }
      throw error;
    }
  } catch (error) {
    logger.error('获取交易记录失败:', error);
    res.status(500).json({ error: '获取交易记录失败', message: error.message });
  }
});

// 删除上传记录及其关联的交易记录
router.delete('/uploads/:uploadId', async (req, res) => {
  try {
    const { uploadId } = req.params;
    const userId = req.user ? req.user.id : null;
    
    const uploadsDir = path.join(__dirname, '../../../database/uploads');
    const transactionsDir = path.join(__dirname, '../../../database/transactions');
    
    // 确保目录存在
    try {
      await fs.access(uploadsDir);
      await fs.access(transactionsDir);
    } catch (error) {
      return res.status(404).json({ error: '上传记录不存在' });
    }
    
    // 读取上传记录
    try {
      const uploadFilePath = path.join(uploadsDir, `${uploadId}.json`);
      const uploadContent = await fs.readFile(uploadFilePath, 'utf-8');
      const uploadRecord = JSON.parse(uploadContent);
      
      // 如果指定了用户ID，验证记录所有权
      if (userId && uploadRecord.userId !== userId) {
        return res.status(403).json({ error: '无权删除此记录' });
      }
      
      // 删除交易记录文件
      const transactionsFilePath = path.join(transactionsDir, `${uploadId}.json`);
      try {
        await fs.unlink(transactionsFilePath);
      } catch (error) {
        logger.error(`删除交易记录文件 ${transactionsFilePath} 失败:`, error);
        // 继续执行，尝试删除上传记录文件
      }
      
      // 删除上传记录文件
      await fs.unlink(uploadFilePath);
      
      // 尝试删除原始上传文件
      if (uploadRecord.path) {
        try {
          await fs.unlink(uploadRecord.path);
          logger.info(`成功删除原始文件: ${uploadRecord.path}`);
        } catch (fileError) {
          logger.error(`删除原始文件失败: ${uploadRecord.path}`, fileError);
          // 文件删除失败不影响整体操作，继续返回成功
        }
      }
      
      res.json({ 
        success: true, 
        message: '上传记录及关联的交易记录已成功删除' 
      });
    } catch (error) {
      if (error.code === 'ENOENT') {
        return res.status(404).json({ error: '上传记录不存在' });
      }
      throw error;
    }
  } catch (error) {
    logger.error('删除上传记录失败:', error);
    res.status(500).json({ error: '删除上传记录失败', message: error.message });
  }
});

// 格式化文件大小
function formatFileSize(bytes) {
  if (bytes < 1024) return bytes + ' B';
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB';
  if (bytes < 1024 * 1024 * 1024) return (bytes / (1024 * 1024)).toFixed(2) + ' MB';
  return (bytes / (1024 * 1024 * 1024)).toFixed(2) + ' GB';
}

module.exports = router; 