const express = require('express');
const { query } = require('../db');
const { authMiddleware } = require('../auth');
const winston = require('winston');

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

// 设置月度预算
router.post('/', authMiddleware, async (req, res) => {
  try {
    const { amount, month, year, category } = req.body;

    // 检查是否已存在该月份的预算
    const existingBudget = await query(
      'SELECT id FROM budgets WHERE user_id = $1 AND month = $2 AND year = $3 AND category = $4',
      [req.userId, month, year, category]
    );

    let result;
    if (existingBudget.rows.length > 0) {
      // 更新现有预算
      result = await query(
        'UPDATE budgets SET amount = $1, updated_at = CURRENT_TIMESTAMP WHERE id = $2 RETURNING id',
        [amount, existingBudget.rows[0].id]
      );
    } else {
      // 创建新预算
      result = await query(
        'INSERT INTO budgets (user_id, amount, month, year, category) VALUES ($1, $2, $3, $4, $5) RETURNING id',
        [req.userId, amount, month, year, category]
      );
    }

    res.status(201).json({ id: result.rows[0].id });
  } catch (error) {
    logger.error('设置预算失败:', error);
    res.status(500).json({ error: '设置预算失败，请稍后重试' });
  }
});

// 获取月度预算和支出统计
router.get('/status', authMiddleware, async (req, res) => {
  try {
    const { month, year } = req.query;

    // 获取所有预算类别
    const budgets = await query(
      'SELECT category, amount FROM budgets WHERE user_id = $1 AND month = $2 AND year = $3',
      [req.userId, month, year]
    );

    // 获取当月支出
    const expenses = await query(
      'SELECT category, SUM(amount) as total FROM transactions WHERE user_id = $1 AND EXTRACT(MONTH FROM transaction_date) = $2 AND EXTRACT(YEAR FROM transaction_date) = $3 AND is_income = false GROUP BY category',
      [req.userId, month, year]
    );

    // 计算每个类别的预算使用情况
    const budgetStatus = budgets.rows.map(budget => {
      const expense = expenses.rows.find(e => e.category === budget.category);
      const spent = expense ? parseFloat(expense.total) : 0;
      const remaining = budget.amount - spent;
      const percentage = (spent / budget.amount) * 100;

      return {
        category: budget.category,
        budget: budget.amount,
        spent,
        remaining,
        percentage,
        status: percentage >= 100 ? '超支' : percentage >= 80 ? '接近预算' : '正常'
      };
    });

    res.json(budgetStatus);
  } catch (error) {
    logger.error('获取预算状态失败:', error);
    res.status(500).json({ error: '获取预算状态失败，请稍后重试' });
  }
});

// 获取超支预警
router.get('/alerts', authMiddleware, async (req, res) => {
  try {
    const currentDate = new Date();
    const currentMonth = currentDate.getMonth() + 1;
    const currentYear = currentDate.getFullYear();

    // 获取当月预算和支出
    const budgetStatus = await query(
      `SELECT 
        b.category,
        b.amount as budget_amount,
        COALESCE(SUM(t.amount), 0) as spent_amount
      FROM budgets b
      LEFT JOIN transactions t ON 
        b.category = t.category AND
        EXTRACT(MONTH FROM t.transaction_date) = $2 AND
        EXTRACT(YEAR FROM t.transaction_date) = $3 AND
        t.is_income = false AND
        t.user_id = b.user_id
      WHERE b.user_id = $1 AND b.month = $2 AND b.year = $3
      GROUP BY b.category, b.amount`,
      [req.userId, currentMonth, currentYear]
    );

    // 筛选出超支或接近预算的类别
    const alerts = budgetStatus.rows
      .map(row => {
        const percentage = (parseFloat(row.spent_amount) / row.budget_amount) * 100;
        if (percentage >= 80) {
          return {
            category: row.category,
            budget: row.budget_amount,
            spent: parseFloat(row.spent_amount),
            percentage,
            status: percentage >= 100 ? '超支' : '接近预算'
          };
        }
        return null;
      })
      .filter(alert => alert !== null);

    res.json(alerts);
  } catch (error) {
    logger.error('获取预算预警失败:', error);
    res.status(500).json({ error: '获取预算预警失败，请稍后重试' });
  }
});

module.exports = router;