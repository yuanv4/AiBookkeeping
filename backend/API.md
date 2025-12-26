# AI 账单汇集工具 - 后端 API 文档

## 基本信息

- **Base URL**: `http://localhost:3001/api`
- **认证方式**: JWT Bearer Token
- **数据格式**: JSON

## 认证

所有需要认证的接口都需要在请求头中携带 JWT token:

```
Authorization: Bearer <token>
```

## API 端点

### 1. 认证接口 (`/api/auth`)

#### 1.1 用户注册

- **URL**: `POST /api/auth/register`
- **认证**: 不需要
- **请求体**:
  ```json
  {
    "username": "string (必填, 3-20字符)",
    "password": "string (必填, 最少6字符)"
  }
  ```
- **响应**: `201 Created`
  ```json
  {
    "success": true,
    "data": {
      "token": "string",
      "user": {
        "id": "string",
        "username": "string",
        "createdAt": "string"
      }
    }
  }
  ```

#### 1.2 用户登录

- **URL**: `POST /api/auth/login`
- **认证**: 不需要
- **请求体**:
  ```json
  {
    "username": "string (必填)",
    "password": "string (必填)"
  }
  ```
- **响应**: `200 OK`
  ```json
  {
    "success": true,
    "data": {
      "token": "string",
      "user": {
        "id": "string",
        "username": "string"
      }
    }
  }
  ```

#### 1.3 获取当前用户信息

- **URL**: `GET /api/auth/me`
- **认证**: 需要
- **响应**: `200 OK`
  ```json
  {
    "success": true,
    "data": {
      "id": "string",
      "username": "string",
      "createdAt": "string"
    }
  }
  ```

#### 1.4 刷新 Token

- **URL**: `POST /api/auth/refresh`
- **认证**: 需要
- **响应**: `200 OK`
  ```json
  {
    "success": true,
    "data": {
      "token": "string"
    },
    "message": "Token 刷新成功"
  }
  ```

#### 1.5 修改密码

- **URL**: `POST /api/auth/change-password`
- **认证**: 需要
- **请求体**:
  ```json
  {
    "oldPassword": "string (必填)",
    "newPassword": "string (必填, 最少6字符)"
  }
  ```
- **响应**: `200 OK`
  ```json
  {
    "message": "密码修改成功"
  }
  ```

#### 1.6 登出

- **URL**: `POST /api/auth/logout`
- **认证**: 需要
- **响应**: `200 OK`
  ```json
  {
    "message": "登出成功"
  }
  ```

### 2. 交易记录接口 (`/api/transactions`)

**注意**: 所有交易接口都需要认证

#### 2.1 获取所有交易

- **URL**: `GET /api/transactions`
- **认证**: 需要
- **响应**: `200 OK`
  ```json
  [
    {
      "transactionId": "string",
      "platform": "string",
      "transactionTime": "string",
      "amount": "number",
      "description": "string",
      "category": "string",
      ...
    }
  ]
  ```

#### 2.2 批量创建/更新交易

- **URL**: `POST /api/transactions/batch-upsert`
- **认证**: 需要
- **请求体**:
  ```json
  {
    "transactions": [
      {
        "transactionId": "string (必填)",
        "platform": "string (必填)",
        "transactionTime": "string (必填, ISO 8601)",
        "amount": "number (必填)",
        "description": "string (必填)",
        "category": "string (可选)",
        "counterparty": "string (可选)",
        ...
      }
    ]
  }
  ```
- **响应**: `200 OK`
  ```json
  {
    "success": true,
    "count": "number"
  }
  ```

#### 2.3 按月查询交易

- **URL**: `GET /api/transactions/month/:year/:month`
- **认证**: 需要
- **参数**:
  - `year`: 年份 (数字)
  - `month`: 月份 (1-12)
- **响应**: `200 OK`
  ```json
  {
    "year": "number",
    "month": "number",
    "count": "number",
    "transactions": [...]
  }
  ```

#### 2.4 按平台查询交易

- **URL**: `GET /api/transactions/platform/:platform`
- **认证**: 需要
- **参数**:
  - `platform`: 平台名称 (`alipay`, `wechat`, `bank`)
- **响应**: `200 OK`
  ```json
  {
    "platform": "string",
    "count": "number",
    "transactions": [...]
  }
  ```

#### 2.5 清空所有交易

- **URL**: `DELETE /api/transactions`
- **认证**: 需要
- **响应**: `200 OK`
  ```json
  {
    "success": true,
    "message": "所有交易已清空"
  }
  ```

