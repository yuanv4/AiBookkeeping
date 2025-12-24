/**
 * AI 服务适配器基类
 * 定义所有 AI 适配器必须实现的接口
 */
export class AIAdapter {
  constructor(config) {
    this.config = config
  }

  /**
   * 初始化 AI 服务
   */
  async init() {
    throw new Error('init() must be implemented by subclass')
  }

  /**
   * 分类单笔交易
   * @param {Object} transaction - 交易对象
   * @param {Array} existingCategories - 已有分类列表
   * @returns {Promise<Object>} 分类结果
   */
  async classifyTransaction(transaction, existingCategories) {
    throw new Error('classifyTransaction() must be implemented by subclass')
  }

  /**
   * 批量分类交易（默认实现：逐个调用）
   * @param {Array} transactions - 交易列表
   * @param {Array} existingCategories - 已有分类列表
   * @returns {Promise<Array>} 分类结果列表
   */
  async classifyBatch(transactions, existingCategories) {
    const results = []
    for (const tx of transactions) {
      const result = await this.classifyTransaction(tx, existingCategories)
      results.push(result)
    }
    return results
  }

  /**
   * 根据交易数据生成初始分类体系
   * @param {Array} transactions - 交易样本
   * @returns {Promise<Array>} 分类列表
   */
  async generateCategorySystem(transactions) {
    throw new Error('generateCategorySystem() must be implemented by subclass')
  }

  /**
   * 测试 AI 服务连接
   * @returns {Promise<boolean>} 连接是否成功
   */
  async testConnection() {
    throw new Error('testConnection() must be implemented by subclass')
  }

  /**
   * 解析 AI 返回的 JSON
   * 提取内容中的 JSON 部分
   * @param {string} content - AI 返回的文本内容
   * @returns {Object} 解析后的 JSON 对象
   */
  parseJSONResponse(content) {
    // 尝试匹配完整的 JSON 对象
    const jsonMatch = content.match(/\{[\s\S]*\}/)
    if (!jsonMatch) {
      throw new Error('AI 返回格式错误：未找到 JSON 对象')
    }

    try {
      return JSON.parse(jsonMatch[0])
    } catch (error) {
      throw new Error(`AI 返回 JSON 解析失败：${error.message}`)
    }
  }

  /**
   * 生成交易唯一标识
   * @param {Object} transaction - 交易对象
   * @returns {string} 唯一标识
   */
  generateTransactionId(transaction) {
    const { transactionTime, counterparty, amount, description } = transaction
    return `${transactionTime}_${counterparty}_${amount}_${description || ''}`
      .replace(/\s+/g, '_')
      .substring(0, 100)
  }
}
