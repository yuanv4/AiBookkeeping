const express = require('express');
const multer = require('multer');
const path = require('path');
const fs = require('fs');
const fsp = fs.promises; // 添加Promise版本的fs
const xlsx = require('xlsx');
const { authMiddleware } = require('../auth/middleware');
const winston = require('winston');
const { v4: uuidv4 } = require('uuid');

const router = express.Router();

// 获取日志记录器实例
const logger = winston.createLogger({
  level: process.env.LOG_LEVEL || 'info',
  format: winston.format.combine(
    winston.format.timestamp({
      format: 'YYYY-MM-DD HH:mm:ss'
    }),
    winston.format.printf(({ level, message, timestamp, requestId, file, stats, duration, status, error, ...meta }) => {
      // 格式化文件信息
      let fileInfo = '';
      if (file) {
        fileInfo = ` | 文件: ${file.originalname}`;
        if (file.size) fileInfo += ` (${(file.size/1024).toFixed(2)}KB)`;
      }

      // 格式化统计信息
      let statsInfo = '';
      if (stats) {
        if (stats.transactionCount) statsInfo = ` | 记录数: ${stats.transactionCount}`;
        if (stats.parseTime) statsInfo += ` | 解析耗时: ${stats.parseTime}ms`;
      }

      // 格式化错误信息
      let errorInfo = '';
      if (error) {
        errorInfo = ` | 错误: ${error.message}`;
        if (error.stack) {
          errorInfo += ` | 堆栈: ${error.stack}`;
        }
      }

      // 格式化请求ID和处理时间
      let reqInfo = requestId ? ` | 请求ID: ${requestId}` : '';
      let durationInfo = duration ? ` | 处理时间: ${duration}ms` : '';
      let statusInfo = status ? ` | 状态: ${status}` : '';

      // 组合所有信息
      return `${timestamp} [${level.toUpperCase()}] ${message}${reqInfo}${fileInfo}${statsInfo}${durationInfo}${statusInfo}${errorInfo}`;
    })
  ),
  transports: [
    // 错误日志
    new winston.transports.File({ 
      filename: path.join(__dirname, '../logs/error.log'),
      level: 'error',
      maxsize: 5242880, // 5MB
      maxFiles: 5,
      tailable: true,
      options: { flags: 'a' } // 追加模式
    }),
    // 常规日志
    new winston.transports.File({ 
      filename: path.join(__dirname, '../logs/combined.log'),
      maxsize: 10485760, // 10MB
      maxFiles: 5,
      tailable: true,
      options: { flags: 'a' } // 追加模式
    }),
    // 开发环境下的控制台输出
    new winston.transports.Console({
      format: winston.format.combine(
        winston.format.colorize(),
        winston.format.simple()
      )
    })
  ]
});

// 确保日志目录存在
const logDir = path.join(__dirname, '../logs');
if (!fs.existsSync(logDir)) {
  fs.mkdirSync(logDir, { recursive: true });
}

const errorLogPath = path.join(logDir, 'error.log');
const combinedLogPath = path.join(logDir, 'combined.log');

// 清空日志文件
fs.writeFileSync(errorLogPath, '');
fs.writeFileSync(combinedLogPath, '');

    // 确保上传目录存在
const uploadDir = process.env.UPLOAD_DIR || path.join(__dirname, '../../../uploads');
    if (!fs.existsSync(uploadDir)) {
      fs.mkdirSync(uploadDir, { recursive: true });
    }

// 配置文件存储
const storage = multer.memoryStorage();

// 添加请求追踪ID中间件
const addRequestId = (req, res, next) => {
  req.requestId = Date.now().toString(36) + Math.random().toString(36).substr(2);
  next();
};

