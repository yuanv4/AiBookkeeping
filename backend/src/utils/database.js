import { PrismaClient } from '@prisma/client'
import bcrypt from 'bcryptjs'
import fs from 'fs'
import path from 'path'
import { fileURLToPath } from 'url'
import { execSync } from 'child_process'

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)

// 动态解析数据库绝对路径，确保无论从哪里运行都指向正确的数据库文件
const backendDir = path.resolve(__dirname, '../..')
const dbAbsolutePath = path.join(backendDir, 'data', 'bookkeeping.db')

// 设置 DATABASE_URL 环境变量为绝对路径
process.env.DATABASE_URL = `file:${dbAbsolutePath}`

console.log(`📂 数据库路径: ${dbAbsolutePath}`)

const prisma = new PrismaClient()

/**
 * 初始化数据库
 * - 检查数据库文件是否存在
 * - 如果不存在,运行 Prisma push 创建表结构
 * - 创建默认用户和配置
 */
export async function initializeDatabase() {
  try {
    const dbPath = path.join(__dirname, '../../data/bookkeeping.db')
    const dbExists = fs.existsSync(dbPath)

    if (!dbExists) {
      console.log('📦 数据库不存在,开始初始化...')

      // 确保数据目录存在
      const dataDir = path.dirname(dbPath)
      if (!fs.existsSync(dataDir)) {
        fs.mkdirSync(dataDir, { recursive: true })
        console.log('  ✅ 数据目录已创建')
      }

      // 运行 prisma db push 创建表结构
      console.log('  ⏳ 正在创建数据库表...')
      try {
        // 设置环境变量，确保 Prisma CLI 使用正确的数据库路径
        const env = {
          ...process.env,
          DATABASE_URL: `file:${dbAbsolutePath}`
        }
        execSync('npx prisma db push --skip-generate', {
          cwd: path.join(__dirname, '../../'),
          stdio: 'pipe',
          env
        })
        console.log('  ✅ 数据库表创建成功')
      } catch (error) {
        console.error('  ❌ 创建数据库表失败:', error.message)
        throw new Error('数据库表创建失败,请确保 Prisma 已正确配置')
      }

      // 等待数据库文件创建完成
      await new Promise(resolve => setTimeout(resolve, 500))
    } else {
      console.log('✅ 数据库文件已存在')

      // 无论数据库是否存在,都运行一次 prisma db push 确保表结构是最新的
      console.log('  ⏳ 检查数据库表结构...')
      try {
        // 设置环境变量，确保 Prisma CLI 使用正确的数据库路径
        const env = {
          ...process.env,
          DATABASE_URL: `file:${dbAbsolutePath}`
        }
        execSync('npx prisma db push --skip-generate', {
          cwd: path.join(__dirname, '../../'),
          stdio: 'pipe',
          env
        })
        console.log('  ✅ 数据库表结构检查完成')
      } catch (error) {
        console.error('  ⚠️  数据库表结构检查失败(可忽略):', error.message)
      }
    }

    // 检查是否有管理员用户,如果没有则创建
    const adminCount = await prisma.user.count({
      where: { username: 'admin' }
    })

    if (adminCount === 0) {
      console.log('👤 未检测到管理员用户,创建默认用户...')
      const defaultPassword = process.env.DEFAULT_ADMIN_PASSWORD || 'admin123'
      const hashedPassword = await bcrypt.hash(defaultPassword, 10)

      const admin = await prisma.user.create({
        data: {
          username: 'admin',
          password: hashedPassword
        }
      })

      console.log(`  ✅ 管理员用户已创建: admin / ${defaultPassword}`)
      console.log('  ⚠️  请在生产环境中立即修改默认密码！')
      console.log('🎉 数据库初始化完成!')
    } else {
      console.log('✅ 管理员用户已存在,跳过创建')
    }
  } catch (error) {
    console.error('❌ 数据库初始化失败:', error)
    throw error
  }
}

export { prisma }
