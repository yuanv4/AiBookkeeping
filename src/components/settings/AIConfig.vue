<template>
  <div class="ai-config-panel">
    <div class="config-header">
      <h3>⚙️ AI 智能分类配置</h3>
      <p class="config-desc">配置 AI 后，规则引擎无法识别的交易将由 AI 自动分类</p>
    </div>

    <div class="config-form">
      <!-- AI 提供商选择 -->
      <div class="form-group">
        <label class="form-label">AI 提供商：</label>
        <select v-model="localConfig.provider" class="form-select" :disabled="!localConfig.enabled">
          <option v-for="(provider, key) in providers" :key="key" :value="key">
            {{ provider.name }} {{ provider.recommended ? '(推荐)' : '' }}
          </option>
        </select>
      </div>

      <!-- API Key 输入 -->
      <div class="form-group">
        <label class="form-label">API Key：</label>
        <div class="input-with-action">
          <input
            v-model="localConfig.apiKey"
            :type="showApiKey ? 'text' : 'password'"
            placeholder="请输入 API Key"
            class="form-input"
            :disabled="!localConfig.enabled"
          />
          <button
            @click="showApiKey = !showApiKey"
            class="icon-button"
            :disabled="!localConfig.enabled"
            :title="showApiKey ? '隐藏' : '显示'"
          >
            {{ showApiKey ? '👁️' : '🔒' }}
          </button>
        </div>
        <div class="form-hint">
          <a
            v-if="localConfig.provider === 'qianwen'"
            href="https://dashscope.aliyun.com/"
            target="_blank"
            class="hint-link"
          >
            🔗 获取通义千问 API Key
          </a>
          <a
            v-else-if="localConfig.provider === 'wenxin'"
            href="https://cloud.baidu.com/product/wenxinworkshop"
            target="_blank"
            class="hint-link"
          >
            🔗 获取文心一言 API Key
          </a>
        </div>
      </div>

      <!-- 模型选择（可选） -->
      <div class="form-group" v-if="localConfig.provider && providers[localConfig.provider]">
        <label class="form-label">模型：</label>
        <select v-model="localConfig.model" class="form-select" :disabled="!localConfig.enabled">
          <option value="">使用默认模型</option>
          <option v-for="model in providers[localConfig.provider].models" :key="model" :value="model">
            {{ model }}
          </option>
        </select>
      </div>

      <!-- 启用开关 -->
      <div class="form-group checkbox-group">
        <label class="checkbox-label">
          <input
            type="checkbox"
            v-model="localConfig.enabled"
            class="checkbox"
          />
          <span>启用 AI 智能分类</span>
        </label>
        <div class="form-hint">
          {{ localConfig.enabled ? '✅ AI 已启用' : 'ℹ️ 仅使用规则引擎分类' }}
        </div>
      </div>

      <!-- 回退开关 -->
      <div class="form-group checkbox-group" v-if="localConfig.enabled">
        <label class="checkbox-label">
          <input
            type="checkbox"
            v-model="localConfig.fallbackToRules"
            class="checkbox"
          />
          <span>AI 失败时回退到规则引擎</span>
        </label>
        <div class="form-hint">ℹ️ 推荐开启，确保即使 AI 不可用也能正常分类</div>
      </div>

      <!-- 价格提示 -->
      <div class="price-hint" v-if="localConfig.enabled && providers[localConfig.provider]">
        <span class="hint-icon">💰</span>
        <span>预估价格：约 ¥{{ providers[localConfig.provider].price }}/千次调用</span>
        <span class="hint-detail">（月处理1000笔交易约 ¥1-2）</span>
      </div>

      <!-- 操作按钮 -->
      <div class="form-actions">
        <button
          @click="testConnection"
          class="btn btn-secondary"
          :disabled="!localConfig.enabled || !localConfig.apiKey || testing"
        >
          {{ testing ? '测试中...' : '🔍 测试连接' }}
        </button>
        <button
          @click="saveConfig"
          class="btn btn-primary"
          :disabled="saving"
        >
          {{ saving ? '保存中...' : '💾 保存配置' }}
        </button>
      </div>

      <!-- 测试结果 -->
      <div v-if="testResult" class="test-result" :class="{ success: testResult.success, error: !testResult.success }">
        {{ testResult.success ? '✅' : '❌' }} {{ testResult.message }}
      </div>

      <!-- 保存结果 -->
      <div v-if="saveResult" class="save-result" :class="{ success: saveResult }">
        ✅ 配置已保存
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue'
import { AI_PROVIDERS } from '../../config/aiConfig.js'
import { loadAIConfig, saveAIConfig, validateAIConfig } from '../../config/aiConfig.js'
import { testAIConfig } from '../../utils/aiCategorizer.js'

