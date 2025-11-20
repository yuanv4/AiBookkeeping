/* 分类映射管理页面 JavaScript */

class CategoryMappingManager {
    constructor() {
        this.mappingTable = null;
        this.allCategories = [];
        this.basicCategories = [];
        this.showInactive = false;
        this.selectedRows = [];

        this.init();
    }

    async init() {
        try {
            await this.loadBasicCategories();
            await this.loadData();
            this.initTable();
            this.setupEventListeners();
            this.renderUnmappedCategories();
        } catch (error) {
            console.error('初始化失败:', error);
            this.showNotification('页面初始化失败', 'error');
        }
    }

    async loadBasicCategories() {
        try {
            const response = await fetch('/api/category-mapping/categories');
            const data = await response.json();
            if (data.success) {
                this.basicCategories = data.data;
            }
        } catch (error) {
            console.error('加载基础分类失败:', error);
        }
    }

    async loadData() {
        try {
            // 并行加载数据
            const [categoriesResponse, statsResponse] = await Promise.all([
                fetch('/api/category-mapping/source-categories'),
                fetch('/api/category-mapping/statistics')
            ]);

            const categoriesData = await categoriesResponse.json();
            const statsData = await statsResponse.json();

            if (categoriesData.success) {
                this.allCategories = categoriesData.data;
            }

            if (statsData.success) {
                this.updateStatistics(statsData.data);
            }
        } catch (error) {
            console.error('加载数据失败:', error);
            throw error;
        }
    }

    initTable() {
        const tableData = this.filterCategories(this.allCategories);

        this.mappingTable = new Tabulator("#mapping-table", {
            data: tableData,
            selectableRows: 2, // 允许多选
            layout: "fitDataFill",
            pagination: "local",
            paginationSize: 20,
            columns: [
                {
                    title: "数据源分类",
                    field: "source_category",
                    headerFilter: true,
                    minWidth: 200,
                    formatter: this.formatterSourceCategory.bind(this)
                },
                {
                    title: "交易数量",
                    field: "transaction_count",
                    sorter: "number",
                    width: 100,
                    formatter: this.formatterTransactionCount.bind(this)
                },
                {
                    title: "映射分类",
                    field: "target_category",
                    width: 150,
                    editor: "select",
                    editorParams: this.getCategoryOptions.bind(this),
                    formatter: this.formatterTargetCategory.bind(this),
                    cellEdited: this.onMappingChanged.bind(this)
                },
                {
                    title: "状态",
                    field: "is_active",
                    width: 80,
                    formatter: "tickCross",
                    cellEdited: this.onStatusChanged.bind(this)
                },
                {
                    title: "操作",
                    width: 120,
                    formatter: this.formatterActions.bind(this)
                }
            ],
            rowSelectionChanged: (data, rows) => {
                this.selectedRows = rows;
                this.updateBatchButton();
            }
        });
    }

    filterCategories(categories) {
        if (this.showInactive) {
            return categories;
        }
        return categories.filter(cat => cat.has_mapping && cat.is_active);
    }

    getCategoryOptions() {
        const options = [];
        this.basicCategories.forEach(cat => {
            options[cat.code] = cat.name;
        });
        return options;
    }

    formatterSourceCategory(cell, formatterParams, onRendered) {
        const value = cell.getValue();
        const data = cell.getRow().getData();
        return `
            <div class="icon-with-text">
                ${data.has_mapping ?
                    `<span class="status-indicator ${data.is_active ? 'active' : 'inactive'}"></span>` :
                    `<span class="status-indicator inactive"></span>`
                }
                <span>${value}</span>
            </div>
        `;
    }

    formatterTransactionCount(cell, formatterParams, onRendered) {
        const value = cell.getValue();
        return `<span class="transaction-count">${value}</span>`;
    }

    formatterTargetCategory(cell, formatterParams, onRendered) {
        const value = cell.getValue();
        const data = cell.getRow().getData();

        if (!value) {
            return '<span class="text-muted">未设置</span>';
        }

        const category = this.basicCategories.find(cat => cat.code === value);
        if (category) {
            return `<span class="category-tag ${category.code}">${category.name}</span>`;
        }
        return value;
    }

