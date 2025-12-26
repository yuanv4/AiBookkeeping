#!/usr/bin/env node

/**
 * Prisma 客户端生成优化脚本
 * 跨平台版本 (Windows/Linux/Mac)
 *
 * 用法:
 *   node scripts/setup-prisma.js
 *   或
 *   npm run setup:prisma
 */

import { execSync } from 'child_process'
import fs from 'fs'
import path from 'path'
import { fileURLToPath } from 'url'

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)
// scripts 目录的父目录是项目根目录
const rootDir = path.resolve(__dirname, '..')

// 颜色输出
const colors = {
  reset: '\x1b[0m',
  bright: '\x1b[1m',
  red: '\x1b[31m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
}

function log(message, color = 'reset') {
  console.log(`${colors[color]}${message}${colors.reset}`)
}

function exec(command, options = {}) {
  try {
    const output = execSync(command, {
      cwd: rootDir,
      stdio: 'pipe',
      ...options
    })
    return { success: true, output: output.toString() }
  } catch (error) {
    return { success: false, error: error.message }
  }
}

async function checkNodeProcesses() {
  log('[1/5] 检查 Node 进程...', 'blue')

  const isWindows = process.platform === 'win32'
  let hasNodeProcesses = false

  if (isWindows) {
    const result = exec('tasklist /FI "IMAGENAME eq node.exe"')
    hasNodeProcesses = result.output.includes('node.exe')
  } else {
    const result = exec('pgrep -x node || true')
    hasNodeProcesses = result.success && result.output.trim().length > 0
  }

  if (hasNodeProcesses) {
    log('  ⚠️  警告: 检测到 Node 进程正在运行', 'yellow')
    log('     建议先关闭所有 Node 进程以避免文件锁定问题', 'yellow')
    return true // 警告但继续
  } else {
    log('  ✅ 未检测到运行中的 Node 进程', 'green')
    return false
  }
}

async function cleanOldClient() {
  log('[2/5] 清理旧的 Prisma 客户端...', 'blue')

  const prismaDir = path.join(rootDir, 'node_modules', '.prisma')
  const clientDir = path.join(rootDir, 'node_modules', '@prisma', 'client')

  let removed = false

  if (fs.existsSync(prismaDir)) {
    fs.rmSync(prismaDir, { recursive: true, force: true })
    log('  ✅ 已删除 node_modules/.prisma', 'green')
    removed = true
  }

  if (fs.existsSync(clientDir)) {
    fs.rmSync(clientDir, { recursive: true, force: true })
    log('  ✅ 已删除 node_modules/@prisma/client', 'green')
    removed = true
  }

  if (!removed) {
    log('  ℹ️  没有需要清理的文件', 'yellow')
  }

  return true
}

async function regenerateClient() {
  log('[3/5] 重新生成 Prisma 客户端...', 'blue')

  try {
    // 切换到项目根目录执行命令
    const originalDir = process.cwd()
    process.chdir(rootDir)

    try {
      execSync('npx prisma generate', { stdio: 'inherit' })
      log('  ✅ Prisma 客户端生成成功', 'green')
      return true
    } finally {
      process.chdir(originalDir)
    }
  } catch (error) {
    log('  ❌ Prisma 客户端生成失败', 'red')
    log(`     错误: ${error.message}`, 'red')
    return false
  }
}

async function pushDatabaseSchema() {
  log('[4/5] 检查数据库状态...', 'blue')

  const dbPath = path.join(rootDir, 'data', 'bookkeeping.db')

  if (fs.existsSync(dbPath)) {
    log('  ℹ️  数据库已存在,跳过 schema 推送', 'yellow')
    log('     如需重置数据库,请运行: npm run prisma:reset', 'yellow')
    return true
  }

  log('  ⏳ 数据库不存在,推送 schema...', 'yellow')

  // 确保数据目录存在
  const dataDir = path.dirname(dbPath)
  if (!fs.existsSync(dataDir)) {
    fs.mkdirSync(dataDir, { recursive: true })
    log('  ✅ 已创建数据目录', 'green')
  }

  try {
    // 切换到项目根目录执行命令
    const originalDir = process.cwd()
    process.chdir(rootDir)

    try {
      execSync('npx prisma db push --skip-generate', { stdio: 'inherit' })
      log('  ✅ 数据库 schema 推送成功', 'green')
      return true
    } finally {
      process.chdir(originalDir)
    }
  } catch (error) {
    log('  ❌ 数据库 schema 推送失败', 'red')
    log(`     错误: ${error.message}`, 'red')
    return false
  }
}

async function seedDatabase() {
  log('[5/5] 检查数据库种子...', 'blue')

  const dbPath = path.join(rootDir, 'data', 'bookkeeping.db')

  if (!fs.existsSync(dbPath)) {
    log('  ℹ️  数据库不存在,跳过种子数据', 'yellow')
    return true
  }

  // 尝试连接数据库检查是否有管理员用户
  // 这里简单检查数据库文件大小,如果太小说明可能是空的
  const stats = fs.statSync(dbPath)
  if (stats.size < 1024) { // 小于 1KB 可能是空数据库
    log('  ⏳ 数据库可能是空的,运行种子脚本...', 'yellow')

    try {
      // 切换到项目根目录执行命令
      const originalDir = process.cwd()
      process.chdir(rootDir)

      try {
        execSync('npm run prisma:seed', { stdio: 'inherit' })
        log('  ✅ 种子数据创建成功', 'green')
        return true
      } finally {
        process.chdir(originalDir)
      }
    } catch (error) {
      log('  ⚠️  种子数据创建失败(但不影响使用)', 'yellow')
      return true // 种子失败不影响继续
    }
  } else {
    log('  ℹ️  数据库已存在数据,跳过种子', 'yellow')
    return true
  }
}

async function main() {
  console.log('')
  log('========================================', 'bright')
  log('  Prisma 客户端设置脚本', 'bright')
  log('========================================', 'bright')
  console.log('')

  try {
    // 1. 检查 Node 进程
    await checkNodeProcesses()

    // 2. 清理旧客户端
    const cleaned = await cleanOldClient()
    if (!cleaned) {
      log('❌ 清理失败', 'red')
      process.exit(1)
    }

    // 3. 重新生成客户端
    const regenerated = await regenerateClient()
    if (!regenerated) {
      log('❌ Prisma 客户端生成失败', 'red')
      process.exit(1)
    }

    // 4. 推送数据库 schema
    const pushed = await pushDatabaseSchema()
    if (!pushed) {
      log('⚠️  数据库 schema 推送失败,但客户端可用', 'yellow')
    }

    // 5. 种子数据
    await seedDatabase()

    console.log('')
    log('========================================', 'bright')
    log('  ✅ Prisma 设置完成!', 'green')
    log('========================================', 'bright')
    console.log('')
    log('下一步:', 'blue')
    log('  - 启动开发服务器: npm run dev', 'yellow')
    log('  - 查看数据库: npm run prisma:studio', 'yellow')
    console.log('')

  } catch (error) {
    console.log('')
    log('❌ 发生错误:', 'red')
    log(error.message, 'red')
    console.log('')
    process.exit(1)
  }
}

main()
