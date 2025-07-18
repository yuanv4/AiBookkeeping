/**
 * 交易记录页面的JavaScript逻辑
 * 使用TransactionsTable组件实现筛选、排序和表格显示功能
 */

import BasePage from '../common/BasePage.js';

export default class TransactionsPage extends BasePage {
    constructor() {
        super();
        this.transactions = [];
        this.totalCount = 0;
        this.transactionsTable = null;
    }

    init() {
        // 加载数据
        this.loadPageData();

        // 初始化表格组件
        this.initTransactionsTable();
    }

    initTransactionsTable() {
        // 创建TransactionsTable实例
        this.transactionsTable = new TransactionsTable('transactions-table', {
            data: this.transactions,
            onDataChange: (filteredData) => {
                // 当数据变化时的回调
                console.log('Filtered data changed:', filteredData.length);
            }
        });
    }

    loadPageData() {
        // 从统一数据源加载数据
        const pageDataElement = document.getElementById('page-data');
        if (pageDataElement) {
            try {
                const initialDataJson = pageDataElement.getAttribute('data-initial-data');
                const initialData = JSON.parse(initialDataJson || '{}');

                // 加载交易数据
                this.transactions = initialData.transactions || [];
                this.totalCount = initialData.total_count || 0;

            } catch (error) {
                console.error('解析页面数据时出错:', error);
                this.transactions = [];
                this.totalCount = 0;
            }
        }
    }
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    const transactionsPage = new TransactionsPage();
    transactionsPage.init();
});
