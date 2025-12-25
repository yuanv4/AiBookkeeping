<template>
  <div class="dashboard-view">
    <!-- 无数据状态：首次访问引导 -->
    <div v-if="!hasData" class="empty-dashboard">
      <div class="welcome-section">
        <div class="welcome-icon">📊</div>
        <h1 class="welcome-title">欢迎使用 AI 账单汇集工具</h1>
        <p class="welcome-subtitle">智能解析多平台账单，一键生成专业财务分析报告</p>
      </div>

      <div class="upload-section">
        <FileUploader
          upload-text="点击或拖拽账单文件到此处"
          upload-hint="支持微信支付、支付宝、建设银行、招商银行等账单文件"
          @files-added="handleFilesAdded"
        />
      </div>

      <!-- 处理按钮 -->
      <div v-if="files.length > 0" class="action-section">
        <button
          class="btn btn-primary btn-lg"
          :disabled="processing"
          @click="processFiles"
        >
          {{ processing ? '处理中...' : `开始处理 ${files.length} 个文件` }}
        </button>
      </div>

      <!-- 功能介绍 -->
      <div class="features-section">
        <div class="feature-grid">
          <div class="feature-card">
            <div class="feature-icon">🔍</div>
            <h3 class="feature-title">智能识别</h3>
            <p class="feature-desc">自动识别微信、支付宝、银行等不同平台账单格式</p>
          </div>
          <div class="feature-card">
            <div class="feature-icon">🏷️</div>
            <h3 class="feature-title">AI 自动分类</h3>
            <p class="feature-desc">使用人工智能自动为每笔交易打上消费分类标签</p>
          </div>
          <div class="feature-card">
            <div class="feature-icon">📈</div>
            <h3 class="feature-title">数据可视化</h3>
            <p class="feature-desc">丰富的图表展示，让您的消费习惯一目了然</p>
          </div>
          <div class="feature-card">
            <div class="feature-icon">🔒</div>
            <h3 class="feature-title">隐私安全</h3>
            <p class="feature-desc">所有数据处理均在本地完成，不上传任何个人信息</p>
          </div>
        </div>
      </div>

      <!-- 支持的平台 -->
      <div class="platforms-section">
        <h3 class="platforms-title">支持的平台</h3>
        <div class="platforms-list">
          <div class="platform-item">
            <span class="platform-icon">💙</span>
            <span class="platform-name">支付宝</span>
          </div>
          <div class="platform-item">
            <span class="platform-icon">💚</span>
            <span class="platform-name">微信支付</span>
          </div>
          <div class="platform-item">
            <span class="platform-icon">🏦</span>
            <span class="platform-name">建设银行</span>
          </div>
          <div class="platform-item">
            <span class="platform-icon">🏦</span>
            <span class="platform-name">招商银行</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 有数据状态：专业仪表板 -->
    <div v-else class="data-dashboard">
      <!-- 快捷操作栏 -->
      <div class="card actions-card">
        <div class="actions-left">
          <button class="btn btn-primary" @click="showUploadModal = true">
            📁 上传新账单
          </button>
          <button class="btn btn-secondary" @click="exportData">
            📤 导出数据
          </button>
        </div>
        <div class="actions-right">
          <button class="btn btn-danger" @click="confirmClearData">
            🗑️ 清除数据
          </button>
        </div>
      </div>

      <!-- 统计概览 -->
      <div class="summary-cards">
        <div class="summary-card">
          <div class="summary-icon">📋</div>
          <div class="summary-content">
            <div class="summary-label">总交易笔数</div>
            <div class="summary-value">{{ statistics.total }}</div>
          </div>
        </div>
        <div class="summary-card income">
          <div class="summary-icon">💰</div>
          <div class="summary-content">
            <div class="summary-label">总收入</div>
            <div class="summary-value">¥{{ statistics.income.toFixed(2) }}</div>
          </div>
        </div>
        <div class="summary-card expense">
          <div class="summary-icon">💸</div>
          <div class="summary-content">
            <div class="summary-label">总支出</div>
            <div class="summary-value">¥{{ Math.abs(statistics.expense).toFixed(2) }}</div>
          </div>
        </div>
        <div class="summary-card">
          <div class="summary-icon">📊</div>
          <div class="summary-content">
            <div class="summary-label">净收支</div>
            <div class="summary-value" :style="{ color: statistics.net >= 0 ? '#10b981' : '#ef4444' }">
              ¥{{ statistics.net.toFixed(2) }}
            </div>
          </div>
        </div>
      </div>

      <!-- 消费洞察 -->
      <InsightCard :transactions="transactions" />

      <!-- 图表区域 -->
      <div class="charts-grid">
        <div class="card chart-card">
          <h3 class="chart-title">📈 月度收支趋势</h3>
          <TrendChart :transactions="transactions" />
        </div>
        <div class="card chart-card">
          <h3 class="chart-title">🍩 消费构成</h3>
          <CategoryPie :transactions="transactions" />
        </div>
      </div>

      <!-- 上传模态框 -->
      <div v-if="showUploadModal" class="modal-overlay" @click.self="showUploadModal = false">
        <div class="modal-content">
          <div class="modal-header">
            <h2>上传新账单</h2>
            <button class="modal-close" @click="showUploadModal = false">×</button>
          </div>
          <div class="modal-body">
            <FileUploader @files-added="handleFilesAdded" />
            <div v-if="files.length > 0" class="modal-actions">
              <button
                class="btn btn-primary"
                :disabled="processing"
                @click="processFiles"
              >
                {{ processing ? '处理中...' : `开始处理 ${files.length} 个文件` }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAppStore } from '../stores/appStore.js'
