import { prisma } from '../app.js'
import crypto from 'crypto'

export default async function migrationRoutes(fastify) {
  // 所有路由需要认证
  fastify.addHook('onRequest', fastify.authenticate)

  // 计算校验和
  async function calculateChecksum(dataString) {
    return crypto.createHash('sha256').update(dataString).digest('hex')
  }

  // 从前端导出的 JSON 导入到后端
  fastify.post('/import', async (request, reply) => {
    const { exportData } = request.body

    if (!exportData || !exportData.data) {
      return reply.status(400).send({
        error: 'Invalid input',
        message: 'exportData 格式不正确'
      })
    }

    // 验证校验和
    if (exportData.checksum) {
      const calculatedChecksum = await calculateChecksum(JSON.stringify(exportData.data))
      if (calculatedChecksum !== exportData.checksum) {
        return reply.status(400).send({
          error: 'Checksum mismatch',
          message: '数据校验和失败,可能已损坏'
        })
      }
    }

    const { transactions, categories, transactionCategories, corrections } = exportData.data
    const userId = request.user.userId

    // 导入交易数据（幂等：重复导入不重复）
    let txCount = 0
    if (transactions?.length > 0) {
      for (const tx of transactions) {
        await prisma.transaction.upsert({
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
            originalData: tx.originalData
          },
          create: {
            ...tx,
            transactionTime: new Date(tx.transactionTime),
            originalData: tx.originalData ? (typeof tx.originalData === 'string' ? tx.originalData : JSON.stringify(tx.originalData)) : null
          }
        })
        txCount++
      }
    }

    // 导入分类数据
    let catCount = 0
    if (categories?.length > 0) {
      for (const cat of categories) {
        await prisma.category.upsert({
          where: { id: cat.id },
          update: {
            name: cat.name,
            description: cat.description,
            color: cat.color,
            icon: cat.icon
          },
          create: cat
        })
        catCount++
      }
    }

    // 导入交易分类映射（对象格式 → 数组行）
    let txCatCount = 0
    if (transactionCategories && typeof transactionCategories === 'object') {
      for (const [transactionId, data] of Object.entries(transactionCategories)) {
        await prisma.transactionCategory.upsert({
          where: { transactionId },
          update: {
            category: data.category,
            subcategory: data.subcategory,
            confidence: data.confidence,
            reasoning: data.reasoning,
            isManual: data.isManual ?? false
          },
          create: {
            transactionId,
            ...data,
            isManual: data.isManual ?? false
          }
        })
        txCatCount++
      }
    }

    // 导入纠正历史
    let corrCount = 0
    if (corrections?.length > 0) {
      for (const corr of corrections) {
        await prisma.correction.create({
          data: corr
        }).catch(() => {
          // 忽略重复记录
        })
        corrCount++
      }
    }

    return {
      success: true,
      message: '数据导入成功',
      stats: {
        transactions: txCount,
        categories: catCount,
        transactionCategories: txCatCount,
        corrections: corrCount
      }
    }
  })

  // 验证导入（返回后端统计，供前端核对）
  fastify.get('/verify', async () => {
    const [txCount, catCount, txCatCount, corrCount] = await Promise.all([
      prisma.transaction.count(),
      prisma.category.count(),
      prisma.transactionCategory.count(),
      prisma.correction.count()
    ])

    return {
      backend: {
        transactions: txCount,
        categories: catCount,
        transactionCategories: txCatCount,
        corrections: corrCount
      },
      schemaVersion: '1.0.0',
      appVersion: '1.0.0',
      timestamp: new Date().toISOString()
    }
  })
}
