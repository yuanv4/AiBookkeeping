import { AIAdapter } from './aiAdapter.js'
import { generateCategoriesPrompt, classifyPrompt, batchClassifyPrompt } from './prompts.js'

/**
 * Ollama AI 服务适配器
 * 用于本地 Ollama 服务
 */
export class OllamaAdapter extends AIAdapter {
  /**
   * 初始化 Ollama 服务
   */
  async init() {
    try {
      // 验证 Ollama 服务是否运行
      const response = await fetch(`${this.config.baseURL}/tags`)
      if (!response.ok) {
        throw new Error('无法连接到 Ollama 服务，请确认服务已启动')
      }
      console.log('✅ Ollama 服务连接成功')
    } catch (error) {
      throw new Error(`Ollama 初始化失败：${error.message}`)
    }
  }

  /**
   * 生成分类体系
   */
  async generateCategorySystem(transactions) {
    const prompt = generateCategoriesPrompt(transactions)

    const response = await this._chat(prompt)
    const result = this.parseJSONResponse(response)

    return result.categories || []
  }

  /**
   * 分类单笔交易
   */
  async classifyTransaction(transaction, existingCategories) {
    const prompt = classifyPrompt(transaction, existingCategories)

    const response = await this._chat(prompt)
    return this.parseJSONResponse(response)
  }

  /**
   * 批量分类交易
   */
  async classifyBatch(transactions, existingCategories) {
    const batchSize = 50
    const results = []

    for (let i = 0; i < transactions.length; i += batchSize) {
      const batch = transactions.slice(i, i + batchSize)
      const prompt = batchClassifyPrompt(batch, existingCategories)

      const response = await this._chat(prompt)
      const batchResults = this.parseJSONResponse(response)

      results.push(...(batchResults.results || batchResults))
    }

    return results
  }

  /**
   * 测试连接
   */
  async testConnection() {
    try {
      const response = await fetch(`${this.config.baseURL}/api/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          model: this.config.model,
          prompt: 'Hi',
          stream: false
        })
      })
      return response.ok
    } catch {
      return false
    }
  }

  /**
   * 调用 Ollama 聊天 API
   * @private
   */
  async _chat(prompt) {
    const response = await fetch(`${this.config.baseURL}/api/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        model: this.config.model,
        messages: [{ role: 'user', content: prompt }],
        stream: false
      })
    })

    if (!response.ok) {
      throw new Error(`Ollama API 调用失败：${response.statusText}`)
    }

    const data = await response.json()
    return data.message?.content || ''
  }
}