### 3. 分类接口 (`/api/categories`)

**注意**: 所有分类接口都需要认证

#### 3.1 获取所有分类

- **URL**: `GET /api/categories`
- **认证**: 需要
- **响应**: `200 OK`
  ```json
  [
    {
      "id": "string",
      "name": "string",
      "description": "string",
      "color": "string",
      "icon": "string",
      "parentId": "string"
    }
  ]
  ```

#### 3.2 全量替换分类

- **URL**: `PUT /api/categories`
- **认证**: 需要
- **请求体**:
  ```json
  {
    "categories": [
      {
        "id": "string",
        "name": "string",
        "description": "string",
        ...
      }
    ]
  }
  ```
- **响应**: `200 OK`
  ```json
  {
    "success": true,
    "count": "number"
  }
  ```

#### 3.3 获取交易分类映射

- **URL**: `GET /api/categories/transaction-categories`
- **认证**: 需要
- **响应**: `200 OK`
  ```json
  {
    "transactionId1": {
      "category": "string",
      "subcategory": "string",
      "confidence": "number",
      "reasoning": "string",
      "isManual": "boolean",
      "updatedAt": "string"
    },
    ...
  }
  ```

#### 3.4 更新单个交易分类

- **URL**: `PUT /api/categories/transaction-categories/:transactionId`
- **认证**: 需要
- **请求体**:
  ```json
  {
    "category": "string",
    "subcategory": "string",
    "confidence": "number",
    "reasoning": "string",
    "isManual": "boolean"
  }
  ```
- **响应**: `200 OK`
  ```json
  {
    "id": "string",
    "transactionId": "string",
    "category": "string",
    ...
  }
  ```

#### 3.5 批量更新交易分类

- **URL**: `POST /api/categories/transaction-categories/batch-upsert`
- **认证**: 需要
- **请求体**:
  ```json
  {
    "updates": [
      {
        "transactionId": "string",
        "categoryData": {...}
      }
    ]
  }
  ```
- **响应**: `200 OK`
  ```json
  {
    "success": true,
    "count": "number"
  }
  ```

#### 3.6 获取纠正历史

- **URL**: `GET /api/categories/corrections`
- **认证**: 需要
- **响应**: `200 OK`
  ```json
  [
    {
      "id": "string",
      "transactionId": "string",
      "originalCategory": "string",
      "correctedCategory": "string",
      "timestamp": "string"
    }
  ]
  ```

#### 3.7 添加纠正记录

- **URL**: `POST /api/categories/corrections`
- **认证**: 需要
- **请求体**:
  ```json
  {
    "transactionId": "string (必填)",
    "originalCategory": "string (必填)",
    "correctedCategory": "string (必填)"
  }
  ```
- **响应**: `200 OK`
  ```json
  {
    "id": "string",
    "transactionId": "string",
    ...
  }
  ```

### 4. 统计接口 (`/api/statistics`)

**注意**: 所有统计接口都需要认证

#### 4.1 获取总体统计

- **URL**: `GET /api/statistics/overview`
- **认证**: 需要
- **响应**: `200 OK`
  ```json
  {
    "overview": {
      "totalIncome": "number",
      "totalExpense": "number",
      "netIncome": "number",
      "totalCount": "number"
    },
    "byPlatform": [...],
    "byCategory": [...]
  }
  ```

#### 4.2 获取月度统计

- **URL**: `GET /api/statistics/monthly?year=2024`
- **认证**: 需要
- **参数**:
  - `year`: 年份 (可选,默认当前年份)
- **响应**: `200 OK`
  ```json
  {
    "year": "number",
    "months": [
      {
        "month": "number",
        "income": "number",
        "expense": "number",
        "net": "number",
        "count": "number",
        "categoryBreakdown": {...}
      }
    ]
  }
  ```

#### 4.3 获取分类统计

- **URL**: `GET /api/statistics/category?type=expense&startDate=2024-01-01&endDate=2024-12-31`
- **认证**: 需要
- **参数**:
  - `type`: 类型 (可选, `income` 或 `expense`)
  - `startDate`: 开始日期 (可选)
  - `endDate`: 结束日期 (可选)
- **响应**: `200 OK`
  ```json
  {
    "byCategory": [...],
    "byCategoryAndMonth": [...]
  }
  ```

#### 4.4 获取收支趋势

- **URL**: `GET /api/statistics/trend?months=12`
- **认证**: 需要
- **参数**:
  - `months`: 月数 (可选,默认 12,最大 60)
