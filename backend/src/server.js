import { createApp } from './app.js'

async function start() {
  const app = await createApp()

  try {
    const host = process.env.HOST || '0.0.0.0'
    const port = parseInt(process.env.PORT || '3001', 10)

    await app.listen({ port, host })

    console.log(`
╔════════════════════════════════════════════════════════╗
║  🚀 AI 账单汇集工具后端服务启动成功                      ║
╠════════════════════════════════════════════════════════╣
║  地址: http://${host}:${port}                           ║
║  健康检查: http://${host}:${port}/api/health             ║
║  API 文档: 见 README.md                                  ║
╚════════════════════════════════════════════════════════╝
    `)
  } catch (err) {
    app.log.error(err)
    process.exit(1)
  }
}

start()
