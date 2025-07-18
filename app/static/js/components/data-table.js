/**
 * DataTable - 通用表格组件
 * 支持筛选、排序、分页等功能
 */
class DataTable {
    constructor(tableId, options = {}) {
        this.tableId = tableId;
        this.options = {
            sortable: true,
            filterable: false,
            data: [],
            columns: [],
            onDataChange: null,
            ...options
        };
        
        this.originalData = [];
        this.filteredData = [];
        this.currentSort = { column: null, direction: null };
        this.activeFilters = {};
        
        this.init();
    }
    
    init() {
        this.initElements();
        this.setupEventListeners();
        this.setData(this.options.data);
    }
    
    initElements() {
        this.container = document.querySelector(`[data-table-id="${this.tableId}"]`);
        this.table = document.getElementById(this.tableId);
        this.tbody = document.getElementById(`${this.tableId}-body`);
        this.noDataDiv = document.getElementById(`${this.tableId}-no-data`);
        this.filteredCountElement = document.getElementById(`${this.tableId}-filtered-count`);
        
        // 筛选相关元素
        this.filterForm = document.getElementById(`${this.tableId}-filter-form`);
        this.filterPanel = document.getElementById(`${this.tableId}-filter-panel`);
        this.toggleFiltersBtn = document.getElementById(`${this.tableId}-toggle-filters`);
        this.applyFiltersBtn = document.getElementById(`${this.tableId}-apply-filters`);
        this.resetFiltersBtn = document.getElementById(`${this.tableId}-reset-filters`);
        this.clearAllFiltersBtn = document.getElementById(`${this.tableId}-clear-all-filters`);
        this.activeFiltersContainer = document.getElementById(`${this.tableId}-active-filters-container`);
        this.activeFiltersBadges = document.getElementById(`${this.tableId}-active-filters-badges`);
        this.resetAllBtn = document.getElementById(`${this.tableId}-reset-all`);
    }
    
    setupEventListeners() {
        // 排序事件
        if (this.options.sortable && this.table) {
            this.table.querySelectorAll('.sortable').forEach(header => {
                header.addEventListener('click', (e) => {
                    const columnIndex = parseInt(header.getAttribute('data-sort'));
                    this.handleSort(columnIndex);
                });
            });
        }
        
        // 筛选事件
        if (this.options.filterable) {
            // 筛选按钮事件
            if (this.applyFiltersBtn) {
                this.applyFiltersBtn.addEventListener('click', () => this.applyFilters());
            }
            
            if (this.resetFiltersBtn) {
                this.resetFiltersBtn.addEventListener('click', () => this.resetFilters());
            }
            
            if (this.clearAllFiltersBtn) {
                this.clearAllFiltersBtn.addEventListener('click', () => this.clearAllFilters());
            }
            
            if (this.resetAllBtn) {
                this.resetAllBtn.addEventListener('click', () => this.clearAllFilters());
            }
            
            // 筛选面板切换
            if (this.toggleFiltersBtn) {
                this.toggleFiltersBtn.addEventListener('click', () => this.toggleFilterPanel());
            }
            

            
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
            if (this.filterForm) {
                const inputs = this.filterForm.querySelectorAll('input, select');
                inputs.forEach(input => {
                    input.addEventListener('change', () => {
                        this.updateActiveFilters();
                    });
                });
            }
        }
    }
    
    setData(data) {
        this.originalData = [...data];
        this.filteredData = [...data];
        this.render();
    }
    
    handleSort(columnIndex) {
        if (!this.options.sortable) return;
        
        const header = this.table.querySelector(`[data-sort="${columnIndex}"]`);
        if (!header) return;
        
        // 更新排序状态
        if (this.currentSort.column === columnIndex) {
            // 同一列：切换排序方向
            if (this.currentSort.direction === 'asc') {
                this.currentSort.direction = 'desc';
            } else if (this.currentSort.direction === 'desc') {
                this.currentSort = { column: null, direction: null };
            } else {
                this.currentSort.direction = 'asc';
            }
        } else {
            // 不同列：设置为升序
            this.currentSort = { column: columnIndex, direction: 'asc' };
        }
        
        // 更新排序图标
        this.updateSortIcons();
        
        // 执行排序
        this.sortData();
        this.render();
    }
    
    updateSortIcons() {
        // 清除所有排序样式
        this.table.querySelectorAll('.sortable').forEach(header => {
            header.classList.remove('sort-asc', 'sort-desc');
        });
        
        // 设置当前排序列的样式
        if (this.currentSort.column !== null) {
            const header = this.table.querySelector(`[data-sort="${this.currentSort.column}"]`);
            if (header) {
                header.classList.add(`sort-${this.currentSort.direction}`);
            }
        }
    }
    
    sortData() {
        if (this.currentSort.column === null) {
            this.filteredData = [...this.originalData];
            this.applyCurrentFilters();
            return;
        }
        
        this.filteredData.sort((a, b) => {
            const aValue = this.getCellValue(a, this.currentSort.column);
            const bValue = this.getCellValue(b, this.currentSort.column);
            
            let result = 0;
            
            // 数字比较
            if (!isNaN(aValue) && !isNaN(bValue)) {
                result = parseFloat(aValue) - parseFloat(bValue);
            }
            // 日期比较
            else if (this.isDate(aValue) && this.isDate(bValue)) {
                result = new Date(aValue) - new Date(bValue);
            }
            // 字符串比较
            else {
                result = String(aValue).localeCompare(String(bValue));
            }
            
            return this.currentSort.direction === 'desc' ? -result : result;
        });
    }
    
