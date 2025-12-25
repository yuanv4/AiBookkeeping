<template>
  <div class="data-settings">
    <h2 class="settings-title">数据管理</h2>

    <!-- 数据统计 -->
    <div class="section">
      <h3 class="section-title">数据统计</h3>
      <div class="stats-grid">
        <div class="stat-card">
          <div class="stat-icon">📋</div>
          <div class="stat-content">
            <div class="stat-label">交易记录</div>
            <div class="stat-value">{{ statistics.total }}</div>
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-icon">💰</div>
          <div class="stat-content">
            <div class="stat-label">总收入</div>
            <div class="stat-value income">¥{{ statistics.income.toFixed(2) }}</div>
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-icon">💸</div>
          <div class="stat-content">
            <div class="stat-label">总支出</div>
            <div class="stat-value expense">¥{{ Math.abs(statistics.expense).toFixed(2) }}</div>
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-icon">📁</div>
          <div class="stat-content">
            <div class="stat-label">已上传文件</div>
            <div class="stat-value">{{ files.length }}</div>
          </div>
        </div>
      </div>
    </div>

    <!-- 备份管理 -->
    <div class="section">
      <h3 class="section-title">数据备份</h3>
      <div class="section-content">
        <p class="section-desc">
          创建本地备份,防止数据丢失。备份将保存在浏览器本地数据库中。
        </p>
        <button @click="createBackup" class="btn btn-primary" :disabled="creatingBackup">
          {{ creatingBackup ? '正在创建备份...' : '💾 立即备份' }}
        </button>

        <!-- 备份列表 -->
        <div v-if="backups.length > 0" class="backup-list">
          <div class="backup-list-header">
            <h4>备份列表 ({{ backups.length }})</h4>
            <p class="backup-hint">保留最近 10 个备份</p>
          </div>
          <div class="backup-items">
            <div v-for="backup in backups" :key="backup.id" class="backup-item">
              <div class="backup-info">
                <div class="backup-time">🕒 {{ backup.formattedTime }}</div>
                <div class="backup-size">📦 {{ formatSize(backup.size) }}</div>
              </div>
              <div class="backup-actions">
                <button
                  @click="restoreFromBackup(backup)"
                  class="btn btn-small"
                  :disabled="restoring"
                >
                  {{ restoring ? '恢复中...' : '恢复' }}
                </button>
                <button
                  @click="deleteBackup(backup.id)"
                  class="btn btn-small btn-danger"
                  :disabled="restoring"
                >
                  删除
                </button>
              </div>
            </div>
          </div>
        </div>
        <div v-else class="no-backups">
          <p>暂无备份，点击上方按钮创建第一个备份</p>
        </div>
      </div>
    </div>

    <!-- 恢复进度模态框 -->
    <div v-if="restoring" class="modal-overlay">
      <div class="modal-content">
        <h3>正在恢复数据...</h3>
        <div class="progress-bar">
          <div class="progress-fill" :style="{ width: '100%' }"></div>
        </div>
        <p class="progress-message">{{ restoreProgress.message }}</p>
        <p class="progress-hint">请不要关闭浏览器窗口</p>
      </div>
    </div>

    <!-- 导出数据 -->
    <div class="section">
      <h3 class="section-title">导出数据</h3>
      <div class="section-content">
        <p class="section-desc">
          将您的账单数据导出为备份文件,便于保存和恢复
        </p>
        <div class="export-options">
          <select v-model="exportFormat" class="export-select">
            <option value="json">完整备份 (JSON)</option>
            <option value="excel">Excel 文件</option>
            <option value="csv">CSV 文件</option>
          </select>
          <button @click="exportData" class="btn btn-primary" :disabled="!hasData">
            📤 导出数据
          </button>
        </div>
        <div class="storage-info">
          <p>💾 已用空间: {{ storageInfo.usedFormatted }} ({{ storageInfo.itemCount }} 项)</p>
          <p v-if="storageInfo.isNearQuotaLimit" class="warning">
            ⚠️ 存储空间接近上限,建议清理数据或导出备份
          </p>
        </div>
      </div>
    </div>

    <!-- 清除数据 -->
    <div class="section danger-zone">
      <h3 class="section-title">危险区域</h3>
      <div class="section-content">
        <p class="section-desc">
          清除所有数据将删除所有已上传的文件和解析结果,此操作不可恢复。
          建议先执行"导出完整备份"。
        </p>
        <button class="btn btn-primary" @click="exportFormat = 'json'; exportData()">
          📤 先导出完整备份
        </button>
        <button class="btn btn-danger" @click="confirmClearData">
          🗑️ 清除所有数据
        </button>
      </div>
    </div>

    <!-- 数据说明 -->
    <div class="section">
      <h3 class="section-title">关于数据存储</h3>
      <div class="info-box">
        <div class="info-item">
          <span class="info-icon">🔒</span>
          <div class="info-content">
            <div class="info-title">本地存储</div>
            <div class="info-desc">所有数据存储在您的浏览器本地，不会上传到任何服务器</div>
          </div>
        </div>
        <div class="info-item">
          <span class="info-icon">🧹</span>
          <div class="info-content">
            <div class="info-title">自动清理</div>
            <div class="info-desc">清除浏览器数据会导致所有账单数据丢失，请定期导出备份</div>
          </div>
        </div>
        <div class="info-item">
          <span class="info-icon">📊</span>
          <div class="info-content">
            <div class="info-title">数据格式</div>
            <div class="info-desc">支持导出为标准 Excel 格式，可在其他软件中打开分析</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, onMounted } from 'vue'
