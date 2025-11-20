/**
 * 商户分类管理页面 - 基于数据源映射的新版本
 */

export default class MerchantCategoriesPage {
    constructor() {
        this.merchantsTable = null;
        this.detailsPanel = document.getElementById('merchant-detail-panel');
        this.categories = window.CATEGORIES || [];
    }

    async init() {
        try {
            await this.loadMerchantsData();
            this.initMerchantsTable();
            this.setupEventListeners();
            this.updateMerchantCount();
        } catch (error) {
            console.error('页面初始化失败:', error);
            this.showNotification('页面初始化失败', 'error');
        }
    }

    async loadMerchantsData() {
        try {
            const response = await fetch('/api/merchant-categories/uncategorized-merchants');
            const data = await response.json();

            if (!data.success) {
                throw new Error(data.error || '加载商户数据失败');
            }

            this.merchantsData = data.data;
            return this.merchantsData;
        } catch (error) {
            console.error('加载商户数据失败:', error);
            throw error;
        }
    }

    initMerchantsTable() {
        this.merchantsTable = new Tabulator("#merchants-table", {
            data: this.merchantsData || [],
            layout: "fitDataFill",
            pagination: "local",
            paginationSize: 20,
            placeholder: "暂无未映射分类的商户",
            selectableRows: 1, // 单选
            columns: [
                {
                    title: "商户名称",
                    field: "merchant_name",
                    headerFilter: "input",
                    headerFilterPlaceholder: "搜索商户...",
                    minWidth: 200,
                    formatter: function(cell) {
                        const value = cell.getValue();
                        return `<span class="fw-medium text-primary">${value}</span>`;
                    }
                },
                {
                    title: "原始分类",
                    field: "source_category",
                    headerFilter: true,
                    minWidth: 150,
                    formatter: function(cell) {
                        const value = cell.getValue();
                        return `<span class="badge bg-warning text-dark">${value || '无分类'}</span>`;
                    }
                },
                {
                    title: "交易次数",
                    field: "transaction_count",
                    sorter: "number",
                    width: 100,
                    formatter: function(cell) {
                        const value = cell.getValue();
                        return `<span class="fw-semibold">${value} 笔</span>`;
                    }
                },
                {
                    title: "总金额",
                    field: "total_amount",
                    sorter: "number",
                    width: 120,
                    formatter: function(cell) {
                        const value = cell.getValue();
                        return `¥${value.toFixed(2)}`;
                    }
                },
                {
                    title: "最近交易",
                    field: "latest_date",
                    sorter: "string",
                    width: 120,
                    formatter: function(cell) {
                        const value = cell.getValue();
                        return `<small class="text-muted">${value}</small>`;
                    }
                }
            ]
        });

        // 行点击事件
        this.merchantsTable.on("rowSelectionChanged", (data, rows) => {
            if (rows.length > 0) {
                const merchantData = rows[0].getData();
                this.showMerchantDetails(merchantData);
            } else {
                this.hideMerchantDetails();
            }
        });
    }

    async showMerchantDetails(merchant) {
        try {
            const params = new URLSearchParams();
            params.append('name', merchant.merchant_name);

            const response = await fetch(`/api/merchant-categories/merchant-detail?${params}`);
            const data = await response.json();

            if (!data.success) {
                throw new Error(data.error || '获取商户详情失败');
            }

            this.renderMerchantDetails(data.data, merchant);
        } catch (error) {
            console.error('获取商户详情失败:', error);
            this.showNotification('获取商户详情失败: ' + error.message, 'error');
        }
    }

    renderMerchantDetails(data, merchant) {
        const merchantInfo = data.merchant;
        const categoryGroups = data.category_groups;

        let html = `
            <div class="merchant-details">
                <!-- 商户基本信息 -->
                <div class="mb-4">
                    <h6 class="mb-3 text-primary">
                        <i class="fas fa-store me-2"></i>${merchantInfo.name}
                    </h6>
                    <div class="row small text-muted">
                        <div class="col-6">
                            <div>总交易: <span class="fw-semibold">${merchantInfo.transaction_count} 笔</span></div>
                            <div>总收入: <span class="text-success fw-semibold">${merchantInfo.income_count} 笔</span></div>
                        </div>
                        <div class="col-6">
                            <div>总支出: <span class="text-danger fw-semibold">${merchantInfo.expense_count} 笔</span></div>
                            <div>总金额: <span class="fw-semibold">¥${merchantInfo.total_amount.toFixed(2)}</span></div>
                        </div>
                    </div>
                </div>
        `;

        // 分类分组信息
        html += '<div class="category-groups">';
        if (categoryGroups.length > 0) {
            html += '<h6 class="mb-3">分类详情</h6>';
            categoryGroups.forEach((group, index) => {
                const mappedText = group.is_mapped ?
                    `<span class="badge bg-success">${this.getCategoryName(group.mapped_category)}</span>` :
                    '<span class="badge bg-warning">未映射</span>';

                html += `
                    <div class="category-group mb-3 p-3 border rounded">
                        <div class="d-flex justify-content-between align-items-start mb-2">
                            <div>
                                <div class="fw-medium">${group.source_category}</div>
                                <small class="text-muted">交易 ${group.transaction_count} 笔，总金额 ¥${group.total_amount.toFixed(2)}</small>
                            </div>
                            <div>
                                ${mappedText}
                            </div>
                        </div>
                `;

                if (!group.is_mapped) {
                    html += `
                        <div class="mt-2">
                            <div class="btn-group btn-group-sm">
                                ${this.renderCategoryButtons(merchantInfo.name, group.source_category)}
                            </div>
                        </div>
                    `;
                }

                // 最近交易
                if (group.recent_transactions && group.recent_transactions.length > 0) {
                    html += `
                        <div class="mt-3">
                            <small class="text-muted">最近交易:</small>
                            <div class="mt-1">
                                ${group.recent_transactions.slice(0, 3).map(tx => `
                                    <div class="small text-muted">
                                        ${tx.date} · ¥${tx.amount.toFixed(2)} · ${tx.description.substring(0, 20)}...
                                    </div>
                                `).join('')}
                            </div>
                        </div>
                    `;
                }

                html += '</div>';
            });
        } else {
            html += '<p class="text-muted">暂无交易记录</p>';
        }

        html += '</div></div>';

        this.detailsPanel.innerHTML = html;
    }

