/**
 * AI 配置文件
 * 支持多种 AI 平台：通义千问、文心一言、ChatGPT 等
 */

// AI 提供商配置
export const AI_PROVIDERS = {
  qianwen: {
    name: '通义千问（阿里云）',
    baseUrl: 'https://dashscope.aliyuncs.com/compatible-mode/v1',
    models: ['qwen-turbo', 'qwen-plus', 'qwen-max'],
    defaultModel: 'qwen-turbo',
    price: 0.008, // 元/千次调用（估算）
    recommended: true
  },
  wenxin: {
    name: '文心一言（百度）',
    baseUrl: 'https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat',
    models: ['eb-instant', 'completions_pro', 'ernie-4.0'],
    defaultModel: 'eb-instant',
    price: 0.012,
    recommended: false
  },
  chatgpt: {
    name: 'ChatGPT（OpenAI）',
    baseUrl: 'https://api.openai.com/v1',
    models: ['gpt-3.5-turbo', 'gpt-4'],
    defaultModel: 'gpt-3.5-turbo',
    price: 0.02,
    recommended: false
  }
}

// 默认配置
export const DEFAULT_AI_CONFIG = {
  provider: 'qianwen',
  apiKey: '',
  model: '',
  enabled: false,
  fallbackToRules: true,
  timeout: 10000 // 10秒超时
}

/**
 * 从 localStorage 加载 AI 配置
 */
export function loadAIConfig() {
  try {
    const saved = localStorage.getItem('ai_config')
    if (saved) {
      return { ...DEFAULT_AI_CONFIG, ...JSON.parse(saved) }
    }
  } catch (error) {
    console.error('加载 AI 配置失败:', error)
  }
  return { ...DEFAULT_AI_CONFIG }
}

/**
 * 保存 AI 配置到 localStorage
 */
export function saveAIConfig(config) {
  try {
    localStorage.setItem('ai_config', JSON.stringify(config))
    return true
  } catch (error) {
    console.error('保存 AI 配置失败:', error)
    return false
  }
}

/**
 * 验证 AI 配置是否有效
 */
export function validateAIConfig(config) {
  if (!config.enabled) return { valid: true, message: 'AI 未启用' }

  if (!config.provider) {
    return { valid: false, message: '请选择 AI 提供商' }
  }

  if (!config.apiKey) {
    return { valid: false, message: '请输入 API Key' }
  }

  const provider = AI_PROVIDERS[config.provider]
  if (!provider) {
    return { valid: false, message: '无效的 AI 提供商' }
  }

  return { valid: true, message: '配置有效' }
}

/**
 * 获取完整的 API 配置
 */
export function getProviderConfig(provider) {
  const config = AI_PROVIDERS[provider]
  if (!config) {
    throw new Error(`未知的 AI 提供商: ${provider}`)
  }
  return config
}
