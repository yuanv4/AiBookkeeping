/**
 * AI 分类提示词系统
 */

/**
 * 生成分类体系 Prompt
 * @param {Array} transactions - 交易样本
 * @returns {string} 提示词
 */
export function generateCategoriesPrompt(transactions) {
  // 取前 100 笔交易作为样本
  const samples = transactions.slice(0, 100).map(t =>
    `- ${t.counterparty || '未知商户'} / ${t.description || '无描述'} / ¥${Math.abs(t.amount)}`
  ).join('\n')

  return `你是专业的账单分析助手。请分析以下交易数据，创建合理的消费分类体系。

要求：
1. 分类层级：一级分类 8-12 个，根据需要设置二级分类
2. 分类名称：简洁易懂（4 字以内）
3. 覆盖全面：确保所有交易都能找到对应分类
4. 避免重复：分类之间边界清晰
5. 图标适配：为每个分类选择合适的 emoji 图标

交易样本：
${samples}

请以 JSON 格式返回分类体系：
{
  "categories": [
    {
      "id": "cat_001",
      "name": "餐饮美食",
      "icon": "🍔",
      "description": "各类餐饮消费",
      "subcategories": ["早餐", "午餐", "晚餐", "外卖", "零食"]
    }
  ]
}`
}

/**
 * 交易分类 Prompt
 * @param {Object} transaction - 交易对象
 * @param {Array} existingCategories - 已有分类列表
 * @returns {string} 提示词
 */
export function classifyPrompt(transaction, existingCategories) {
  const categoryList = existingCategories.map(cat =>
    `- ${cat.icon} ${cat.name}: ${cat.description || ''}`
  ).join('\n')

  return `你是专业的账单分类助手。根据以下信息对交易进行分类。

已有分类体系：
${categoryList}

待分类交易：
- 交易对方：${transaction.counterparty || '未知'}
- 商品描述：${transaction.description || '无'}
- 金额：¥${Math.abs(transaction.amount)}
- 支付方式：${transaction.paymentMethod || '未知'}

规则：
1. 必须从已有分类中选择最合适的一个
2. 考虑商户名称和商品描述的语义
3. 返回置信度（0-1 之间的数值）

请以 JSON 格式返回：
{
  "category": "餐饮美食",
  "subcategory": "外卖",
  "confidence": 0.95,
  "reasoning": "美团外卖属于餐饮外卖"
}`
}

/**
 * 批量分类 Prompt
 * @param {Array} transactions - 交易列表
 * @param {Array} existingCategories - 已有分类列表
 * @returns {string} 提示词
 */
export function batchClassifyPrompt(transactions, existingCategories) {
  const categoryList = existingCategories.map(cat =>
    `- ${cat.icon} ${cat.name}: ${cat.description || ''}`
  ).join('\n')

  const txList = transactions.map((t, i) =>
    `${i + 1}. ID:${i} | ${t.counterparty || '未知'} / ${t.description || '无'} / ¥${Math.abs(t.amount)}`
  ).join('\n')

  return `你是专业的账单分类助手。批量分类以下交易，一次处理最多 50 笔。

已有分类体系：
${categoryList}

待分类交易：
${txList}

请以 JSON 格式返回分类结果：
{
  "results": [
    { "id": 0, "category": "餐饮美食", "confidence": 0.95 },
    { "id": 1, "category": "交通出行", "confidence": 0.88 }
  ]
}`
}
