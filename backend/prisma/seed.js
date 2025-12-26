import { PrismaClient } from '@prisma/client'
import bcrypt from 'bcryptjs'

const prisma = new PrismaClient()

async function seed() {
  console.log('🌱 开始数据库初始化...')

  // 创建默认管理员用户
  const defaultPassword = process.env.DEFAULT_ADMIN_PASSWORD || 'admin123'
  const hashedPassword = await bcrypt.hash(defaultPassword, 10)

  const admin = await prisma.user.upsert({
    where: { username: 'admin' },
    update: {},
    create: {
      username: 'admin',
      password: hashedPassword,
    },
  })

  console.log(`✅ 管理员用户已创建: admin / ${defaultPassword}`)
  console.log('⚠️  请在生产环境中立即修改默认密码！')

  // 创建默认配置
  const defaultAIConfig = {
    provider: 'ollama',
    baseURL: 'http://localhost:11434/v1',
    model: 'qwen2.5:7b',
    timeout: 30000,
    enabled: false,
    fallbackToRules: true,
  }

  await prisma.appConfig.upsert({
    where: {
      userId_key: {
        userId: admin.id,
        key: 'ai_config'
      }
    },
    update: {},
    create: {
      userId: admin.id,
      key: 'ai_config',
      value: JSON.stringify(defaultAIConfig)
    }
  })

  console.log('✅ 默认 AI 配置已创建')

  console.log('🎉 数据库初始化完成！')
}

seed()
  .catch((e) => {
    console.error('❌ 种子数据创建失败:', e)
    process.exit(1)
  })
  .finally(async () => {
    await prisma.$disconnect()
  })
