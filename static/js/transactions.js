/**
 * 交易记录页面JavaScript
 * 提供交易记录的过滤、分页和显示功能
 */

// 全局变量
let transactions = [];
let totalItems = 0;
let currentPage = 1;
let itemsPerPage = 20;
let totalPages = 1;

document.addEventListener('DOMContentLoaded', function() {
    console.log('transactions.js 脚本已加载');
    
    // 从页面检查数据元素是否存在
    const transactionsDataElement = document.getElementById('transactions-data');
    if (transactionsDataElement) {
        console.log('找到transactions-data元素');
        console.log('data-transactions属性值：', transactionsDataElement.getAttribute('data-transactions'));
    } else {
        console.error('找不到transactions-data元素');
    }
    
    // 初始化数据
    initializeData();
    
    // 绑定事件
    document.getElementById('apply-filters').addEventListener('click', applyFilters);
    document.getElementById('reset-filters').addEventListener('click', resetFilters);
    document.getElementById('reset-all').addEventListener('click', resetFilters);
    document.getElementById('download-csv').addEventListener('click', downloadCSV);
});

/**
 * 初始化数据
 */
function initializeData() {
    // 从页面获取数据
    totalItems = parseInt(document.getElementById('total-count').textContent) || 0;
    currentPage = parseInt(document.getElementById('current-page-data').getAttribute('data-page')) || 1;
    itemsPerPage = parseInt(document.getElementById('current-page-data').getAttribute('data-limit')) || 20;
    totalPages = parseInt(document.getElementById('current-page-data').getAttribute('data-pages')) || 1;
    
    try {
        // 尝试解析交易数据
        console.log("正在解析交易数据");
        const transactionsJson = document.getElementById('transactions-data').getAttribute('data-transactions');
        
        if (transactionsJson) {
            // 解析JSON数据
            transactions = JSON.parse(transactionsJson);
            console.log(`成功解析${transactions.length}条交易记录`);
            
            // 检查第一条记录
            if (transactions.length > 0) {
                console.log("第一条记录示例:", transactions[0]);
            }
            
            // 填充银行/卡号筛选器选项
            populateBankAccountOptions();
            
            // 初始化表格
            renderTable();
        } else {
            console.error("未找到交易数据");
            transactions = [];
        }
    } catch (error) {
        console.error("解析交易数据时出错:", error);
        // 解析失败时使用空数组
        transactions = [];
    }
}

/**
 * 填充银行/卡号组合选项
 */
function populateBankAccountOptions() {
    // 从交易记录中提取银行和账号
    const bankAccounts = new Map();
    
    // 获取URL参数中的已选银行和账号
    const urlParams = new URLSearchParams(window.location.search);
    const selectedBank = urlParams.get('bank') || '';
    const selectedAccount = urlParams.get('account_number') || '';
    
    // 组合筛选的值（格式：bank:account）
    let selectedValue = '';
    if (selectedBank) {
        selectedValue += selectedBank;
    }
    selectedValue += ':';
    if (selectedAccount) {
        selectedValue += selectedAccount;
    }
    
    // 为每条交易记录创建银行:账号组合
    transactions.forEach(transaction => {
        const bank = transaction['银行'] || '';
        const accountNumber = transaction['账号'] || '';
        
        if (bank && accountNumber) {
            // 只保留同时有银行和卡号的选项
            const optionText = `${bank} - ${accountNumber}`;
            const optionValue = `${bank}:${accountNumber}`;
            
            // 添加到Map中（使用Map确保唯一性）
            bankAccounts.set(optionValue, optionText);
        }
    });
    
    // 填充下拉菜单
    const bankAccountSelect = document.getElementById('bankAccount');
    bankAccountSelect.innerHTML = '';
    
    // 将选项添加到下拉菜单
    Array.from(bankAccounts.entries())
        .sort((a, b) => a[1].localeCompare(b[1])) // 按显示文本排序
        .forEach(([value, text]) => {
            const option = document.createElement('option');
            option.value = value;
            option.textContent = text;
            if (value === selectedValue) {
                option.selected = true;
            }
            bankAccountSelect.appendChild(option);
        });
        
    // 如果没有选项被选中，默认选中第一个选项
    if (bankAccountSelect.selectedIndex === -1 && bankAccountSelect.options.length > 0) {
        bankAccountSelect.selectedIndex = 0;
    }
}

/**
 * 应用筛选条件
 */
