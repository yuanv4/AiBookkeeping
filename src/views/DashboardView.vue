<template>
  <div class="dashboard-view">
    <!-- 无数据状态：引导用户去设置页面 -->
    <div v-if="!hasData" class="empty-dashboard">
      <div class="welcome-section">
        <div class="welcome-icon">📊</div>
        <h1 class="welcome-title">欢迎使用 AI 账单汇集工具</h1>
        <p class="welcome-subtitle">智能解析多平台账单，一键生成专业财务分析报告</p>
      </div>

      <div class="empty-state-card">
        <div class="empty-icon">📁</div>
        <h2 class="empty-title">暂无账单数据</h2>
        <p class="empty-desc">前往设置页面上传账单文件，开始您的财务管理之旅</p>
        <router-link to="/settings/data" class="btn btn-primary btn-lg">
          ⚙️ 前往设置上传账单
        </router-link>
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
            <div class="feature-icon">📈</div>
            <h3 class="feature-title">数据可视化</h3>
            <p class="feature-desc">丰富的图表展示，让您的消费习惯一目了然</p>
          </div>
          <div class="feature-card">
            <div class="feature-icon">🔒</div>
            <h3 class="feature-title">隐私安全</h3>
            <p class="feature-desc">数据存储在后端服务器，安全加密传输</p>
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

      <!-- 财务指标 -->
      <FinancialMetrics
        :statistics="statistics"
        :monthly-stats="monthlyStats"
        :yearly-stats="yearlyStats"
      />

      <!-- 近期大额交易列表 -->
      <LargeTransactionList
        :transactions="transactions"
        :limit="10"
        @time-range-change="handleTimeRangeChange"
      />
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useAppStore } from '../stores/appStore.js'
import FinancialMetrics from '../components/dashboard/FinancialMetrics.vue'
import LargeTransactionList from '../components/dashboard/LargeTransactionList.vue'

const appStore = useAppStore()

const transactions = computed(() => appStore.transactions)
const statistics = computed(() => appStore.statistics)
const hasData = computed(() => appStore.hasData)

// 本月收支统计
const monthlyStats = computed(() => {
  const now = new Date()
  const currentMonth = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`

  const monthlyTransactions = transactions.value.filter(t =>
    // 边界保护：确保 transactionTime 存在
    t.transactionTime && t.transactionTime.startsWith(currentMonth)
  )

  const income = monthlyTransactions
    .filter(t => t.amount > 0)
    .reduce((sum, t) => sum + t.amount, 0)

  const expense = monthlyTransactions
    .filter(t => t.amount < 0)
    .reduce((sum, t) => sum + t.amount, 0)

  return { income, expense, net: income + expense }
})

// 本年收支统计
const yearlyStats = computed(() => {
  const currentYear = new Date().getFullYear()

  const yearlyTransactions = transactions.value.filter(t =>
    // 边界保护：确保 transactionTime 存在且有效
    t.transactionTime && new Date(t.transactionTime).getFullYear() === currentYear
  )

  const income = yearlyTransactions
    .filter(t => t.amount > 0)
    .reduce((sum, t) => sum + t.amount, 0)

  const expense = yearlyTransactions
    .filter(t => t.amount < 0)
    .reduce((sum, t) => sum + t.amount, 0)

  return { income, expense, net: income + expense }
})

function handleTimeRangeChange(range) {
  console.log('时间范围变化:', range)
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

.empty-state-card {
  background: var(--bg-card);
  border: var(--card-border);
  border-radius: var(--radius-lg);
  padding: 50px 30px;
  text-align: center;
  margin-bottom: 50px;
}

.empty-icon {
  font-size: 56px;
  margin-bottom: 20px;
}

.empty-title {
  font-size: 20px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 12px 0;
}

.empty-desc {
  font-size: 14px;
  color: var(--text-secondary);
  margin: 0 0 24px 0;
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

/* 按钮样式 */
.btn {
  display: inline-block;
  padding: 10px 20px;
  border: none;
  border-radius: var(--radius-md);
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  text-decoration: none;
  transition: all var(--duration-base) ease;
}

.btn-primary {
  background: var(--color-primary);
  color: white;
}

.btn-primary:hover {
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

  .summary-cards {
    grid-template-columns: 1fr;
  }
}
</style>
