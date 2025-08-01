/**
 * 商户分类管理页面的JavaScript逻辑
 * 使用Tabulator表格库实现商户列表展示和AI推荐分类功能
 */

import { showNotification } from '../common/notifications.js';
import { getTabulatorCommonConfig, getTabulatorFormatters } from '../common/utils.js';

export default class MerchantCategoriesPage {
    constructor() {
        this.merchants = [];
        this.merchantsTable = null;
    }

    init() {
        // 初始化表格
        this.initMerchantsTable();

        // 初始化详情面板
        this.detailPanel = new MerchantDetailPanel();

        // 设置行点击事件
        this.setupRowClickEvents();

        // 加载商户数据
        this.loadMerchantsData();
    }

    initMerchantsTable() {
        const commonConfig = getTabulatorCommonConfig();
        const formatters = getTabulatorFormatters();

        this.merchantsTable = new Tabulator("#merchants-table", {
            ...commonConfig,
            data: this.merchants,
            paginationSize: 20,
            placeholder: "暂无未分类商户",
            columns: [
                {
                    title: "商户名称",
                    field: "merchant_name",
                    headerFilter: "input",
                    headerFilterPlaceholder: "搜索商户...",
                    responsive: 0,
                    formatter: function(cell) {
                        const value = cell.getValue();
                        return `<span class="fw-medium">${value}</span>`;
                    }
                },
                {
                    title: "交易次数",
                    field: "transaction_count",
                    sorter: "number",
                    responsive: 2,
                    formatter: function(cell) {
                        return `<span class="fw-semibold">${cell.getValue()} 笔</span>`;
                    }
                },
                {
                    title: "总金额",
                    field: "total_amount",
                    sorter: "number",
                    responsive: 1,
                    formatter: formatters.currency
                },
                {
                    title: "最近交易",
                    field: "latest_date",
                    sorter: "string", // 改为字符串排序，YYYY/MM/DD格式天然支持正确排序
                    responsive: 3,
                    formatter: formatters.dateFormat
                },
                {
                    title: "AI建议",
                    field: "ai_suggestion",
                    hozAlign: "left",
                    responsive: 2,
                    formatter: (cell) => this.formatAISuggestion(cell)
                }
            ]
        });
    }

    setupRowClickEvents() {
        // 使用Tabulator内置的选择状态变化事件
        this.merchantsTable.on("rowSelectionChanged", (_, rows) => {
            if (rows.length > 0) {
                // 有行被选中，显示商户详情
                const selectedRow = rows[0]; // 由于限制只能选择一行，取第一个
                const merchantData = selectedRow.getData();
                this.detailPanel.showMerchant(merchantData);
            } else {
                // 没有行被选中，隐藏详情面板
                this.detailPanel.hideMerchant();
            }
        });
    }

    formatAISuggestion(cell) {
        const suggestion = cell.getValue();
        if (!suggestion || suggestion.confidence === 0) {
            return '<span class="text-dark"><i data-lucide="help-circle" class="me-1"></i>未分类</span>';
        }

        const icon = window.CATEGORIES_CONFIG?.[suggestion.category]?.icon || 'help-circle';
        return `<span class="text-dark" title="置信度: ${suggestion.confidence}%">
                    <i data-lucide="${icon}" class="me-1"></i>${suggestion.category_name}
                </span>`;
    }

    async confirmCategory(merchantName, category, categoryName) {
        try {
            const response = await fetch('/merchant-categories/api/confirm-ai-suggestion', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ merchant_name: merchantName, category })
            });

            const result = await response.json();
            if (result.success) {
                showNotification(
                    `已将 ${result.data.merchant_name} 的分类更新为 ${categoryName}，共影响 ${result.data.updated_transactions} 笔交易`,
                    'success'
                );

                // 移除商户并更新统计
                const row = this.merchantsTable.getRows().find(r => r.getData().merchant_name === merchantName);
                if (row) row.delete();

                this.merchants = this.merchants.filter(m => m.merchant_name !== merchantName);
                this.updateStatistics();
                return true;
            } else {
                showNotification(`分类更新失败: ${result.error}`, 'error');
                return false;
            }
        } catch (error) {
            showNotification(`网络错误: ${error.message}`, 'error');
            return false;
        }
    }

    async loadMerchantsData() {
        try {
            const response = await fetch('/merchant-categories/api/uncategorized-merchants');
            const result = await response.json();

            if (result.success) {
                this.merchants = result.data;
                this.merchantsTable.setData(this.merchants);
                this.updateStatistics();

                // 重新渲染图标
                if (window.lucide) window.lucide.createIcons();
            } else {
                showNotification('加载商户数据失败', 'error');
            }
        } catch (error) {
            showNotification(`加载数据失败: ${error.message}`, 'error');
        }
    }

    updateStatistics() {
        const count = this.merchants.length;
        const badgeElement = document.getElementById('merchant-count-badge');
        if (badgeElement) {
            badgeElement.textContent = `(共 ${count} 个商户)`;
        }
    }
}

/**
 * 商户详情面板类
 * 管理右侧详情面板的显示和交互
 */
class MerchantDetailPanel {
    constructor() {
        this.container = document.getElementById('merchant-detail-panel');
        this.currentMerchant = null;
        this.cache = new Map();
    }

