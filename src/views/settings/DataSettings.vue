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

    <!-- 导出数据 -->
    <div class="section">
      <h3 class="section-title">导出数据</h3>
      <div class="section-content">
        <p class="section-desc">
          将您的账单数据导出为 Excel 文件，便于保存和分析
        </p>
        <button class="btn btn-primary" @click="exportData" :disabled="!hasData">
          📤 导出为 Excel
        </button>
      </div>
    </div>

    <!-- 清除数据 -->
    <div class="section danger-zone">
      <h3 class="section-title">危险区域</h3>
      <div class="section-content">
        <p class="section-desc">
          清除所有数据将删除所有已上传的文件和解析结果，此操作不可恢复。
        </p>
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
import { computed } from 'vue'
import { useAppStore } from '../../stores/appStore.js'
import * as XLSX from 'xlsx'

const appStore = useAppStore()

const files = computed(() => appStore.files)
const transactions = computed(() => appStore.transactions)
const statistics = computed(() => appStore.statistics)
const hasData = computed(() => appStore.hasData)

function exportData() {
  if (transactions.value.length === 0) {
    alert('没有可导出的数据')
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
}

function confirmClearData() {
  if (confirm('确定要清除所有数据吗？此操作不可恢复！\n\n所有已上传的文件和解析结果将被永久删除。')) {
    appStore.clearAllData()
    alert('数据已清除')
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
  color: #1f2937;
  margin: 0 0 30px 0;
}

.section {
  margin-bottom: 30px;
  padding-bottom: 30px;
  border-bottom: 1px solid #e5e7eb;
}

.section:last-child {
  border-bottom: none;
  padding-bottom: 0;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
  margin: 0 0 15px 0;
}

.section-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  flex-wrap: wrap;
}

.section-desc {
  font-size: 14px;
  color: #6b7280;
  margin: 0;
  flex: 1;
  min-width: 200px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 15px;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 15px;
  padding: 15px;
  background: #f9fafb;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
}

.stat-icon {
  font-size: 28px;
}

.stat-content {
  flex: 1;
}

.stat-label {
  font-size: 12px;
  color: #6b7280;
  margin-bottom: 4px;
}

.stat-value {
  font-size: 20px;
  font-weight: 700;
  color: #1f2937;
}

.stat-value.income {
  color: #10b981;
}

.stat-value.expense {
  color: #ef4444;
}

.danger-zone {
  background: #fef2f2;
  padding: 20px;
  border-radius: 8px;
  border: 1px solid #fecaca;
}

.danger-zone .section-title {
  color: #dc2626;
}

.danger-zone .section-desc {
  color: #991b1b;
}

.info-box {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.info-item {
  display: flex;
  gap: 15px;
  padding: 15px;
  background: #f9fafb;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
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
  color: #1f2937;
  margin-bottom: 4px;
}

.info-desc {
  font-size: 13px;
  color: #6b7280;
  margin: 0;
  line-height: 1.5;
}

.btn {
  padding: 10px 20px;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  white-space: nowrap;
}

.btn-primary {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.btn-primary:hover:not(:disabled) {
  opacity: 0.9;
  transform: translateY(-1px);
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-danger {
  background: #ef4444;
  color: white;
}

.btn-danger:hover {
  background: #dc2626;
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
