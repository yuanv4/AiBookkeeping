/**
 * 交易记录页面的JavaScript逻辑
 * 使用现代化的类结构重构筛选、分页和表格显示功能
 */

import BasePage from '../common/BasePage.js';
import { escapeHtml, urlHandler, ui, formatDate } from '../common/utils.js';

export default class TransactionsPage extends BasePage {
    constructor() {
        super();
        this.currentPage = 1;
        this.itemsPerPage = 20;
        this.totalPages = 1;
        this.transactions = [];
    }
    
    init() {
        // 先绑定元素和设置事件监听器
        this.bindElements();
        this.setupEventListeners();
        
        // 然后加载数据
        this.loadPageData();
        
        // 最后渲染页面（此时数据已加载）
        this.renderPage();
    }
    
    bindElements() {
        this.elements = {
            // 统一数据元素
            pageDataElement: document.getElementById('page-data'),
            
            // 表格元素
            tableBody: document.getElementById('transactions-table-body'),
            noDataElement: document.getElementById('transactions-table-no-data'),
            tableContainer: document.querySelector('.table-responsive'),
            
            // 分页元素
            pagination: document.getElementById('transactions-table-pagination'),
            paginationContainer: document.getElementById('transactions-table-pagination-container'),
            
            // 筛选元素
            filterForm: document.querySelector('.filter-form'),
            applyFiltersBtn: document.getElementById('apply-filters'),
            resetFiltersBtn: document.getElementById('reset-filters'),
            clearAllFiltersBtn: document.getElementById('clear-all-filters'),
            
            // 活跃筛选条件
            activeFiltersContainer: document.getElementById('active-filters-container'),
            activeFiltersBadges: document.getElementById('active-filters-badges'),
            
            // 统计元素
            filteredCountElement: document.getElementById('transactions-table-filtered-count')
        };
    }
    
    loadPageData() {
        // 从统一数据源加载数据
        if (this.elements.pageDataElement) {
            try {
                const initialDataJson = this.elements.pageDataElement.getAttribute('data-initial-data');
                const initialData = JSON.parse(initialDataJson || '{}');
                
                // 加载交易数据
                this.transactions = initialData.transactions || [];
                
                // 加载分页信息 - 修正字段名以匹配serialize_pagination过滤器
                const pagination = initialData.pagination || {};
                this.currentPage = parseInt(pagination.current_page || '1');
                this.itemsPerPage = parseInt(pagination.per_page || '20');
                this.totalPages = parseInt(pagination.total_pages || '1');
                
            } catch (error) {
                console.error('解析页面数据时出错:', error);
                this.transactions = [];
                this.currentPage = 1;
                this.itemsPerPage = 20;
                this.totalPages = 1;
            }
        }
    }
    
