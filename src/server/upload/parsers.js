const xlsx = require('xlsx');
const fs = require('fs');
const path = require('path');
const parse = require('csv-parse/lib/sync');

// 解析招商银行CSV文件
const parseCMBCSV = async (filePath) => {
  try {
    console.log('开始解析CSV文件:', filePath);
    const fileContent = fs.readFileSync(filePath, 'utf8');
    console.log('CSV文件内容前100个字符:', fileContent.substring(0, 100));
    
    // 查找数据开始行
    const lines = fileContent.split('\n');
    let dataStartIndex = 0;
    
    // 尝试查找招商银行CSV的表头行
    for (let i = 0; i < lines.length; i++) {
      if (lines[i].includes('账单日期,交易金额,支出/收入,账户余额,交易方式,分类,备注')) {
        dataStartIndex = i + 1; // 跳过表头
        console.log('找到表头行，数据开始于第', dataStartIndex, '行');
        break;
      }
    }
    
    // 如果没找到标准表头，尝试直接解析
    const transactions = [];
    
    // 从数据行开始处理
    for (let i = dataStartIndex; i < lines.length; i++) {
      const line = lines[i].trim();
      if (!line) continue; // 跳过空行
      
      // 尝试直接按逗号分割
      const columns = line.split(',');
      if (columns.length < 3) continue; // 至少需要日期、金额、类型

      // 尝试解析每一列
      let transactionDate = '';
      let amount = 0;
      let isIncome = false;
      let memo = '';
      let counterparty = '';
      
      // 根据列数判断CSV格式并解析
      if (columns.length >= 3) {
        // 假设第一列是日期
        transactionDate = formatDate(columns[0]);
        
        // 假设第二列是金额
        amount = parseAmount(columns[1]);
        
        // 假设第三列可能包含收支信息
        isIncome = columns[2].includes('收入') || amount > 0;
        
        // 如果有更多列，尝试获取备注和交易对手
        if (columns.length > 3) {
          memo = columns[3] || '';
        }
        
        if (columns.length > 4) {
          counterparty = columns[4] || '';
        }
        
        // 创建交易记录
        if (transactionDate && !isNaN(amount)) {
          transactions.push({
            transaction_date: transactionDate,
            amount: Math.abs(amount),
            is_income: isIncome,
            memo: memo,
            counterparty: counterparty,
            category: '',
            balance: 0
          });
        }
      }
    }
    
    console.log('CSV解析完成，共解析', transactions.length, '条记录');
    
    if (transactions.length === 0) {
      console.log('直接使用xlsx解析CSV文件');
      return await parseCSVWithXLSX(filePath);
    }
    
    return transactions;
  } catch (error) {
    console.error('解析CSV文件失败:', error);
    // 尝试使用XLSX作为备选方案
    try {
      console.log('尝试使用xlsx解析CSV文件');
      return await parseCSVWithXLSX(filePath);
    } catch (xlsxError) {
      console.error('xlsx解析也失败:', xlsxError);
      throw new Error(`解析CSV文件失败: ${error.message}`);
    }
  }
};

// 使用xlsx库解析CSV文件（备选方案）
const parseCSVWithXLSX = async (filePath) => {
  const workbook = xlsx.readFile(filePath, {
    type: 'file',
    raw: true,
    cellDates: true
  });
  
  const sheetName = workbook.SheetNames[0];
  const worksheet = workbook.Sheets[sheetName];
  const data = xlsx.utils.sheet_to_json(worksheet, {
    header: 1,
    defval: '',
    raw: false
  });
  
  // 跳过可能的表头行
  const transactions = [];
  let headerFound = false;
  
  for (let i = 0; i < data.length; i++) {
    const row = data[i];
    if (row.length < 2) continue; // 至少要有日期和金额
    
    // 检查第一个单元格是否像日期
    const firstCell = String(row[0]).trim();
    if (/\d{4}[-/]\d{1,2}[-/]\d{1,2}/.test(firstCell) || 
        /\d{1,2}[-/]\d{1,2}[-/]\d{4}/.test(firstCell)) {
      // 找到类似日期的行，这可能是数据行
      headerFound = true;
    }
    
    if (headerFound) {
      // 尝试解析为交易记录
      const transactionDate = formatDate(row[0]);
      let amount = 0;
      let isIncome = false;
      
      // 找到金额字段
      for (let j = 1; j < row.length; j++) {
        const value = parseAmount(row[j]);
        if (!isNaN(value) && value !== 0) {
          amount = value;
          isIncome = value > 0;
          break;
        }
      }
      
      if (transactionDate && !isNaN(amount)) {
        transactions.push({
          transaction_date: transactionDate,
          amount: Math.abs(amount),
          is_income: isIncome,
          memo: row[2] || '',
          counterparty: row[3] || '',
          category: '',
          balance: 0
        });
      }
    }
  }
  
  if (transactions.length === 0) {
    throw new Error('未能从CSV文件中解析出有效的交易记录');
  }
  
  return transactions;
};