    formatterActions(cell, formatterParams, onRendered) {
        const data = cell.getRow().getData();

        return `
            <div class="btn-group btn-group-sm" role="group">
                <button type="button" class="btn btn-outline-primary"
                        onclick="categoryMappingManager.editMapping('${data.source_category}')">
                    <i class="fas fa-edit"></i>
                </button>
                <button type="button" class="btn btn-outline-danger"
                        onclick="categoryMappingManager.deleteMapping('${data.source_category}')"
                        ${data.has_mapping ? '' : 'disabled'}>
                    <i class="fas fa-trash"></i>
                </button>
            </div>
        `;
    }

    onMappingChanged(cell) {
        const row = cell.getRow();
        const data = row.getData();

        this.updateMapping(data.source_category, data.target_category);
    }

    onStatusChanged(cell) {
        const row = cell.getRow();
        const data = row.getData();

        this.updateMappingStatus(data.source_category, data.is_active);
    }

    async updateMapping(sourceCategory, targetCategory) {
        try {
            const response = await fetch(`/api/category-mapping/mapping/${encodeURIComponent(sourceCategory)}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    target_category: targetCategory
                })
            });

            const result = await response.json();
            if (result.success) {
                this.showNotification('映射更新成功', 'success');
            } else {
                this.showNotification('映射更新失败: ' + result.error, 'error');
            }
        } catch (error) {
            console.error('更新映射失败:', error);
            this.showNotification('更新失败', 'error');
        }
    }

    async updateMappingStatus(sourceCategory, isActive) {
        try {
            const response = await fetch(`/api/category-mapping/mapping/${encodeURIComponent(sourceCategory)}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    is_active: isActive
                })
            });

            const result = await response.json();
            if (result.success) {
                this.showNotification('状态更新成功', 'success');
            } else {
                this.showNotification('状态更新失败: ' + result.error, 'error');
            }
        } catch (error) {
            console.error('更新状态失败:', error);
            this.showNotification('更新失败', 'error');
        }
    }

    async deleteMapping(sourceCategory) {
        if (!confirm(`确定要删除 "${sourceCategory}" 的映射吗？`)) {
            return;
        }

        try {
            const response = await fetch(`/api/category-mapping/mapping/${encodeURIComponent(sourceCategory)}`, {
                method: 'DELETE'
            });

            const result = await response.json();
            if (result.success) {
                this.showNotification('映射删除成功', 'success');
                await this.loadData();
                this.mappingTable.replaceData(this.filterCategories(this.allCategories));
                this.renderUnmappedCategories();
            } else {
                this.showNotification('映射删除失败: ' + result.error, 'error');
            }
        } catch (error) {
            console.error('删除映射失败:', error);
            this.showNotification('删除失败', 'error');
        }
    }

    editMapping(sourceCategory) {
        const modal = new bootstrap.Modal(document.getElementById('mappingModal'));
        const category = this.allCategories.find(cat => cat.source_category === sourceCategory);

        document.getElementById('sourceCategory').value = sourceCategory;
        document.getElementById('targetCategory').value = category.target_category || '';
        document.getElementById('isActive').checked = category.is_active;

        // 填充目标分类选项
        const targetSelect = document.getElementById('targetCategory');
        targetSelect.innerHTML = '<option value="">请选择目标分类</option>';
        this.basicCategories.forEach(cat => {
            const option = document.createElement('option');
            option.value = cat.code;
            option.textContent = cat.name;
            option.selected = cat.code === category.target_category;
            targetSelect.appendChild(option);
        });

        modal.show();
    }

    setupEventListeners() {
        // 添加映射按钮
        document.getElementById('add-mapping-btn').addEventListener('click', () => {
            this.showAddMappingDialog();
        });

        // 保存映射按钮
        document.getElementById('saveMappingBtn').addEventListener('click', () => {
            this.saveMapping();
        });

        // 切换显示状态
        document.getElementById('toggle-inactive-btn').addEventListener('click', () => {
            this.toggleInactive();
        });

        // 批量映射按钮
        document.getElementById('batch-map-btn').addEventListener('click', () => {
            this.showBatchMappingDialog();
        });

        // 批量保存按钮
        document.getElementById('saveBatchMappingBtn').addEventListener('click', () => {
            this.saveBatchMapping();
        });

        // 发现新分类按钮
        document.getElementById('discover-btn').addEventListener('click', () => {
            this.discoverNewCategories();
        });

        // 加载更多未映射分类
        document.getElementById('load-more-unmapped-btn').addEventListener('click', () => {
            this.loadMoreUnmapped();
        });
    }

    showAddMappingDialog() {
        const modal = new bootstrap.Modal(document.getElementById('mappingModal'));

        document.getElementById('sourceCategory').value = '';
        document.getElementById('targetCategory').value = '';
        document.getElementById('isActive').checked = true;

        // 填充目标分类选项
        const targetSelect = document.getElementById('targetCategory');
        targetSelect.innerHTML = '<option value="">请选择目标分类</option>';
        this.basicCategories.forEach(cat => {
            const option = document.createElement('option');
            option.value = cat.code;
            option.textContent = cat.name;
            targetSelect.appendChild(option);
        });

        // 启用源分类输入
        document.getElementById('sourceCategory').readonly = false;

        modal.show();
    }

    async saveMapping() {
        const sourceCategory = document.getElementById('sourceCategory').value.trim();
        const targetCategory = document.getElementById('targetCategory').value;
        const isActive = document.getElementById('isActive').checked;

        if (!sourceCategory || !targetCategory) {
            this.showNotification('请填写所有必要字段', 'error');
            return;
        }

        try {
            const response = await fetch('/api/category-mapping/mapping', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    source_category: sourceCategory,
                    target_category: targetCategory,
                    is_active: isActive
                })
            });

            const result = await response.json();
            if (result.success) {
                this.showNotification('映射保存成功', 'success');
                bootstrap.Modal.getInstance(document.getElementById('mappingModal')).hide();
                await this.loadData();
                this.mappingTable.replaceData(this.filterCategories(this.allCategories));
                this.renderUnmappedCategories();
            } else {
                this.showNotification('映射保存失败: ' + result.error, 'error');
            }
        } catch (error) {
            console.error('保存映射失败:', error);
            this.showNotification('保存失败', 'error');
        }
    }

    toggleInactive() {
        this.showInactive = !this.showInactive;
        const btn = document.getElementById('toggle-inactive-btn');
        btn.textContent = this.showInactive ? '仅显示启用' : '显示所有';

        this.mappingTable.replaceData(this.filterCategories(this.allCategories));
    }

    updateBatchButton() {
        const btn = document.getElementById('batch-map-btn');
        btn.disabled = this.selectedRows.length === 0;
    }

    showBatchMappingDialog() {
        if (this.selectedRows.length === 0) {
            this.showNotification('请先选择要操作的分类', 'error');
            return;
        }

        const modal = new bootstrap.Modal(document.getElementById('batchMappingModal'));
        const content = document.getElementById('batchMappingContent');

        let html = '';
        this.selectedRows.forEach(row => {
            const data = row.getData();
            html += `
                <div class="batch-mapping-item">
                    <div class="batch-mapping-source">${data.source_category}</div>
                    <div class="batch-mapping-target">
                        <select class="form-select form-select-sm" data-source="${data.source_category}">
                            <option value="">请选择目标分类</option>
                            ${this.basicCategories.map(cat =>
                                `<option value="${cat.code}">${cat.name}</option>`
                            ).join('')}
                        </select>
                    </div>
                    <div class="batch-mapping-check">
                        <div class="form-check">
                            <input type="checkbox" class="form-check-input"
                                   data-source="${data.source_category}" checked>
                        </div>
                    </div>
                </div>
            `;
        });

        content.innerHTML = html;
        modal.show();
    }

    async saveBatchMapping() {
        const items = document.querySelectorAll('.batch-mapping-item');
        const mappings = [];

        items.forEach(item => {
            const checkbox = item.querySelector('input[type="checkbox"]');
            const select = item.querySelector('select');

            if (checkbox.checked && select.value) {
                mappings.push({
                    source_category: select.dataset.source,
                    target_category: select.value
                });
            }
        });

        if (mappings.length === 0) {
            this.showNotification('请选择要映射的分类和目标分类', 'error');
            return;
        }

        try {
            const response = await fetch('/api/category-mapping/batch-mapping', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ mappings })
            });

            const result = await response.json();
            if (result.success) {
                this.showNotification(result.data.message, 'success');
                bootstrap.Modal.getInstance(document.getElementById('batchMappingModal')).hide();
                await this.loadData();
                this.mappingTable.replaceData(this.filterCategories(this.allCategories));
                this.renderUnmappedCategories();
            } else {
                this.showNotification('批量映射失败: ' + result.error, 'error');
            }
        } catch (error) {
            console.error('批量映射失败:', error);
            this.showNotification('批量映射失败', 'error');
        }
    }

    async discoverNewCategories() {
        try {
            const response = await fetch('/api/category-mapping/discover-categories');
            const result = await response.json();

            if (result.success) {
                this.showNotification(`发现 ${result.data.unmapped_count} 个未映射分类`, 'info');
                this.renderUnmappedCategories();
            } else {
                this.showNotification('发现分类失败: ' + result.error, 'error');
            }
        } catch (error) {
            console.error('发现分类失败:', error);
            this.showNotification('发现分类失败', 'error');
        }
    }

    renderUnmappedCategories() {
        const container = document.getElementById('unmapped-categories');
        const unmapped = this.allCategories
            .filter(cat => !cat.has_mapping || !cat.is_active)
            .sort((a, b) => b.transaction_count - a.transaction_count)
            .slice(0, 10);

        if (unmapped.length === 0) {
            container.innerHTML = '<p class="text-muted text-center">没有未映射的分类</p>';
            return;
        }

        let html = '';
        unmapped.forEach(category => {
            html += `
                <div class="unmapped-category-item">
                    <div>
                        <div class="unmapped-category-name">${category.source_category}</div>
                        <small class="unmapped-category-count">${category.transaction_count} 笔交易</small>
                    </div>
                    <div class="unmapped-category-action">
                        <button class="btn btn-sm btn-outline-primary"
                                onclick="categoryMappingManager.quickMap('${category.source_category}')">
                            映射
                        </button>
                    </div>
                </div>
            `;
        });

        container.innerHTML = html;
    }

    quickMap(sourceCategory) {
        this.editMapping(sourceCategory);
    }

    loadMoreUnmapped() {
        // 这里可以实现加载更多未映射分类的逻辑
        this.showNotification('加载更多功能开发中...', 'info');
    }

    updateStatistics(stats) {
        document.getElementById('total-sources').textContent = stats.unique_sources;
        document.getElementById('mapped-sources').textContent = stats.mapped_sources;
        document.getElementById('unmapped-sources').textContent = stats.unique_sources - stats.mapped_sources;
        document.getElementById('mapping-rate').textContent = stats.mapping_rate + '%';
    }

    showNotification(message, type = 'info') {
        const toast = document.createElement('div');
        toast.className = `toast align-items-center text-white bg-${type === 'error' ? 'danger' : type === 'success' ? 'success' : 'primary'} border-0`;
        toast.setAttribute('role', 'alert');

        toast.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        `;

        const container = document.createElement('div');
        container.className = 'toast-container position-fixed top-0 end-0 p-3';
        container.appendChild(toast);
        document.body.appendChild(container);

        const bsToast = new bootstrap.Toast(toast);
        bsToast.show();

        toast.addEventListener('hidden.bs.toast', () => {
            container.remove();
        });
    }
}

// 初始化
const categoryMappingManager = new CategoryMappingManager();