    getCellValue(rowData, columnIndex) {
        if (Array.isArray(rowData)) {
            return rowData[columnIndex] || '';
        }
        
        // 如果是对象，根据列配置获取值
        if (this.options.columns && this.options.columns[columnIndex]) {
            const column = this.options.columns[columnIndex];
            return rowData[column.field] || '';
        }
        
        return '';
    }
    
    isDate(value) {
        return !isNaN(Date.parse(value));
    }
    
    applyFilters() {
        this.collectFilterValues();
        this.applyCurrentFilters();
        this.render();
        this.updateActiveFilters();
    }
    
    collectFilterValues() {
        this.activeFilters = {};
        
        if (!this.filterForm) return;
        
        const inputs = this.filterForm.querySelectorAll('input, select');
        inputs.forEach(input => {
            if (input.value.trim()) {
                this.activeFilters[input.id] = input.value.trim();
            }
        });
    }
    
    applyCurrentFilters() {
        this.filteredData = this.originalData.filter(row => {
            return this.matchesFilters(row);
        });
    }
    
    matchesFilters(row) {
        // 子类应该重写此方法来实现具体的筛选逻辑
        return true;
    }
    
    resetFilters() {
        if (this.filterForm) {
            this.filterForm.reset();
        }
        this.activeFilters = {};
        this.filteredData = [...this.originalData];
        this.render();
        this.updateActiveFilters();
    }
    
    clearAllFilters() {
        this.resetFilters();
    }
    
    updateActiveFilters() {
        if (!this.activeFiltersContainer || !this.activeFiltersBadges) return;
        
        this.activeFiltersBadges.innerHTML = '';
        
        const hasActiveFilters = Object.keys(this.activeFilters).length > 0;
        this.activeFiltersContainer.style.display = hasActiveFilters ? 'block' : 'none';
        
        // 显示活跃筛选条件
        Object.entries(this.activeFilters).forEach(([key, value]) => {
            const badge = this.createFilterBadge(key, value);
            this.activeFiltersBadges.appendChild(badge);
        });
    }
    
    createFilterBadge(key, value) {
        const badge = document.createElement('span');
        badge.className = 'badge bg-primary';
        badge.innerHTML = `${this.getFilterLabel(key)}: ${value} <button type="button" class="btn-close btn-close-white ms-1" data-filter-key="${key}"></button>`;
        
        // 添加删除事件
        badge.querySelector('.btn-close').addEventListener('click', (e) => {
            this.removeFilter(key);
        });
        
        return badge;
    }
    
    getFilterLabel(key) {
        // 子类可以重写此方法来提供更好的标签
        return key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
    }
    
    removeFilter(key) {
        delete this.activeFilters[key];
        
        // 清除对应的输入框
        const input = document.getElementById(key);
        if (input) {
            input.value = '';
        }
        
        this.applyCurrentFilters();
        this.render();
        this.updateActiveFilters();
    }
    
    toggleFilterPanel() {
        if (!this.filterPanel || !this.toggleFiltersBtn) return;
        
        const isVisible = this.filterPanel.style.display !== 'none';
        this.filterPanel.style.display = isVisible ? 'none' : 'block';
        
        const toggleText = this.toggleFiltersBtn.querySelector('.filter-toggle-text');
        const toggleIcon = this.toggleFiltersBtn.querySelector('.lucide-icon');
        
        if (toggleText) {
            toggleText.textContent = isVisible ? '展开' : '收起';
        }
        
        if (toggleIcon) {
            toggleIcon.style.transform = isVisible ? 'rotate(180deg)' : 'rotate(0deg)';
        }
    }
    

    
    render() {
        if (!this.tbody) return;
        
        this.tbody.innerHTML = '';
        
        if (this.filteredData.length === 0) {
            this.showNoData();
            return;
        }
        
        this.showTableData();
        
        // 更新统计信息
        if (this.filteredCountElement) {
            this.filteredCountElement.textContent = this.filteredData.length;
        }
        
        // 渲染数据行
        this.filteredData.forEach((rowData, index) => {
            const row = this.createRow(rowData, index);
            this.tbody.appendChild(row);
        });
        
        // 触发数据变化回调
        if (this.options.onDataChange) {
            this.options.onDataChange(this.filteredData);
        }
    }
    
    createRow(rowData, index) {
        // 子类应该重写此方法来创建具体的行元素
        const row = document.createElement('tr');
        row.innerHTML = '<td colspan="100%">请重写 createRow 方法</td>';
        return row;
    }
    
    showNoData() {
        if (this.noDataDiv) {
            this.noDataDiv.classList.remove('d-none');
        }
        if (this.table) {
            this.table.style.display = 'none';
        }
    }
    
    showTableData() {
        if (this.noDataDiv) {
            this.noDataDiv.classList.add('d-none');
        }
        if (this.table) {
            this.table.style.display = 'table';
        }
    }
}

// 导出类
window.DataTable = DataTable;