// 文件类型过滤
const fileFilter = (req, file, cb) => {
  const logContext = {
    requestId: req.requestId,
    file: {
      originalname: file.originalname,
      mimetype: file.mimetype,
      size: file.size
    }
  };

  logger.info('收到文件上传请求', logContext);

  const allowedMimes = [
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'application/vnd.ms-excel',
    'text/csv',
    'application/csv'
  ];
  
  if (allowedMimes.includes(file.mimetype) || 
      file.originalname.toLowerCase().endsWith('.xlsx') || 
      file.originalname.toLowerCase().endsWith('.xls') ||
      file.originalname.toLowerCase().endsWith('.csv')) {
    logger.info('文件类型验证通过', logContext);
    cb(null, true);
  } else {
    logger.error('文件类型验证失败', {
      ...logContext,
      allowedMimes,
      receivedMime: file.mimetype
    });
    cb(new Error('只支持Excel文件(.xlsx, .xls)和CSV文件(.csv)格式'), false);
  }
};

// 配置multer
const upload = multer({
  storage: storage,
  fileFilter: fileFilter,
  limits: {
    fileSize: 10 * 1024 * 1024 // 10MB
  }
});

// 解析Excel文件
const parseExcel = (filePath) => {
  try {
  const workbook = xlsx.readFile(filePath);
  const sheetName = workbook.SheetNames[0];
  const worksheet = workbook.Sheets[sheetName];
    
    // 获取数据范围
    const range = xlsx.utils.decode_range(worksheet['!ref']);
    const headers = [];
    
    // 读取表头
    for (let col = range.s.c; col <= range.e.c; col++) {
      const cellAddress = xlsx.utils.encode_cell({ r: range.s.r, c: col });
      const cell = worksheet[cellAddress];
      headers[col] = cell ? cell.v : '';
    }

    // 列名映射
    const columnMap = {
      '记账日期': 'transaction_date',
      '交易日期': 'transaction_date',
      '日期': 'transaction_date',
      '时间': 'transaction_date',
      
      '交易金额': 'amount',
      '金额': 'amount',
      '发生金额': 'amount',
      
      '货币': 'currency',
      '币种': 'currency',
      
      '交易摘要': 'memo',
      '摘要': 'memo',
      '备注': 'memo',
      '说明': 'memo',
      
      '对手信息': 'counterparty',
      '对方户名': 'counterparty',
      '交易对手': 'counterparty',
      
      '联机余额': 'balance',
      '余额': 'balance',
      
      '收支类型': 'is_income',
      '类型': 'is_income',
      '交易类型': 'is_income'
    };

    // 转换数据
    const data = [];
    for (let row = range.s.r + 1; row <= range.e.r; row++) {
      const rowData = {};
      let hasData = false;

      for (let col = range.s.c; col <= range.e.c; col++) {
        const cellAddress = xlsx.utils.encode_cell({ r: row, c: col });
        const cell = worksheet[cellAddress];
        const header = columnMap[headers[col]] || headers[col];
        
        if (cell) {
          hasData = true;
          rowData[header] = cell.v;
          
          // 根据交易金额判断收支类型
          if (header === 'amount') {
            rowData.is_income = cell.v > 0;
          }
        }
      }

      if (hasData) {
        // 设置默认分类
        if (!rowData.category) {
          rowData.category = rowData.memo ? getCategoryFromMemo(rowData.memo, rowData.counterparty) : '其他';
        }
        data.push(rowData);
      }
    }

    return data;
  } catch (error) {
    throw new Error('Excel文件解析失败：' + error.message);
  }
};

