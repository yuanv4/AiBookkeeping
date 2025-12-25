/**
 * AI 配置文件
 * 职责: 配置默认值 + 校验,不涉及存储操作
 * ⚠️ 存储由 categoryStore 统一管理
 */

// AI 提供商配置(供 UI 选择使用)
export const AI_PROVIDERS = {
  ollama: {
    name: 'Ollama (本地)',
    baseUrl: 'http://localhost:11434/v1',
    models: ['qwen2.5:7b', 'llama3', 'mistral'],
    defaultModel: 'qwen2.5:7b',
    requiresApiKey: false
  },
  openai: {
    name: 'OpenAI 兼容',
    baseUrl: 'https://api.openai.com/v1',
    models: ['gpt-3.5-turbo', 'gpt-4'],
    defaultModel: 'gpt-3.5-turbo',
    requiresApiKey: true
  },
  qianwen: {
    name: '通义千问 (阿里云)',
    baseUrl: 'https://dashscope.aliyuncs.com/compatible-mode/v1',
    models: ['qwen-turbo', 'qwen-plus', 'qwen-max'],
    defaultModel: 'qwen-turbo',
    requiresApiKey: true
  }
}

// 默认配置(用于初始化 categoryStore)
export const DEFAULT_AI_CONFIG = {
  provider: 'ollama',
  apiKey: '',
  baseURL: 'http://localhost:11434/v1',
  model: 'qwen2.5:7b',
  timeout: 30000,
  enabled: false,           // 新增: 是否启用 AI 分类
  fallbackToRules: true     // 新增: AI 失败时回退到规则分类
}

/**
 * 验证 AI 配置是否有效
 */
export function validateAIConfig(config) {
  if (!config.enabled) {
    return { valid: true, message: 'AI 未启用' }
  }

  if (!config.provider) {
    return { valid: false, message: '请选择 AI 提供商' }
  }

  const provider = AI_PROVIDERS[config.provider]
  if (!provider) {
    return { valid: false, message: '无效的 AI 提供商' }
  }

  if (provider.requiresApiKey && !config.apiKey) {
    return { valid: false, message: '请输入 API Key' }
  }

  return { valid: true, message: '配置有效' }
}

/**
 * 获取完整的提供商配置
 */
export function getProviderConfig(provider) {
  const config = AI_PROVIDERS[provider]
  if (!config) {
    throw new Error(`未知的 AI 提供商: ${provider}`)
  }
  return config
}

// ❌ 删除 loadAIConfig() 和 saveAIConfig()
// ✅ 存储操作由 categoryStore 统一管理
