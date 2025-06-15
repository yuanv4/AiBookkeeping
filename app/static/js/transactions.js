/**
 * 交易记录页面的JavaScript逻辑
 * 负责处理筛选、分页和表格显示
 */

document.addEventListener('DOMContentLoaded', function() {
    console.log("交易记录页面初始化...");
    
    // 获取分页和交易数据
    const pageDataElement = document.getElementById('current-page-data');
    const transactionsDataElement = document.getElementById('transactions-data');
    
    if (!pageDataElement || !transactionsDataElement) {
        console.error('找不到必要的数据元素');
        return;
    }
    
    // 初始化分页信息
    let currentPage = parseInt(pageDataElement.getAttribute('data-page') || '1');
    const itemsPerPage = parseInt(pageDataElement.getAttribute('data-limit') || '20');
    const totalPages = parseInt(pageDataElement.getAttribute('data-pages') || '1');
    
    // 解析交易数据
    let transactions = [];
    try {
        const transactionsJson = transactionsDataElement.getAttribute('data-transactions');
        console.log('获取到交易数据:', transactionsJson.substring(0, 100) + '...');
        transactions = JSON.parse(transactionsJson);
        console.log(`成功解析${transactions.length}条交易记录`);
    } catch (error) {
        console.error('解析交易数据时出错:', error);
        transactions = [];
    }
    
    // 检查表格元素
    const tableBody = document.getElementById('transactions-body');
    const noDataElement = document.getElementById('no-data');
    const paginationContainer = document.getElementById('pagination-container');
    
    console.log('表格主体元素:', tableBody ? '找到' : '未找到');
    console.log('无数据提示元素:', noDataElement ? '找到' : '未找到');
    console.log('分页容器元素:', paginationContainer ? '找到' : '未找到');
    
    // 初始化表格
    renderTransactionTable();
    
    // 初始化分页
    renderPagination();
    
    // 初始化筛选表单
    initFilterForm();
    
    // 初始化交易行格式化
    initTransactionRowFormatting();
    
    // 初始化活跃筛选条件显示
    initActiveFiltersDisplay();
    
    // 初始化快速筛选按钮
    initQuickFilters();
    
    // 初始化清除筛选功能
    initClearFilters();
});

/**
 * 初始化交易行格式化功能
 */
function initTransactionRowFormatting() {
    // 美化交易金额显示
    function formatTransactionRows() {
        const tbody = document.querySelector('#transactions-body');
        if (tbody) {
            const rows = tbody.querySelectorAll('tr');
            rows.forEach(row => {
                const amountCell = row.querySelector('td:nth-child(5)');
                if (amountCell) {
                    const amount = parseFloat(amountCell.textContent.replace(/[^\d.-]/g, ''));
                    if (amount > 0) {
                        amountCell.classList.add('transaction-amount', 'positive');
                    } else if (amount < 0) {
                        amountCell.classList.add('transaction-amount', 'negative');
                    }
                }
                
                const typeCell = row.querySelector('td:nth-child(3) .badge');
                if (typeCell) {
                    typeCell.classList.add('transaction-badge');
                }
            });
        }
    }
    
    // 监听表格变化
    const observer = new MutationObserver(formatTransactionRows);
    const target = document.querySelector('#transactions-body');
    if (target) {
        observer.observe(target, { childList: true, subtree: true });
    }
    
    // 初始化时也执行一次
    setTimeout(formatTransactionRows, 500);
    console.log('[TRANSACTIONS] 交易行格式化功能已初始化');
}

/**
 * 初始化筛选表单功能
 */
function initFilterForm() {
    // 设置清除单个筛选条件的功能
    function setupClearInputButtons() {
        document.querySelectorAll('.clear-input').forEach(btn => {
            btn.addEventListener('click', function() {
                const inputGroup = this.closest('.filter-input-group');
                const input = inputGroup.querySelector('input, select');
                if (input) {
                    input.value = '';
                    // 触发change事件以更新活跃筛选条件
                    input.dispatchEvent(new Event('change'));
                }
            });
        });
    }
    
    setupClearInputButtons();
    console.log('[TRANSACTIONS] 筛选表单功能已初始化');
}

/**
 * 初始化活跃筛选条件显示功能
 */
