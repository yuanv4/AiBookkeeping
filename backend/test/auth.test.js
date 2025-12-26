import { test } from 'tap'
import { createApp } from '../src/app.js'
import { prisma } from '../src/app.js'

let app
let testToken

test('setup', async () => {
  app = await createApp()
  await app.ready()

  // 清理所有测试用户数据
  await prisma.user.deleteMany({
    where: {
      username: {
        contains: 'test_'
      }
    }
  })
})

test('POST /api/auth/register - 用户注册', async (t) => {
  const response = await app.inject({
    method: 'POST',
    url: '/api/auth/register',
    payload: {
      username: 'test_user',
      password: 'test123456'
    }
  })

  // 调试:打印响应
  if (response.statusCode !== 201) {
    console.log('Unexpected response:', response.statusCode, response.json())
  }

  t.equal(response.statusCode, 201)

  const json = response.json()
  t.ok(json.success, '响应应该成功')
  t.ok(json.data.token, '应该返回 token')
  t.ok(json.data.user, '应该返回用户信息')
  t.equal(json.data.user.username, 'test_user', '用户名应该匹配')
  t.notOk(json.data.user.password, '不应该返回密码')

  testToken = json.data.token
})

test('POST /api/auth/register - 重复注册应该失败', async (t) => {
  const response = await app.inject({
    method: 'POST',
    url: '/api/auth/register',
    payload: {
      username: 'test_user',
      password: 'test123456'
    }
  })

  t.equal(response.statusCode, 409)
})

test('POST /api/auth/register - 缺少必填字段应该失败', async (t) => {
  const response = await app.inject({
    method: 'POST',
    url: '/api/auth/register',
    payload: {
      username: 'test_user2'
      // 缺少 password
    }
  })

  t.equal(response.statusCode, 400)
})

test('POST /api/auth/login - 用户登录', async (t) => {
  const response = await app.inject({
    method: 'POST',
    url: '/api/auth/login',
    payload: {
      username: 'test_user',
      password: 'test123456'
    }
  })

  t.equal(response.statusCode, 200)

  const json = response.json()
  t.ok(json.success, '响应应该成功')
  t.ok(json.data.token, '应该返回 token')
  t.ok(json.data.user, '应该返回用户信息')
  t.equal(json.data.user.username, 'test_user', '用户名应该匹配')
})

test('POST /api/auth/login - 错误的密码应该失败', async (t) => {
  const response = await app.inject({
    method: 'POST',
    url: '/api/auth/login',
    payload: {
      username: 'test_user',
      password: 'wrongpassword'
    }
  })

  t.equal(response.statusCode, 401)

  const json = response.json()
  t.notOk(json.success, '响应应该失败')
})

test('POST /api/auth/login - 不存在的用户应该失败', async (t) => {
  const response = await app.inject({
    method: 'POST',
    url: '/api/auth/login',
    payload: {
      username: 'nonexistent_user',
      password: 'test123456'
    }
  })

  t.equal(response.statusCode, 401)
})

test('GET /api/auth/me - 获取当前用户信息', async (t) => {
  const response = await app.inject({
    method: 'GET',
    url: '/api/auth/me',
    headers: {
      authorization: `Bearer ${testToken}`
    }
  })

  t.equal(response.statusCode, 200)

  const json = response.json()
  t.ok(json.success, '响应应该成功')
  t.ok(json.data, '应该返回用户数据')
  t.equal(json.data.username, 'test_user', '用户名应该匹配')
})

test('GET /api/auth/me - 没有 token 应该失败', async (t) => {
  const response = await app.inject({
    method: 'GET',
    url: '/api/auth/me'
  })

  t.equal(response.statusCode, 401)
})

test('GET /api/auth/me - 无效的 token 应该失败', async (t) => {
  const response = await app.inject({
    method: 'GET',
    url: '/api/auth/me',
    headers: {
      authorization: 'Bearer invalid_token'
    }
  })

  t.equal(response.statusCode, 401)
})

test('POST /api/auth/refresh - 刷新 token', async (t) => {
  const response = await app.inject({
    method: 'POST',
    url: '/api/auth/refresh',
    headers: {
      authorization: `Bearer ${testToken}`
    }
  })

  t.equal(response.statusCode, 200)

  const json = response.json()
  t.ok(json.success, '响应应该成功')
  t.ok(json.data.token, '应该返回新的 token')
})

test('teardown', async () => {
  // 清理测试数据
  await prisma.user.deleteMany({
    where: {
      username: {
        contains: 'test_'
      }
    }
  })

  await app.close()
})
