/**
 * 仪表盘页面入口脚本
 */

import FinancialDashboard from '../pages/dashboard.js';

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    const dashboard = new FinancialDashboard();
    dashboard.init();
}); 