import FileUploader from '../components/common/FileUploader.vue'
import InsightCard from '../components/analysis/InsightCard.vue'
import TrendChart from '../components/charts/TrendChart.vue'
import CategoryPie from '../components/charts/CategoryPie.vue'
import * as XLSX from 'xlsx'

const router = useRouter()
const appStore = useAppStore()

const showUploadModal = ref(false)

const files = computed(() => appStore.files)
const transactions = computed(() => appStore.transactions)
const processing = computed(() => appStore.processing)
const statistics = computed(() => appStore.statistics)
const hasData = computed(() => appStore.hasData)

function handleFilesAdded() {
  // 文件添加后的处理
}

async function processFiles() {
  try {
    await appStore.processFiles()
    showUploadModal.value = false
  } catch (error) {
    alert('处理文件失败: ' + error.message)
  }
}

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

async function confirmClearData() {
  if (confirm('确定要清除所有数据吗？此操作不可恢复。')) {
    await appStore.performClearAll()
  }
}
</script>

<style scoped>
.dashboard-view {
  width: 100%;
}

/* 空状态样式 */
.empty-dashboard {
  max-width: 900px;
  margin: 0 auto;
}

.welcome-section {
  text-align: center;
  margin-bottom: 40px;
}

.welcome-icon {
  font-size: 64px;
  margin-bottom: 20px;
}

.welcome-title {
  font-size: 28px;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0 0 10px 0;
}

.welcome-subtitle {
  font-size: 16px;
  color: var(--text-secondary);
  margin: 0;
}

.upload-section {
  margin-bottom: 30px;
}

.action-section {
  text-align: center;
  margin-bottom: 50px;
}

.features-section {
  margin-bottom: 50px;
}

.feature-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;
}

.feature-card {
  background: var(--bg-card);
  padding: 25px;
  border-radius: var(--radius-lg);
  text-align: center;
  border: var(--card-border);
  transition: border-color var(--duration-base) ease;
}

.feature-card:hover {
  border-color: var(--border-strong);
}

.feature-icon {
  font-size: 40px;
  margin-bottom: 15px;
}

.feature-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 8px 0;
}

.feature-desc {
  font-size: 13px;
  color: var(--text-secondary);
  margin: 0;
  line-height: 1.5;
}

.platforms-section {
  text-align: center;
}

.platforms-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 20px 0;
}

.platforms-list {
  display: flex;
  justify-content: center;
  gap: 30px;
  flex-wrap: wrap;
}

.platform-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: var(--text-secondary);
}

.platform-icon {
  font-size: 24px;
}

/* 数据仪表板样式 */
.data-dashboard {
  width: 100%;
}

.actions-card {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.actions-left,
.actions-right {
  display: flex;
  gap: 10px;
}

.summary-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 20px;
  margin-bottom: 20px;
}

.summary-card {
  background: var(--bg-card);
  padding: 20px;
  border-radius: var(--radius-lg);
  display: flex;
  align-items: center;
  gap: 15px;
  border: var(--card-border);
  transition: border-color var(--duration-base) ease;
}

.summary-card:hover {
  border-color: var(--border-strong);
}

.summary-icon {
  font-size: 36px;
}

.summary-content {
  flex: 1;
}

.summary-label {
  font-size: 13px;
  color: var(--text-secondary);
  margin-bottom: 5px;
}

.summary-value {
  font-size: 24px;
  font-weight: 700;
  color: var(--text-primary);
}

.summary-card.income .summary-value {
  color: var(--color-success);
}

.summary-card.expense .summary-value {
  color: var(--color-danger);
}

.charts-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: 20px;
}

.chart-card {
  padding: 20px;
}

.chart-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 15px 0;
}

/* 模态框样式 */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  width: 90%;
  max-width: 600px;
  max-height: 90vh;
  overflow: auto;
  border: var(--card-border);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: var(--border-default);
}

.modal-header h2 {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}

.modal-close {
  background: none;
  border: none;
  font-size: 28px;
  color: var(--text-secondary);
  cursor: pointer;
  padding: 0;
  width: 30px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-sm);
}

.modal-close:hover {
  background: var(--color-gray-100);
}

.modal-body {
  padding: 20px;
}

.modal-actions {
  margin-top: 20px;
  text-align: center;
}

/* 按钮样式 */
.btn {
  padding: 10px 20px;
  border: none;
  border-radius: var(--radius-md);
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all var(--duration-base) ease;
}

.btn-primary {
  background: var(--color-primary);
  color: white;
}

.btn-primary:hover:not(:disabled) {
  opacity: 0.9;
}

.btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-secondary {
  background: var(--bg-card);
  color: var(--text-secondary);
  border: var(--border-default);
}

.btn-secondary:hover {
  background: var(--color-gray-50);
  border-color: var(--border-strong);
}

.btn-danger {
  background: var(--color-danger);
  color: white;
}

.btn-danger:hover {
  opacity: 0.9;
}

.btn-lg {
  padding: 14px 32px;
  font-size: 16px;
}

/* 响应式 */
@media (max-width: 768px) {
  .welcome-title {
    font-size: 22px;
  }

  .feature-grid {
    grid-template-columns: 1fr;
  }

  .actions-card {
    flex-direction: column;
    gap: 15px;
  }

  .actions-left,
  .actions-right {
    width: 100%;
    flex-direction: column;
  }

  .summary-cards {
    grid-template-columns: 1fr;
  }

  .charts-grid {
    grid-template-columns: 1fr;
  }
}
</style>
