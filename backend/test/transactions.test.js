import { test } from 'tap'
import { createApp } from '../src/app.js'
import { prisma } from '../src/app.js'

let app
let testToken
let testTransactionId

test('setup', async () => {
  app = await createApp()
  await app.ready()

  // 创建测试用户
  const response = await app.inject({
    method: 'POST',
    url: '/api/auth/register',
    payload: {
      username: 'test_tx_user',
      password: 'test123456'
    }
  })

  testToken = response.json().data.token

  // 清理旧数据
  await prisma.transaction.deleteMany({})
})

test('POST /api/transactions/batch-upsert - 批量创建交易', async (t) => {
  const transactions = [
    {
      transactionId: 'TX001',
      platform: 'alipay',
      transactionTime: new Date('2024-01-15T10:30:00Z'),
      amount: -100.50,
      description: '超市购物',
      category: '购物'
    },
    {
      transactionId: 'TX002',
      platform: 'wechat',
      transactionTime: new Date('2024-01-16T14:20:00Z'),
      amount: -50.00,
      description: '餐饮',
      category: '餐饮'
    },
    {
      transactionId: 'TX003',
      platform: 'alipay',
      transactionTime: new Date('2024-01-17T09:00:00Z'),
      amount: 5000.00,
      description: '工资收入',
      category: '工资'
    }
  ]

  const response = await app.inject({
    method: 'POST',
    url: '/api/transactions/batch-upsert',
    headers: {
      authorization: `Bearer ${testToken}`
    },
    payload: { transactions }
  })

  t.equal(response.statusCode, 200)

  const json = response.json()
  t.ok(json.success, '响应应该成功')
  t.equal(json.count, 3, '应该创建 3 条交易')

  testTransactionId = transactions[0].transactionId
})

test('GET /api/transactions - 获取所有交易', async (t) => {
  const response = await app.inject({
    method: 'GET',
    url: '/api/transactions',
    headers: {
      authorization: `Bearer ${testToken}`
    }
  })

  t.equal(response.statusCode, 200)

  const json = response.json()
  t.ok(Array.isArray(json), '应该返回数组')
  t.equal(json.length, 3, '应该有 3 条交易')
})

test('GET /api/transactions/month/:year/:month - 按月查询', async (t) => {
  const response = await app.inject({
    method: 'GET',
    url: '/api/transactions/month/2024/1',
    headers: {
      authorization: `Bearer ${testToken}`
    }
  })

  t.equal(response.statusCode, 200)

  const json = response.json()
  t.equal(json.year, 2024, '年份应该匹配')
  t.equal(json.month, 1, '月份应该匹配')
  t.equal(json.count, 3, '应该有 3 条交易')
  t.ok(Array.isArray(json.transactions), 'transactions 应该是数组')
})

test('GET /api/transactions/month/:year/:month - 无效的月份应该失败', async (t) => {
  const response = await app.inject({
    method: 'GET',
    url: '/api/transactions/month/2024/13',
    headers: {
      authorization: `Bearer ${testToken}`
    }
  })

  t.equal(response.statusCode, 400)
})

test('GET /api/transactions/platform/:platform - 按平台查询', async (t) => {
  const response = await app.inject({
    method: 'GET',
    url: '/api/transactions/platform/alipay',
    headers: {
      authorization: `Bearer ${testToken}`
    }
  })

  t.equal(response.statusCode, 200)

  const json = response.json()
  t.equal(json.platform, 'alipay', '平台应该匹配')
  t.equal(json.count, 2, '应该有 2 条支付宝交易')
})

test('GET /api/transactions/platform/:platform - 无效的平台应该失败', async (t) => {
  const response = await app.inject({
    method: 'GET',
    url: '/api/transactions/platform/invalid',
    headers: {
      authorization: `Bearer ${testToken}`
    }
  })

  t.equal(response.statusCode, 400)
})

test('POST /api/transactions/batch-upsert - 更新已存在的交易', async (t) => {
  const transactions = [
    {
      transactionId: 'TX001',
      platform: 'alipay',
      transactionTime: new Date('2024-01-15T10:30:00Z'),
      amount: -150.00, // 更新金额
      description: '超市购物-更新',
      category: '购物'
    }
  ]

  const response = await app.inject({
    method: 'POST',
    url: '/api/transactions/batch-upsert',
    headers: {
      authorization: `Bearer ${testToken}`
    },
    payload: { transactions }
  })

  t.equal(response.statusCode, 200)

  // 验证更新
  const getResponse = await app.inject({
    method: 'GET',
    url: '/api/transactions',
    headers: {
      authorization: `Bearer ${testToken}`
    }
  })

  const updatedTx = getResponse.json().find(tx => tx.transactionId === 'TX001')
  t.equal(updatedTx.amount, -150.00, '金额应该更新')
  t.equal(updatedTx.description, '超市购物-更新', '描述应该更新')
})

test('DELETE /api/transactions - 清空所有交易', async (t) => {
  const response = await app.inject({
    method: 'DELETE',
    url: '/api/transactions',
    headers: {
      authorization: `Bearer ${testToken}`
    }
  })

  t.equal(response.statusCode, 200)

  const json = response.json()
  t.ok(json.success, '响应应该成功')

  // 验证已清空
  const getResponse = await app.inject({
    method: 'GET',
    url: '/api/transactions',
    headers: {
      authorization: `Bearer ${testToken}`
    }
  })

  t.equal(getResponse.json().length, 0, '应该没有交易记录')
})

test('teardown', async () => {
  await prisma.transaction.deleteMany({})
  await prisma.user.deleteMany({
    where: {
      username: {
        contains: 'test_'
      }
    }
  })

  await app.close()
})