// 解析CSV文件
const parseCSV = async (filePath) => {
  try {
    const content = await fs.promises.readFile(filePath, 'utf-8');
    const lines = content.split('\n');
    const data = [];
    
    // 找到实际的数据开始行（跳过表头信息）
    let headerIndex = -1;
    for (let i = 0; i < lines.length; i++) {
      if (lines[i].includes('记账日期,货币,交易金额,联机余额,交易摘要,对手信息')) {
        headerIndex = i;
        break;
      }
    }

    if (headerIndex === -1) {
      throw new Error('无法识别CSV文件格式，请确保包含必要的列名');
    }

    // 解析交易数据
    for (let i = headerIndex + 2; i < lines.length; i++) {
      const line = lines[i].trim();
      
      // 跳过空行、表头和提示信息
      if (!line || 
          line.startsWith('温馨提示') || 
          line.startsWith('---') || 
          line.includes('Transaction Statement') || 
          line.includes('招商银行交易流水') ||
          line.includes('Amount')) {
        continue;
      }

      // 解析CSV行，处理可能包含逗号的字段
      const fields = line.split(',').map(field => 
        field.replace(/^["']|["']$/g, '').trim() // 移除引号和空格
      );

      if (fields.length < 6) continue; // 招商银行CSV必须包含6个字段

      // 提取字段（按照招商银行CSV格式）
      const [date, currency, amount, balance, memo, counterparty] = fields;
      
      // 跳过无效数据行
      if (!date || !amount || isNaN(parseFloat(amount))) {
        continue;
      }

      // 解析金额（移除货币符号和其他非数字字符）
      const parsedAmount = parseFloat(amount.replace(/[¥$,\s]/g, ''));
      const parsedBalance = parseFloat(balance.replace(/[¥$,\s]/g, ''));
      
      if (isNaN(parsedAmount)) continue;

      // 构建交易记录
      const transaction = {
        transaction_date: formatDate(date).toISOString().split('T')[0],
        amount: Math.abs(parsedAmount),
        is_income: parsedAmount > 0,
        memo: memo,
        counterparty: counterparty,
        category: getCategoryFromMemo(memo, counterparty),
        balance: parsedBalance,
        currency: currency === '人民币' ? 'CNY' : currency
      };

      data.push(transaction);
    }

    if (data.length === 0) {
      throw new Error('未能从CSV文件中解析出有效的交易记录');
    }

    return data;
  } catch (error) {
    logger.error('CSV解析错误:', error);
    throw new Error('CSV文件解析失败：' + error.message);
  }
};

// 根据交易摘要和对手信息智能判断分类
const getCategoryFromMemo = (memo, counterparty) => {
  if (!memo && !counterparty) return '其他';
  
  const text = (memo + ' ' + counterparty).toLowerCase();
  const categoryRules = [
    { keywords: ['工资', '薪资', '工资收入', '工资发放'], category: '工资收入' },
    { keywords: ['餐饮', '美食', '饭店', '食堂', '超市', '商场', '外卖', '美团', '饿了么', '牛肉面', '豆夫'], category: '餐饮' },
    { keywords: ['交通', '公交', '地铁', '打车', '高铁', '火车', '飞机'], category: '交通' },
    { keywords: ['房租', '水电', '物业', '煤气'], category: '居住' },
    { keywords: ['话费', '网费', '通信'], category: '通讯' },
    { keywords: ['转账', '汇款', 'cds', '扫码'], category: '转账' },
    { keywords: ['提现', 'atm'], category: '取现' },
    { keywords: ['医院', '药店', '诊所'], category: '医疗' },
    { keywords: ['利息', '理财', '基金'], category: '投资理财' },
    { keywords: ['京东', '拼多多', '淘宝', '天猫', '电商', '商城'], category: '网上购物' },
    { keywords: ['红包', '微信'], category: '红包转账' }
  ];

  for (const rule of categoryRules) {
    if (rule.keywords.some(keyword => text.includes(keyword))) {
      return rule.category;
    }
  }

  return '其他';
};

// 格式化日期
const formatDate = (date) => {
  if (!date) return new Date();
  if (date instanceof Date) return date;
  
  // 处理Excel日期序列号
  if (typeof date === 'number') {
    // Excel的日期序列号从1900年1月1日开始
    const excelEpoch = new Date(1900, 0, 1);
    return new Date(excelEpoch.getTime() + (date - 1) * 24 * 60 * 60 * 1000);
  }
  
  // 处理字符串日期
  if (typeof date === 'string') {
    // 移除可能存在的多余空格
    date = date.trim();
    
    // 尝试解析常见的日期格式
    const formats = [
      /^(\d{4})-(\d{2})-(\d{2})$/,  // YYYY-MM-DD
      /^(\d{2})-(\d{2})-(\d{4})$/,  // DD-MM-YYYY
      /^(\d{4})\/(\d{2})\/(\d{2})$/,  // YYYY/MM/DD
      /^(\d{2})\/(\d{2})\/(\d{4})$/,  // DD/MM/YYYY
      /^(\d{4})(\d{2})(\d{2})$/,    // YYYYMMDD
      /^(\d{2})(\d{2})(\d{4})$/     // DDMMYYYY
    ];
    
    for (const format of formats) {
      const match = date.match(format);
      if (match) {
        const [_, part1, part2, part3] = match;
        // 判断是否为YYYYMMDD格式
        if (part1.length === 4) {
          return new Date(parseInt(part1), parseInt(part2) - 1, parseInt(part3));
        } else {
          // 其他格式中，年份在最后
          return new Date(parseInt(part3), parseInt(part2) - 1, parseInt(part1));
        }
      }
    }
    
    // 尝试使用Date.parse()解析其他格式
    const parsed = Date.parse(date);
    if (!isNaN(parsed)) {
      return new Date(parsed);
    }
  }
  
  // 如果无法解析，返回当前日期并记录错误
  logger.error('无法解析日期格式:', date);
  return new Date();
};

// 处理金额
const parseAmount = (amount) => {
  if (typeof amount === 'number') return amount;
  if (!amount) return 0;
  
  // 移除货币符号和空格
  let cleanAmount = amount.toString().replace(/[¥$,\s]/g, '');
  
  // 尝试转换为数字
  const number = parseFloat(cleanAmount);
  return isNaN(number) ? 0 : number;
};

// 判断是否为收入
const determineIsIncome = (value) => {
  if (typeof value === 'boolean') return value;
  if (!value) return false;
  
  const incomeKeywords = ['收入', '入账', '转入', 'income', '1', 'true', 'yes'];
  return incomeKeywords.includes(value.toString().toLowerCase());
};

// 清理临时文件
const cleanupTempFile = (filePath) => {
  if (filePath && fs.existsSync(filePath)) {
  fs.unlink(filePath, (err) => {
    if (err) {
      logger.error('临时文件删除失败:', err);
    }
  });
  }
};

// 添加解析招商银行CSV文件的函数
async function parseCMBCSV(filePath) {
  const transactions = [];
  const content = await fs.promises.readFile(filePath, 'utf-8');
  const lines = content.split('\n');
  
  // 找到数据开始的行（包含表头的那一行）
  let dataStartIndex = -1;
  for (let i = 0; i < lines.length; i++) {
    if (lines[i].includes('记账日期,货币,交易金额,联机余额,交易摘要,对手信息')) {
      dataStartIndex = i;
      break;
    }
  }

  if (dataStartIndex === -1) {
    throw new Error('无法找到数据起始行');
  }

  // 跳过表头，从数据行开始处理
  for (let i = dataStartIndex + 2; i < lines.length; i++) {
    const line = lines[i].trim();
    
    // 跳过空行和分隔行
    if (!line || line.startsWith('---') || line.startsWith('温馨提示') || line.includes('Amount')) {
      continue;
    }

    // 解析CSV行
    const fields = line.split(',').map(field => field.trim());
    if (fields.length >= 6) {
      const [date, currency, amount, balance, type, counterparty] = fields;
      
      // 跳过无效数据行
      if (!date || !amount || isNaN(parseFloat(amount))) {
        continue;
      }

      // 解析日期
      const parsedDate = formatDate(date);
      if (!parsedDate || isNaN(parsedDate.getTime())) {
        logger.error('日期解析失败:', date);
        continue;
      }

      // 解析金额，移除货币符号和逗号
      const parsedAmount = parseFloat(amount.replace(/[¥,]/g, ''));
      
      // 确定收支类型
      const isIncome = parsedAmount > 0;

      // 确定交易类别
      let category = '其他';
      const typeStr = (type + ' ' + counterparty).toLowerCase();
      
      if (typeStr.includes('工资') || typeStr.includes('代发')) {
        category = '工资收入';
      } else if (typeStr.includes('还款')) {
        category = '还款';
      } else if (typeStr.includes('转账') || typeStr.includes('汇款')) {
        category = '转账';
      } else if (typeStr.includes('餐') || typeStr.includes('饭') || typeStr.includes('食') || typeStr.includes('美团') || typeStr.includes('外卖')) {
        category = '餐饮';
      } else if (typeStr.includes('超市') || typeStr.includes('商城') || typeStr.includes('京东') || typeStr.includes('拼多多')) {
        category = '购物';
      } else if (typeStr.includes('地铁') || typeStr.includes('交通') || typeStr.includes('出行')) {
        category = '交通';
      } else if (typeStr.includes('基金') || typeStr.includes('理财')) {
        category = '投资理财';
      }

      transactions.push({
        transaction_date: parsedDate.toISOString().split('T')[0],
        amount: Math.abs(parsedAmount), // 保存绝对值
        is_income: isIncome,
        category: category,
        memo: type,
        counterparty: counterparty,
        balance: parseFloat(balance.replace(/[¥,]/g, '')),
        currency: 'CNY'
      });
    }
  }

  if (transactions.length === 0) {
    throw new Error('未能从CSV文件中解析出有效的交易记录');
  }

  return transactions;
}

// 添加数据格式化函数
const formatTransaction = (record) => {
  try {
    // 确保金额是数字类型
    let amount = 0;
    try {
      if (typeof record.amount === 'string') {
        amount = parseFloat(record.amount);
      } else if (typeof record.amount === 'number') {
        amount = record.amount;
      } else {
        amount = 0;
      }
    } catch (e) {
      amount = 0;
      console.error('金额格式化错误:', e);
    }
    
    // 保留数字类型，不要转换为格式化字符串
    return {
      transaction_date: record.transaction_date,
      amount: amount, // 返回数字类型
      is_income: record.is_income,
      category: record.category || '未分类',
      memo: record.memo || '',
      counterparty: record.counterparty || ''
    };
  } catch (error) {
    console.error('交易格式化错误:', error);
    // 返回安全的默认值
    return {
      transaction_date: record.transaction_date || '',
      amount: 0, // 返回数字 0，而不是字符串
      is_income: !!record.is_income,
      category: record.category || '未分类',
      memo: record.memo || '',
      counterparty: record.counterparty || ''
    };
  }
};

// 添加数据统计函数
const calculateStats = (transactions) => {
  try {
    const stats = {
      totalIncome: 0,
      totalExpense: 0,
      categoryStats: {},
      dateRange: {
        start: null,
        end: null
      }
    };

    transactions.forEach(record => {
      try {
        // 确保金额是数字类型
        let amount = 0;
        if (typeof record.amount === 'string') {
          amount = parseFloat(record.amount) || 0;
        } else if (typeof record.amount === 'number') {
          amount = record.amount;
        }
        
        if (record.is_income) {
          stats.totalIncome += amount;
        } else {
          stats.totalExpense += amount;
        }

        // 统计分类
        const category = record.category || '未分类';
        if (!stats.categoryStats[category]) {
          stats.categoryStats[category] = {
            income: 0,
            expense: 0,
            count: 0
          };
        }
        stats.categoryStats[category].count++;
        if (record.is_income) {
          stats.categoryStats[category].income += amount;
        } else {
          stats.categoryStats[category].expense += amount;
        }

        // 更新日期范围
        if (record.transaction_date) {
          const date = new Date(record.transaction_date);
          if (!isNaN(date.getTime())) {
            if (!stats.dateRange.start || date < new Date(stats.dateRange.start)) {
              stats.dateRange.start = record.transaction_date;
            }
            if (!stats.dateRange.end || date > new Date(stats.dateRange.end)) {
              stats.dateRange.end = record.transaction_date;
            }
          }
        }
      } catch (error) {
        console.error('处理单条记录统计错误:', error);
      }
    });

    // 不要格式化数字为字符串，保留原始数字
    return stats;
  } catch (error) {
    console.error('计算统计数据错误:', error);
    return {
      totalIncome: 0,
      totalExpense: 0,
      categoryStats: {},
      dateRange: {
        start: null,
        end: null
      }
    };
  }
};

// 修改为使用文件系统存储数据
const saveToFileSystem = async (userId, fileInfo, transactions) => {
  try {
    // 生成唯一ID
    const uploadId = uuidv4();
    const timestamp = new Date().toISOString();
    
    // 计算汇总数据
    let totalIncome = 0;
    let totalExpense = 0;
    let maxIncome = 0;
    let maxExpense = 0;
    
    for (const transaction of transactions) {
      // 确保金额是数字
      const amount = typeof transaction.amount === 'number' 
        ? transaction.amount 
        : parseFloat(transaction.amount) || 0;
      
      if (transaction.is_income) {
        totalIncome += amount;
        maxIncome = Math.max(maxIncome, amount);
      } else {
        totalExpense += amount;
        maxExpense = Math.max(maxExpense, amount);
      }
    }
    
    // 按月汇总数据
    const monthlyData = {};
    for (const transaction of transactions) {
      const date = new Date(transaction.transaction_date);
      const month = `${date.getFullYear()}-${(date.getMonth() + 1).toString().padStart(2, '0')}`;
      
      if (!monthlyData[month]) {
        monthlyData[month] = { income: 0, expense: 0 };
      }
      
      const amount = parseFloat(transaction.amount) || 0;
      
      if (transaction.is_income) {
        monthlyData[month].income += amount;
      } else {
        monthlyData[month].expense += amount;
      }
    }
    
    // 按类别汇总支出数据
    const categoryData = {};
    for (const transaction of transactions) {
      if (!transaction.is_income && transaction.category) {
        if (!categoryData[transaction.category]) {
          categoryData[transaction.category] = 0;
        }
        
        const amount = parseFloat(transaction.amount) || 0;
        categoryData[transaction.category] += amount;
      }
    }
    
    // 创建上传记录
    const uploadRecord = {
      id: uploadId,
      userId: userId || 'anonymous',
      filename: fileInfo.originalname,
      originalName: fileInfo.originalname,
      mimeType: fileInfo.mimetype,
      size: fileInfo.size,
      path: fileInfo.path,
      createdAt: timestamp,
      // 汇总数据
      summary: {
        transactionCount: transactions.length,
        totalIncome: totalIncome,
        totalExpense: totalExpense,
        balance: totalIncome - totalExpense,
        maxIncome: maxIncome,
        maxExpense: maxExpense
      }
    };
    
    // 图表数据
    const charts = {
      monthly: Object.keys(monthlyData).map(month => ({
        month,
        income: monthlyData[month].income,
        expense: monthlyData[month].expense
      })).sort((a, b) => a.month.localeCompare(b.month)),
      
      categories: Object.keys(categoryData)
        .map(category => ({ 
          category, 
          amount: categoryData[category] 
        }))
        .filter(item => item.amount > 0)
        .sort((a, b) => b.amount - a.amount)
        .slice(0, 10) // 只返回前10个类别
    };
    
    // 确保目录存在
    const uploadsDir = path.join(__dirname, '../../../database/uploads');
    const transactionsDir = path.join(__dirname, '../../../database/transactions');
    
    if (!fs.existsSync(uploadsDir)) {
      fs.mkdirSync(uploadsDir, { recursive: true });
    }
    
    if (!fs.existsSync(transactionsDir)) {
      fs.mkdirSync(transactionsDir, { recursive: true });
    }
    
    // 保存上传记录
    await fsp.writeFile(
      path.join(uploadsDir, `${uploadId}.json`),
      JSON.stringify(uploadRecord, null, 2)
    );
    
    // 保存交易记录
    await fsp.writeFile(
      path.join(transactionsDir, `${uploadId}.json`),
      JSON.stringify(transactions, null, 2)
    );
    
    logger.info(`成功保存上传记录和${transactions.length}条交易记录到文件系统`);
    
    // 返回完整数据对象
    return {
      success: true,
      savedToStorage: true,
      uploadId,
      summary: uploadRecord.summary,
      charts,
      transactions
    };
  } catch (error) {
    logger.error('保存数据到文件系统失败:', error);
    throw error;
  }
};

// 修改路由处理上传请求的函数，使用文件系统保存
router.post('/', addRequestId, upload.single('file'), async (req, res) => {
  const requestId = req.requestId;
  const startTime = Date.now();
  
  try {
    logger.info('开始处理文件上传请求', { 
      requestId, 
      headers: req.headers,
      body: req.body,
      file: req.file ? {
        originalname: req.file.originalname,
        mimetype: req.file.mimetype,
        size: req.file.size
      } : null
    });
    
    if (!req.file) {
      logger.error('未收到文件', { requestId });
      throw new Error('未收到文件');
    }

    // 验证文件类型
    const fileType = req.file.mimetype;
    logger.info('文件类型验证', { 
      requestId, 
      fileType,
      originalname: req.file.originalname
    });

    if (!['application/vnd.ms-excel', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 'text/csv'].includes(fileType)) {
      logger.error('不支持的文件类型', { 
        requestId, 
        fileType,
        originalname: req.file.originalname
      });
      throw new Error('不支持的文件类型');
    }

    // 创建临时文件
    const tempFilePath = path.join(uploadDir, `temp_${Date.now()}_${req.file.originalname}`);
    logger.info('准备创建临时文件', { 
      requestId, 
      tempFilePath,
      bufferSize: req.file.buffer.length
    });

    try {
      await fs.promises.writeFile(tempFilePath, req.file.buffer);
      logger.info('临时文件创建成功', { 
        requestId, 
        tempFilePath,
        fileSize: req.file.size
      });
    } catch (writeError) {
      logger.error('临时文件创建失败', { 
        requestId, 
        error: writeError,
        tempFilePath
      });
      throw new Error('临时文件创建失败：' + writeError.message);
    }

    // 解析文件
    let transactions = [];
    try {
      if (fileType === 'text/csv') {
        logger.info('开始解析CSV文件', { requestId, tempFilePath });
        transactions = await parseCMBCSV(tempFilePath);
        logger.info('CSV文件解析完成', { 
          requestId, 
          transactionCount: transactions.length,
          sampleTransaction: transactions[0]
        });
      } else {
        logger.info('开始解析Excel文件', { requestId, tempFilePath });
        transactions = await parseExcel(tempFilePath);
        logger.info('Excel文件解析完成', { 
          requestId, 
          transactionCount: transactions.length,
          sampleTransaction: transactions[0]
        });
      }
    } catch (parseError) {
      logger.error('文件解析失败', { 
        requestId, 
        error: parseError,
        tempFilePath
      });
      throw new Error('文件解析失败：' + parseError.message);
    }

    // 删除临时文件
    try {
      await fs.promises.unlink(tempFilePath);
      logger.info('临时文件删除成功', { requestId, tempFilePath });
    } catch (unlinkError) {
      logger.error('临时文件删除失败', { 
        requestId, 
        error: unlinkError,
        tempFilePath
      });
      // 不抛出错误，继续处理
    }

    // 数据验证和清理
    logger.info('开始数据验证', { 
      requestId, 
      totalRecords: transactions.length
    });

    const validTransactions = [];
    const invalidRecords = [];
    const warnings = [];

    transactions.forEach((record, index) => {
      try {
        // 验证日期格式
        if (!record.transaction_date || !/^\d{4}-\d{2}-\d{2}$/.test(record.transaction_date)) {
          throw new Error('无效的日期格式');
        }

        // 验证金额
        const amount = typeof record.amount === 'string' ? parseFloat(record.amount) : record.amount;
        if (isNaN(amount)) {
          throw new Error('无效的金额');
        }
        
        // 确保记录中的金额是数字类型
        record.amount = amount;

        // 验证必填字段
        if (!record.memo) {
          warnings.push({
            row: index + 1,
            field: 'memo',
            message: '摘要为空'
          });
        }

        validTransactions.push(record);
      } catch (error) {
        invalidRecords.push({
          row: index + 1,
          error: error.message,
          data: record
        });
      }
    });

    logger.info('数据验证完成', { 
      requestId, 
      validCount: validTransactions.length,
      invalidCount: invalidRecords.length,
      warningCount: warnings.length
    });

    // 计算统计数据
    const stats = calculateStats(validTransactions);
    logger.info('统计数据计算完成', { 
      requestId, 
      stats
    });

    // 格式化所有数据而不是分页
    logger.info('开始格式化交易数据', {
      requestId,
      dataCount: validTransactions.length
    });
    
    const formatStartTime = Date.now();
    
    // 使用批量处理优化，每次处理500条数据
    const batchSize = 500;
    const formattedTransactions = [];
    
    for (let i = 0; i < validTransactions.length; i += batchSize) {
      const batch = validTransactions.slice(i, i + batchSize);
      const formattedBatch = batch.map(formatTransaction);
      formattedTransactions.push(...formattedBatch);
      
      // 记录批处理进度
      if ((i + batchSize) % 2000 === 0 || i + batchSize >= validTransactions.length) {
        logger.info('批量格式化进度', {
          requestId,
          processed: Math.min(i + batchSize, validTransactions.length),
          total: validTransactions.length,
          percent: Math.round((Math.min(i + batchSize, validTransactions.length) / validTransactions.length) * 100) + '%'
        });
      }
    }
    
    const formatEndTime = Date.now();
    const formatTime = formatEndTime - formatStartTime;
    
    logger.info('所有交易数据格式化完成', {
      requestId,
      count: formattedTransactions.length,
      timeUsed: formatTime + 'ms',
      speed: formatTime > 0 ? Math.round(formattedTransactions.length / (formatTime / 1000)) + '条/秒' : 'N/A'
    });

    // 将解析后的数据保存到文件系统
    const userId = req.user ? req.user.id : null; // 如果用户已登录，获取用户ID
    let uploadId = null;
    
    try {
      const result = await saveToFileSystem(userId, req.file, formattedTransactions);
      logger.info('数据已成功保存到文件系统', {
        requestId,
        uploadId: result.uploadId,
        transactionCount: formattedTransactions.length
      });
      
      // 返回完整数据结果
      res.json(result);
    } catch (error) {
      logger.error('保存数据到文件系统失败', {
        requestId,
        error
      });
      // 文件系统保存失败，但仍然返回解析的数据
      res.json({ 
        success: true, 
        savedToStorage: false,
        transactions: formattedTransactions,
        summary: {
          transactionCount: formattedTransactions.length,
          totalIncome: stats.totalIncome,
          totalExpense: stats.totalExpense,
          balance: stats.totalIncome - stats.totalExpense
        },
        message: '文件已上传并解析，但保存到文件系统失败'
      });
    }
  } catch (error) {
    logger.error('文件处理失败', { 
      requestId, 
      error: {
        message: error.message,
        code: error.code || 'PROCESSING_ERROR',
        stack: error.stack
      }
    });

    res.status(500).json({
      success: false,
      error: {
        code: error.code || 'PROCESSING_ERROR',
        message: error.message,
        details: error.stack
      }
    });
  }
});

// 定期清理过期文件
const cleanupExpiredFiles = () => {
  const uploadDir = process.env.UPLOAD_DIR || './uploads';
  const expirationTime = 7 * 24 * 60 * 60 * 1000; // 7天

  fs.readdir(uploadDir, (err, files) => {
    if (err) {
      logger.error('读取上传目录失败:', err);
      return;
    }

    const now = Date.now();
    files.forEach(file => {
      const filePath = path.join(uploadDir, file);
      fs.stat(filePath, (err, stats) => {
        if (err) {
          logger.error('获取文件状态失败:', err);
          return;
        }

        if (now - stats.mtimeMs > expirationTime) {
          cleanupTempFile(filePath);
        }
      });
    });
  });
};

// 每天执行一次清理
setInterval(cleanupExpiredFiles, 24 * 60 * 60 * 1000);

// 添加错误处理中间件
router.use((err, req, res, next) => {
  logger.error('上传路由错误', { 
    error: err, 
    url: req.url, 
    method: req.method,
    requestId: req.requestId || 'unknown'
  });
  res.status(500).json({
    success: false,
    error: {
      message: err.message || '服务器内部错误',
      code: err.code || 'SERVER_ERROR'
    }
  });
});

module.exports = router;