// 格式化日期
const formatDate = (dateStr) => {
  if (!dateStr) return '';
  
  // 尝试解析各种日期格式
  let date;
  
  // 处理常见的日期格式
  if (typeof dateStr === 'string') {
    // 清理日期字符串，移除引号和多余空格
    dateStr = dateStr.replace(/['"]/g, '').trim();
    
    // 尝试各种日期格式
    const formats = [
      // YYYY-MM-DD 或 YYYY/MM/DD
      /(\d{4})[-/](\d{1,2})[-/](\d{1,2})/,
      // DD-MM-YYYY 或 DD/MM/YYYY
      /(\d{1,2})[-/](\d{1,2})[-/](\d{4})/,
      // YYYYMMDD
      /(\d{4})(\d{2})(\d{2})/,
      // 中文日期格式 YYYY年MM月DD日
      /(\d{4})年(\d{1,2})月(\d{1,2})日/
    ];
    
    for (const regex of formats) {
      const match = dateStr.match(regex);
      if (match) {
        // 根据不同格式解析日期
        if (match[0].includes('年') || match[1].length === 4) {
          // YYYY-MM-DD 或 YYYY年MM月DD日
          date = `${match[1]}-${match[2].padStart(2, '0')}-${match[3].padStart(2, '0')}`;
        } else {
          // DD-MM-YYYY
          date = `${match[3]}-${match[2].padStart(2, '0')}-${match[1].padStart(2, '0')}`;
        }
        break;
      }
    }
    
    // 如果上面的正则都无法匹配，尝试直接使用Date对象解析
    if (!date) {
      const d = new Date(dateStr);
      if (!isNaN(d.getTime())) {
        date = d.toISOString().split('T')[0];
      }
    }
  } else if (dateStr instanceof Date) {
    date = dateStr.toISOString().split('T')[0];
  }
  
  return date || '';
};

// 解析金额
const parseAmount = (value) => {
  if (!value) return 0;
  
  // 如果是数字，直接返回
  if (typeof value === 'number') return value;
  
  // 如果是字符串，移除货币符号、逗号等并解析
  if (typeof value === 'string') {
    // 移除常见的货币符号和其他非数字字符，但保留负号
    const cleanedValue = value.replace(/[¥$,\s]/g, '');
    return parseFloat(cleanedValue) || 0;
  }
  
  return 0;
};

// 解析Excel文件
const parseExcel = async (filePath) => {
  try {
    const workbook = xlsx.readFile(filePath, {
      type: 'file',
      cellDates: true
    });
    const sheetName = workbook.SheetNames[0];
    const worksheet = workbook.Sheets[sheetName];
    const data = xlsx.utils.sheet_to_json(worksheet, {
      raw: false,
      dateNF: 'YYYY-MM-DD'
    });
    
    // 转换数据格式
    const transactions = data.map(row => {
      // 尝试查找日期字段
      let transactionDate = '';
      for (const [key, value] of Object.entries(row)) {
        if (key.includes('日期') || key.includes('时间') || key.toLowerCase().includes('date')) {
          transactionDate = formatDate(value);
          if (transactionDate) break;
        }
      }
      
      // 尝试查找金额字段
      let amount = 0;
      let isIncome = false;
      for (const [key, value] of Object.entries(row)) {
        if (key.includes('金额') || key.toLowerCase().includes('amount')) {
          amount = parseAmount(value);
          break;
        }
      }
      
      // 尝试查找收支类型字段
      for (const [key, value] of Object.entries(row)) {
        if (key.includes('收支') || key.includes('类型') || key.toLowerCase().includes('type')) {
          isIncome = String(value).includes('收入') || String(value).includes('income');
          break;
        }
      }
      
      // 如果没有明确的收支类型，根据金额正负判断
      if (amount !== 0) {
        isIncome = amount > 0;
      }
      
      // 尝试查找摘要、备注字段
      let memo = '';
      for (const [key, value] of Object.entries(row)) {
        if (key.includes('摘要') || key.includes('备注') || key.toLowerCase().includes('memo')) {
          memo = String(value);
          break;
        }
      }
      
      // 尝试查找对手信息字段
      let counterparty = '';
      for (const [key, value] of Object.entries(row)) {
        if (key.includes('对手') || key.includes('对方') || key.toLowerCase().includes('party')) {
          counterparty = String(value);
          break;
        }
      }
      
      return {
        transaction_date: transactionDate,
        amount: Math.abs(amount),
        is_income: isIncome,
        memo: memo || '',
        counterparty: counterparty || '',
        category: '',
        balance: 0
      };
    }).filter(tx => tx.transaction_date && !isNaN(tx.amount));
    
    if (transactions.length === 0) {
      throw new Error('未能从Excel文件中解析出有效的交易记录');
    }
    
    return transactions;
  } catch (error) {
    console.error('解析Excel文件失败:', error);
    throw new Error(`解析Excel文件失败: ${error.message}`);
  }
};

module.exports = {
  parseCMBCSV,
  parseExcel
}; 