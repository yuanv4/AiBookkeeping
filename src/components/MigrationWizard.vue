<template>
  <div class="migration-wizard" v-if="showWizard">
    <div class="wizard-overlay" @click="state === 'confirm' && skipMigration()"></div>
    <div class="wizard-content">
      <h2>📦 数据迁移向导</h2>
      <p>检测到您有旧版存储的数据,建议迁移到新的存储系统以获得更好的性能和容量。</p>

      <div v-if="state === 'confirm'" class="wizard-step">
        <div class="data-summary">
          <p>旧数据统计:</p>
          <ul>
            <li>交易记录: {{ oldData.transactions?.length || 0 }} 条</li>
            <li>分类数据: {{ oldData.categories?.length || 0 }} 个</li>
            <li>预计耗时: < 1 分钟</li>
          </ul>
        </div>
        <div class="wizard-actions">
          <button @click="startMigration" class="btn btn-primary">
            开始迁移
          </button>
          <button @click="skipMigration" class="btn btn-secondary">
            暂不迁移(继续使用旧存储)
          </button>
        </div>
      </div>

      <div v-else-if="state === 'migrating'" class="wizard-step">
        <div class="progress-bar">
          <div class="progress-fill" :style="{ width: `${progressPercent}%` }"></div>
        </div>
        <p class="progress-message">{{ progressMessage }}</p>
      </div>

      <div v-else-if="state === 'completed'" class="wizard-step">
        <p class="success">✅ 迁移成功!</p>
        <div class="migration-result">
          <p>已迁移数据:</p>
          <ul>
            <li>交易记录: {{ result.migratedCounts.transactions }} 条</li>
            <li>分类数据: {{ result.migratedCounts.categories }} 个</li>
          </ul>
        </div>
        <div class="wizard-actions">
          <button @click="clearOldAndFinish" class="btn btn-primary">
            清除旧数据并完成
          </button>
          <button @click="finish" class="btn btn-secondary">
            稍后清理(保留旧数据)
          </button>
        </div>
        <p class="warning">⚠️ 旧数据仍保留在 localStorage 中,建议确认无误后清理</p>
      </div>

      <div v-else-if="state === 'failed'" class="wizard-step">
        <p class="error">❌ 迁移失败: {{ error }}</p>
        <div class="wizard-actions">
          <button @click="retry" class="btn btn-primary">
            重试
          </button>
          <button @click="rollback" class="btn btn-secondary">
            回滚并继续使用旧存储
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { shouldMigrate, migrateToIndexedDB, rollbackMigration, clearLocalStorageAfterMigration } from '../utils/dataMigrator.js'
import { storage } from '../utils/storage.js'
import { useNotificationStore } from '../stores/notificationStore.js'

const notificationStore = useNotificationStore()
const showWizard = ref(false)
const state = ref('confirm') // confirm | migrating | completed | failed
const progressMessage = ref('')
const progressCurrent = ref(0)
const progressTotal = ref(0)
const result = ref(null)
const error = ref(null)
const oldData = ref({})

onMounted(async () => {
  const needMigration = await shouldMigrate()
  if (needMigration) {
    oldData.value = {
      transactions: storage.get('transactions', []),
      categories: storage.get('categories', [])
    }
    showWizard.value = true
  }
})

const progressPercent = computed(() => {
  if (progressTotal.value === 0) return 0
  return Math.round((progressCurrent.value / progressTotal.value) * 100)
})

async function startMigration() {
  state.value = 'migrating'

  try {
    const migrationResult = await migrateToIndexedDB(({ current, total, message }) => {
      progressCurrent.value = current
      progressTotal.value = total
      progressMessage.value = message
    })

    result.value = migrationResult
    state.value = 'completed'
  } catch (err) {
    error.value = err.message
    state.value = 'failed'
  }
}

async function rollback() {
  try {
    await rollbackMigration()
    showWizard.value = false
    notificationStore.show('已回滚到旧存储', 'info')
  } catch (err) {
    notificationStore.show('回滚失败: ' + err.message, 'error')
  }
}

async function clearOldAndFinish() {
  try {
    await clearLocalStorageAfterMigration()
    showWizard.value = false
    notificationStore.show('迁移完成,旧数据已清除', 'success')
  } catch (err) {
    notificationStore.show('清除失败: ' + err.message, 'error')
  }
}

function skipMigration() {
  showWizard.value = false
}

function finish() {
  showWizard.value = false
}

function retry() {
  state.value = 'confirm'
}
</script>

<style scoped>
.migration-wizard {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 10000;
  display: flex;
  align-items: center;
  justify-content: center;
}

.wizard-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
}

.wizard-content {
  position: relative;
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  padding: 32px;
  max-width: 500px;
  width: 90%;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
}

.wizard-content h2 {
  margin: 0 0 16px 0;
  font-size: 24px;
  color: var(--text-primary);
}

.wizard-content > p {
  color: var(--text-secondary);
  margin-bottom: 24px;
}

.data-summary, .migration-result {
  background: var(--bg-secondary);
  padding: 16px;
  border-radius: var(--radius-md);
  margin-bottom: 24px;
}

.data-summary p, .migration-result p {
  margin: 0 0 8px 0;
  font-weight: 600;
  color: var(--text-primary);
}

.data-summary ul, .migration-result ul {
  margin: 0;
  padding-left: 20px;
  color: var(--text-secondary);
}

.wizard-actions {
  display: flex;
  gap: 12px;
}

.btn {
  flex: 1;
  padding: 12px 20px;
  border: none;
  border-radius: var(--radius-md);
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all var(--duration-base);
}

.btn-primary {
  background: var(--color-primary);
  color: white;
}

.btn-primary:hover {
  opacity: 0.9;
}

.btn-secondary {
  background: var(--bg-secondary);
  color: var(--text-primary);
  border: var(--input-border);
}

.progress-bar {
  width: 100%;
  height: 8px;
  background: var(--bg-secondary);
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: 16px;
}

.progress-fill {
  height: 100%;
  background: var(--color-primary);
  transition: width 0.3s ease;
}

.progress-message {
  text-align: center;
  color: var(--text-secondary);
  margin: 0;
}

.success {
  color: var(--color-success);
  font-weight: 600;
  margin-bottom: 16px;
}

.error {
  color: var(--color-danger);
  margin-bottom: 16px;
}

.warning {
  color: var(--color-warning);
  font-size: 13px;
  margin-top: 16px;
  text-align: center;
}
</style>