    setupEventListeners() {
        // 筛选按钮事件
        if (this.elements.applyFiltersBtn) {
            this.elements.applyFiltersBtn.addEventListener('click', () => {
                this.applyFilters();
            });
        }
        
        if (this.elements.resetFiltersBtn) {
            this.elements.resetFiltersBtn.addEventListener('click', () => {
                this.resetFilters();
            });
        }
        
        if (this.elements.clearAllFiltersBtn) {
            this.elements.clearAllFiltersBtn.addEventListener('click', () => {
                this.clearAllFilters();
            });
        }
        
        // 快速筛选按钮
        document.querySelectorAll('.quick-filter').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const filterType = e.target.getAttribute('data-filter-type');
                this.handleQuickFilter(filterType);
            });
        });
        
        // 清除单个输入按钮
        document.querySelectorAll('.clear-input').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const inputGroup = e.target.closest('.filter-input-group');
                const input = inputGroup?.querySelector('input, select');
                if (input) {
                    input.value = '';
                    input.dispatchEvent(new Event('change'));
                }
            });
        });
        
        // 筛选输入框变化事件
        if (this.elements.filterForm) {
            const inputs = this.elements.filterForm.querySelectorAll('input, select');
            inputs.forEach(input => {
                input.addEventListener('change', () => {
                    this.updateActiveFilters();
                });
            });
        }
    }
    
    renderPage() {
        this.renderTransactionTable();
        this.renderPagination();
        this.updateActiveFilters();
        this.initTransactionRowFormatting();
    }
    
    renderTransactionTable() {
        if (!this.elements.tableBody) return;
        
        this.elements.tableBody.innerHTML = '';
        
        if (this.transactions.length === 0) {
            this.showNoData();
            return;
        }
        
        this.showTableData();
        
        // 更新统计信息
        if (this.elements.filteredCountElement) {
            this.elements.filteredCountElement.textContent = this.transactions.length;
        }
        
        // 渲染交易行
        this.transactions.forEach((transaction, index) => {
            const row = this.createTransactionRow(transaction, index);
            this.elements.tableBody.appendChild(row);
        });
    }
    
    createTransactionRow(transaction, index) {
        const amount = parseFloat(transaction.amount || 0);
        const balance = parseFloat(transaction.balance || 0);
        
        // 根据模板中的表头顺序：['日期', '账户', '金额', '余额', '对手信息', '摘要']
        const rowHtml = `
            <tr>
                <td>${escapeHtml(transaction.date || '')}</td>
                <td>${escapeHtml(transaction.account_name || transaction.account_number || '')}</td>
                <td class="${amount >= 0 ? 'positive' : 'negative'}">${amount.toFixed(2)}</td>
                <td>${balance.toFixed(2)}</td>
                <td>${escapeHtml(transaction.counterparty || '')}</td>
                <td>${escapeHtml(transaction.description || '')}</td>
            </tr>
        `;
        
        return ui.createDOMElement(rowHtml);
    }
    
    showNoData() {
        if (this.elements.noDataElement) {
            // 使用Bootstrap类操作而不是直接设置CSS
            this.elements.noDataElement.classList.remove('d-none');
            this.elements.noDataElement.classList.add('d-flex');
        }
        if (this.elements.paginationContainer) {
            this.elements.paginationContainer.style.display = 'none';
        }
        if (this.elements.tableContainer) {
            this.elements.tableContainer.style.display = 'none';
        }
    }
    
    showTableData() {
        if (this.elements.noDataElement) {
            // 使用Bootstrap类操作而不是直接设置CSS
            this.elements.noDataElement.classList.add('d-none');
            this.elements.noDataElement.classList.remove('d-flex');
        }
        if (this.elements.paginationContainer) {
            this.elements.paginationContainer.style.display = 'block';
        }
        if (this.elements.tableContainer) {
            this.elements.tableContainer.style.display = 'block';
        }
    }
    
    renderPagination() {
        ui.renderPagination({
            currentPage: this.currentPage,
            totalPages: this.totalPages,
            containerId: 'transactions-table-pagination',
            onPageClick: (page) => this.goToPage(page)
        });
    }
    
    goToPage(page) {
        urlHandler.set('page', page);
    }
    
    initTransactionRowFormatting() {
        // 美化交易金额显示
        const formatRows = () => {
            if (this.elements.tableBody) {
                const rows = this.elements.tableBody.querySelectorAll('tr');
                rows.forEach(row => {
                    // 金额列现在是第3列（td:nth-child(3)）
                    const amountCell = row.querySelector('td:nth-child(3)');
                    if (amountCell) {
                        const amount = parseFloat(amountCell.textContent.replace(/[^\d.-]/g, ''));
                        if (amount > 0) {
                            amountCell.classList.add('transaction-amount', 'positive');
                        } else if (amount < 0) {
                            amountCell.classList.add('transaction-amount', 'negative');
                        }
                    }
                    
                    // 交易类型列现在是第6列（td:nth-child(6)）
                    const typeCell = row.querySelector('td:nth-child(6) .badge');
                    if (typeCell) {
                        typeCell.classList.add('transaction-badge');
                    }
                });
            }
        };
        
        // 监听表格变化
        if (this.elements.tableBody) {
            const observer = new MutationObserver(formatRows);
            observer.observe(this.elements.tableBody, { childList: true, subtree: true });
        }
        
        // 初始化时执行一次
        setTimeout(formatRows, 100);
    }
    
    updateActiveFilters() {
        const urlParams = urlHandler.getAll();
        
        if (!this.elements.activeFiltersBadges || !this.elements.activeFiltersContainer) return;
        
        this.elements.activeFiltersBadges.innerHTML = '';
        
        const filterLabels = {
            'account_number': '银行/卡号',
            'search': '关键词',
            'start_date': '开始日期',
            'end_date': '结束日期',
            'min_amount': '最小金额',
            'max_amount': '最大金额'
        };
        
        let hasActiveFilters = false;
        
        Object.entries(urlParams).forEach(([key, value]) => {
            if (key !== 'page' && value) {
                hasActiveFilters = true;
                const label = filterLabels[key] || key;
                
                const badgeHtml = `
                    <div class="filter-badge">
                        <span>${escapeHtml(label)}: ${escapeHtml(value)}</span>
                        <span class="close-icon" data-param="${key}">
                            <i data-lucide="x" class="lucide-icon lucide-icon-sm"></i>
                        </span>
                    </div>
                `;
                
                const badge = ui.createDOMElement(badgeHtml);
                this.elements.activeFiltersBadges.appendChild(badge);
            }
        });
        
        // 初始化 Lucide Icons
        if (typeof lucide !== 'undefined') {
            lucide.createIcons();
        }
        
        // 显示或隐藏筛选条件区域
        this.elements.activeFiltersContainer.style.display = hasActiveFilters ? 'block' : 'none';
        
        // 绑定移除筛选条件事件
        document.querySelectorAll('.filter-badge .close-icon').forEach(icon => {
            icon.addEventListener('click', (e) => {
                const param = e.target.getAttribute('data-param');
                this.removeFilterParam(param);
            });
        });
    }
    
    handleQuickFilter(filterType) {
        const today = new Date();
        
        // 重置相关筛选字段
        this.resetFilterFields(['start_date_filter', 'end_date_filter', 'min_amount_filter', 'max_amount_filter']);
        
        switch(filterType) {
            case 'today':
                const todayStr = formatDate(today);
                this.setFilterValue('start_date_filter', todayStr);
                this.setFilterValue('end_date_filter', todayStr);
                break;
                
            case 'last7days':
                const last7days = new Date();
                last7days.setDate(today.getDate() - 6);
                this.setFilterValue('start_date_filter', formatDate(last7days));
                this.setFilterValue('end_date_filter', formatDate(today));
                break;
                
            case 'thisMonth':
                const firstDay = new Date(today.getFullYear(), today.getMonth(), 1);
                this.setFilterValue('start_date_filter', formatDate(firstDay));
                this.setFilterValue('end_date_filter', formatDate(today));
                break;
                
            case 'income':
                this.setFilterValue('min_amount_filter', '0.01');
                break;
                
            case 'expense':
                this.setFilterValue('max_amount_filter', '-0.01');
                break;
        }
        
        // 自动应用筛选
        this.applyFilters();
    }
    
    resetFilterFields(fieldIds) {
        fieldIds.forEach(id => {
            const element = document.getElementById(id);
            if (element) {
                element.value = '';
            }
        });
    }
    
    setFilterValue(fieldId, value) {
        const element = document.getElementById(fieldId);
        if (element) {
            element.value = value;
        }
    }
    
    applyFilters() {
        // 获取筛选值
        const filters = {
            'account_number': this.getFilterValue('account_number_filter'),
            'search': this.getFilterValue('counterparty_filter'),
            'start_date': this.getFilterValue('start_date_filter'),
            'end_date': this.getFilterValue('end_date_filter'),
            'min_amount': this.getFilterValue('min_amount_filter'),
            'max_amount': this.getFilterValue('max_amount_filter'),
            'account_name_filter': this.getFilterValue('account_name_filter'),
            'currency': this.getFilterValue('currency_filter')
        };
        
        // 检查去重选项
        const distinctElement = document.getElementById('distinct_filter');
        if (distinctElement && distinctElement.checked) {
            filters.distinct = 'true';
        }
        
        // 重置到第一页
        filters.page = '1';
        
        // 使用 urlHandler 批量设置参数
        urlHandler.setMultiple(filters);
    }
    
    getFilterValue(fieldId) {
        const element = document.getElementById(fieldId);
        return element ? element.value : '';
    }
    
    resetFilters() {
        const filterFields = [
            'account_number_filter', 'counterparty_filter',
            'start_date_filter', 'end_date_filter', 'min_amount_filter',
            'max_amount_filter', 'account_name_filter', 'currency_filter',
            'distinct_filter'
        ];
        
        filterFields.forEach(fieldId => {
            const element = document.getElementById(fieldId);
            if (element) {
                if (element.type === 'checkbox') {
                    element.checked = false;
                } else {
                    element.value = '';
                }
            }
        });
        
        // 使用 urlHandler 清除所有参数
        urlHandler.setMultiple({});
    }
    
    clearAllFilters() {
        urlHandler.setMultiple({});
    }
    
    removeFilterParam(param) {
        urlHandler.remove(param);
    }
}

