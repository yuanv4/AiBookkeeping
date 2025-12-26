import { prisma } from '../app.js'

export default async function transactionRoutes(fastify) {
  // 所有路由需要认证
  fastify.addHook('onRequest', fastify.authenticate)

  // 获取所有交易
  fastify.get('/', async () => {
    const transactions = await prisma.transaction.findMany({
      orderBy: { transactionTime: 'desc' }
    })

    return transactions
  })

  // 批量 upsert 交易（幂等：相同 transactionId 会更新）
  fastify.post('/batch-upsert', async (request, reply) => {
    const { transactions } = request.body

    if (!Array.isArray(transactions)) {
      return reply.status(400).send({
        error: 'Invalid input',
        message: 'transactions 必须是数组'
      })
    }

    // 批量 upsert（Prisma 不支持原生批量 upsert，需要逐个处理）
    const results = []
    for (const tx of transactions) {
      const result = await prisma.transaction.upsert({
        where: { transactionId: tx.transactionId },
        update: {
          platform: tx.platform,
          bankName: tx.bankName,
          transactionTime: new Date(tx.transactionTime),
          transactionType: tx.transactionType,
          amount: tx.amount,
          fee: tx.fee,
          counterparty: tx.counterparty,
          category: tx.category,
          description: tx.description,
          paymentMethod: tx.paymentMethod,
          account: tx.account,
          status: tx.status,
          merchantOrderId: tx.merchantOrderId,
          remark: tx.remark,
          originalData: tx.originalData ? JSON.stringify(tx.originalData) : null
        },
        create: {
          ...tx,
          transactionTime: new Date(tx.transactionTime),
          originalData: tx.originalData ? JSON.stringify(tx.originalData) : null
        }
      })
      results.push(result)
    }

    return {
      success: true,
      count: results.length
    }
  })

  // 清空所有交易（慎用）
  fastify.delete('/', async () => {
    await prisma.transaction.deleteMany()

    return {
      success: true,
      message: '所有交易已清空'
    }
  })

  // 按月查询交易
  fastify.get('/month/:year/:month', async (request, reply) => {
    const { year, month } = request.params
    const yearNum = parseInt(year)
    const monthNum = parseInt(month)

    if (isNaN(yearNum) || isNaN(monthNum) || monthNum < 1 || monthNum > 12) {
      return reply.status(400).send({
        error: 'Invalid parameters',
        message: '年份和月份格式不正确'
      })
    }

    // 计算月份起止时间（使用 UTC 避免时区问题）
    const startDate = new Date(Date.UTC(yearNum, monthNum - 1, 1, 0, 0, 0))
    const endDate = new Date(Date.UTC(yearNum, monthNum, 1, 0, 0, 0))

    const transactions = await prisma.transaction.findMany({
      where: {
        transactionTime: {
          gte: startDate,
          lt: endDate
        }
      },
      orderBy: { transactionTime: 'desc' }
    })

    return {
      year: yearNum,
      month: monthNum,
      count: transactions.length,
      transactions
    }
  })

  // 按平台查询交易
  fastify.get('/platform/:platform', async (request, reply) => {
    const { platform } = request.params

    const validPlatforms = ['alipay', 'wechat', 'bank']
    if (!validPlatforms.includes(platform)) {
      return reply.status(400).send({
        error: 'Invalid platform',
        message: `平台必须是: ${validPlatforms.join(', ')}`
      })
    }

    const transactions = await prisma.transaction.findMany({
      where: { platform },
      orderBy: { transactionTime: 'desc' }
    })

    return {
      platform,
      count: transactions.length,
      transactions
    }
  })
}
