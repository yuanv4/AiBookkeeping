/**
 * 交易记录页面的JavaScript逻辑
 * 使用Tabulator表格库实现筛选、排序和表格显示功能
 */

import BasePage from '../common/BasePage.js';
import {
    createTransactionsTable,
    updateTransactionsSummary,
    TableRegistry
} from '../common/utils.js';

export default class TransactionsPage extends BasePage {
    constructor() {
        super();
        this.transactions = [];
        this.totalCount = 0;
        this.transactionsTable = null;
        this.summaryElements = {};
        this.categoriesConfig = {};
    }

    init() {
        // 加载数据
        this.loadPageData();

        // 初始化汇总元素引用
        this.initSummaryElements();

        // 初始化表格组件
        this.initTransactionsTable();

        // 初始化导出功能
        this.initExportButtons();
    }

    initSummaryElements() {
        // 获取汇总信息元素的引用
        this.summaryElements = {
            totalIncome: document.getElementById('summary-income-amount'),
            totalExpense: document.getElementById('summary-expense-amount'),
            incomeCount: document.getElementById('summary-income-count'),
            expenseCount: document.getElementById('summary-expense-count'),
            latestBalance: document.getElementById('summary-latest-balance')
        };
    }

    initTransactionsTable() {
        // 使用工具函数创建Tabulator表格，传递分类配置
        this.transactionsTable = createTransactionsTable('transactions-table', this.transactions, {
            // 数据变化时的回调
            dataFiltered: (filters, rows) => {
                this.updateSummary();
            },
            dataLoaded: (data) => {
                this.updateSummary();
            },
            // 行点击事件
            rowClick: (e, row) => {
                console.log('点击了交易记录:', row.getData());
            }
        }, this.categoriesConfig);
    }

    initExportButtons() {
        // CSV导出
        const csvBtn = document.getElementById('export-csv-btn');
        if (csvBtn) {
            csvBtn.addEventListener('click', () => {
                this.exportData('csv');
            });
        }

        // Excel导出
        const excelBtn = document.getElementById('export-excel-btn');
        if (excelBtn) {
            excelBtn.addEventListener('click', () => {
                this.exportData('xlsx');
            });
        }
    }

    exportData(format) {
        if (!this.transactionsTable) return;

        const filename = `交易记录_${new Date().toISOString().split('T')[0]}`;

        try {
            this.transactionsTable.download(format, `${filename}.${format}`, {
                sheetName: "交易记录"
            });
        } catch (error) {
            console.error('导出失败:', error);
            // 可以显示错误提示
        }
    }

    updateSummary() {
        // 使用工具函数更新汇总信息
        updateTransactionsSummary(this.transactionsTable, this.summaryElements);
    }

    loadPageData() {
        // 从统一数据源加载数据
        const pageDataElement = document.getElementById('page-data');
        if (pageDataElement) {
            try {
                const initialDataJson = pageDataElement.getAttribute('data-initial-data');
                const initialData = JSON.parse(initialDataJson || '{}');

                // 加载交易数据并转换为Tabulator格式
                this.transactions = this.transformTransactionData(initialData.transactions || []);
                this.totalCount = initialData.total_count || 0;

                // 加载分类配置
                this.categoriesConfig = initialData.categories_config || {};

                // 将分类配置设置为全局变量，供utils.js中的函数使用
                window.categoriesConfig = this.categoriesConfig;

            } catch (error) {
                console.error('解析页面数据时出错:', error);
                this.transactions = [];
                this.totalCount = 0;
            }
        }
    }

    transformTransactionData(rawTransactions) {
        // 将后端数据转换为Tabulator需要的格式
        return rawTransactions.map(transaction => ({
            id: transaction.id,
            date: transaction.date,
            category: transaction.category || 'other',
            account: this.formatAccountDisplay(transaction),
            counterparty: transaction.counterparty || '',
            description: transaction.description || '',
            amount: parseFloat(transaction.amount) || 0,
            balance: parseFloat(transaction.balance_after) || 0,
            // 保留原始数据以备后用
            _raw: transaction
        }));
    }

    formatAccountDisplay(transaction) {
        // 构建账户显示文本：户名-卡号
        if (transaction.name && transaction.account_number) {
            return `${transaction.name}-${transaction.account_number}`;
        }
        return transaction.name || transaction.account_number || '';
    }

    // 刷新表格数据（用于后续的数据更新）
    refreshTableData(newTransactions) {
        if (this.transactionsTable) {
            const transformedData = this.transformTransactionData(newTransactions);
            this.transactionsTable.setData(transformedData);
            this.updateSummary();
        }
    }

    // 销毁页面时清理资源
    destroy() {
        if (this.transactionsTable) {
            TableRegistry.destroy('transactions-table');
            this.transactionsTable = null;
        }
    }
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    const transactionsPage = new TransactionsPage();
    transactionsPage.init();
});