function initActiveFiltersDisplay() {
    // 更新活跃筛选条件展示
    function updateActiveFilters() {
        const urlParams = new URLSearchParams(window.location.search);
        const badgesContainer = document.getElementById('active-filters-badges');
        const activeFiltersContainer = document.getElementById('active-filters-container');
        
        if (!badgesContainer || !activeFiltersContainer) return;
        
        badgesContainer.innerHTML = '';
        
        const filterLabels = {
            'category': '交易类型',
            'bankAccount': '银行/卡号',
            'search': '关键词',
            'startDate': '开始日期',
            'endDate': '结束日期',
            'minAmount': '最小金额',
            'maxAmount': '最大金额'
        };
        
        let hasActiveFilters = false;
        
        urlParams.forEach((value, key) => {
            if (key !== 'page' && value) {
                hasActiveFilters = true;
                const label = filterLabels[key] || key;
                
                const badge = document.createElement('div');
                badge.className = 'filter-badge';
                badge.innerHTML = `
                    <span>${label}: ${value}</span>
                    <span class="close-icon" data-param="${key}">
                        <i data-lucide="x" class="lucide-icon lucide-icon-sm text-muted"></i>
                    </span>
                `;
                badgesContainer.appendChild(badge);
            }
        });
        
        // 初始化新添加的 Lucide Icons
        if (typeof lucide !== 'undefined') {
            lucide.createIcons();
        }
        
        // 显示或隐藏筛选条件区域
        activeFiltersContainer.style.display = hasActiveFilters ? 'block' : 'none';
        
        // 绑定移除筛选条件事件
        document.querySelectorAll('.filter-badge .close-icon').forEach(icon => {
            icon.addEventListener('click', function() {
                const param = this.getAttribute('data-param');
                const url = new URL(window.location.href);
                url.searchParams.delete(param);
                window.location.href = url.toString();
            });
        });
    }
    
    updateActiveFilters();
    console.log('[TRANSACTIONS] 活跃筛选条件显示功能已初始化');
}

/**
 * 初始化快速筛选按钮功能
 */
function initQuickFilters() {
    // 初始化快速筛选按钮
    function setupQuickFilters() {
        document.querySelectorAll('.quick-filter').forEach(btn => {
            btn.addEventListener('click', function() {
                const filterType = this.getAttribute('data-filter-type');
                const today = new Date();
                
                // 清除当前的日期和金额筛选
                document.getElementById('startDate').value = '';
                document.getElementById('endDate').value = '';
                document.getElementById('minAmount').value = '';
                document.getElementById('maxAmount').value = '';
                
                switch(filterType) {
                    case 'today':
                        const todayStr = today.toISOString().split('T')[0];
                        document.getElementById('startDate').value = todayStr;
                        document.getElementById('endDate').value = todayStr;
                        break;
                    case 'last7days':
                        const last7days = new Date();
                        last7days.setDate(today.getDate() - 6);
                        document.getElementById('startDate').value = last7days.toISOString().split('T')[0];
                        document.getElementById('endDate').value = today.toISOString().split('T')[0];
                        break;
                    case 'thisMonth':
                        const firstDay = new Date(today.getFullYear(), today.getMonth(), 1);
                        document.getElementById('startDate').value = firstDay.toISOString().split('T')[0];
                        document.getElementById('endDate').value = today.toISOString().split('T')[0];
                        break;
                    case 'income':
                        document.getElementById('minAmount').value = '0.01';
                        break;
                    case 'expense':
                        document.getElementById('maxAmount').value = '-0.01';
                        break;
                }
                
                // 自动应用筛选条件
                document.getElementById('apply-filters').click();
            });
        });
    }
    
    setupQuickFilters();
    console.log('[TRANSACTIONS] 快速筛选按钮功能已初始化');
}

/**
 * 初始化清除筛选功能
 */
function initClearFilters() {
    // 绑定清除所有筛选条件按钮
    function setupClearAllFilters() {
        const clearAllBtn = document.getElementById('clear-all-filters');
        if (clearAllBtn) {
            clearAllBtn.addEventListener('click', function() {
                window.location.href = window.location.pathname;
            });
        }
    }
    
    setupClearAllFilters();
    console.log('[TRANSACTIONS] 清除筛选功能已初始化');
}

/**
 * 原有的筛选表单初始化功能
 */