// 状态
const providers = AI_PROVIDERS
const localConfig = ref({ enabled: false, provider: 'qianwen', apiKey: '', model: '', fallbackToRules: true })
const showApiKey = ref(false)
const testing = ref(false)
const saving = ref(false)
const testResult = ref(null)
const saveResult = ref(null)

// 加载配置
onMounted(() => {
  const saved = loadAIConfig()
  localConfig.value = { ...localConfig.value, ...saved }
})

// 监听配置变化，清除测试结果
watch(() => localConfig.value, () => {
  testResult.value = null
  saveResult.value = null
}, { deep: true })

// 测试连接
async function testConnection() {
  testing.value = true
  testResult.value = null

  try {
    // 验证配置
    const validation = validateAIConfig(localConfig.value)
    if (!validation.valid) {
      testResult.value = {
        success: false,
        message: validation.message
      }
      return
    }

    // 测试 API 调用
    const result = await testAIConfig(localConfig.value)
    testResult.value = result
  } catch (error) {
    testResult.value = {
      success: false,
      message: error.message
    }
  } finally {
    testing.value = false
  }
}

// 保存配置
function saveConfig() {
  saving.value = true
  saveResult.value = null

  try {
    const success = saveAIConfig(localConfig.value)

    if (success) {
      saveResult.value = true
      setTimeout(() => {
        saveResult.value = null
      }, 2000)
    } else {
      testResult.value = {
        success: false,
        message: '保存配置失败，请检查浏览器存储权限'
      }
    }
  } catch (error) {
    testResult.value = {
      success: false,
      message: `保存失败: ${error.message}`
    }
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
.ai-config-panel {
  background: #f8f9fa;
  border-radius: 12px;
  padding: 24px;
  margin-bottom: 20px;
}

.config-header h3 {
  margin: 0 0 8px 0;
  font-size: 1.3rem;
  color: #333;
}

.config-desc {
  margin: 0;
  font-size: 0.9rem;
  color: #666;
}

.config-form {
  margin-top: 20px;
}

.form-group {
  margin-bottom: 20px;
}

.form-label {
  display: block;
  font-weight: 500;
  margin-bottom: 8px;
  color: #333;
}

.form-select,
.form-input {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 0.95rem;
  transition: border-color 0.3s;
}

.form-select:focus,
.form-input:focus {
  outline: none;
  border-color: #667eea;
}

.form-input:disabled,
.form-select:disabled {
  background: #f5f5f5;
  cursor: not-allowed;
}

.input-with-action {
  display: flex;
  gap: 8px;
}

.input-with-action .form-input {
  flex: 1;
}

.icon-button {
  padding: 10px 16px;
  background: #f0f0f0;
  border: 1px solid #ddd;
  border-radius: 6px;
  cursor: pointer;
  font-size: 1.2rem;
  transition: all 0.3s;
}

.icon-button:hover:not(:disabled) {
  background: #e0e0e0;
}

.icon-button:disabled {
  cursor: not-allowed;
  opacity: 0.5;
}

.form-hint {
  margin-top: 6px;
  font-size: 0.85rem;
  color: #666;
}

.hint-link {
  color: #667eea;
  text-decoration: none;
}

.hint-link:hover {
  text-decoration: underline;
}

.checkbox-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  font-weight: normal;
}

.checkbox {
  width: 18px;
  height: 18px;
  cursor: pointer;
}

.price-hint {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px;
  background: #fff3cd;
  border: 1px solid #ffc107;
  border-radius: 6px;
  font-size: 0.9rem;
  color: #856404;
}

.hint-icon {
  font-size: 1.2rem;
}

.hint-detail {
  font-size: 0.85rem;
  opacity: 0.8;
}

.form-actions {
  display: flex;
  gap: 12px;
  margin-top: 24px;
}

.btn {
  flex: 1;
  padding: 12px 20px;
  border: none;
  border-radius: 6px;
  font-size: 1rem;
  cursor: pointer;
  transition: all 0.3s;
}

.btn-secondary {
  background: #6c757d;
  color: white;
}

.btn-secondary:hover:not(:disabled) {
  background: #5a6268;
}

.btn-primary {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.btn-primary:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
}

.test-result,
.save-result {
  margin-top: 16px;
  padding: 12px;
  border-radius: 6px;
  font-size: 0.95rem;
}

.test-result.success,
.save-result.success {
  background: #d4edda;
  color: #155724;
  border: 1px solid #c3e6cb;
}

.test-result.error {
  background: #f8d7da;
  color: #721c24;
  border: 1px solid #f5c6cb;
}
</style>