import { useAppStore } from '../../stores/appStore.js'
import { useCategoryStore } from '../../stores/categoryStore.js'
import { useNotificationStore } from '../../stores/notificationStore.js'
import { storage } from '../../utils/storage.js'
import { exportToJSON, exportToCSV } from '../../utils/dataExporter.js'
import { createBackup as createBackupUtil, saveBackup, getBackupList, deleteBackup as deleteBackupUtil, restoreBackup as restoreBackupUtil } from '../../utils/backupManager.js'
import { db } from '../../utils/indexedDB.js'
import * as XLSX from 'xlsx'

const appStore = useAppStore()
const categoryStore = useCategoryStore()
const notificationStore = useNotificationStore()

const exportFormat = ref('json')
const storageInfo = ref({})
const backups = ref([])
const creatingBackup = ref(false)
const restoring = ref(false)
const restoreProgress = ref({})

onMounted(async () => {
  storageInfo.value = storage.getStorageInfo()
  storageInfo.value.isNearQuotaLimit = storage.isNearQuotaLimit()
  await loadBackups()
})

const files = computed(() => appStore.files)
const transactions = computed(() => appStore.transactions)
const statistics = computed(() => appStore.statistics)
const hasData = computed(() => appStore.hasData)

async function exportData() {
  try {
    let content, filename, mimeType

    if (exportFormat.value === 'json') {
      const data = await exportToJSON(
        appStore.transactions,
        categoryStore.categories,
        categoryStore.transactionCategories,
        categoryStore.corrections,
        categoryStore.aiConfig
      )
      content = JSON.stringify(data, null, 2)
      filename = `账单备份_${new Date().toISOString().slice(0, 10)}.json`
      mimeType = 'application/json'
    } else if (exportFormat.value === 'csv') {
      content = exportToCSV(appStore.transactions)
      filename = `账单明细_${new Date().toISOString().slice(0, 10)}.csv`
      mimeType = 'text/csv'
    } else {
      // Excel 导出保持原逻辑
      if (transactions.value.length === 0) {
        notificationStore.show('没有可导出的数据', 'warning')
        return
      }

      const exportData = transactions.value.map(t => ({
        '交易时间': new Date(t.transactionTime).toLocaleString('zh-CN'),
        '平台': t.platform === 'alipay' ? '支付宝' : t.platform === 'wechat' ? '微信支付' : t.bankName || '银行',
        '类型': t.transactionType === 'income' ? '收入' : '支出',
        '交易对方': t.counterparty || '',
        '描述': t.description || '',
        '金额': t.amount,
        '支付方式': t.paymentMethod || '',
        '分类': t.category || '未分类'
      }))

      const worksheet = XLSX.utils.json_to_sheet(exportData)
      const workbook = XLSX.utils.book_new()
      XLSX.utils.book_append_sheet(workbook, worksheet, '账单明细')
      XLSX.writeFile(workbook, `账单汇总_${new Date().toISOString().slice(0, 10)}.xlsx`)
      notificationStore.show('导出成功', 'success')
      return
    }

    const blob = new Blob([content], { type: mimeType })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    a.click()
    URL.revokeObjectURL(url)

    notificationStore.show('导出成功', 'success')
  } catch (error) {
    console.error('导出失败:', error)
    notificationStore.show('导出失败: ' + error.message, 'error')
  }
}

