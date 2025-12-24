import { AIAdapter } from './aiAdapter.js'
import { generateCategoriesPrompt, classifyPrompt, batchClassifyPrompt } from './prompts.js'

/**
 * OpenAI 兼容 AI 服务适配器
 * 支持 OpenAI、通义千问、文心一言、DeepSeek 等
 */
export class OpenAIAdapter extends AIAdapter {
  /**
   * 初始化 OpenAI 兼容服务
   */
  async init() {
    try {
      // 验证 API Key
      const response = await fetch(`${this.config.baseURL}/models`, {
        headers: {
          'Authorization': `Bearer ${this.config.apiKey}`
        }
      })

      if (!response.ok) {
        throw new Error('API Key 验证失败，请检查配置')
      }
      console.log('✅ OpenAI 兼容服务连接成功')
    } catch (error) {
      throw new Error(`OpenAI 初始化失败：${error.message}`)
    }
  }

  /**
   * 生成分类体系
   */
  async generateCategorySystem(transactions) {
    const prompt = generateCategoriesPrompt(transactions)
    const content = await this._chat(prompt)
    const result = this.parseJSONResponse(content)

    return result.categories || []
  }

  /**
   * 分类单笔交易
   */
  async classifyTransaction(transaction, existingCategories) {
    const prompt = classifyPrompt(transaction, existingCategories)
    const content = await this._chat(prompt)

    return this.parseJSONResponse(content)
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
      const content = await this._chat(prompt)
      const batchResults = this.parseJSONResponse(content)

      results.push(...(batchResults.results || batchResults))
    }

    return results
  }

  /**
   * 测试连接
   */
  async testConnection() {
    try {
      const response = await fetch(`${this.config.baseURL}/models`, {
        headers: {
          'Authorization': `Bearer ${this.config.apiKey}`
        }
      })
      return response.ok
    } catch {
      return false
    }
  }

  /**
   * 调用 OpenAI 兼容聊天 API
   * @private
   */
  async _chat(prompt) {
    const response = await fetch(`${this.config.baseURL}/chat/completions`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${this.config.apiKey}`
      },
      body: JSON.stringify({
        model: this.config.model,
        messages: [{ role: 'user', content: prompt }],
        temperature: 0.3
      })
    })

    if (!response.ok) {
      const errorText = await response.text()
      throw new Error(`API 调用失败 (${response.status}): ${errorText}`)
    }

    const data = await response.json()
    return data.choices?.[0]?.message?.content || ''
  }
}
