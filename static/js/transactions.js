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
    
    // 绑定事件处理
    bindEventHandlers();
    
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
            const bank = transaction['bank_name'] || transaction['银行'] || '';
            const accountNumber = transaction['account_number'] || transaction['账号'] || '';
            
            if (bank && accountNumber) {
                // 只保留同时有银行和卡号的选项
                const optionText = `${bank} - ${accountNumber}`;
                const optionValue = `${bank}:${accountNumber}`;
                
                bankAccounts.set(optionValue, optionText);
            }
        });
        
        // 构建下拉选项
        const bankAccountSelect = document.getElementById('bankAccount');
        if (bankAccountSelect) {
            // 首先添加"全部"选项
            const allOption = document.createElement('option');
            allOption.value = '';
            allOption.textContent = '全部银行/卡号';
            bankAccountSelect.appendChild(allOption);
            
            // 添加实际选项
            bankAccounts.forEach((text, value) => {
                const option = document.createElement('option');
                option.value = value;
                option.textContent = text;
                
                // 如果与URL参数匹配，则选中
                if (value === selectedValue) {
                    option.selected = true;
                }
                
                bankAccountSelect.appendChild(option);
            });
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
            
            if (noDataElement) noDataElement.style.display = 'flex';
            if (paginationContainer) paginationContainer.style.display = 'none';
            return;
        }
        
        console.log(`准备渲染${transactions.length}条交易记录`);
        
        // 显示交易数据
        const noDataElement = document.getElementById('no-data');
        const paginationContainer = document.getElementById('pagination-container');
        
        if (noDataElement) noDataElement.style.display = 'none';
        if (paginationContainer) paginationContainer.style.display = 'block';
        
        // 显示记录计数
        const filteredCountElement = document.getElementById('filtered-count');
        if (filteredCountElement) filteredCountElement.textContent = transactions.length;
        
        // 计算当前页的交易记录
        const startIndex = (currentPage - 1) * itemsPerPage;
        const endIndex = Math.min(startIndex + itemsPerPage, transactions.length);
        const pageTransactions = transactions.slice(startIndex, endIndex);
        
        console.log(`当前页显示记录: ${startIndex+1} - ${endIndex} (共${transactions.length}条)`);
        
        // 添加交易记录到表格
        pageTransactions.forEach((transaction, index) => {
            const row = document.createElement('tr');
            
            // 序号列
            const indexCell = document.createElement('td');
            indexCell.textContent = startIndex + index + 1;
            row.appendChild(indexCell);
            
            // 日期列
            const dateCell = document.createElement('td');
            dateCell.textContent = transaction['transaction_date'] || transaction['交易日期'] || '';
            row.appendChild(dateCell);
            
            // 类型列
            const typeCell = document.createElement('td');
            typeCell.textContent = transaction['transaction_type'] || transaction['交易类型'] || '';
            row.appendChild(typeCell);
            
            // 交易对象列
            const merchantCell = document.createElement('td');
            merchantCell.textContent = transaction['counterparty'] || transaction['交易对象'] || '';
            row.appendChild(merchantCell);
            
            // 金额列
            const amountCell = document.createElement('td');
            const amount = parseFloat(transaction['amount'] || transaction['交易金额'] || 0);
            amountCell.textContent = amount.toFixed(2);
            amountCell.className = amount >= 0 ? 'positive' : 'negative';
            row.appendChild(amountCell);
            
            // 账户余额列
            const balanceCell = document.createElement('td');
            const balance = parseFloat(transaction['balance'] || transaction['账户余额'] || 0);
            balanceCell.textContent = balance.toFixed(2);
            row.appendChild(balanceCell);
            
            // 账号列
            const accountCell = document.createElement('td');
            accountCell.textContent = transaction['account_number'] || transaction['账号'] || '';
            row.appendChild(accountCell);
            
            // 银行列
            const bankCell = document.createElement('td');
            bankCell.textContent = transaction['bank_name'] || transaction['银行'] || '';
            row.appendChild(bankCell);
            
            tableBody.appendChild(row);
        });
        
        console.log('交易表格渲染完成');
    }
    
    /**
     * 渲染分页控件
     */
    function renderPagination() {
        const pagination = document.getElementById('pagination');
        if (!pagination) return;
        
        // 清空分页内容
        pagination.innerHTML = '';
        
        if (totalPages <= 1) {
            return; // 如果只有一页，不显示分页控件
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
    }
    
    /**
     * 跳转到指定页
     */
    function goToPage(page) {
        currentPage = page;
        
        // 构建URL参数
        const urlParams = new URLSearchParams(window.location.search);
        urlParams.set('page', currentPage);
        
        // 更新URL，不刷新页面
        const newUrl = `${window.location.pathname}?${urlParams.toString()}`;
        window.history.pushState({ path: newUrl }, '', newUrl);
        
        // 重新渲染表格和分页
        renderTransactionTable();
        renderPagination();
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
        
        // 下载CSV按钮点击事件
        const downloadCsvBtn = document.getElementById('download-csv');
        if (downloadCsvBtn) {
            downloadCsvBtn.addEventListener('click', downloadCSV);
        }
    }
    
    /**
     * 应用筛选条件
     */
    function applyFilters() {
        // 获取筛选值
        const category = document.getElementById('category').value;
        const bankAccount = document.getElementById('bankAccount').value;
        const search = document.getElementById('search').value;
        
        // 构建URL参数
        const urlParams = new URLSearchParams();
        if (category) urlParams.set('type', category);
        if (bankAccount) urlParams.set('account_id', bankAccount);
        if (search) urlParams.set('search', search);
        urlParams.set('page', '1'); // 重置到第一页
        
        // 重定向到新URL
        window.location.href = `${window.location.pathname}?${urlParams.toString()}`;
    }
    
    /**
     * 重置筛选条件
     */
    function resetFilters() {
        // 重置所有筛选器
        document.getElementById('category').value = '';
        document.getElementById('bankAccount').value = '';
        document.getElementById('search').value = '';
        
        // 重定向到无筛选的URL
        window.location.href = window.location.pathname;
    }
    
    /**
     * 下载CSV文件
     */
    function downloadCSV() {
        if (transactions.length === 0) {
            alert('没有可导出的交易记录');
            return;
        }
        
        // 获取标题行
        const headers = ['序号', '日期', '类型', '交易对象', '金额', '账户余额', '账号', '银行'];
        
        // 准备CSV内容
        let csvContent = headers.join(',') + '\n';
        
        // 添加数据行
        transactions.forEach((transaction, index) => {
            const row = [
                index + 1,
                `"${transaction['transaction_date'] || ''}"`,
                `"${transaction['transaction_type'] || ''}"`,
                `"${transaction['counterparty'] || ''}"`,
                transaction['amount'] || 0,
                transaction['balance'] || 0,
                `"${transaction['account_number'] || ''}"`,
                `"${transaction['bank_name'] || ''}"`
            ];
            
            csvContent += row.join(',') + '\n';
        });
        
        // 创建下载链接
        const encodedUri = encodeURI('data:text/csv;charset=utf-8,' + csvContent);
        const link = document.createElement('a');
        link.setAttribute('href', encodedUri);
        link.setAttribute('download', '交易记录.csv');
        document.body.appendChild(link);
        
        // 点击链接下载
        link.click();
        
        // 清理
        document.body.removeChild(link);
    }
    
    /**
     * 初始化筛选表单
     */
    function initFilterForm() {
        const filterForm = document.querySelector('.filter-form');
        if (!filterForm) return;
        
        // 获取URL参数
        const urlParams = new URLSearchParams(window.location.search);
        
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
            
            // 添加change事件监听器
            input.addEventListener('change', function() {
                // 更新URL参数
                const url = new URL(window.location.href);
                const paramName = this.name;
                const paramValue = this.value;
                
                if (paramValue) {
                    url.searchParams.set(paramName, paramValue);
                } else {
                    url.searchParams.delete(paramName);
                }
                
                // 重置页码
                url.searchParams.set('page', '1');
                
                // 跳转到新URL
                window.location.href = url.toString();
            });
        });
    }
}); 