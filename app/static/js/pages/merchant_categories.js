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
        this.loadPageData();
        
        // 初始化表格
        this.initMerchantsTable();
        
        // 加载商户数据
        this.loadMerchantsData();
    }

    loadPageData() {
        const pageDataElement = document.getElementById('page-data');
        if (pageDataElement) {
            const initialData = JSON.parse(pageDataElement.textContent);
            this.categoriesConfig = initialData.categories_config || {};
            
            // 设置全局变量供工具函数使用
            window.categoriesConfig = this.categoriesConfig;
        }
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
                    title: "分类",
                    field: "category",
                    width: 150,
                    editor: "list",
                    editorParams: this.createCategoryEditorParams(),
                    formatter: this.createCategoryFormatter(),
                    cellEdited: (cell) => this.handleCategoryEdit(cell)
                }
            ]
        });
    }

    createCategoryEditorParams() {
        const options = {};
        if (this.categoriesConfig && Object.keys(this.categoriesConfig).length > 0) {
            for (const [code, info] of Object.entries(this.categoriesConfig)) {
                if (code !== 'uncategorized') { // 排除未分类选项
                    options[code] = info.name;
                }
            }
        }
        return {
            values: options,
            clearable: false,
            placeholder: "选择分类"
        };
    }

    createCategoryFormatter() {
        return (cell) => {
            const categoryCode = cell.getValue();
            const categoryInfo = this.categoriesConfig[categoryCode];
            
            if (categoryInfo) {
                return `<span class="category-badge d-flex align-items-center">
                    <i data-lucide="${categoryInfo.icon}" class="text-${categoryInfo.color}" style="width: 1rem; height: 1rem;"></i>
                    <span class="ms-2 small">${categoryInfo.name}</span>
                </span>`;
            }
            return categoryCode;
        };
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
