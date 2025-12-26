import { prisma } from '../app.js'

export default async function statisticsRoutes(fastify) {
  // 所有路由需要认证
  fastify.addHook('onRequest', fastify.authenticate)

  /**
   * GET /api/statistics/overview
   * 获取总体统计数据
   */
  fastify.get('/overview', async () => {
    // 总收入
    const totalIncome = await prisma.transaction.aggregate({
      where: {
        amount: { gt: 0 }
      },
      _sum: {
        amount: true
      }
    })

    // 总支出
    const totalExpense = await prisma.transaction.aggregate({
      where: {
        amount: { lt: 0 }
      },
      _sum: {
        amount: true
      }
    })

    // 交易总数
    const totalCount = await prisma.transaction.count()

    // 按平台统计
    const platformStats = await prisma.transaction.groupBy({
      by: ['platform'],
      _count: {
        transactionId: true
      },
      _sum: {
        amount: true
      }
    })

    // 按分类统计
    const categoryStats = await prisma.transaction.groupBy({
      by: ['category'],
      _count: {
        transactionId: true
      },
      _sum: {
        amount: true
      },
      where: {
        category: {
          not: null
        }
      }
    })

    return {
      overview: {
        totalIncome: totalIncome._sum.amount || 0,
        totalExpense: totalExpense._sum.amount || 0,
        netIncome: (totalIncome._sum.amount || 0) + (totalExpense._sum.amount || 0),
        totalCount
      },
      byPlatform: platformStats.map(stat => ({
        platform: stat.platform,
        count: stat._count.transactionId,
        amount: stat._sum.amount || 0
      })),
      byCategory: categoryStats.map(stat => ({
        category: stat.category,
        count: stat._count.transactionId,
        amount: stat._sum.amount || 0
      }))
    }
  })

  /**
   * GET /api/statistics/monthly
   * 获取月度统计数据
   */
  fastify.get('/monthly', async (request, reply) => {
    const { year } = request.query
    const currentYear = year ? parseInt(year) : new Date().getFullYear()

    if (isNaN(currentYear)) {
      return reply.status(400).send({
        error: 'Invalid parameters',
        message: '年份必须是有效的数字'
      })
    }

    // 获取该年所有交易
    const startDate = new Date(currentYear, 0, 1)
    const endDate = new Date(currentYear + 1, 0, 1)

    const transactions = await prisma.transaction.findMany({
      where: {
        transactionTime: {
          gte: startDate,
          lt: endDate
        }
      },
      select: {
        transactionTime: true,
        amount: true,
        category: true
      }
    })

    // 按月聚合
    const monthlyStats = Array.from({ length: 12 }, (_, month) => {
      const monthTransactions = transactions.filter(tx => {
        return tx.transactionTime.getMonth() === month
      })

      const income = monthTransactions
        .filter(tx => tx.amount > 0)
        .reduce((sum, tx) => sum + tx.amount, 0)

      const expense = monthTransactions
        .filter(tx => tx.amount < 0)
        .reduce((sum, tx) => sum + tx.amount, 0)

      // 按分类统计
      const categoryBreakdown = {}
      monthTransactions.forEach(tx => {
        if (tx.category) {
          if (!categoryBreakdown[tx.category]) {
            categoryBreakdown[tx.category] = { income: 0, expense: 0 }
          }
          if (tx.amount > 0) {
            categoryBreakdown[tx.category].income += tx.amount
          } else {
            categoryBreakdown[tx.category].expense += tx.amount
          }
        }
      })

      return {
        month: month + 1,
        income,
        expense,
        net: income + expense,
        count: monthTransactions.length,
        categoryBreakdown
      }
    })

    return {
      year: currentYear,
      months: monthlyStats
    }
  })

  /**
   * GET /api/statistics/category
   * 获取分类统计数据
   */
  fastify.get('/category', async (request, reply) => {
    const { type, startDate, endDate } = request.query

    // 构建时间过滤条件
    const timeFilter = {}
    if (startDate && endDate) {
      const start = new Date(startDate)
      const end = new Date(endDate)

      if (isNaN(start.getTime()) || isNaN(end.getTime())) {
        return reply.status(400).send({
          error: 'Invalid parameters',
          message: '日期格式不正确'
        })
      }

      timeFilter.transactionTime = {
        gte: start,
        lte: end
      }
    }

    // 构建类型过滤条件
    const typeFilter = {}
    if (type === 'income') {
      typeFilter.amount = { gt: 0 }
    } else if (type === 'expense') {
      typeFilter.amount = { lt: 0 }
    }

    // 按分类统计
    const categoryStats = await prisma.transaction.groupBy({
      by: ['category'],
      _count: {
        transactionId: true
      },
      _sum: {
        amount: true
      },
      where: {
        ...timeFilter,
        ...typeFilter,
        category: {
          not: null
        }
      }
    })

    // 按分类和月份统计
    const categoryMonthlyStats = await prisma.$queryRaw`
      SELECT
        category,
        EXTRACT(YEAR FROM "transactionTime") as year,
        EXTRACT(MONTH FROM "transactionTime") as month,
        COUNT(*) as count,
        SUM(amount) as total
      FROM "Transaction"
      WHERE category IS NOT NULL
        ${startDate ? prisma.$queryRaw`AND "transactionTime" >= ${new Date(startDate)}` : prisma.$queryRaw``}
        ${endDate ? prisma.$queryRaw`AND "transactionTime" <= ${new Date(endDate)}` : prisma.$queryRaw``}
      GROUP BY category, year, month
      ORDER BY category, year, month
    `

    return {
      byCategory: categoryStats.map(stat => ({
        category: stat.category,
        count: stat._count.transactionId,
        total: stat._sum.amount || 0
      })),
      byCategoryAndMonth: categoryMonthlyStats
    }
  })

  /**
   * GET /api/statistics/trend
   * 获取收支趋势数据
   */
  fastify.get('/trend', async (request, reply) => {
    const { months = 12, type = 'all' } = request.query
    const monthCount = parseInt(months)

    if (isNaN(monthCount) || monthCount < 1 || monthCount > 60) {
      return reply.status(400).send({
        error: 'Invalid parameters',
        message: 'months 必须是 1-60 之间的数字'
      })
    }

    // 计算起始日期
    const now = new Date()
    const startDate = new Date(now.getFullYear(), now.getMonth() - monthCount, 1)

    // 获取交易数据
    const transactions = await prisma.transaction.findMany({
      where: {
        transactionTime: {
          gte: startDate
        }
      },
      orderBy: {
        transactionTime: 'asc'
      },
      select: {
        transactionTime: true,
        amount: true,
        category: true
      }
    })

    // 按月聚合
    const monthlyData = []
    for (let i = 0; i < monthCount; i++) {
      const date = new Date(now.getFullYear(), now.getMonth() - monthCount + i, 1)
      const monthTransactions = transactions.filter(tx => {
        return tx.transactionTime.getMonth() === date.getMonth() &&
               tx.transactionTime.getFullYear() === date.getFullYear()
      })

      const income = monthTransactions
        .filter(tx => tx.amount > 0)
        .reduce((sum, tx) => sum + tx.amount, 0)

      const expense = monthTransactions
        .filter(tx => tx.amount < 0)
        .reduce((sum, tx) => sum + tx.amount, 0)

      monthlyData.push({
        date: date.toISOString().substring(0, 7), // YYYY-MM
        income,
        expense,
        net: income + expense
      })
    }

    return {
      period: {
        startDate: startDate.toISOString(),
        endDate: now.toISOString(),
        months: monthCount
      },
      data: monthlyData
    }
  })

  /**
   * GET /api/statistics/platform
   * 获取平台统计数据
   */
  fastify.get('/platform', async () => {
    const platformStats = await prisma.transaction.groupBy({
      by: ['platform'],
      _count: {
        transactionId: true
      },
      _sum: {
        amount: true
      }
    })

    return {
      platforms: platformStats.map(stat => ({
        platform: stat.platform,
        count: stat._count.transactionId,
        totalAmount: stat._sum.amount || 0
      }))
    }
  })
}
