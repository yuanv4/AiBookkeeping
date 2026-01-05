<template>
  <div class="transactions-view">
    <!-- 空状态 -->
    <div v-if="!hasData" class="empty-state">
      <div class="empty-icon"><FileTextOutlined /></div>
      <h3>暂无账单数据</h3>
      <p>请先在设置页面上传账单文件</p>
      <router-link to="/settings/data" class="btn btn-primary">
        前往上传
      </router-link>
    </div>

    <!-- 交易列表 -->
    <div v-else class="transactions-content">
      <!-- 筛选器 -->
      <div class="card filters-card">
        <div class="filters-row">
          <div class="filter-group search-box">
            <input
              v-model="filterStore.searchQuery"
              type="text"
              placeholder="搜索交易对方、商品描述..."
              @input="filterStore.resetPage"
            />
          </div>
          <div class="filter-group">
            <label>平台:</label>
            <select v-model="filterStore.filterPlatform" @change="filterStore.resetPage">
              <option value="">全部</option>
              <option value="alipay">支付宝</option>
              <option value="wechat">微信支付</option>
              <option value="bank">银行</option>
            </select>
          </div>
          <div class="filter-group">
            <label>类型:</label>
            <select v-model="filterStore.filterType" @change="filterStore.resetPage">
              <option value="">全部</option>
              <option value="income">收入</option>
              <option value="expense">支出</option>
            </select>
          </div>
          <div class="filter-group">
            <label>分类:</label>
            <select v-model="filterStore.filterCategory" @change="filterStore.resetPage">
              <option value="">全部</option>
              <option v-for="cat in filterStore.categories" :key="cat" :value="cat">{{ cat }}</option>
            </select>
          </div>
          <button class="btn btn-secondary" @click="clearFilters">
            清除筛选
          </button>
        </div>
      </div>

      <!-- 交易表格 -->
      <div class="card table-card">
        <div class="table-container">
          <table>
            <thead>
              <tr>
                <th>交易时间</th>
                <th>平台</th>
                <th>类型</th>
                <th>分类</th>
                <th>交易对方</th>
                <th>描述</th>
                <th class="text-right">金额</th>
                <th>支付方式</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="tx in paginatedTransactions" :key="tx.transactionId">
                <td class="num">{{ formatDateTime(tx.transactionTime) }}</td>
                <td>
                  <span class="tag">
                    <BankOutlined v-if="tx.platform === 'bank'" />
                    <AlipayCircleOutlined v-else-if="tx.platform === 'alipay'" />
                    <WechatOutlined v-else-if="tx.platform === 'wechat'" />
                    {{ getPlatformLabel(tx) }}
                  </span>
                </td>
                <td>
                  <span class="tag" :class="tx.transactionType === 'income' ? 'tag--success' : 'tag--danger'">
                    {{ tx.transactionType === 'income' ? '收入' : '支出' }}
                  </span>
                </td>
                <td>
                  <span v-if="tx.category" class="tag">{{ tx.category }}</span>
                  <span v-else class="text-muted">未分类</span>
                </td>
                <td>{{ tx.counterparty || '-' }}</td>
                <td>{{ tx.description || '-' }}</td>
                <td class="text-right">
                  <span class="money" :class="tx.amount >= 0 ? 'money--pos' : 'money--neg'">
                    {{ formatMoney(tx.amount) }}
                  </span>
                </td>
                <td>{{ tx.paymentMethod || '-' }}</td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- 分页 -->
        <div class="pagination">
          <button
            class="btn btn-sm"
            :disabled="filterStore.currentPage === 1"
            @click="changePage(filterStore.currentPage - 1)"
          >
            上一页
          </button>
          <span class="page-info">
            第 {{ filterStore.currentPage }} / {{ totalPages }} 页
            (共 {{ filteredTransactions.length }} 条)
          </span>
          <button
            class="btn btn-sm"
            :disabled="filterStore.currentPage === totalPages"
            @click="changePage(filterStore.currentPage + 1)"
          >
            下一页
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useAppStore } from '../stores/appStore.js'
import { useFilterStore } from '../stores/filterStore.js'
import {
  FileTextOutlined,
  BankOutlined,
  AlipayCircleOutlined,
  WechatOutlined
} from '@ant-design/icons-vue'