function applyFilters() {
    // 获取筛选条件
    const category = document.getElementById('category').value;
    const bankAccount = document.getElementById('bankAccount').value;
    const search = document.getElementById('search').value.toLowerCase();
    
    // 解析银行和卡号（格式：bank:account）
    let bank = '';
    let account = '';
    
    if (bankAccount) {
        const parts = bankAccount.split(':');
        if (parts.length === 2) {
            bank = parts[0];
            account = parts[1];
        }
    }
    
    // 构建查询参数
    let queryParams = new URLSearchParams();
    queryParams.set('page', '1'); // 重置到第一页
    
    if (category) queryParams.set('type', category);
    
    if (search) queryParams.set('counterparty', search);
    
    // 银行参数 - 现在总是添加，因为总会有一个选中的银行卡号组合
    if (bank) queryParams.set('bank', bank);
    
    // 账号参数 - 现在总是添加，因为总会有一个选中的银行卡号组合
    if (account) queryParams.set('account_number', account);
    
    // 重新加载页面
    window.location.href = window.location.pathname + '?' + queryParams.toString();
}

/**
 * 重置筛选条件
 */
function resetFilters() {
    // 获取当前选中的银行/卡号选项
    const bankAccount = document.getElementById('bankAccount');
    if (bankAccount.options.length > 0) {
        // 设置为第一个选项
        bankAccount.selectedIndex = 0;
        
        // 获取选中选项的值
        const selectedOption = bankAccount.options[0].value;
        
        // 解析银行和卡号
        let bank = '';
        let account = '';
        
        if (selectedOption) {
            const parts = selectedOption.split(':');
            if (parts.length === 2) {
                bank = parts[0];
                account = parts[1];
            }
        }
        
        // 构建查询参数，只包含必要的银行和卡号参数
        let queryParams = new URLSearchParams();
        if (bank) queryParams.set('bank', bank);
        if (account) queryParams.set('account_number', account);
        
        // 重新加载页面
        window.location.href = window.location.pathname + '?' + queryParams.toString();
    } else {
        // 如果没有任何选项，简单地重新加载页面
        window.location.href = window.location.pathname;
    }
}

/**
 * 渲染表格
 */
function renderTable() {
    console.log("开始渲染表格，数据条数:", transactions.length);
    
    // 更新计数
    document.getElementById('filtered-count').textContent = transactions.length;
    document.getElementById('total-count').textContent = totalItems;
    
    // 显示/隐藏无数据提示
    if (transactions.length === 0) {
        document.getElementById('transactions-table').style.display = 'none';
        document.getElementById('pagination-container').style.display = 'none';
        document.getElementById('no-data').style.display = 'block';
        return;
    } else {
        document.getElementById('transactions-table').style.display = 'table';
        document.getElementById('pagination-container').style.display = 'block';
        document.getElementById('no-data').style.display = 'none';
    }
    
    // 渲染表格内容
    const tbody = document.getElementById('transactions-body');
    tbody.innerHTML = '';
    
    // 计算序号起始值
    const startIndex = (currentPage - 1) * itemsPerPage;
    
    transactions.forEach((transaction, index) => {
        try {
            const tr = document.createElement('tr');
            
            // 获取日期，确保日期存在
            let formattedDate = transaction['交易日期'] || '';
            
            // 格式化金额，确保金额是数字，否则默认为0
            let amount = 0;
            try {
                amount = parseFloat(transaction['交易金额']);
                if (isNaN(amount)) amount = 0;
            } catch (e) {
                console.error("金额解析错误:", e);
                amount = 0;
            }
            const formattedAmount = amount.toFixed(2);
            const amountClass = amount > 0 ? 'positive' : (amount < 0 ? 'negative' : '');
            
            // 格式化余额，确保余额是数字，否则默认为0
            let balance = 0;
            try {
                balance = parseFloat(transaction['账户余额']);
                if (isNaN(balance)) balance = 0;
            } catch (e) {
                console.error("余额解析错误:", e);
                balance = 0;
            }
            const formattedBalance = balance.toFixed(2);
            
            // 确定交易类型标签颜色
            let typeClass = 'bg-primary';
            let transactionType = transaction['交易类型'] || '未知';
            if (transactionType.includes('退款')) {
                typeClass = 'bg-success';
            } else if (transactionType.includes('转账')) {
                typeClass = 'bg-info';
            } else if (transactionType.includes('收入') || transactionType.includes('收款')) {
                typeClass = 'bg-success';
            }
            
            // 设置交易对象
            const transactionObject = transaction['交易对象'] || '';
            
            // 获取银行和账号信息
            const bank = transaction['银行'] || '未知银行';
            const accountNumber = transaction['账号'] || '未知账号';
            
            tr.innerHTML = `
                <td>${startIndex + index + 1}</td>
                <td>${formattedDate}</td>
                <td><span class="badge ${typeClass}">${transactionType}</span></td>
                <td>${transactionObject}</td>
                <td class="${amountClass}">${amount > 0 ? '+' : ''}${formattedAmount}</td>
                <td>${formattedBalance}</td>
                <td><span class="badge bg-light text-dark">${accountNumber}</span></td>
                <td><span class="badge bg-secondary">${bank}</span></td>
            `;
            
            tbody.appendChild(tr);
        } catch (error) {
            console.error("渲染表格行时出错:", error, "数据:", transaction);
        }
    });
    
    // 渲染分页控件
    renderPagination();
}

