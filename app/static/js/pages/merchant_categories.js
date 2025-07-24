/**
 * 商户分类管理页面的JavaScript逻辑
 * 使用Tabulator表格库实现商户列表展示和分类编辑功能
 */

import BasePage from '../common/BasePage.js';
import { showNotification } from '../common/notifications.js';
import { getTabulatorCommonConfig, getTabulatorFormatters } from '../common/utils.js';

export default class MerchantCategoriesPage extends BasePage {
    constructor() {
        super();
        this.merchants = [];
        this.merchantsTable = null;
        this.categoriesConfig = {};
    }

    init() {
        // 加载页面数据
        const pageDataElement = document.getElementById('page-data');
        if (pageDataElement) {
            const initialData = JSON.parse(pageDataElement.textContent);
            this.categoriesConfig = initialData.categories_config || {};
        }

        // 初始化表格
        this.initMerchantsTable();

        // 设置事件委托
        this.setupEventDelegation();

        // 加载商户数据
        this.loadMerchantsData();
    }

    initMerchantsTable() {
        const commonConfig = getTabulatorCommonConfig();
        const formatters = getTabulatorFormatters();

        this.merchantsTable = new Tabulator("#merchants-table", {
            ...commonConfig,
            data: this.merchants,
            paginationSize: 50,
            placeholder: "暂无未分类商户",
            columns: [
                {
                    title: "商户名称",
                    field: "merchant_name",
                    width: 200,
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
                    width: 100,
                    sorter: "number",
                    responsive: 2,
                    formatter: function(cell) {
                        return `<span class="fw-semibold">${cell.getValue()} 笔</span>`;
                    }
                },
                {
                    title: "总金额",
                    field: "total_amount",
                    width: 120,
                    sorter: "number",
                    responsive: 1,
                    formatter: formatters.currency
                },
                {
                    title: "最近交易",
                    field: "latest_date",
                    width: 120,
                    sorter: "date",
                    responsive: 3,
                    formatter: formatters.dateFormat
                },
                {
                    title: "AI建议",
                    field: "ai_suggestion",
                    width: 120,
                    responsive: 2,
                    formatter: (cell) => this.formatAISuggestion(cell),
                    cellClick: (_, cell) => this.showMerchantDetailModal(cell.getRow().getData())
                },
                {
                    title: "操作",
                    field: "actions",
                    width: 80,
                    responsive: 1,
                    formatter: () => `<button class="btn btn-sm btn-success confirm-btn">确认</button>`
                }
            ]
        });
    }

