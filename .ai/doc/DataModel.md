# 个人收支管理系统数据模型设计

## 1. 数据模型概述

本文档描述了个人收支管理系统的核心数据实体、实体间关系以及各实体的属性定义。系统采用文件系统存储数据，使用JSON格式组织数据结构。

## 2. 文件组织结构

```
data/
  ├── accounts.json     # 账户信息
  ├── categories.json   # 交易分类
  ├── transactions.json # 交易记录
  ├── budgets.json     # 预算配置
  └── tags.json        # 标签数据
```

## 3. 数据结构定义

### 3.1 账户（accounts.json）

```json
{
  "accounts": [
    {
      "id": "string",
      "name": "string",
      "type": "string",
      "balance": "number",
      "currency": "string",
      "created_at": "string",
      "updated_at": "string"
    }
  ]
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| id | string | 账户ID，UUID格式 |
| name | string | 账户名称 |
| type | string | 账户类型 |
| balance | number | 账户余额 |
| currency | string | 货币类型 |
| created_at | string | 创建时间 |
| updated_at | string | 更新时间 |

### 3.2 交易记录（transactions.json）

```json
{
  "transactions": [
    {
      "id": "string",
      "account_id": "string",
      "category_id": "string",
      "amount": "number",
      "type": "string",
      "description": "string",
      "date": "string",
      "tags": ["string"],
      "created_at": "string",
      "updated_at": "string"
    }
  ]
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| id | string | 交易ID，UUID格式 |
| account_id | string | 账户ID |
| category_id | string | 分类ID |
| amount | number | 交易金额 |
| type | string | 交易类型（收入/支出/转账）|
| description | string | 交易描述 |
| date | string | 交易日期 |
| tags | array | 标签列表 |
| created_at | string | 创建时间 |
| updated_at | string | 更新时间 |

### 3.3 交易分类（categories.json）

```json
{
  "categories": [
    {
      "id": "string",
      "name": "string",
      "type": "string",
      "parent_id": "string",
      "created_at": "string",
      "updated_at": "string"
    }
  ]
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| id | string | 分类ID，UUID格式 |
| name | string | 分类名称 |
| type | string | 分类类型（收入/支出）|
| parent_id | string | 父分类ID |
| created_at | string | 创建时间 |
| updated_at | string | 更新时间 |



### 3.5 标签（tags.json）

```json
{
  "tags": [
    {
      "id": "string",
      "name": "string",
      "created_at": "string",
      "updated_at": "string"
    }
  ]
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| id | string | 标签ID，UUID格式 |
| name | string | 标签名称 |
| created_at | string | 创建时间 |
| updated_at | string | 更新时间 |

## 4. 数据关系

```
[Accounts] 1 --- * [Transactions]
[Categories] 1 --- * [Transactions]
[Categories] 1 --- * [Budgets]
[Tags] * --- * [Transactions]
```

## 5. 数据完整性

### 5.1 引用完整性
- 删除账户前，检查是否存在关联的交易记录
- 删除分类前，检查是否存在关联的交易记录和预算
- 删除标签前，更新相关交易记录的标签列表

### 5.2 数据一致性
- 定期备份JSON文件
- 文件写入操作采用原子性操作
- 维护文件版本历史

### 5.3 数据验证
- 字段类型检查
- 必填字段验证
- 数据格式验证
- 引用关系验证