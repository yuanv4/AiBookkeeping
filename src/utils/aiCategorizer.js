/**
 * AI 智能分类器
 * 使用 AI API 进行交易分类
 */

import { CATEGORIES } from './categoryRules.js'
import { getProviderConfig } from '../config/aiConfig.js'

/**
 * 使用 AI 分类交易
 * @param {Object} transaction - 交易对象
 * @param {Object} aiConfig - AI 配置
 * @returns {Promise<string>} - 分类名称
 */
export async function categorizeByAI(transaction, aiConfig) {
  // ⚠️ 不再调用 loadAIConfig(),aiConfig 必须由调用方传入
  if (!aiConfig) {
    throw new Error('AI 配置未提供，请从 categoryStore 获取')
  }

  const config = aiConfig

  if (!config.enabled || !config.apiKey) {
    throw new Error('AI 未启用或缺少 API Key')
  }

  const providerConfig = getProviderConfig(config.provider)
  const model = config.model || providerConfig.defaultModel

  // 构建 Prompt
  const prompt = buildClassificationPrompt(transaction)

  try {
    // 调用 AI API
    const response = await callAIAPI(providerConfig, model, prompt, config.apiKey)

    // 解析响应
    const category = parseAIResponse(response)

    return category
  } catch (error) {
    console.error('AI API 调用失败:', error)
    throw error
  }
}

/**
 * 构建分类 Prompt
 */
function buildClassificationPrompt(transaction) {
  const categoryList = CATEGORIES.join('、')

  return `你是一个专业的账单分类助手。请将以下交易归类到这些类别之一：
${categoryList}

交易信息：
- 交易对方：${transaction.counterparty || '未知'}
- 商品描述：${transaction.description || '未知'}
- 金额：${Math.abs(transaction.amount)} 元
- 收支类型：${transaction.transactionType === 'income' ? '收入' : '支出'}
- 支付方式：${transaction.paymentMethod || '未知'}

规则：
1. 只返回类别名称，不要其他解释
2. 如果无法确定，返回"其他"
3. 不要添加任何标点符号或额外文字

分类：`.trim()
}

/**
 * 调用 AI API（支持多种提供商）
 */
async function callAIAPI(providerConfig, model, prompt, apiKey) {
  const { provider, baseUrl } = providerConfig

  // 通义千问和 ChatGPT 使用兼容的 OpenAI 格式
  if (provider === 'qianwen' || provider === 'chatgpt') {
    return await callOpenAICompatibleAPI(baseUrl, model, prompt, apiKey)
  }

  // 文心一言使用特殊格式
  if (provider === 'wenxin') {
    return await callWenxinAPI(prompt, apiKey)
  }

  throw new Error(`不支持的 AI 提供商: ${provider}`)
}

/**
 * 调用 OpenAI 兼容的 API（通义千问、ChatGPT）
 */
async function callOpenAICompatibleAPI(baseUrl, model, prompt, apiKey) {
  const response = await fetch(`${baseUrl}/chat/completions`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${apiKey}`
    },
    body: JSON.stringify({
      model: model,
      messages: [
        {
          role: 'user',
          content: prompt
        }
      ],
      temperature: 0.1, // 降低随机性，提高准确性
      max_tokens: 50
    })
  })

  if (!response.ok) {
    const error = await response.json()
    throw new Error(`API 调用失败: ${error.error?.message || response.statusText}`)
  }

  const data = await response.json()
  return data.choices[0].message.content.trim()
}

/**
 * 调用文心一言 API
 */
async function callWenxinAPI(prompt, apiKey) {
  // 文心一言的 API Key 格式为: {apikey}.{secret_key}
  const [apiKeyId, secretKey] = apiKey.split('.')

  if (!secretKey) {
    throw new Error('文心一言 API Key 格式错误，应为: {apikey}.{secret_key}')
  }

  // 获取 access_token
  const tokenResponse = await fetch(
    `https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id=${apiKeyId}&client_secret=${secretKey}`
  )
  const tokenData = await tokenResponse.json()

  if (!tokenData.access_token) {
    throw new Error('获取文心一言 access_token 失败')
  }

  // 调用聊天接口
  const response = await fetch(
    `https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/eb-instant?access_token=${tokenData.access_token}`,
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        messages: [
          {
            role: 'user',
            content: prompt
          }
        ]
      })
    }
  )

  if (!response.ok) {
    throw new Error(`文心一言 API 调用失败: ${response.statusText}`)
  }

  const data = await response.json()
  return data.result?.trim() || ''
}

/**
 * 解析 AI 响应
 */
function parseAIResponse(response) {
  // 移除可能的标点符号
  let category = response.replace(/[。，、；：""''！？\n\r]/g, '').trim()

  // 验证分类是否有效
  if (!CATEGORIES.includes(category)) {
    console.warn(`AI 返回无效分类: ${category}，使用"其他"`)
    return '其他'
  }

  return category
}

/**
 * 测试 AI 配置是否有效
 */
export async function testAIConfig(config) {
  try {
    const result = await categorizeByAI({
      counterparty: '测试商户',
      description: '测试交易',
      amount: 100,
      transactionType: 'expense',
      paymentMethod: '测试'
    }, config)

    return {
      success: true,
      message: `连接成功！测试分类结果: ${result}`
    }
  } catch (error) {
    return {
      success: false,
      message: `连接失败: ${error.message}`
    }
  }
}