    async showMerchant(merchantData) {
        this.currentMerchant = merchantData;

        // 显示加载状态
        this.showLoadingState();

        try {
            // 检查缓存
            const cacheKey = merchantData.merchant_name;
            let detailData = this.cache.get(cacheKey);

            if (!detailData) {
                // 获取详细信息
                const params = new URLSearchParams({ name: merchantData.merchant_name });
                const response = await fetch(`/merchant-categories/api/merchant-detail?${params}`);
                const result = await response.json();

                if (result.success) {
                    detailData = result.data;
                    // 缓存5分钟
                    this.cache.set(cacheKey, detailData);
                    setTimeout(() => this.cache.delete(cacheKey), 5 * 60 * 1000);
                } else {
                    this.showErrorState(result.error);
                    return;
                }
            }

            // 显示详情内容
            this.showDetailContent(detailData);

        } catch (error) {
            this.showErrorState(error.message);
        }
    }

    hideMerchant() {
        this.currentMerchant = null;

        // 显示空状态
        this.container.innerHTML = `
            <div class="detail-empty-state">
                <div class="mb-3">
                    <i data-lucide="mouse-pointer-click" class="text-muted" style="width: 48px; height: 48px;"></i>
                </div>
                <h6 class="text-muted mb-2">选择商户查看详情</h6>
                <p class="text-muted small mb-0">
                    点击左侧表格中的任意商户行<br>
                    查看详细信息和快速分类
                </p>
            </div>
        `;

        // 重新渲染图标
        if (window.lucide) window.lucide.createIcons();
    }

    showLoadingState() {
        this.container.innerHTML = `
            <div class="detail-loading-state text-center py-5">
                <div class="spinner-border text-primary mb-3" role="status">
                    <span class="visually-hidden">加载中...</span>
                </div>
                <h6 class="text-muted mb-2">加载商户详情</h6>
                <p class="text-muted small mb-0">正在获取详细信息...</p>
            </div>
        `;
    }

    showErrorState(errorMessage) {
        this.container.innerHTML = `
            <div class="detail-error-state text-center py-5">
                <div class="mb-3">
                    <i data-lucide="alert-circle" class="text-danger" style="width: 48px; height: 48px;"></i>
                </div>
                <h6 class="text-danger mb-2">加载失败</h6>
                <p class="text-muted small mb-3">${errorMessage}</p>
                <button class="btn btn-sm btn-outline-primary" onclick="this.closest('.detail-error-state').parentElement.previousElementSibling.click()">
                    重试
                </button>
            </div>
        `;

        // 重新渲染图标
        if (window.lucide) window.lucide.createIcons();
    }

    showDetailContent(data) {
        const { merchant, ai_suggestion, recent_transactions, categories } = data;

        this.container.innerHTML = `
            <div class="detail-content active">
                <!-- 商户名称 -->
                <div class="mb-3">
                    <div class="text-center p-3 bg-light rounded">
                        <h5 class="mb-0 text-primary fw-bold" style="word-break: break-all;">
                            <i data-lucide="building" class="me-2"></i>${merchant.name}
                        </h5>
                    </div>
                </div>

                <!-- 商户统计信息 -->
                <div class="mb-4">
                    <h6 class="detail-section-title mb-3">
                        <i data-lucide="bar-chart" class="me-2"></i>统计信息
                    </h6>
                    <div class="row g-3">
                        <div class="col-6">
                            <div class="text-center p-3 detail-card">
                                <div class="text-muted small">交易次数</div>
                                <div class="fw-bold detail-value-primary fs-5">${merchant.transaction_count}</div>
                                <div class="text-muted small">笔</div>
                            </div>
                        </div>
                        <div class="col-6">
                            <div class="text-center p-3 detail-card">
                                <div class="text-muted small">总金额</div>
                                <div class="fw-bold ${merchant.total_amount >= 0 ? 'detail-value-success' : 'detail-value-danger'} fs-5">
                                    ¥${merchant.total_amount.toFixed(2)}
                                </div>
                                <div class="text-muted small">元</div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- 最近交易记录 (移动到第二位) -->
                <div class="mb-4">
                    <h6 class="detail-section-title mb-3">
                        <i data-lucide="clock" class="me-2"></i>最近交易记录
                    </h6>
                    <div class="transaction-list p-2" style="max-height: 200px; overflow-y: auto;">
                        ${recent_transactions.slice(0, 8).map(t => `
                            <div class="d-flex justify-content-between align-items-center py-2 border-bottom border-light">
                                <div class="small text-muted">${t.date}</div>
                                <div class="small ${t.amount >= 0 ? 'detail-value-success' : 'detail-value-danger'}">
                                    ¥${t.amount.toFixed(2)}
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>

                <!-- 选择分类 (融入AI置信度信息) -->
                <div>
                    <h6 class="detail-section-title mb-3">
                        <i data-lucide="tags" class="me-2"></i>选择分类
                    </h6>
                    <div class="p-3 ai-analysis-card">
                        <div class="row g-2">
                            ${categories.slice(0, 6).map(cat => {
                                const isAIRecommended = ai_suggestion.confidence > 0 && ai_suggestion.category_name === cat.name;
                                const confidenceText = isAIRecommended ? ` ${ai_suggestion.confidence}%` : '';
                                const buttonClass = isAIRecommended ? 'btn btn-sm w-100 ai-recommended-btn' : 'btn btn-sm w-100 category-btn-normal';

                                return `
                                    <div class="col-6">
                                        <button class="${buttonClass}"
                                                onclick="window.merchantCategoriesPage.confirmCategory('${merchant.name}', '${cat.code}', '${cat.name}')">
                                            <i data-lucide="${cat.icon}" class="me-1"></i>
                                            ${cat.name}${confidenceText}
                                        </button>
                                    </div>
                                `;
                            }).join('')}
                        </div>
                    </div>
                </div>
            </div>
        `;

        // 重新渲染图标
        if (window.lucide) window.lucide.createIcons();
    }
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    const page = new MerchantCategoriesPage();
    window.merchantCategoriesPage = page; // 全局引用供详情面板使用
    page.init();
});