    setupEventDelegation() {
        // 使用事件委托处理确认按钮点击
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('confirm-btn')) {
                const row = e.target.closest('.tabulator-row');
                if (row) {
                    const merchantData = this.merchantsTable.getRow(row).getData();
                    this.confirmAISuggestion(merchantData.id);
                }
            }
        });
    }



    formatAISuggestion(cell) {
        const suggestion = cell.getValue();
        if (!suggestion) return '<span class="badge bg-secondary ai-suggestion-badge"><i data-lucide="help-circle"></i> 未知</span>';

        const { confidence, category_name, category } = suggestion;

        // 获取分类颜色和图标
        const categoryInfo = this.categoriesConfig[category];
        const colorClass = categoryInfo ? categoryInfo.color : 'secondary';
        const iconName = categoryInfo ? categoryInfo.icon : 'help-circle';

        return `<span class="badge bg-${colorClass} ai-suggestion-badge" title="置信度: ${confidence}%">
                    <i data-lucide="${iconName}"></i> ${category_name}
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

    async confirmAISuggestion(merchantId) {
        const merchant = this.merchants.find(m => m.id === merchantId);
        if (!merchant?.ai_suggestion) {
            showNotification('无法找到商户信息', 'error');
            return;
        }

        await this.confirmCategory(
            merchant.merchant_name,
            merchant.ai_suggestion.category,
            merchant.ai_suggestion.category_name
        );
    }

    async showMerchantDetailModal(merchant) {
        try {
            // 获取商户详细信息
            const response = await fetch(`/merchant-categories/api/merchant-detail/${encodeURIComponent(merchant.merchant_name)}`);
            const result = await response.json();

            if (result.success) {
                this.createMerchantDetailModal(result.data);
            } else {
                showNotification(`获取商户详情失败: ${result.error}`, 'error');
            }

        } catch (error) {
            showNotification(`网络错误: ${error.message}`, 'error');
        }
    }

    createMerchantDetailModal(data) {
        // 优化的弹窗HTML
        const modalHtml = `
            <div class="modal fade" id="merchantDetailModal" tabindex="-1">
                <div class="modal-dialog">
                    <div class="modal-content">
                        <div class="modal-header bg-light">
                            <h5 class="modal-title d-flex align-items-center">
                                <i class="bi bi-shop me-2 text-primary"></i>
                                商户分类 - ${data.merchant.name}
                            </h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <!-- 基本信息卡片 -->
                            <div class="card mb-3">
                                <div class="card-body py-2">
                                    <div class="row text-center">
                                        <div class="col-6">
                                            <div class="text-muted small">交易次数</div>
                                            <div class="fw-bold text-primary">${data.merchant.transaction_count}笔</div>
                                        </div>
                                        <div class="col-6">
                                            <div class="text-muted small">总金额</div>
                                            <div class="fw-bold ${data.merchant.total_amount >= 0 ? 'text-success' : 'text-danger'}">
                                                ¥${data.merchant.total_amount.toFixed(2)}
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <!-- 最近交易 -->
                            <div class="mb-3">
                                <h6 class="text-muted mb-2">
                                    <i class="bi bi-clock-history me-1"></i>最近交易
                                </h6>
                                <div class="bg-light rounded p-2">
                                    ${data.recent_transactions.slice(0, 3).map(t =>
                                        `<div class="d-flex justify-content-between align-items-center py-1">
                                            <span class="small text-muted">${t.date}</span>
                                            <span class="small ${t.amount >= 0 ? 'text-success' : 'text-danger'} fw-bold">
                                                ¥${t.amount.toFixed(2)}
                                            </span>
                                            <span class="small text-truncate ms-2" style="max-width: 120px;" title="${t.description}">
                                                ${t.description}
                                            </span>
                                        </div>`
                                    ).join('')}
                                </div>
                            </div>

                            <!-- 分类选择 -->
                            <div>
                                <h6 class="text-muted mb-2">
                                    <i class="bi bi-tags me-1"></i>选择分类
                                </h6>
                                <select class="form-select" id="categorySelect">
                                    ${data.categories.map(cat => `
                                        <option value="${cat.code}" ${cat.code === data.ai_suggestion.category ? 'selected' : ''}>
                                            ${cat.name}${cat.code === data.ai_suggestion.category ? ' (AI推荐)' : ''}
                                        </option>
                                    `).join('')}
                                </select>
                            </div>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-outline-secondary" data-bs-dismiss="modal">取消</button>
                            <button type="button" class="btn btn-primary" id="confirmCategoryBtn">
                                <i class="bi bi-check-lg me-1"></i>确认分类
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // 移除已存在的弹窗并添加新弹窗
        document.getElementById('merchantDetailModal')?.remove();
        document.body.insertAdjacentHTML('beforeend', modalHtml);

        // 简化的交互初始化
        this.initModalInteractions(data);
        new bootstrap.Modal(document.getElementById('merchantDetailModal')).show();
    }

    initModalInteractions(data) {
        const modal = document.getElementById('merchantDetailModal');

        modal.querySelector('#confirmCategoryBtn').addEventListener('click', async () => {
            const selectedCategory = modal.querySelector('#categorySelect').value;
            if (!selectedCategory) {
                showNotification('请选择一个分类', 'warning');
                return;
            }

            const categoryInfo = data.categories.find(c => c.code === selectedCategory);
            const success = await this.confirmCategory(data.merchant.name, selectedCategory, categoryInfo.name);

            if (success) {
                bootstrap.Modal.getInstance(modal).hide();
            }
        });
    }

    async handleCategoryEdit(cell) {
        const rowData = cell.getRow().getData();
        const newCategory = cell.getValue();
        const merchantName = rowData.merchant_name;

        try {
            // 显示加载状态
            cell.getElement().style.opacity = '0.5';

            const response = await fetch(`/merchant-categories/api/merchant/${encodeURIComponent(merchantName)}/category`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    category: newCategory
                })
            });

            const result = await response.json();

            if (result.success) {
                const data = result.data;
                const categoryName = this.categoriesConfig[newCategory]?.name || newCategory;
                
                showNotification(
                    `已将 ${data.merchant_name} 的分类更新为 ${categoryName}，共影响 ${data.updated_transactions} 笔交易`,
                    'success'
                );

                // 从表格中移除已分类的商户
                cell.getRow().delete();

                // 更新商户数组和统计信息
                this.merchants = this.merchants.filter(m => m.merchant_name !== data.merchant_name);
                this.updateStatistics();

            } else {
                // 更新失败，恢复原值
                cell.restoreOldValue();
                showNotification(`更新失败: ${result.error}`, 'error');
            }

        } catch (error) {
            // 网络错误，恢复原值
            cell.restoreOldValue();
            showNotification(`网络错误: ${error.message}`, 'error');
        } finally {
            // 恢复显示状态
            cell.getElement().style.opacity = '1';
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
                setTimeout(() => {
                    if (window.lucide) {
                        window.lucide.createIcons();
                    }
                }, 100);
            } else {
                showNotification('加载商户数据失败', 'error');
            }
        } catch (error) {
            showNotification(`加载数据失败: ${error.message}`, 'error');
        }
    }

    updateStatistics() {
        const count = this.merchants.length;

        // 更新统计卡片（如果存在）
        const countElement = document.getElementById('uncategorized-count');
        if (countElement) {
            countElement.textContent = count;
        }

        // 更新表格标题中的统计信息
        const badgeElement = document.getElementById('merchant-count-badge');
        if (badgeElement) {
            badgeElement.textContent = `(共 ${count} 个商户)`;
        }
    }
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    const page = new MerchantCategoriesPage();
    page.init();
});
