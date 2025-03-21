# 个人收支管理系统API接口文档

## 1. API概述

本文档描述了个人收支管理系统的RESTful API接口规范。所有API遵循RESTful设计原则，使用HTTP协议进行通信，数据格式采用JSON。

## 2. 接口规范

### 2.1 请求规范

- 基础URL: `/api/v1`
- 请求方法: GET, POST, PUT, DELETE
- 请求头:
  ```
  Content-Type: application/json
  ```

### 2.2 响应规范

- 状态码:
  - 200: 成功
  - 201: 创建成功
  - 400: 请求参数错误
  - 404: 资源不存在
  - 500: 服务器错误

- 响应格式:
  ```json
  {
    "code": 200,
    "message": "success",
    "data": {}
  }
  ```

## 3. 账户接口

### 3.1 获取账户列表

- 请求路径: `/accounts`
- 请求方法: GET
- 响应示例:
  ```json
  {
    "code": 200,
    "message": "success",
    "data": {
      "accounts": [
        {
          "id": "uuid-v4",
          "name": "现金账户",
          "type": "cash",
          "balance": 1000.00,
          "currency": "CNY"
        }
      ]
    }
  }
  ```

### 3.2 创建账户

- 请求路径: `/accounts`
- 请求方法: POST
- 请求参数:
  ```json
  {
    "name": "string",
    "type": "string",
    "balance": "number",
    "currency": "string"
  }
  ```
- 响应示例:
  ```json
  {
    "code": 201,
    "message": "创建成功",
    "data": {
      "id": "uuid-v4",
      "name": "现金账户",
      "type": "cash",
      "balance": 1000.00,
      "currency": "CNY"
    }
  }
  ```

## 4. 交易接口

### 4.1 获取交易列表

- 请求路径: `/transactions`
- 请求方法: GET
- 查询参数:
  - start_date: 开始日期
  - end_date: 结束日期
  - type: 交易类型
  - category_id: 分类ID
  - account_id: 账户ID
  - page: 页码
  - limit: 每页数量
- 响应示例:
  ```json
  {
    "code": 200,
    "message": "success",
    "data": {
      "total": 100,
      "transactions": [
        {
          "id": "uuid-v4",
          "account_id": "uuid-v4",
          "category_id": "uuid-v4",
          "amount": 100.00,
          "type": "expense",
          "description": "午餐",
          "date": "2024-01-01",
          "tags": ["食品"]
        }
      ]
    }
  }
  ```

### 4.2 创建交易

- 请求路径: `/transactions`
- 请求方法: POST
- 请求参数:
  ```json
  {
    "account_id": "string",
    "category_id": "string",
    "amount": "number",
    "type": "string",
    "description": "string",
    "date": "string",
    "tags": ["string"]
  }
  ```
- 响应示例:
  ```json
  {
    "code": 201,
    "message": "创建成功",
    "data": {
      "id": "uuid-v4",
      "account_id": "uuid-v4",
      "category_id": "uuid-v4",
      "amount": 100.00,
      "type": "expense",
      "description": "午餐",
      "date": "2024-01-01",
      "tags": ["食品"]
    }
  }
  ```