    renderCategoryButtons(merchantName, sourceCategory) {
        const favoriteCategories = ['food', 'shopping', 'transport', 'entertainment'];
        const buttons = [];

        favoriteCategories.forEach(categoryCode => {
            const category = this.categories.find(cat => cat.code === categoryCode);
            if (category) {
                buttons.push(`
                    <button class="btn btn-outline-primary btn-sm"
                            onclick="merchantPage.quickMap('${merchantName}', '${sourceCategory}', '${categoryCode}')"
                            title="${category.name}">
                        ${category.icon ? `<i class="fas fa-${category.icon}"></i>` : ''}
                        ${category.name}
                    </button>
                `);
            }
        });

        buttons.push(`
            <button class="btn btn-outline-secondary btn-sm dropdown-toggle"
                    data-bs-toggle="dropdown">
                更多
            </button>
            <ul class="dropdown-menu">
                ${this.categories.map(cat => `
                    <li>
                        <a class="dropdown-item" href="#"
                           onclick="merchantPage.quickMap('${merchantName}', '${sourceCategory}', '${cat.code}')">
                            ${cat.icon ? `<i class="fas fa-${cat.icon} me-2"></i>` : ''}
                            ${cat.name}
                        </a>
                    </li>
                `).join('')}
            </ul>
        `);

        return buttons.join('');
    }

    async quickMap(merchantName, sourceCategory, targetCategory) {
        try {
            const response = await fetch('/api/merchant-categories/quick-mapping', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    merchant_name: merchantName,
                    source_category: sourceCategory,
                    category: targetCategory
                })
            });

            const result = await response.json();
            if (result.success) {
                this.showNotification(result.data.message, 'success');

                // 刷新商户列表和详情
                await this.loadMerchantsData();
                this.merchantsTable.replaceData(this.merchantsData);

                // 重新显示当前商户详情
                const selectedRows = this.merchantsTable.getSelectedRows();
                if (selectedRows.length > 0) {
                    const merchantData = selectedRows[0].getData();
                    this.showMerchantDetails(merchantData);
                }
            } else {
                this.showNotification('映射失败: ' + result.error, 'error');
            }
        } catch (error) {
            console.error('快速映射失败:', error);
            this.showNotification('映射失败', 'error');
        }
    }

    getCategoryName(categoryCode) {
        const category = this.categories.find(cat => cat.code === categoryCode);
        return category ? category.name : categoryCode;
    }

    getCategoryIcon(categoryCode) {
        const category = this.categories.find(cat => cat.code === categoryCode);
        return category ? category.icon : '';
    }

    hideMerchantDetails() {
        this.detailsPanel.innerHTML = `
            <div class="detail-empty-state text-center py-5">
                <div class="mb-3">
                    <i class="fas fa-mouse-pointer fa-2x text-muted"></i>
                </div>
                <h6 class="text-muted mb-2">选择商户查看详情</h6>
                <p class="text-muted small mb-0">点击左侧表格中的任意商户行<br>查看详细信息和快速分类</p>
            </div>
        `;
    }

    updateMerchantCount() {
        const badge = document.getElementById('merchant-count-badge');
        if (badge) {
            const count = this.merchantsData ? this.merchantsData.length : 0;
            badge.textContent = `(共 ${count} 个商户)`;
        }
    }

    setupEventListeners() {
        // 导出按钮（暂时给个提示）
        document.querySelector('[onclick*="导出"]')?.addEventListener('click', () => {
            this.showNotification('导出功能开发中...', 'info');
        });
    }

    showNotification(message, type = 'info') {
        // 使用全局通知函数（如果存在）
        if (window.showNotification) {
            window.showNotification(message, type);
        } else {
            console.log(`[${type.toUpperCase()}] ${message}`);
        }
    }
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', () => {
    window.merchantPage = new MerchantCategoriesPage();
    window.merchantPage.init();
});