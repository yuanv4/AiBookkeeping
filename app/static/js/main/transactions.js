/**
 * 交易记录页面入口脚本
 */

import TransactionsPage from '../pages/transactions.js';

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    const transactionsPage = new TransactionsPage();
    transactionsPage.init();
}); 