async function confirmClearData() {
  const info = appStore.clearAllData()

  if (confirm(`确定要清除所有数据吗?\n\n将要删除:\n${info.dataTypes.map(d => '- ' + d).join('\n')}\n\n此操作不可恢复!`)) {
    await appStore.performClearAll()
    // notification 已经在 performClearAll 中显示
  }
}

// ========== 备份管理 ==========

async function loadBackups() {
  try {
    backups.value = await getBackupList()
  } catch (error) {
    console.error('加载备份列表失败:', error)
  }
}

async function createBackup() {
  creatingBackup.value = true
  try {
    const backupData = await createBackupUtil()
    await saveBackup(backupData)
    await loadBackups()
    notificationStore.show('备份创建成功', 'success')
  } catch (error) {
    console.error('创建备份失败:', error)
    notificationStore.show('备份失败: ' + error.message, 'error')
  } finally {
    creatingBackup.value = false
  }
}

async function restoreFromBackup(backup) {
  if (!confirm(`确定要从 ${backup.formattedTime} 的备份恢复吗?\n\n⚠️ 当前数据将被覆盖!\n\n建议先创建当前数据的备份。`)) {
    return
  }

  restoring.value = true
  try {
    // 从 IndexedDB 获取备份数据
    const backupRecord = await db.backups.get(backup.id)
    if (!backupRecord) {
      throw new Error('备份不存在')
    }

    await restoreBackupUtil(backupRecord.data, (progress) => {
      restoreProgress.value = progress
    })

    notificationStore.show('恢复成功!页面将在 2 秒后刷新', 'success')
    setTimeout(() => {
      window.location.reload()
    }, 2000)
  } catch (error) {
    console.error('恢复失败:', error)
    notificationStore.show('恢复失败: ' + error.message, 'error')
  } finally {
    restoring.value = false
  }
}

async function deleteBackup(backupId) {
  if (!confirm('确定要删除此备份吗?')) return

  try {
    await deleteBackupUtil(backupId)
    await loadBackups()
    notificationStore.show('备份已删除', 'success')
  } catch (error) {
    console.error('删除备份失败:', error)
    notificationStore.show('删除失败: ' + error.message, 'error')
  }
}

function formatSize(bytes) {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(2) + ' MB'
}
</script>

<style scoped>
.data-settings {
  width: 100%;
}

.settings-title {
  font-size: 24px;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0 0 24px 0;
}

.section {
  margin-bottom: 24px;
  padding-bottom: 24px;
  border-bottom: var(--card-border);
}

.section:last-child {
  border-bottom: none;
  padding-bottom: 0;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 12px 0;
}

.section-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.section-desc {
  font-size: 14px;
  color: var(--text-secondary);
  margin: 0;
}

