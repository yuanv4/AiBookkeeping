/**
 * TransactionsTable - 交易记录表格组件
 * 继承自DataTable，实现交易记录特定的功能
 */
class TransactionsTable extends DataTable {
    constructor(tableId, options = {}) {
        super(tableId, {
            sortable: true,
            filterable: true,
            columns: [
                { field: 'date', type: 'date' },
                { field: 'account', type: 'string' },
                { field: 'counterparty', type: 'string' },
                { field: 'description', type: 'string' },
                { field: 'amount', type: 'number' },
                { field: 'balance', type: 'number' }
            ],
            ...options
        });
        
        // 汇总相关元素
        this.summaryFooter = document.getElementById('transactions-summary-footer');
        this.summaryExpenseAmount = document.getElementById('summary-expense-amount');
        this.summaryExpenseCount = document.getElementById('summary-expense-count');
        this.summaryIncomeAmount = document.getElementById('summary-income-amount');
        this.summaryIncomeCount = document.getElementById('summary-income-count');
        this.summaryLatestBalance = document.getElementById('summary-latest-balance');
    }
    
    getCellValue(rowData, columnIndex) {
        const fields = ['date', 'account', 'counterparty', 'description', 'amount', 'balance'];
        const field = fields[columnIndex];
        
        if (field === 'account') {
            // 构建账户显示文本：户名-卡号
            return rowData.account_name && rowData.account_number
                ? `${rowData.account_name}-${rowData.account_number}`
                : (rowData.account_name || rowData.account_number || '');
        }
        
        return rowData[field] || '';
    }
    
    matchesFilters(row) {
        for (const [filterId, filterValue] of Object.entries(this.activeFilters)) {
            if (!this.matchesFilter(row, filterId, filterValue)) {
                return false;
            }
        }
        return true;
    }
    
    matchesFilter(row, filterId, filterValue) {
        const lowerFilterValue = filterValue.toLowerCase();
        
        switch (filterId) {
            case `${this.tableId}-account-filter`:
                const accountText = this.getCellValue(row, 1).toLowerCase();
                return accountText.includes(lowerFilterValue);
                
            case `${this.tableId}-counterparty-filter`:
                const counterparty = (row.counterparty || '').toLowerCase();
                return counterparty.includes(lowerFilterValue);
                
            case `${this.tableId}-description-filter`:
                const description = (row.description || '').toLowerCase();
                return description.includes(lowerFilterValue);
                
            case `${this.tableId}-date-start`:
                const startDate = new Date(filterValue);
                const rowDate = new Date(row.date);
                return rowDate >= startDate;
                
            case `${this.tableId}-date-end`:
                const endDate = new Date(filterValue);
                const rowDateEnd = new Date(row.date);
                return rowDateEnd <= endDate;
                

                
            default:
                return true;
        }
    }
    
    getFilterLabel(key) {
        const labels = {
            [`${this.tableId}-account-filter`]: '账户',
            [`${this.tableId}-counterparty-filter`]: '对手信息',
            [`${this.tableId}-description-filter`]: '摘要',
            [`${this.tableId}-date-start`]: '开始日期',
            [`${this.tableId}-date-end`]: '结束日期'
        };
        
        return labels[key] || key;
    }
    

    

    
    createRow(transaction, index) {
        const amount = parseFloat(transaction.amount || 0);
        const balance = parseFloat(transaction.balance || 0);
        
        // 构建账户显示文本
        const accountDisplay = this.getCellValue(transaction, 1);
        
        const row = document.createElement('tr');
        row.innerHTML = `
            <td class="text-start">${this.escapeHtml(transaction.date || '')}</td>
            <td class="text-start">
                <span class="d-inline-block transaction-cell-truncate-sm" title="${this.escapeHtml(accountDisplay)}">
                    ${this.escapeHtml(accountDisplay)}
                </span>
            </td>
            <td class="text-start">
                <span class="d-inline-block transaction-cell-truncate-md" title="${this.escapeHtml(transaction.counterparty || '')}">
                    ${this.escapeHtml(transaction.counterparty || '')}
                </span>
            </td>
            <td class="text-start">
                <span class="d-inline-block transaction-cell-truncate" title="${this.escapeHtml(transaction.description || '')}">
                    ${this.escapeHtml(transaction.description || '')}
                </span>
            </td>
            <td class="text-end transaction-amount ${amount >= 0 ? 'positive' : 'negative'}">${amount.toFixed(2)}</td>
            <td class="text-end">${balance.toFixed(2)}</td>
        `;
        
        return row;
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    render() {
        super.render();
        this.updateSummaryFooter();
    }
    
    calculateSummaryData() {
        let expenseAmount = 0;
        let expenseCount = 0;
        let incomeAmount = 0;
        let incomeCount = 0;
        let latestBalance = 0;

        // 遍历当前显示的交易记录
        this.filteredData.forEach((transaction, index) => {
            const amount = parseFloat(transaction.amount || 0);
            const balance = parseFloat(transaction.balance || 0);

            if (amount < 0) {
                // 支出（负数）
                expenseAmount += Math.abs(amount);
                expenseCount++;
            } else if (amount > 0) {
                // 收入（正数）
                incomeAmount += amount;
                incomeCount++;
            }

            // 最新余额（取最后一条记录的余额）
            if (index === this.filteredData.length - 1) {
                latestBalance = balance;
            }
        });

        return {
            expenseAmount,
            expenseCount,
            incomeAmount,
            incomeCount,
            latestBalance
        };
    }
    
    updateSummaryFooter() {
        if (!this.summaryFooter) return;

        const summary = this.calculateSummaryData();

        // 更新支出信息
        if (this.summaryExpenseAmount) {
            this.summaryExpenseAmount.textContent = `¥${summary.expenseAmount.toFixed(2)}`;
        }
        if (this.summaryExpenseCount) {
            this.summaryExpenseCount.textContent = `${summary.expenseCount}笔`;
        }

        // 更新收入信息
        if (this.summaryIncomeAmount) {
            this.summaryIncomeAmount.textContent = `¥${summary.incomeAmount.toFixed(2)}`;
        }
        if (this.summaryIncomeCount) {
            this.summaryIncomeCount.textContent = `${summary.incomeCount}笔`;
        }

        // 更新最新余额
        if (this.summaryLatestBalance) {
            this.summaryLatestBalance.textContent = `¥${summary.latestBalance.toFixed(2)}`;
        }

        // 根据是否有数据显示或隐藏汇总行
        if (this.filteredData.length > 0) {
            this.summaryFooter.style.display = 'block';
        } else {
            this.summaryFooter.style.display = 'none';
        }
    }
}

// 导出类
window.TransactionsTable = TransactionsTable;
