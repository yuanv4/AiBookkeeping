import Fastify from 'fastify'
import cors from '@fastify/cors'
import jwt from '@fastify/jwt'
import path from 'path'
import { fileURLToPath } from 'url'
import { prisma, initializeDatabase } from './utils/database.js'

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)

// 创建 Fastify 应用实例
export async function createApp() {
  // 初始化数据库
  await initializeDatabase()

  const app = Fastify({
    logger: {
      level: process.env.LOG_LEVEL || 'info'
    },
    // 增加请求体大小限制（默认 1MB，改为 10MB）
    bodyLimit: 10 * 1024 * 1024
  })

  // 注册 CORS 插件
  await app.register(cors, {
    origin: process.env.CORS_ORIGIN || 'http://localhost:3000',
    credentials: true
  })

  // 注册 JWT 插件
  await app.register(jwt, {
    secret: process.env.JWT_SECRET || 'your-secret-key-change-in-production'
  })

  // 认证中间件
  app.decorate('authenticate', async (request, reply) => {
    try {
      await request.jwtVerify()
    } catch (err) {
      reply.send(err)
    }
  })

  // 健康检查端点（无需认证）
  app.get('/api/health', async () => {
    return {
      status: 'ok',
      timestamp: new Date().toISOString(),
      database: 'connected'
    }
  })

  // 注册路由
  await app.register(import('./routes/auth.js'), { prefix: '/api/auth' })
  await app.register(import('./routes/transactions.js'), { prefix: '/api/transactions' })
  await app.register(import('./routes/categories.js'), { prefix: '/api/categories' })
  await app.register(import('./routes/config.js'), { prefix: '/api/config' })
  await app.register(import('./routes/backup.js'), { prefix: '/api/backup' })
  await app.register(import('./routes/migration.js'), { prefix: '/api/migration' })
  await app.register(import('./routes/statistics.js'), { prefix: '/api/statistics' })

  // 全局错误处理
  app.setErrorHandler((error, request, reply) => {
    app.log.error(error)

    // 记录请求信息
    const requestInfo = {
      method: request.method,
      url: request.url,
      headers: {
        'user-agent': request.headers['user-agent'],
        'content-type': request.headers['content-type']
      }
    }
    app.log.debug({ requestInfo, error: error.message }, 'Request failed')

    // 验证错误
    if (error.validation) {
      reply.status(400).send({
        success: false,
        error: 'Validation Error',
        message: error.message,
        details: error.validation,
        timestamp: new Date().toISOString()
      })
      return
    }

    // Prisma 唯一约束冲突
    if (error.code === 'P2002') {
      reply.status(409).send({
        success: false,
        error: 'Conflict',
        message: '资源已存在',
        field: error.meta?.target,
        timestamp: new Date().toISOString()
      })
      return
    }

    // Prisma 记录未找到
    if (error.code === 'P2025') {
      reply.status(404).send({
        success: false,
        error: 'Not Found',
        message: '请求的资源不存在',
        timestamp: new Date().toISOString()
      })
      return
    }

    // JWT 认证错误
    if (error.name === 'UnauthorizedError') {
      reply.status(401).send({
        success: false,
        error: 'Unauthorized',
        message: '认证失败,请重新登录',
        timestamp: new Date().toISOString()
      })
      return
    }

    // 通用错误响应
    const statusCode = error.statusCode || 500
    const isDevelopment = process.env.NODE_ENV !== 'production'

    reply.status(statusCode).send({
      success: false,
      error: error.name || 'Internal Server Error',
      message: error.message || '服务器内部错误',
      ...(isDevelopment && { stack: error.stack }), // 开发环境返回堆栈信息
      timestamp: new Date().toISOString()
    })
  })

  // 优雅关闭
  app.addHook('onClose', async () => {
    await prisma.$disconnect()
  })

  return app
}

// 导出 prisma 实例供其他模块使用
export { prisma }
