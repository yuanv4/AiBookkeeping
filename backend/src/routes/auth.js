import { prisma } from '../app.js'
import bcrypt from 'bcryptjs'

export default async function authRoutes(fastify) {
  // 用户注册
  fastify.post('/register', async (request, reply) => {
    const { username, password } = request.body

    if (!username || !password) {
      return reply.status(400).send({
        error: 'Missing fields',
        message: '用户名和密码不能为空'
      })
    }

    if (password.length < 6) {
      return reply.status(400).send({
        error: 'Invalid password',
        message: '密码长度不能少于 6 位'
      })
    }

    // 检查用户名是否已存在
    const existingUser = await prisma.user.findUnique({
      where: { username }
    })

    if (existingUser) {
      return reply.status(409).send({
        error: 'Conflict',
        message: '用户名已存在'
      })
    }

    const hashedPassword = await bcrypt.hash(password, 10)

    const user = await prisma.user.create({
      data: {
        username,
        password: hashedPassword
      },
      select: {
        id: true,
        username: true,
        createdAt: true
      }
    })

    const token = fastify.jwt.sign({
      userId: user.id,
      username: user.username
    })

    return reply.status(201).send({
      success: true,
      data: {
        token,
        user
      }
    })
  })

  // 用户登录
  fastify.post('/login', async (request, reply) => {
    const { username, password } = request.body

    if (!username || !password) {
      return reply.status(400).send({
        error: 'Missing fields',
        message: '用户名和密码不能为空'
      })
    }

    const user = await prisma.user.findUnique({
      where: { username }
    })

    if (!user) {
      return reply.status(401).send({
        error: 'Unauthorized',
        message: '用户名或密码错误'
      })
    }

    const isValid = await bcrypt.compare(password, user.password)

    if (!isValid) {
      return reply.status(401).send({
        error: 'Unauthorized',
        message: '用户名或密码错误'
      })
    }

    const token = fastify.jwt.sign({
      userId: user.id,
      username: user.username
    })

    return {
      success: true,
      data: {
        token,
        user: {
          id: user.id,
          username: user.username
        }
      }
    }
  })

  // 获取当前用户信息（需要认证）
  fastify.get('/me', {
    onRequest: [fastify.authenticate]
  }, async (request, reply) => {
    const user = await prisma.user.findUnique({
      where: { id: request.user.userId },
      select: {
        id: true,
        username: true,
        createdAt: true
      }
    })

    if (!user) {
      return reply.status(404).send({
        error: 'Not Found',
        message: '用户不存在'
      })
    }

    return {
      success: true,
      data: user
    }
  })

  // 刷新 token
  fastify.post('/refresh', {
    onRequest: [fastify.authenticate]
  }, async (request, reply) => {
    const token = fastify.jwt.sign({
      userId: request.user.userId,
      username: request.user.username
    })

    return {
      success: true,
      data: {
        token
      },
      message: 'Token 刷新成功'
    }
  })

  // 修改密码（需要认证）
  fastify.post('/change-password', {
    onRequest: [fastify.authenticate]
  }, async (request, reply) => {
    const { oldPassword, newPassword } = request.body

    if (!oldPassword || !newPassword) {
      return reply.status(400).send({
        error: 'Missing fields',
        message: '旧密码和新密码不能为空'
      })
    }

    if (newPassword.length < 6) {
      return reply.status(400).send({
        error: 'Invalid password',
        message: '新密码长度不能少于 6 位'
      })
    }

    const user = await prisma.user.findUnique({
      where: { id: request.user.userId }
    })

    if (!user) {
      return reply.status(404).send({
        error: 'Not Found',
        message: '用户不存在'
      })
    }

    const isValid = await bcrypt.compare(oldPassword, user.password)

    if (!isValid) {
      return reply.status(401).send({
        error: 'Unauthorized',
        message: '旧密码错误'
      })
    }

    const hashedPassword = await bcrypt.hash(newPassword, 10)

    await prisma.user.update({
      where: { id: user.id },
      data: { password: hashedPassword }
    })

    return {
      message: '密码修改成功'
    }
  })

  // 登出（前端删除 token 即可，后端仅返回成功）
  fastify.post('/logout', {
    onRequest: [fastify.authenticate]
  }, async () => {
    return {
      message: '登出成功'
    }
  })
}