function initOriginalFilterForm() {
    initFilterForm();
    
    // 绑定事件处理
    bindEventHandlers();
    
    /**
     * 填充账户筛选选项 (基于 account_name 和 account_number)
     */
    function populateBankAccountOptions() {
        const accountSelect = document.getElementById('account_number_filter'); // 改为针对 account_number_filter
        if (!accountSelect) return;

        // 从 transactions-data 获取传递过来的 accounts 列表 (由 app.py 提供)
        const accountsDataElement = document.getElementById('accounts-data-for-filter'); 
        let accounts = [];
        if (accountsDataElement) {
            try {
                accounts = JSON.parse(accountsDataElement.getAttribute('data-accounts'));
            } catch (e) {
                console.error("Error parsing accounts data for filter: ", e);
            }
        }

        // 获取URL参数中的已选账号
        const urlParams = new URLSearchParams(window.location.search);
        const selectedAccountNumber = urlParams.get('account_number') || '';
        const selectedAccountName = urlParams.get('account_name_filter') || '';

        // 清空现有选项
        accountSelect.innerHTML = '<option value="">全部账户</option>';

        const uniqueAccounts = new Map();
        transactions.forEach(t => {
            if (t.account_number) { // 确保 account_number 存在
                const key = `${t.account_name || 'N/A'}-${t.account_number}`;
                if (!uniqueAccounts.has(t.account_number)) { // 使用 account_number 作为唯一键，避免重复账号
                    uniqueAccounts.set(t.account_number, {
                        text: `${t.account_name || '未命名账户'} (${t.account_number})`,
                        account_number: t.account_number,
                        account_name: t.account_name || ''
                    });
                }
            }
        });
        
        // 如果 accounts (从后端获取的账户列表) 不为空，优先使用它来填充，因为它更全
        if (accounts && accounts.length > 0) {
            uniqueAccounts.clear(); // 清除从当前页交易记录中提取的账户
            accounts.forEach(acc => {
                if (acc.account_number) {
                    if (!uniqueAccounts.has(acc.account_number)){
                        uniqueAccounts.set(acc.account_number, {
                            text: `${acc.account_name || '未命名账户'} (${acc.account_number})`,
                            account_number: acc.account_number,
                            account_name: acc.account_name || ''
                        });
                    }
                }
            });
        }

        uniqueAccounts.forEach(acc_info => {
            const option = document.createElement('option');
            option.value = acc_info.account_number; // 值直接是 account_number
            option.textContent = acc_info.text;
            option.dataset.accountName = acc_info.account_name; // 存储 account_name 以便需要时使用
            
            if (acc_info.account_number === selectedAccountNumber) {
                option.selected = true;
            }
            accountSelect.appendChild(option);
        });

        // 联动 account_name_filter (如果存在)
        const accountNameInput = document.getElementById('account_name_filter');
        if (accountNameInput && selectedAccountName) {
            accountNameInput.value = selectedAccountName;
        }
    }
    
    /**
     * 渲染交易表格
     */
    function renderTransactionTable() {
        const tableBody = document.getElementById('transactions-body');
        if (!tableBody) {
            console.error('找不到表格主体元素 transactions-body');
            return;
        }
        
        // 清空表格内容
        tableBody.innerHTML = '';
        
        // 检查是否有交易数据
        if (transactions.length === 0) {
            console.log('没有交易数据，显示空数据提示');
            const noDataElement = document.getElementById('no-data');
            const paginationContainer = document.getElementById('pagination-container');
            const tableContainer = document.querySelector('.table-responsive');
            
            if (noDataElement) noDataElement.style.setProperty('display', 'flex', 'important');
            if (paginationContainer) paginationContainer.style.display = 'none';
            if (tableContainer) tableContainer.style.display = 'none';
            return;
        }
        
        console.log(`准备渲染${transactions.length}条交易记录`);
        
        // 显示交易数据
        const noDataElement = document.getElementById('no-data');
        const paginationContainer = document.getElementById('pagination-container');
        const tableContainer = document.querySelector('.table-responsive');
        
        if (noDataElement) noDataElement.style.setProperty('display', 'none', 'important');
        if (paginationContainer) paginationContainer.style.display = 'block';
        if (tableContainer) tableContainer.style.display = 'block';
        
        // 显示记录计数
        const filteredCountElement = document.getElementById('filtered-count');
        if (filteredCountElement) filteredCountElement.textContent = transactions.length;
        
        // 直接使用服务器返回的数据，不再进行客户端分页切片
        // 服务器已经根据page参数返回了当前页的数据
        const pageTransactions = transactions;
        
        console.log(`当前页显示记录: ${transactions.length}条`);
        
        // 添加交易记录到表格
        pageTransactions.forEach((transaction, index) => {
            const row = document.createElement('tr');
            
            // 序号列
            const indexCell = document.createElement('td');
            indexCell.textContent = index + 1; // 直接使用索引+1作为序号，不再依赖startIndex
            row.appendChild(indexCell);
            
            // 日期列
            const dateCell = document.createElement('td');
            dateCell.textContent = transaction['transaction_date'] || ''; // 直接使用新字段名
            row.appendChild(dateCell);
            
            // 类型列
            const typeCell = document.createElement('td');
            typeCell.textContent = transaction['transaction_type'] || ''; // 直接使用新字段名
            row.appendChild(typeCell);
            
            // 交易对象列
            const merchantCell = document.createElement('td');
            merchantCell.textContent = transaction['counterparty'] || ''; // 直接使用新字段名
            row.appendChild(merchantCell);
            
            // 金额列
            const amountCell = document.createElement('td');
            const amount = parseFloat(transaction['amount'] || 0);
            amountCell.textContent = amount.toFixed(2);
            amountCell.className = amount >= 0 ? 'positive' : 'negative';
            row.appendChild(amountCell);
            
            // 账户余额列
            const balanceCell = document.createElement('td');
            const balance = parseFloat(transaction['balance'] || 0);
            balanceCell.textContent = balance.toFixed(2);
            row.appendChild(balanceCell);

            // 币种列 (新)
            const currencyCell = document.createElement('td');
            currencyCell.textContent = transaction['currency'] || '';
            row.appendChild(currencyCell);
            
            // 账号列
            const accountNoCell = document.createElement('td');
            accountNoCell.textContent = transaction['account_number'] || ''; // 直接使用新字段名
            row.appendChild(accountNoCell);
            
            // 账户名称列 (新)
            const accountNameCell = document.createElement('td');
            accountNameCell.textContent = transaction['account_name'] || '';
            row.appendChild(accountNameCell);
            
            tableBody.appendChild(row);
        });
        
        console.log('交易表格渲染完成');
    }
    
    /**
     * 渲染分页控件
     */
    function renderPagination() {
        const pagination = document.getElementById('pagination');
        if (!pagination) {
            console.error('找不到分页容器元素#pagination');
            return;
        }
        
        // 清空分页内容
        pagination.innerHTML = '';
        
        console.log('渲染分页控件，总页数:', totalPages, '当前页:', currentPage);
        
        // 如果总页数为0或未定义，默认设为1
        if (!totalPages || totalPages <= 0) {
            console.warn('总页数异常:', totalPages, '已设置为默认值1');
            totalPages = 1;
        }
        
        if (totalPages <= 1) {
            console.log('只有一页，不显示分页控件');
            return; // 如果只有一页，不显示分页控件
        }
        
        // 确保currentPage在有效范围内
        if (currentPage < 1) {
            currentPage = 1;
            console.warn('当前页小于1，已重置为1');
        } else if (currentPage > totalPages) {
            currentPage = totalPages;
            console.warn('当前页大于总页数，已重置为', totalPages);
        }
        
        // 添加上一页按钮
        const prevLi = document.createElement('li');
        prevLi.className = `page-item ${currentPage === 1 ? 'disabled' : ''}`;
        
        const prevLink = document.createElement('a');
        prevLink.className = 'page-link';
        prevLink.href = '#';
        prevLink.setAttribute('aria-label', '上一页');
        prevLink.innerHTML = '<span aria-hidden="true">&laquo;</span>';
        
        prevLink.addEventListener('click', function(e) {
            e.preventDefault();
            if (currentPage > 1) {
                goToPage(currentPage - 1);
            }
        });
        
        prevLi.appendChild(prevLink);
        pagination.appendChild(prevLi);
        
        // 确定要显示的页码范围
        const maxVisiblePages = 5;
        let startPage = Math.max(1, currentPage - Math.floor(maxVisiblePages / 2));
        let endPage = startPage + maxVisiblePages - 1;
        
        if (endPage > totalPages) {
            endPage = totalPages;
            startPage = Math.max(1, endPage - maxVisiblePages + 1);
        }
        
        console.log('显示页码范围:', startPage, '至', endPage);
        
        // 添加页码按钮
        for (let i = startPage; i <= endPage; i++) {
            const pageLi = document.createElement('li');
            pageLi.className = `page-item ${i === currentPage ? 'active' : ''}`;
            
            const pageLink = document.createElement('a');
            pageLink.className = 'page-link';
            pageLink.href = '#';
            pageLink.textContent = i;
            
            pageLink.addEventListener('click', function(e) {
                e.preventDefault();
                goToPage(i);
            });
            
            pageLi.appendChild(pageLink);
            pagination.appendChild(pageLi);
        }
        
        // 添加下一页按钮
        const nextLi = document.createElement('li');
        nextLi.className = `page-item ${currentPage === totalPages ? 'disabled' : ''}`;
        
        const nextLink = document.createElement('a');
        nextLink.className = 'page-link';
        nextLink.href = '#';
        nextLink.setAttribute('aria-label', '下一页');
        nextLink.innerHTML = '<span aria-hidden="true">&raquo;</span>';
        
        nextLink.addEventListener('click', function(e) {
            e.preventDefault();
            if (currentPage < totalPages) {
                goToPage(currentPage + 1);
            }
        });
        
        nextLi.appendChild(nextLink);
        pagination.appendChild(nextLi);
        
        // 确保分页容器可见
        const paginationContainer = document.getElementById('pagination-container');
        if (paginationContainer) {
            if (totalPages > 1) {
                paginationContainer.style.display = 'block';
                console.log('显示分页容器，共', totalPages, '页');
            } else {
                paginationContainer.style.display = 'none';
                console.log('隐藏分页容器，只有1页');
            }
        }
    }
    
    /**
     * 跳转到指定页
     */
    function goToPage(page) {
        // 构建URL参数
        const urlParams = new URLSearchParams(window.location.search);
        urlParams.set('page', page);
        
        // 重定向到新URL，刷新页面以获取新数据
        window.location.href = `${window.location.pathname}?${urlParams.toString()}`;
        
        // 注意：由于页面会刷新，下面的代码不会执行
        // 保留这段注释是为了说明这一点
    }
    
    /**
     * 绑定事件处理程序
     */
    function bindEventHandlers() {
        // 应用筛选按钮点击事件
        const applyFilterBtn = document.getElementById('apply-filters');
        if (applyFilterBtn) {
            applyFilterBtn.addEventListener('click', applyFilters);
        }
        
        // 重置筛选按钮点击事件
        const resetFilterBtn = document.getElementById('reset-filters');
        if (resetFilterBtn) {
            resetFilterBtn.addEventListener('click', resetFilters);
        }
        
        // 重置全部按钮点击事件
        const resetAllBtn = document.getElementById('reset-all');
        if (resetAllBtn) {
            resetAllBtn.addEventListener('click', resetFilters);
        }
        
        // 清除全部筛选条件按钮
        const clearAllFiltersBtn = document.getElementById('clear-all-filters');
        if (clearAllFiltersBtn) {
            clearAllFiltersBtn.addEventListener('click', function() {
                window.location.href = window.location.pathname;
            });
        }
        
        // 绑定快速筛选按钮
        document.querySelectorAll('.quick-filter').forEach(btn => {
            btn.addEventListener('click', function() {
                const filterType = this.getAttribute('data-filter-type');
                handleQuickFilter(filterType);
            });
        });
        
        // 绑定筛选条件单项清除
        document.querySelectorAll('.clear-input').forEach(btn => {
            btn.addEventListener('click', function() {
                const inputGroup = this.closest('.filter-input-group');
                const input = inputGroup.querySelector('input, select');
                if (input) {
                    input.value = '';
                    input.dispatchEvent(new Event('change'));
                }
            });
        });
        
        // 绑定活跃筛选条件移除
        document.querySelectorAll('.filter-badge .close-icon').forEach(icon => {
            icon.addEventListener('click', function() {
                const param = this.getAttribute('data-param');
                removeFilterParam(param);
            });
        });
        
        // 导出功能已移除
    }
    
    /**
     * 处理快速筛选
     */
    function handleQuickFilter(filterType) {
        const today = new Date();
        
        // 重置相关筛选字段
        document.getElementById('startDate').value = '';
        document.getElementById('endDate').value = '';
        document.getElementById('minAmount').value = '';
        document.getElementById('maxAmount').value = '';
        
        switch(filterType) {
            case 'today':
                const todayStr = today.toISOString().split('T')[0];
                document.getElementById('startDate').value = todayStr;
                document.getElementById('endDate').value = todayStr;
                break;
                
            case 'last7days':
                const last7days = new Date();
                last7days.setDate(today.getDate() - 6);
                document.getElementById('startDate').value = last7days.toISOString().split('T')[0];
                document.getElementById('endDate').value = today.toISOString().split('T')[0];
                break;
                
            case 'thisMonth':
                const firstDay = new Date(today.getFullYear(), today.getMonth(), 1);
                document.getElementById('startDate').value = firstDay.toISOString().split('T')[0];
                document.getElementById('endDate').value = today.toISOString().split('T')[0];
                break;
                
            case 'income':
                document.getElementById('minAmount').value = '0.01';
                break;
                
            case 'expense':
                document.getElementById('maxAmount').value = '-0.01';
                break;
        }
        
        // 自动应用筛选
        applyFilters();
    }
    
    /**
     * 移除指定参数的筛选条件
     */
    function removeFilterParam(param) {
        const url = new URL(window.location.href);
        url.searchParams.delete(param);
        window.location.href = url.toString();
    }
    
    /**
     * 应用筛选条件
     */
    function applyFilters() {
        console.log('开始应用筛选条件...');
        
        // 尝试获取筛选值（同时支持新旧ID）
        const getFilterValue = (oldId, newId) => {
            const oldElement = document.getElementById(oldId);
            const newElement = document.getElementById(newId);
            
            if (oldElement) {
                console.log(`使用旧ID "${oldId}" 获取筛选值:`, oldElement.value);
                return oldElement.value;
            } else if (newElement) {
                console.log(`使用新ID "${newId}" 获取筛选值:`, newElement.value);
                return newElement.value;
            } else {
                console.warn(`未找到筛选元素: ${oldId} 或 ${newId}`);
                return '';
            }
        };
        
        // 获取筛选值（支持新旧ID）
        const transactionType = getFilterValue('category', 'type');
        const accountNumber = getFilterValue('bankAccount', 'account_number_filter');
        const search = getFilterValue('search', 'counterparty_filter');
        const startDate = getFilterValue('startDate', 'start_date_filter');
        const endDate = getFilterValue('endDate', 'end_date_filter');
        const minAmount = getFilterValue('minAmount', 'min_amount_filter');
        const maxAmount = getFilterValue('maxAmount', 'max_amount_filter');
        
        // 可选字段
        const accountName = document.getElementById('account_name_filter') ? 
                            document.getElementById('account_name_filter').value : '';
        const currency = document.getElementById('currency_filter') ? 
                       document.getElementById('currency_filter').value : '';
        const distinct = document.getElementById('distinct_filter') ? 
                       document.getElementById('distinct_filter').checked : false;
        
        console.log('筛选条件汇总:', {
            transactionType, accountNumber, search, startDate, endDate,
            minAmount, maxAmount, accountName, currency, distinct
        });
        
        // 构建URL参数
        const urlParams = new URLSearchParams();
        if (transactionType) urlParams.set('type', transactionType);
        if (accountNumber) urlParams.set('account_number', accountNumber);
        if (accountName) urlParams.set('account_name_filter', accountName);
        if (currency) urlParams.set('currency', currency);
        if (search) urlParams.set('search', search);
        if (startDate) urlParams.set('start_date', startDate);
        if (endDate) urlParams.set('end_date', endDate);
        if (minAmount) urlParams.set('min_amount', minAmount);
        if (maxAmount) urlParams.set('max_amount', maxAmount);
        if (distinct) urlParams.set('distinct', 'true');

        urlParams.set('page', '1'); // 重置到第一页
        
        // 构建URL
        const newUrl = `${window.location.pathname}?${urlParams.toString()}`;
        console.log('重定向到新URL:', newUrl);
        
        // 重定向到新URL
        window.location.href = newUrl;
    }
    
    /**
     * 重置筛选条件
     */
    function resetFilters() {
        console.log('重置所有筛选条件');
        
        // 重置函数，支持多种可能的ID
        const resetField = (ids) => {
            ids.forEach(id => {
                const element = document.getElementById(id);
                if (element) {
                    if (element.type === 'checkbox') {
                        element.checked = false;
                    } else {
                        element.value = '';
                    }
                    console.log(`重置字段: ${id}`);
                }
            });
        };
        
        // 重置所有可能的筛选器字段
        resetField(['category', 'type']);
        resetField(['bankAccount', 'account_number_filter']);
        resetField(['search', 'counterparty_filter']);
        resetField(['startDate', 'start_date_filter']);
        resetField(['endDate', 'end_date_filter']);
        resetField(['minAmount', 'min_amount_filter']);
        resetField(['maxAmount', 'max_amount_filter']);
        resetField(['account_name_filter']);
        resetField(['currency_filter']);
        resetField(['distinct_filter']);
        
        // 重定向到无筛选的URL
        console.log('重定向到基础URL:', window.location.pathname);
        window.location.href = window.location.pathname;
    }
    
    /**
     * 下载CSV文件
     */
    // downloadCSV函数已移除
    
    /**
     * 初始化筛选表单
     */
    function initFilterForm() {
        const filterForm = document.querySelector('.filter-form');
        if (!filterForm) return;
        
        // 获取URL参数
        const urlParams = new URLSearchParams(window.location.search);
        
        // 更新活跃筛选条件展示
        updateActiveFilters(urlParams);
        
        // 获取所有筛选输入
        const inputs = filterForm.querySelectorAll('input, select');
        
        // 为每个输入添加change事件监听器
        inputs.forEach(input => {
            // 设置初始值
            const paramName = input.name;
            const paramValue = urlParams.get(paramName);
            if (paramValue) {
                input.value = paramValue;
            }
            
            // 激活清除按钮
            if (paramValue && input.value) {
                const inputGroup = input.closest('.filter-input-group');
                if (inputGroup) {
                    const clearBtn = inputGroup.querySelector('.clear-input');
                    if (clearBtn) {
                        clearBtn.style.display = 'block';
                    }
                }
            }
        });
    }
    
    /**
     * 更新活跃筛选条件展示
     */
    function updateActiveFilters(urlParams) {
        if (!urlParams) urlParams = new URLSearchParams(window.location.search);
        
        const badgesContainer = document.getElementById('active-filters-badges');
        const activeFiltersContainer = document.getElementById('active-filters-container');
        
        if (!badgesContainer || !activeFiltersContainer) return;
        
        badgesContainer.innerHTML = '';
        
        const filterLabels = {
            'category': '交易类型',
            'type': '交易类型',
            'bankAccount': '银行/卡号',
            'account_number': '银行/卡号',
            'search': '关键词',
            'startDate': '开始日期',
            'start_date': '开始日期',
            'endDate': '结束日期',
            'end_date': '结束日期',
            'minAmount': '最小金额',
            'min_amount': '最小金额',
            'maxAmount': '最大金额',
            'max_amount': '最大金额'
        };
        
        let hasActiveFilters = false;
        
        urlParams.forEach((value, key) => {
            if (key !== 'page' && value) {
                hasActiveFilters = true;
                const label = filterLabels[key] || key;
                
                const badge = document.createElement('div');
                badge.className = 'filter-badge';
                badge.innerHTML = `
                    <span>${label}: ${value}</span>
                    <span class="close-icon" data-param="${key}">
                        <i data-lucide="x" class="lucide-icon lucide-icon-sm"></i>
                    </span>
                `;
                badgesContainer.appendChild(badge);
            }
        });
        
        // 初始化新添加的 Lucide Icons
        if (typeof lucide !== 'undefined') {
            lucide.createIcons();
        }
        
        // 显示或隐藏筛选条件区域
        activeFiltersContainer.style.display = hasActiveFilters ? 'block' : 'none';
        
        // 绑定移除筛选条件事件
        document.querySelectorAll('.filter-badge .close-icon').forEach(icon => {
            icon.addEventListener('click', function() {
                const param = this.getAttribute('data-param');
                removeFilterParam(param);
            });
        });
    }
};