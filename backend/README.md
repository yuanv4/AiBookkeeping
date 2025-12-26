# AI 账单汇集工具 - 后端服务

基于 Fastify + Prisma + SQLite 的后端服务。

## 快速开始

### 1. 安装依赖

```bash
cd backend
npm install
```

### 2. 设置 Prisma (推荐)

使用自动设置脚本(推荐):

```bash
npm run setup:prisma
```

或手动设置:

```bash
# 生成 Prisma 客户端
npm run prisma:generate

# 推送数据库 schema
npx prisma db push

# 创建种子数据
npm run prisma:seed
```

### 3. 启动开发服务器

```bash
npm run dev
```

服务器将在 http://localhost:3001 启动。

### 4. 验证服务

访问健康检查端点:

```bash
curl http://localhost:3001/api/health
```

应返回:

```json
{
  "status": "ok",
  "timestamp": "2025-12-26T...",
  "database": "connected"
}
```

## 默认账户

- **用户名**: `admin`
- **密码**: `admin123`

⚠️ **重要**: 请在生产环境中立即修改默认密码!

## 环境变量

复制 `.env.example` 到 `.env` 并配置:

```bash
# 数据库配置
DATABASE_URL="file:./data/bookkeeping.db"

# JWT 配置
JWT_SECRET="your-secret-key-change-in-production"

# 服务器配置
PORT=3001
HOST="0.0.0.0"

# CORS 配置
CORS_ORIGIN="http://localhost:3000"

# 默认管理员密码
DEFAULT_ADMIN_PASSWORD="admin123"
```

## NPM 脚本

| 命令 | 说明 |
|------|------|
| `npm run dev` | 启动开发服务器(热重载) |
| `npm start` | 启动生产服务器 |
| `npm run setup:prisma` | **推荐**: 自动设置 Prisma(清理+生成+推送) |
| `npm run prisma:generate` | 生成 Prisma 客户端 |
| `npm run prisma:migrate` | 运行数据库迁移 |
| `npm run prisma:studio` | 打开 Prisma Studio(数据库管理界面) |
| `npm run prisma:seed` | 创建种子数据 |
| `npm run prisma:reset` | 重置数据库(⚠️ 会删除所有数据) |

## API 端点

### 认证

- `POST /api/auth/login` - 用户登录
- `GET /api/auth/me` - 获取当前用户信息
- `POST /api/auth/change-password` - 修改密码

### 交易

- `GET /api/transactions` - 获取所有交易
- `POST /api/transactions/batch-upsert` - 批量创建/更新交易
- `DELETE /api/transactions` - 清空所有交易
- `GET /api/transactions/month/:y/:m` - 按月查询交易
- `GET /api/transactions/platform/:p` - 按平台查询交易

### 分类

- `GET /api/categories` - 获取所有分类
- `PUT /api/categories` - 批量更新分类
- `GET /api/categories/transaction-categories` - 获取交易分类映射
- `PUT /api/categories/transaction-categories/:txId` - 更新单笔交易分类
- `POST /api/categories/transaction-categories/batch-upsert` - 批量更新交易分类
- `GET /api/categories/corrections` - 获取分类纠正历史
- `POST /api/categories/corrections` - 添加分类纠正记录
- `DELETE /api/categories/classification` - 清空所有分类数据

### 配置

- `GET /api/config/:key` - 获取配置值
- `PUT /api/config/:key` - 设置配置值
- `DELETE /api/config/:key` - 删除配置
- `DELETE /api/config` - 清空所有配置

### 备份

- `POST /api/backup/create` - 创建备份
- `GET /api/backup/list` - 获取备份列表
- `POST /api/backup/restore/:id` - 恢复备份

### 迁移

- `POST /api/migration/import` - 导入数据
- `GET /api/migration/verify` - 验证数据

### 健康检查

- `GET /api/health` - 服务健康状态(无需认证)

## 错误处理

API 返回统一的错误格式:

```json
{
  "success": false,
  "error": "错误类型",
  "message": "详细错误信息",
  "timestamp": "2025-12-26T..."
}
```

### 常见错误码