/**
 * 渲染分页控件
 */
function renderPagination() {
    const pagination = document.getElementById('pagination');
    pagination.innerHTML = '';
    
    // 如果只有一页，不显示分页
    if (totalPages <= 1) {
        document.getElementById('pagination-container').style.display = 'none';
        return;
    }
    
    document.getElementById('pagination-container').style.display = 'block';
    
    // 上一页按钮
    const prevLi = document.createElement('li');
    prevLi.className = `page-item ${currentPage === 1 ? 'disabled' : ''}`;
    prevLi.innerHTML = `
        <a class="page-link" href="#" aria-label="上一页">
            <i class="material-icons-round">chevron_left</i>
        </a>
    `;
    if (currentPage > 1) {
        prevLi.addEventListener('click', () => goToPage(currentPage - 1));
    }
    pagination.appendChild(prevLi);
    
    // 计算显示的页码范围
    let startPage = Math.max(1, currentPage - 2);
    let endPage = Math.min(totalPages, currentPage + 2);
    
    // 调整，确保显示5个页码
    if (endPage - startPage < 4) {
        if (startPage === 1) {
            endPage = Math.min(5, totalPages);
        } else if (endPage === totalPages) {
            startPage = Math.max(1, totalPages - 4);
        }
    }
    
    // 第一页
    if (startPage > 1) {
        const firstLi = document.createElement('li');
        firstLi.className = 'page-item';
        firstLi.innerHTML = `<a class="page-link" href="#">1</a>`;
        firstLi.addEventListener('click', () => goToPage(1));
        pagination.appendChild(firstLi);
        
        // 省略号
        if (startPage > 2) {
            const ellipsisLi = document.createElement('li');
            ellipsisLi.className = 'page-item disabled';
            ellipsisLi.innerHTML = `<span class="page-link">...</span>`;
            pagination.appendChild(ellipsisLi);
        }
    }
    
    // 页码
    for (let i = startPage; i <= endPage; i++) {
        const pageLi = document.createElement('li');
        pageLi.className = `page-item ${i === currentPage ? 'active' : ''}`;
        pageLi.innerHTML = `<a class="page-link" href="#">${i}</a>`;
        if (i !== currentPage) {
            pageLi.addEventListener('click', () => goToPage(i));
        }
        pagination.appendChild(pageLi);
    }
    
    // 最后一页
    if (endPage < totalPages) {
        // 省略号
        if (endPage < totalPages - 1) {
            const ellipsisLi = document.createElement('li');
            ellipsisLi.className = 'page-item disabled';
            ellipsisLi.innerHTML = `<span class="page-link">...</span>`;
            pagination.appendChild(ellipsisLi);
        }
        
        const lastLi = document.createElement('li');
        lastLi.className = 'page-item';
        lastLi.innerHTML = `<a class="page-link" href="#">${totalPages}</a>`;
        lastLi.addEventListener('click', () => goToPage(totalPages));
        pagination.appendChild(lastLi);
    }
    
    // 下一页按钮
    const nextLi = document.createElement('li');
    nextLi.className = `page-item ${currentPage === totalPages ? 'disabled' : ''}`;
    nextLi.innerHTML = `
        <a class="page-link" href="#" aria-label="下一页">
            <i class="material-icons-round">chevron_right</i>
        </a>
    `;
    if (currentPage < totalPages) {
        nextLi.addEventListener('click', () => goToPage(currentPage + 1));
    }
    pagination.appendChild(nextLi);
}

/**
 * 跳转到指定页
 */
function goToPage(page) {
    const urlParams = new URLSearchParams(window.location.search);
    urlParams.set('page', page);
    window.location.href = window.location.pathname + '?' + urlParams.toString();
}

/**
 * 下载CSV文件
 */
function downloadCSV() {
    // 构建查询参数
    const urlParams = new URLSearchParams(window.location.search);
    urlParams.set('format', 'csv');
    
    // 跳转到下载链接
    window.location.href = window.location.pathname + '?' + urlParams.toString();
} 