- **响应**: `200 OK`
  ```json
  {
    "period": {
      "startDate": "string",
      "endDate": "string",
      "months": "number"
    },
    "data": [
      {
        "date": "string",
        "income": "number",
        "expense": "number",
        "net": "number"
      }
    ]
  }
  ```

#### 4.5 获取平台统计

- **URL**: `GET /api/statistics/platform`
- **认证**: 需要
- **响应**: `200 OK`
  ```json
  {
    "platforms": [
      {
        "platform": "string",
        "count": "number",
        "totalAmount": "number"
      }
    ]
  }
  ```

### 5. 配置接口 (`/api/config`)

**注意**: 所有配置接口都需要认证

#### 5.1 获取配置

- **URL**: `GET /api/config/:key`
- **认证**: 需要
- **参数**:
  - `key`: 配置键名
- **响应**: `200 OK`
  ```json
  {
    "key": "string",
    "value": "string"
  }
  ```

#### 5.2 设置配置

- **URL**: `POST /api/config/:key`
- **认证**: 需要
- **请求体**:
  ```json
  {
    "value": "string"
  }
  ```
- **响应**: `200 OK`
  ```json
  {
    "success": true,
    "message": "配置已保存"
  }
  ```

#### 5.3 删除配置

- **URL**: `DELETE /api/config/:key`
- **认证**: 需要
- **响应**: `200 OK`
  ```json
  {
    "success": true,
    "message": "配置已删除"
  }
  ```

### 6. 备份接口 (`/api/backup`)

**注意**: 所有备份接口都需要认证

#### 6.1 创建备份

- **URL**: `POST /api/backup`
- **认证**: 需要
- **响应**: `200 OK`
  ```json
  {
    "success": true,
    "backupId": "string",
    "timestamp": "number",
    "size": "number"
  }
  ```

#### 6.2 获取备份列表

- **URL**: `GET /api/backup`
- **认证**: 需要
- **响应**: `200 OK`
  ```json
  {
    "backups": [
      {
        "id": "string",
        "timestamp": "number",
        "size": "number",
        "createdAt": "string"
      }
    ]
  }
  ```

#### 6.3 恢复备份

- **URL**: `POST /api/backup/:backupId/restore`
- **认证**: 需要
- **响应**: `200 OK`
  ```json
  {
    "success": true,
    "message": "备份恢复成功"
  }
  ```

#### 6.4 删除备份

- **URL**: `DELETE /api/backup/:backupId`
- **认证**: 需要
- **响应**: `200 OK`
  ```json
  {
    "success": true,
    "message": "备份已删除"
  }
  ```

### 7. 迁移接口 (`/api/migration`)

**注意**: 所有迁移接口都需要认证

#### 7.1 获取迁移状态

- **URL**: `GET /api/migration/status`
- **认证**: 需要
- **响应**: `200 OK`
  ```json
  {
    "status": "string",
    "progress": "number",
    "message": "string"
  }
  ```

#### 7.2 开始迁移

- **URL**: `POST /api/migration/start`
- **认证**: 需要
- **响应**: `200 OK`
  ```json
  {
    "success": true,
    "message": "迁移已开始"
  }
  ```

#### 7.3 回滚迁移

- **URL**: `POST /api/migration/rollback`
- **认证**: 需要
- **响应**: `200 OK`
  ```json
  {
    "success": true,
    "message": "迁移已回滚"
  }
  ```

## 错误响应格式

所有错误响应遵循统一格式:

```json
{
  "success": false,
  "error": "string",
  "message": "string",
  "details": "object (可选)",
  "timestamp": "string"
}
```

### 常见错误码

- `400 Bad Request`: 请求参数错误
- `401 Unauthorized`: 未认证或认证失败
- `404 Not Found`: 资源不存在
- `409 Conflict`: 资源冲突(如用户名已存在)
- `500 Internal Server Error`: 服务器内部错误

## 健康检查

- **URL**: `GET /api/health`
- **认证**: 不需要
- **响应**: `200 OK`
  ```json
  {
    "status": "ok",
    "timestamp": "string",
    "database": "connected"
  }
  ```

## 测试

运行所有测试:
```bash
npm test
```

运行特定测试:
```bash
npm run test:auth
npm run test:transactions
npm run test:statistics
```

## 默认用户

系统初始化后会创建默认管理员用户:
- 用户名: `admin`
- 密码: `admin123`

**重要**: 生产环境请立即修改默认密码!
