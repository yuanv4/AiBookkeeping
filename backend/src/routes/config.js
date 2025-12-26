import { prisma } from '../app.js'

export default async function configRoutes(fastify) {
  // 所有路由需要认证
  fastify.addHook('onRequest', fastify.authenticate)

  // 获取指定配置（对齐 configRepo.get）
  fastify.get('/:key', async (request, reply) => {
    const { key } = request.params
    const userId = request.user.userId

    const config = await prisma.appConfig.findUnique({
      where: {
        userId_key: {
          userId,
          key
        }
      }
    })

    if (!config) {
      return reply.status(404).send({
        error: 'Not Found',
        message: `配置项 ${key} 不存在`
      })
    }

    // 解析 JSON 值
    let value
    try {
      value = JSON.parse(config.value)
    } catch {
      value = config.value
    }

    return {
      key: config.key,
      value
    }
  })

  // 设置配置（对齐 configRepo.set）
  fastify.put('/:key', async (request, reply) => {
    const { key } = request.params
    const { value } = request.body
    const userId = request.user.userId

    if (value === undefined) {
      return reply.status(400).send({
        error: 'Missing value',
        message: 'value 不能为空'
      })
    }

    // 将值转换为 JSON 字符串
    const valueStr = typeof value === 'string' ? value : JSON.stringify(value)

    const config = await prisma.appConfig.upsert({
      where: {
        userId_key: {
          userId,
          key
        }
      },
      update: {
        value: valueStr
      },
      create: {
        userId,
        key,
        value: valueStr
      }
    })

    let parsedValue
    try {
      parsedValue = JSON.parse(config.value)
    } catch {
      parsedValue = config.value
    }

    return {
      key: config.key,
      value: parsedValue
    }
  })

  // 删除指定配置
  fastify.delete('/:key', async (request, reply) => {
    const { key } = request.params
    const userId = request.user.userId

    try {
      await prisma.appConfig.delete({
        where: {
          userId_key: {
            userId,
            key
          }
        }
      })

      return {
        success: true,
        message: `配置项 ${key} 已删除`
      }
    } catch (error) {
      if (error.code === 'P2025') {
        return reply.status(404).send({
          error: 'Not Found',
          message: `配置项 ${key} 不存在`
        })
      }
      throw error
    }
  })

  // 清空当前用户的所有配置（对齐 configRepo.clear）
  fastify.delete('/', async (request, reply) => {
    const userId = request.user.userId

    await prisma.appConfig.deleteMany({
      where: { userId }
    })

    return {
      success: true,
      message: '所有配置已清空'
    }
  })
}
