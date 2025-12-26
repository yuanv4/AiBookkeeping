import { prisma } from '../app.js'

export default async function categoryRoutes(fastify) {
  // 所有路由需要认证
  fastify.addHook('onRequest', fastify.authenticate)

  // ============ 分类体系 API (对齐 categoriesRepo) ============

  // 获取所有分类
  fastify.get('/', async () => {
    const categories = await prisma.category.findMany({
      orderBy: { name: 'asc' }
    })
    return categories
  })

  // 全量替换分类（幂等 upsert）
  fastify.put('/', async (request, reply) => {
    const { categories } = request.body

    if (!Array.isArray(categories)) {
      return reply.status(400).send({
        error: 'Invalid input',
        message: 'categories 必须是数组'
      })
    }

    // 删除所有现有分类
    await prisma.category.deleteMany()

    // 批量创建新分类
    const result = await prisma.category.createMany({
      data: categories,
      skipDuplicates: true
    })

    return {
      success: true,
      count: result.count
    }
  })

  // ============ 交易分类映射 API (对齐 transactionCategoriesRepo) ============

  // 获取所有交易分类映射（返回对象映射格式，对齐前端业务层）
  fastify.get('/transaction-categories', async () => {
    const rows = await prisma.transactionCategory.findMany()

    // 转换为对象映射: { [transactionId]: categoryData }
    const mapping = {}
    rows.forEach(row => {
      mapping[row.transactionId] = {
        category: row.category,
        subcategory: row.subcategory,
        confidence: row.confidence,
        reasoning: row.reasoning,
        isManual: row.isManual,
        updatedAt: row.updatedAt.toISOString()
      }
    })

    return mapping
  })

  // 更新单个交易的分类
  fastify.put('/transaction-categories/:transactionId', async (request, reply) => {
    const { transactionId } = request.params
    const categoryData = request.body

    const result = await prisma.transactionCategory.upsert({
      where: { transactionId },
      update: {
        category: categoryData.category,
        subcategory: categoryData.subcategory,
        confidence: categoryData.confidence,
        reasoning: categoryData.reasoning,
        isManual: categoryData.isManual ?? false
      },
      create: {
        transactionId,
        ...categoryData,
        isManual: categoryData.isManual ?? false
      }
    })

    return result
  })

  // 批量 upsert 交易分类映射
  fastify.post('/transaction-categories/batch-upsert', async (request, reply) => {
    const { updates } = request.body

    if (!Array.isArray(updates)) {
      return reply.status(400).send({
        error: 'Invalid input',
        message: 'updates 必须是数组'
      })
    }

    // 批量 upsert（逐个处理）
    const results = []
    for (const { transactionId, categoryData } of updates) {
      const result = await prisma.transactionCategory.upsert({
        where: { transactionId },
        update: {
          category: categoryData.category,
          subcategory: categoryData.subcategory,
          confidence: categoryData.confidence,
          reasoning: categoryData.reasoning,
          isManual: categoryData.isManual ?? false
        },
        create: {
          transactionId,
          ...categoryData,
          isManual: categoryData.isManual ?? false
        }
      })
      results.push(result)
    }

    return {
      success: true,
      count: results.length
    }
  })

  // 清空交易分类映射
  fastify.delete('/transaction-categories', async () => {
    await prisma.transactionCategory.deleteMany()

    return {
      success: true,
      message: '所有交易分类映射已清空'
    }
  })

  // ============ 用户纠正历史 API (对齐 correctionsRepo) ============

  // 获取所有纠正历史
  fastify.get('/corrections', async () => {
    const corrections = await prisma.correction.findMany({
      orderBy: { timestamp: 'desc' }
    })
    return corrections
  })

  // 添加纠正记录
  fastify.post('/corrections', async (request, reply) => {
    const { transactionId, originalCategory, correctedCategory } = request.body

    if (!transactionId || !originalCategory || !correctedCategory) {
      return reply.status(400).send({
        error: 'Missing fields',
        message: 'transactionId, originalCategory, correctedCategory 不能为空'
      })
    }

    const correction = await prisma.correction.create({
      data: {
        transactionId,
        originalCategory,
        correctedCategory,
        timestamp: new Date()
      }
    })

    return correction
  })

  // 清空纠正历史
  fastify.delete('/corrections', async () => {
    await prisma.correction.deleteMany()

    return {
      success: true,
      message: '所有纠正历史已清空'
    }
  })

  // 清空所有分类数据（分类 + 映射 + 纠正）
  fastify.delete('/classification', async () => {
    await prisma.category.deleteMany()
    await prisma.transactionCategory.deleteMany()
    await prisma.correction.deleteMany()

    return {
      success: true,
      message: '所有分类数据已清空'
    }
  })
}
