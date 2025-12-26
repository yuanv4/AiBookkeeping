<template>
  <div class="data-settings">
    <h2 class="settings-title">数据管理</h2>

    <!-- 模式提示 -->
    <div class="mode-badge remote-mode">
      <span class="badge-icon">☁️</span>
      <span class="badge-text">云端存储 - 数据存储在后端服务器</span>
    </div>

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

    <!-- 导出数据 -->
    <div class="section">
      <h3 class="section-title">导出数据</h3>
      <div class="section-content">
        <p class="section-desc">
          将您的账单数据导出为备份文件,便于保存和分析
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
          <span class="info-icon">☁️</span>
          <div class="info-content">
            <div class="info-title">云端存储</div>
            <div class="info-desc">所有数据存储在后端服务器,可在任何设备上访问</div>
          </div>
        </div>
        <div class="info-item">
          <span class="info-icon">🔐</span>
          <div class="info-content">
            <div class="info-title">数据安全</div>
            <div class="info-desc">通过 HTTPS 加密传输,服务端定期备份</div>
          </div>
        </div>
        <div class="info-item">
          <span class="info-icon">📊</span>
          <div class="info-content">
            <div class="info-title">数据格式</div>
            <div class="info-desc">支持导出为标准 Excel/JSON 格式,可在其他软件中打开分析</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useAppStore } from '../../stores/appStore.js'
import { useCategoryStore } from '../../stores/categoryStore.js'
import { useNotificationStore } from '../../stores/notificationStore.js'
import { exportToJSON, exportToCSV } from '../../utils/dataExporter.js'
import * as XLSX from 'xlsx'

const appStore = useAppStore()
const categoryStore = useCategoryStore()
const notificationStore = useNotificationStore()

const exportFormat = ref('json')

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

.mode-badge {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  border-radius: var(--radius-md);
  margin-bottom: 24px;
  border: 1px solid;
}

.mode-badge.remote-mode {
  background: rgba(59, 130, 246, 0.1);
  border-color: rgba(59, 130, 246, 0.3);
}

.badge-icon {
  font-size: 24px;
  flex-shrink: 0;
}

.badge-text {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
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