// 人民币格式化（带正负号）
const moneyFormatter = new Intl.NumberFormat('zh-CN', {
  style: 'currency',
  currency: 'CNY',
  signDisplay: 'always'
})

function formatMoney(amount) {
  return moneyFormatter.format(amount)
}

const appStore = useAppStore()
const filterStore = useFilterStore()

const transactions = computed(() => appStore.transactions)
const hasData = computed(() => appStore.hasData)

// 筛选后的交易
const filteredTransactions = computed(() => {
  return filterStore.applyFilters(transactions.value)
})

// 分页后的交易
const paginatedTransactions = computed(() => {
  return filterStore.paginate(filteredTransactions.value)
})

// 总页数
const totalPages = computed(() => {
  return filterStore.getTotalPages(filteredTransactions.value)
})

function changePage(page) {
  filterStore.currentPage = page
}

function clearFilters() {
  filterStore.clearFilters()
}

function formatDateTime(isoString) {
  if (!isoString) return '-'
  const date = new Date(isoString)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

function getPlatformLabel(tx) {
  if (tx.platform === 'alipay') return '支付宝'
  if (tx.platform === 'wechat') return '微信支付'
  return tx.bankName || '银行'
}
</script>

<style scoped>
.transactions-view {
  width: 100%;
}

.empty-state {
  text-align: center;
  padding: 80px 20px;
}

.empty-icon {
  font-size: 64px;
  margin-bottom: 20px;
}

.empty-state h3 {
  font-size: 20px;
  color: var(--text-primary);
  margin: 0 0 10px 0;
}

.empty-state p {
  font-size: 14px;
  color: var(--text-secondary);
  margin: 0 0 20px 0;
}

.transactions-content {
  width: 100%;
}

.filters-card {
  margin-bottom: 20px;
}

.filters-row {
  display: flex;
  gap: 15px;
  flex-wrap: wrap;
  align-items: flex-end;
}

.filter-group {
  display: flex;
  align-items: center;
  gap: 8px;
}

.filter-group label {
  font-size: 13px;
  color: var(--text-secondary);
  white-space: nowrap;
}

.filter-group input,
.filter-group select {
  padding: 8px 12px;
  border: var(--border-default);
  border-radius: var(--radius-sm);
  font-size: 14px;
  outline: none;
  transition: border-color var(--duration-base) ease;
}

.filter-group input:focus,
.filter-group select:focus {
  border-color: var(--border-strong);
}

.search-box input {
  min-width: 250px;
}

.table-card {
  overflow: hidden;
}

.table-container {
  overflow-x: auto;
}

table {
  width: 100%;
  border-collapse: collapse;
}

thead {
  background: var(--table-header-bg);
}

th {
  padding: 12px 15px;
  text-align: left;
  font-size: 13px;
  font-weight: 600;
  color: var(--text-secondary);
  border-bottom: var(--table-border);
  white-space: nowrap;
}

td {
  padding: 12px 15px;
  border-bottom: var(--table-border);
  font-size: 14px;
  color: var(--text-primary);
}

tbody tr:hover {
  background: var(--table-hover-bg);
}

.text-muted {
  color: var(--text-tertiary);
  font-size: 13px;
}

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 15px;
  padding: 20px;
  border-top: var(--table-border);
}

.page-info {
  font-size: 14px;
  color: var(--text-secondary);
}


/* 响应式 */
@media (max-width: 768px) {
  .filters-row {
    flex-direction: column;
    align-items: stretch;
  }

  .filter-group {
    flex-direction: column;
    align-items: stretch;
  }

  .search-box input {
    min-width: 100%;
  }

  .table-container {
    font-size: 12px;
  }

  th, td {
    padding: 8px 10px;
  }
}
</style>
