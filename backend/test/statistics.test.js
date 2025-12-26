import { test } from 'tap'
import { createApp } from '../src/app.js'
import { prisma } from '../src/app.js'

let app
let testToken

test('setup', async () => {
  app = await createApp()
  await app.ready()

  // 创建测试用户
  const response = await app.inject({
    method: 'POST',
    url: '/api/auth/register',
    payload: {
      username: 'test_stats_user',
      password: 'test123456'
    }
  })

  testToken = response.json().data.token

  // 清理旧数据
  await prisma.transaction.deleteMany({})

  // 创建测试数据
  const transactions = [
    {
      transactionId: 'STAT001',
      platform: 'alipay',
      transactionTime: new Date('2024-01-15T10:30:00Z'),
      amount: -100.50,
      description: '超市购物',
      category: '购物'
    },
    {
      transactionId: 'STAT002',
      platform: 'wechat',
      transactionTime: new Date('2024-01-16T14:20:00Z'),
      amount: -50.00,
      description: '餐饮',
      category: '餐饮'
    },
    {
      transactionId: 'STAT003',
      platform: 'alipay',
      transactionTime: new Date('2024-01-17T09:00:00Z'),
      amount: 5000.00,
      description: '工资收入',
      category: '工资'
    },
    {
      transactionId: 'STAT004',
      platform: 'alipay',
      transactionTime: new Date('2024-02-10T10:30:00Z'),
      amount: -200.00,
      description: '服装',
      category: '购物'
    },
    {
      transactionId: 'STAT005',
      platform: 'wechat',
      transactionTime: new Date('2024-02-15T14:20:00Z'),
      amount: -80.00,
      description: '外卖',
      category: '餐饮'
    }
  ]

  await app.inject({
    method: 'POST',
    url: '/api/transactions/batch-upsert',
    headers: {
      authorization: `Bearer ${testToken}`
    },
    payload: { transactions }
  })
})

test('GET /api/statistics/overview - 获取总体统计', async (t) => {
  const response = await app.inject({
    method: 'GET',
    url: '/api/statistics/overview',
    headers: {
      authorization: `Bearer ${testToken}`
    }
  })

  t.equal(response.statusCode, 200)

  const json = response.json()
  t.ok(json.overview, '应该有 overview 字段')
  t.equal(json.overview.totalIncome, 5000.00, '总收入应该匹配')
  t.equal(json.overview.totalExpense, -430.50, '总支出应该匹配')
  t.equal(json.overview.totalCount, 5, '总交易数应该匹配')

  t.ok(Array.isArray(json.byPlatform), 'byPlatform 应该是数组')
  t.ok(Array.isArray(json.byCategory), 'byCategory 应该是数组')
})

test('GET /api/statistics/monthly - 获取月度统计', async (t) => {
  const response = await app.inject({
    method: 'GET',
    url: '/api/statistics/monthly?year=2024',
    headers: {
      authorization: `Bearer ${testToken}`
    }
  })

  t.equal(response.statusCode, 200)

  const json = response.json()
  t.equal(json.year, 2024, '年份应该匹配')
  t.ok(Array.isArray(json.months), 'months 应该是数组')
  t.equal(json.months.length, 12, '应该有 12 个月的数据')

  // 验证 1 月的数据
  const january = json.months[0]
  t.equal(january.month, 1, '月份应该是 1')
  t.equal(january.income, 5000.00, '1 月收入应该匹配')
  t.equal(january.expense, -150.50, '1 月支出应该匹配')

  // 验证 2 月的数据
  const february = json.months[1]
  t.equal(february.month, 2, '月份应该是 2')
  t.equal(february.expense, -280.00, '2 月支出应该匹配')
})

test('GET /api/statistics/monthly - 无效的年份应该失败', async (t) => {
  const response = await app.inject({
    method: 'GET',
    url: '/api/statistics/monthly?year=invalid',
    headers: {
      authorization: `Bearer ${testToken}`
    }
  })

  t.equal(response.statusCode, 400)
})

test('GET /api/statistics/category - 获取分类统计', async (t) => {
  const response = await app.inject({
    method: 'GET',
    url: '/api/statistics/category',
    headers: {
      authorization: `Bearer ${testToken}`
    }
  })

  t.equal(response.statusCode, 200)

  const json = response.json()
  t.ok(Array.isArray(json.byCategory), 'byCategory 应该是数组')

  // 查找购物分类
  const shopping = json.byCategory.find(c => c.category === '购物')
  t.ok(shopping, '应该有购物分类')
  t.equal(shopping.count, 2, '购物应该有 2 笔交易')
})

test('GET /api/statistics/trend - 获取收支趋势', async (t) => {
  const response = await app.inject({
    method: 'GET',
    url: '/api/statistics/trend?months=3',
    headers: {
      authorization: `Bearer ${testToken}`
    }
  })

  t.equal(response.statusCode, 200)

  const json = response.json()
  t.ok(json.period, '应该有 period 字段')
  t.equal(json.period.months, 3, '应该有 3 个月的数据')
  t.ok(Array.isArray(json.data), 'data 应该是数组')
  t.equal(json.data.length, 3, '应该有 3 个数据点')
})

test('GET /api/statistics/trend - 无效的月份数应该失败', async (t) => {
  const response = await app.inject({
    method: 'GET',
    url: '/api/statistics/trend?months=100',
    headers: {
      authorization: `Bearer ${testToken}`
    }
  })

  t.equal(response.statusCode, 400)
})

test('GET /api/statistics/platform - 获取平台统计', async (t) => {
  const response = await app.inject({
    method: 'GET',
    url: '/api/statistics/platform',
    headers: {
      authorization: `Bearer ${testToken}`
    }
  })

  t.equal(response.statusCode, 200)

  const json = response.json()
  t.ok(Array.isArray(json.platforms), 'platforms 应该是数组')

  // 验证支付宝平台
  const alipay = json.platforms.find(p => p.platform === 'alipay')
  t.ok(alipay, '应该有支付宝平台')
  t.equal(alipay.count, 3, '支付宝应该有 3 笔交易')

  // 验证微信平台
  const wechat = json.platforms.find(p => p.platform === 'wechat')
  t.ok(wechat, '应该有微信平台')
  t.equal(wechat.count, 2, '微信应该有 2 笔交易')
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
