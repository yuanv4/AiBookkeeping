import Dexie from 'dexie'

/**
 * IndexedDB 数据库封装
 * 数据库名: AiBookkeepingDB
 * 版本: v1
 */

export const db = new Dexie('AiBookkeepingDB')

// 定义数据库结构
// 主键使用稳定业务键,索引基于实际查询场景
db.version(1).stores({
  transactions: 'transactionId, transactionTime, platform, amount',
  categories: '++id, name',
  transaction_categories: 'transactionId',
  corrections: '++id, timestamp',
  app_config: 'key',
  backups: '++id, timestamp',
  migration_state: 'key'
})

// 数据库打开失败处理
db.on('blocked', () => {
  console.error('IndexedDB 被其他标签页阻塞')
})

db.on('versionchange', () => {
  // 其他标签页升级了数据库,关闭当前连接
  db.close()
  window.location.reload()
})