| 状态码 | 说明 |
|--------|------|
| 400 | 请求参数验证失败 |
| 401 | 未认证或认证失败 |
| 404 | 资源不存在 |
| 409 | 资源冲突(如唯一约束) |
| 500 | 服务器内部错误 |

### Prisma 错误码

| 错误码 | 说明 |
|--------|------|
| P2002 | 唯一约束冲突 |
| P2025 | 记录未找到 |

## 数据库初始化(自动)

后端启动时会自动检查并初始化数据库:

1. **检查数据库文件是否存在**
   - 不存在则创建数据目录和数据库

2. **推送 Prisma Schema**
   - 自动运行 `prisma db push` 创建表结构

3. **创建默认用户**
   - 用户名: `admin`
   - 密码: 从环境变量 `DEFAULT_ADMIN_PASSWORD` 读取(默认 `admin123`)

4. **创建默认配置**
   - AI 配置: 默认使用 Ollama 本地模型

### 手动重置数据库

如果需要重置数据库:

```bash
npm run prisma:reset
```

⚠️ **警告**: 此操作会删除所有数据!

## 开发工具

### Prisma Studio

可视化数据库管理界面:

```bash
npm run prisma:studio
```

在浏览器中打开 http://localhost:5555

### 查看 API 日志

开发模式下,服务器会输出详细日志:

```
[info] Server listening at http://0.0.0.0:3001
[info] GET /api/health 200
```

## 故障排除

### 问题1: Prisma 客户端生成失败

**错误**: `EPERM: operation not permitted, rename 'query_engine-windows.dll.node'`

**解决方案**:

1. 关闭所有 Node 进程
2. 运行自动设置脚本:
   ```bash
   npm run setup:prisma
   ```

### 问题2: 数据库不存在的错误

**错误**: `Error: Database does not exist`

**解决方案**:

数据库会在后端首次启动时自动创建。如果没有创建,手动运行:

```bash
npm run setup:prisma
```

### 问题3: 登录失败

**错误**: `"error": "Unauthorized", "message": "用户名或密码错误"`

**解决方案**:

1. 检查数据库是否有管理员用户
2. 重置数据库并重新创建:
   ```bash
   npm run prisma:reset
   ```

## 项目结构

```
backend/
├── prisma/
│   ├── schema.prisma      # 数据库模型定义
│   ├── seed.js            # 种子数据脚本
│   └── dev.db             # SQLite 数据库文件(运行时生成)
├── src/
│   ├── app.js             # Fastify 应用配置
│   ├── server.js          # 服务器入口
│   ├── routes/            # API 路由
│   │   ├── auth.js
│   │   ├── transactions.js
│   │   ├── categories.js
│   │   ├── config.js
│   │   ├── backup.js
│   │   └── migration.js
│   └── utils/
│       └── database.js    # 数据库初始化工具
├── scripts/
│   ├── setup-prisma.js    # Prisma 设置脚本(跨平台)
│   ├── setup-prisma.sh    # Linux/Mac 版本
│   └── setup-prisma.bat   # Windows 版本
├── data/                  # 数据库文件目录(运行时生成)
├── .env                   # 环境变量配置
├── .env.example           # 环境变量示例
└── package.json
```

## 生产部署

### 1. 设置环境变量

确保设置生产环境变量:

```bash
NODE_ENV=production
JWT_SECRET=强密码
DATABASE_URL=生产数据库路径
```

### 2. 构建并启动

```bash
npm run prisma:generate
npm start
```

### 3. 使用 PM2(推荐)

```bash
npm install -g pm2
pm2 start src/server.js --name "ai-bookkeeping-api"
pm2 save
pm2 startup
```

## 安全建议

1. **修改默认密码**: 在生产环境中立即修改管理员密码
2. **使用强 JWT Secret**: 使用随机生成的强密钥
3. **启用 HTTPS**: 在生产环境中使用 HTTPS
4. **限制 CORS**: 将 `CORS_ORIGIN` 设置为实际的前端域名
5. **定期备份**: 定期备份 SQLite 数据库文件

## 许可证

MIT
