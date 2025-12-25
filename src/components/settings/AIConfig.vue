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
  background: var(--bg-card);
  border-radius: var(--radius-md);
  border: var(--card-border);
  padding: 24px;
}

.config-header h3 {
  margin: 0 0 8px 0;
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--text-primary);
}

.config-desc {
  margin: 0;
  font-size: 0.9rem;
  color: var(--text-secondary);
}

.config-form {
  margin-top: 24px;
}

.form-group {
  margin-bottom: 20px;
}

.form-label {
  display: block;
  font-weight: 500;
  margin-bottom: 6px;
  color: var(--text-primary);
}

.form-select,
.form-input {
  width: 100%;
  padding: 10px 12px;
  border: var(--input-border);
  border-radius: var(--input-radius);
  font-size: 0.95rem;
  background: var(--bg-card);
  transition: border-color var(--duration-base);
}

.form-select:focus,
.form-input:focus {
  outline: none;
  border-color: var(--color-primary);
}

.form-select:hover,
.form-input:hover {
  border-color: var(--color-primary-hover);
}

.form-input:disabled,
.form-select:disabled {
  background: var(--bg-disabled);
  cursor: not-allowed;
  opacity: 0.7;
}

.input-with-action {
  display: flex;
  gap: 8px;
}

.input-with-action .form-input {
  flex: 1;
}

.icon-button {
  padding: 10px 12px;
  background: var(--bg-card);
  border: var(--input-border);
  border-radius: var(--input-radius);
  cursor: pointer;
  font-size: 1.1rem;
  transition: background-color var(--duration-base);
}

.icon-button:hover:not(:disabled) {
  background: var(--bg-hover);
}

.icon-button:disabled {
  cursor: not-allowed;
  opacity: 0.5;
}

.form-hint {
  margin-top: 6px;
  font-size: 0.85rem;
  color: var(--text-secondary);
}

.hint-link {
  color: var(--color-primary);
  text-decoration: none;
  font-weight: 500;
}

.hint-link:hover {
  color: var(--color-primary-hover);
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
  font-size: 0.95rem;
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
  padding: 16px;
  background: var(--bg-card);
  border: var(--card-border);
  border-radius: var(--radius-md);
  font-size: 0.9rem;
  color: var(--text-secondary);
}

.hint-icon {
  font-size: 1rem;
  color: var(--color-primary);
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
  border: var(--input-border);
  border-radius: var(--input-radius);
  font-size: 0.95rem;
  font-weight: 500;
  cursor: pointer;
  transition: all var(--duration-base);
  background: var(--bg-card);
  color: var(--text-primary);
}

.btn-secondary {
  color: var(--text-secondary);
}

.btn-secondary:hover:not(:disabled) {
  background: var(--bg-hover);
  border-color: var(--text-secondary);
}

.btn-primary {
  background: var(--color-primary);
  color: white;
  border: 1px solid var(--color-primary);
}

.btn-primary:hover:not(:disabled) {
  background: var(--color-primary-hover);
  border-color: var(--color-primary-hover);
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.test-result,
.save-result {
  margin-top: 16px;
  padding: 12px;
  border-radius: var(--radius-md);
  font-size: 0.9rem;
  font-weight: 500;
  border: var(--card-border);
}

.test-result.success,
.save-result.success {
  background: var(--color-success-light);
  color: var(--color-success);
  border-color: var(--color-success);
}

.test-result.error {
  background: #fef2f2;
  color: var(--color-danger);
  border-color: var(--color-danger);
}
</style>