.export-options {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.export-select {
  padding: 10px 16px;
  border: var(--input-border);
  border-radius: var(--input-radius);
  font-size: 14px;
  background: var(--bg-card);
  color: var(--text-primary);
  cursor: pointer;
}

.storage-info {
  padding: 12px;
  background: var(--bg-secondary);
  border-radius: var(--radius-md);
  border: var(--card-border);
}

.storage-info p {
  font-size: 13px;
  color: var(--text-secondary);
  margin: 0;
  line-height: 1.6;
}

.storage-info .warning {
  color: var(--color-warning);
  font-weight: 500;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 16px;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px;
  background: var(--bg-card);
  border-radius: var(--radius-md);
  border: var(--card-border);
}

.stat-icon {
  font-size: 28px;
}

.stat-content {
  flex: 1;
}

.stat-label {
  font-size: 12px;
  color: var(--text-secondary);
  margin-bottom: 4px;
}

.stat-value {
  font-size: 20px;
  font-weight: 700;
  color: var(--text-primary);
}

.stat-value.income {
  color: var(--color-success);
}

.stat-value.expense {
  color: var(--color-danger);
}

.danger-zone {
  background: var(--bg-card);
  padding: 20px;
  border-radius: var(--radius-md);
  border: 2px solid var(--color-danger);
}

.danger-zone .section-title {
  color: var(--color-danger);
}

.danger-zone .section-desc {
  color: var(--text-secondary);
}

.info-box {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.info-item {
  display: flex;
  gap: 16px;
  padding: 16px;
  background: var(--bg-card);
  border-radius: var(--radius-md);
  border: var(--card-border);
}

.info-icon {
  font-size: 24px;
  flex-shrink: 0;
}

.info-content {
  flex: 1;
}

.info-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 4px;
}

.info-desc {
  font-size: 13px;
  color: var(--text-secondary);
  margin: 0;
  line-height: 1.5;
}

.btn {
  padding: 10px 20px;
  border: var(--input-border);
  border-radius: var(--input-radius);
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all var(--duration-base);
  white-space: nowrap;
  background: var(--bg-card);
  color: var(--text-primary);
}

.btn-primary {
  border-color: var(--color-primary);
  color: var(--text-primary);
}

.btn-primary:hover:not(:disabled) {
  background: var(--color-primary);
  color: white;
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-danger {
  border-color: var(--color-danger);
  color: var(--color-danger);
}

.btn-danger:hover:not(:disabled) {
  background: var(--color-danger);
  color: white;
}

/* 备份列表样式 */
.backup-list {
  margin-top: 20px;
}

.backup-list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.backup-list-header h4 {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}

.backup-hint {
  font-size: 12px;
  color: var(--text-secondary);
  margin: 0;
}

.backup-items {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.backup-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: var(--bg-secondary);
  border-radius: var(--radius-md);
  border: var(--card-border);
}

.backup-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.backup-time {
  font-size: 13px;
  color: var(--text-primary);
  font-weight: 500;
}

.backup-size {
  font-size: 12px;
  color: var(--text-secondary);
}

.backup-actions {
  display: flex;
  gap: 8px;
}

.btn-small {
  padding: 6px 12px;
  font-size: 12px;
}

.no-backups {
  margin-top: 16px;
  padding: 24px;
  text-align: center;
  background: var(--bg-secondary);
  border-radius: var(--radius-md);
  border: var(--card-border);
}

.no-backups p {
  font-size: 14px;
  color: var(--text-secondary);
  margin: 0;
}

/* 模态框样式 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
}

.modal-content {
  background: var(--bg-card);
  padding: 32px;
  border-radius: var(--radius-lg);
  min-width: 320px;
  max-width: 400px;
  text-align: center;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
}

.modal-content h3 {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 20px 0;
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
  animation: shimmer 1.5s infinite;
}

@keyframes shimmer {
  0% {
    opacity: 1;
  }
  50% {
    opacity: 0.6;
  }
  100% {
    opacity: 1;
  }
}

.progress-message {
  font-size: 14px;
  color: var(--text-primary);
  margin: 0 0 8px 0;
}

.progress-hint {
  font-size: 12px;
  color: var(--text-secondary);
  margin: 0;
}

/* 响应式 */
@media (max-width: 768px) {
  .stats-grid {
    grid-template-columns: 1fr;
  }

  .section-content {
    flex-direction: column;
    align-items: stretch;
  }

  .info-item {
    flex-direction: column;
    text-align: center;
  }
}
</style>
