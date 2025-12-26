import { prisma } from '../app.js'
import crypto from 'crypto'

export default async function backupRoutes(fastify) {
  // 所有路由需要认证
  fastify.addHook('onRequest', fastify.authenticate)

  // 计算校验和
  async function calculateChecksum(dataString) {
    return crypto.createHash('sha256').update(dataString).digest('hex')
  }

  // 创建备份
  fastify.post('/create', async (request, reply) => {
    const userId = request.user.userId

    // 并行获取所有数据
    const [transactions, categories, transactionCategories, corrections, aiConfig] = await Promise.all([
      prisma.transaction.findMany(),
      prisma.category.findMany(),
      prisma.transactionCategory.findMany(),
      prisma.correction.findMany(),
      prisma.appConfig.findUnique({
        where: {
          userId_key: {
            userId,
            key: 'ai_config'
          }
        }
      })
    ])

    // 转换交易分类映射为对象格式（前端业务层格式）
    const transactionCategoriesMapping = {}
    transactionCategories.forEach(row => {
      transactionCategoriesMapping[row.transactionId] = {
        category: row.category,
        subcategory: row.subcategory,
        confidence: row.confidence,
        reasoning: row.reasoning,
        isManual: row.isManual,
        updatedAt: row.updatedAt.toISOString()
      }
    })

    // 构建 AI 配置（脱敏 apiKey）
    let aiConfigValue = {}
    if (aiConfig) {
      try {
        aiConfigValue = JSON.parse(aiConfig.value)
        // 脱敏 apiKey
        if (aiConfigValue.apiKey) {
          aiConfigValue.apiKey = '******'
        }
      } catch {
        aiConfigValue = {}
      }
    }

    const backupData = {
      schemaVersion: '1.0.0',
      appVersion: '1.0.0',
      createdAt: new Date().toISOString(),
      data: {
        transactions,
        categories,
        transactionCategories: transactionCategoriesMapping,
        corrections,
        aiConfig: aiConfigValue
      }
    }

    // 计算校验和
    const checksum = await calculateChecksum(JSON.stringify(backupData.data))
    backupData.checksum = checksum

    // 保存到数据库
    const backup = await prisma.backup.create({
      data: {
        timestamp: BigInt(Date.now()),
        checksum,
        data: JSON.stringify(backupData),
        size: JSON.stringify(backupData).length
      }
    })

    // 保留最近 10 个备份
    const allBackups = await prisma.backup.findMany({
      orderBy: { timestamp: 'desc' }
    })

    if (allBackups.length > 10) {
      const toDelete = allBackups.slice(10)
      await prisma.backup.deleteMany({
        where: {
          id: {
            in: toDelete.map(b => b.id)
          }
        }
      })
    }

    return {
      success: true,
      backupId: backup.id,
      timestamp: backup.timestamp,
      checksum
    }
  })

  // 获取备份列表
  fastify.get('/list', async () => {
    const backups = await prisma.backup.findMany({
      orderBy: { timestamp: 'desc' }
    })

    return backups.map(backup => ({
      id: backup.id,
      timestamp: backup.timestamp.toString(),
      formattedTime: new Date(Number(backup.timestamp)).toLocaleString('zh-CN'),
      size: backup.size,
      checksum: backup.checksum
    }))
  })

  // 恢复备份
  fastify.post('/restore/:id', async (request, reply) => {
    const { id } = request.params
    const userId = request.user.userId

    const backup = await prisma.backup.findUnique({
      where: { id }
    })

    if (!backup) {
      return reply.status(404).send({
        error: 'Not Found',
        message: '备份不存在'
      })
    }

    let backupData
    try {
      backupData = JSON.parse(backup.data)
    } catch {
      return reply.status(400).send({
        error: 'Invalid backup',
        message: '备份数据格式错误'
      })
    }

    // 验证校验和
    const calculatedChecksum = await calculateChecksum(JSON.stringify(backupData.data))
    if (calculatedChecksum !== backup.checksum) {
      return reply.status(400).send({
        error: 'Checksum mismatch',
        message: '备份数据已损坏'
      })
    }

    // 清空现有数据
    await prisma.transaction.deleteMany()
    await prisma.category.deleteMany()
    await prisma.transactionCategory.deleteMany()
    await prisma.correction.deleteMany()

    // 恢复交易数据
    if (backupData.data.transactions?.length > 0) {
      await prisma.transaction.createMany({
        data: backupData.data.transactions,
        skipDuplicates: true
      })
    }

    // 恢复分类数据
    if (backupData.data.categories?.length > 0) {
      await prisma.category.createMany({
        data: backupData.data.categories,
        skipDuplicates: true
      })
    }

    // 恢复交易分类映射（对象格式 → 数组行）
    if (backupData.data.transactionCategories) {
      const mappingRows = Object.entries(backupData.data.transactionCategories).map(
        ([transactionId, data]) => ({
          transactionId,
          ...data
        })
      )
      await prisma.transactionCategory.createMany({
        data: mappingRows,
        skipDuplicates: true
      })
    }

    // 恢复纠正历史
    if (backupData.data.corrections?.length > 0) {
      await prisma.correction.createMany({
        data: backupData.data.corrections,
        skipDuplicates: true
      })
    }

    return {
      success: true,
      message: '备份恢复成功'
    }
  })

  // 删除备份
  fastify.delete('/:id', async (request, reply) => {
    const { id } = request.params

    try {
      await prisma.backup.delete({
        where: { id }
      })

      return {
        success: true,
        message: '备份已删除'
      }
    } catch (error) {
      if (error.code === 'P2025') {
        return reply.status(404).send({
          error: 'Not Found',
          message: '备份不存在'
        })
      }
      throw error
    }
  })
}
