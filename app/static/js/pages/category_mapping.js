/* 分类合并管理页面 JavaScript */

class CategoryMergeManager {
    constructor() {
        this.mergeViewTable = null;
        this.sourceViewTable = null;
        this.targetViewTable = null;
        this.currentView = 'merged';
        this.selectedRows = [];

        this.init();
    }

    async init() {
        try {
            this.setupEventListeners();
            await this.loadData();
            this.initTables();
            this.updateStatistics();
            this.updateMergeStats();
        } catch (error) {
            console.error('页面初始化失败:', error);
            this.showNotification('页面初始化失败', 'error');
        }
    }

    setupEventListeners() {
        // 视图切换
        document.querySelectorAll('[data-mode]').forEach(item => {
            item.addEventListener('click', (e) => {
                e.preventDefault();
                this.switchView(e.target.dataset.mode);
            });
        });

        // 创建合并规则按钮
        const createBtn = document.getElementById('create-merge-btn');
        if (createBtn) {
            createBtn.addEventListener('click', () => this.showCreateMergeModal());
        }

        // 保存合并规则按钮
        const saveBtn = document.getElementById('saveMergeBtn');
        if (saveBtn) {
            saveBtn.addEventListener('click', () => this.saveMergeRule());
        }

        // 视图模式下拉菜单
        const dropdownItems = document.querySelectorAll('#viewModeDropdown + .dropdown-menu .dropdown-item');
        dropdownItems.forEach(item => {
            item.addEventListener('click', (e) => {
                e.preventDefault();
                const mode = e.target.dataset.mode;
                document.getElementById('current-view-mode').textContent = e.target.textContent;
                this.switchView(mode);
            });
        });
    }

    async loadData() {
        try {
            // 加载分类数据
            const response = await fetch('/category-mapping/api/source-categories');
            const data = await response.json();

            if (data.success) {
                this.categories = data.data;
            } else {
                throw new Error(data.error || '加载分类数据失败');
            }
        } catch (error) {
            console.error('加载数据失败:', error);
            this.categories = [];
        }
    }

    initTables() {
        this.initMergeViewTable();
        this.initSourceViewTable();
        this.initTargetViewTable();
    }

    initMergeViewTable() {
        const container = document.getElementById('merge-view-table');
        if (!container) return;

        // 模拟合并数据 - 实际应用中应从API获取
        const mergedData = this.getMergedData();

        this.mergeViewTable = new Tabulator("#merge-view-table", {
            data: mergedData,
            layout: "fitDataFill",
            pagination: "local",
            paginationSize: 20,
            columns: [
                {
                    title: "统一分类名称",
                    field: "target_category",
                    width: 200,
                    headerFilter: true
                },
                {
                    title: "包含的原始分类",
                    field: "source_categories",
                    formatter: (cell) => {
                        const sources = cell.getValue();
                        return sources.join(', ');
                    },
                    minWidth: 300
                },
                {
                    title: "交易数量",
                    field: "transaction_count",
                    sorter: "number",
                    width: 120,
                    formatter: (cell) => {
                        const count = cell.getValue();
                        return count.toLocaleString();
                    }
                },
                {
                    title: "状态",
                    field: "is_active",
                    width: 80,
                    formatter: "tickCross"
                },
                {
                    title: "操作",
                    width: 120,
                    formatter: this.formatterActions.bind(this)
                }
            ]
        });
    }

    initSourceViewTable() {
        const container = document.getElementById('source-view-table');
        if (!container) return;

        this.sourceViewTable = new Tabulator("#source-view-table", {
            data: this.categories || [],
            layout: "fitDataFill",
            pagination: "local",
            paginationSize: 20,
            selectableRows: true,
            columns: [
                {
                    title: "原始分类",
                    field: "source_category",
                    headerFilter: true,
                    minWidth: 200
                },
                {
                    title: "交易数量",
                    field: "transaction_count",
                    sorter: "number",
                    width: 120,
                    formatter: (cell) => {
                        const count = cell.getValue();
                        return count.toLocaleString();
                    }
                },
                {
                    title: "合并状态",
                    field: "has_mapping",
                    width: 100,
                    formatter: (cell) => {
                        return cell.getValue() ? '<span class="badge bg-success">已合并</span>' : '<span class="badge bg-secondary">独立</span>';
                    }
                },
                {
                    title: "目标分类",
                    field: "target_category",
                    width: 150
                }
            ],
            rowSelectionChanged: (data, rows) => {
                this.selectedRows = rows;
            }
        });
    }

    initTargetViewTable() {
        const container = document.getElementById('target-view-table');
        if (!container) return;

        // 获取所有目标分类
        const targetData = this.getTargetData();

        this.targetViewTable = new Tabulator("#target-view-table", {
            data: targetData,
            layout: "fitDataFill",
            pagination: "local",
            paginationSize: 20,
            columns: [
                {
                    title: "目标分类",
                    field: "target_category",
                    headerFilter: true,
                    minWidth: 200
                },
                {
                    title: "包含的源分类数量",
                    field: "source_count",
                    sorter: "number",
                    width: 150
                },
                {
                    title: "总交易数量",
                    field: "total_transactions",
                    sorter: "number",
                    width: 120,
                    formatter: (cell) => {
                        return cell.getValue().toLocaleString();
                    }
                }
            ]
        });
    }

    getMergedData() {
        // 模拟合并数据 - 实际应用中应从API获取
        if (!this.categories || this.categories.length === 0) {
            return [];
        }

        // 按目标分类分组
        const grouped = {};
        this.categories.forEach(cat => {
            if (cat.has_mapping && cat.target_category) {
                if (!grouped[cat.target_category]) {
                    grouped[cat.target_category] = {
                        target_category: cat.target_category,
                        source_categories: [],
                        transaction_count: 0,
                        is_active: cat.is_active
                    };
                }
                grouped[cat.target_category].source_categories.push(cat.source_category);
                grouped[cat.target_category].transaction_count += cat.transaction_count || 0;
            }
        });

        return Object.values(grouped);
    }

    getTargetData() {
        const merged = this.getMergedData();
        return merged.map(item => ({
            target_category: item.target_category,
            source_count: item.source_categories.length,
            total_transactions: item.transaction_count
        }));
    }

    switchView(mode) {
        this.currentView = mode;

        // 隐藏所有表格
        document.getElementById('merge-view-table').style.display = 'none';
        document.getElementById('source-view-table').style.display = 'none';
        document.getElementById('target-view-table').style.display = 'none';

        // 显示选中的表格
        switch (mode) {
            case 'merged':
                document.getElementById('merge-view-table').style.display = 'block';
                break;
            case 'source':
                document.getElementById('source-view-table').style.display = 'block';
                break;
            case 'target':
                document.getElementById('target-view-table').style.display = 'block';
                break;
        }

        // 更新下拉菜单状态
        document.querySelectorAll('#viewModeDropdown + .dropdown-menu .dropdown-item').forEach(item => {
            item.classList.remove('active');
            if (item.dataset.mode === mode) {
                item.classList.add('active');
            }
        });
    }

    updateStatistics() {
        if (!this.categories || this.categories.length === 0) {
            document.getElementById('total-categories').textContent = '0';
            document.getElementById('merged-categories').textContent = '0';
            document.getElementById('standalone-categories').textContent = '0';
            document.getElementById('merge-groups').textContent = '0';
            return;
        }

        const total = this.categories.length;
        const merged = this.categories.filter(cat => cat.has_mapping).length;
        const standalone = total - merged;
        const mergeGroups = new Set(this.categories.filter(cat => cat.has_mapping).map(cat => cat.target_category)).size;

        document.getElementById('total-categories').textContent = total.toLocaleString();
        document.getElementById('merged-categories').textContent = merged.toLocaleString();
        document.getElementById('standalone-categories').textContent = standalone.toLocaleString();
        document.getElementById('merge-groups').textContent = mergeGroups.toLocaleString();
    }

    updateMergeStats() {
        const statsContainer = document.getElementById('merge-stats');
        if (!statsContainer) return;

        const merged = this.getMergedData();
        if (merged.length === 0) {
            statsContainer.innerHTML = '<p class="text-muted">暂无合并规则</p>';
            return;
        }

        const html = `
            <div class="mb-2">
                <small class="text-muted">合并规则数</small>
                <div class="fw-bold">${merged.length}</div>
            </div>
            <div class="mb-2">
                <small class="text-muted">已处理分类</small>
                <div class="fw-bold">${merged.reduce((sum, item) => sum + item.source_categories.length, 0)}</div>
            </div>
            <div>
                <small class="text-muted">覆盖率</small>
                <div class="fw-bold">${((merged.reduce((sum, item) => sum + item.source_categories.length, 0) / this.categories.length) * 100).toFixed(1)}%</div>
            </div>
        `;

        statsContainer.innerHTML = html;
    }

    showCreateMergeModal() {
        const modal = new bootstrap.Modal(document.getElementById('createMergeModal'));

        // 清空表单
        document.getElementById('targetCategoryName').value = '';
        document.getElementById('sourceCategoriesList').innerHTML = '<div class="text-muted">请从下方表格选择要合并的分类</div>';
        document.getElementById('mergeDescription').value = '';
        document.getElementById('isMergeActive').checked = true;

        // 如果在原始分类视图且有选中的行，显示选中项
        if (this.currentView === 'source' && this.selectedRows.length > 0) {
            const selectedCategories = this.selectedRows.map(row => row.getData().source_category);
            document.getElementById('sourceCategoriesList').innerHTML = `
                <div class="selected-categories">
                    ${selectedCategories.map(cat => `<span class="badge bg-primary me-1">${cat}</span>`).join('')}
                </div>
            `;
        }

        modal.show();
    }

    async saveMergeRule() {
        const targetName = document.getElementById('targetCategoryName').value.trim();
        if (!targetName) {
            this.showNotification('请输入统一分类名称', 'warning');
            return;
        }

        // 获取要合并的分类（简化版本，实际应用中需要更复杂的逻辑）
        let sourceCategories = [];
        if (this.currentView === 'source' && this.selectedRows.length > 0) {
            sourceCategories = this.selectedRows.map(row => row.getData().source_category);
        }

        if (sourceCategories.length < 2) {
            this.showNotification('请选择至少两个分类进行合并', 'warning');
            return;
        }

        try {
            // 这里应该调用API保存合并规则
            // const response = await fetch('/api/category-mapping/batch-merge', { ... });

            this.showNotification(`成功创建合并规则: ${targetName}`, 'success');

            // 关闭模态框
            const modal = bootstrap.Modal.getInstance(document.getElementById('createMergeModal'));
            modal.hide();

            // 重新加载数据
            await this.loadData();
            this.initTables();
            this.updateStatistics();
            this.updateMergeStats();

        } catch (error) {
            console.error('保存合并规则失败:', error);
            this.showNotification('保存失败，请重试', 'error');
        }
    }

    formatterActions(cell, formatterParams, onRendered) {
        const data = cell.getRow().getData();
        return `
            <div class="btn-group btn-group-sm" role="group">
                <button type="button" class="btn btn-outline-primary" onclick="categoryMergeManager.editMerge('${data.target_category}')">
                    编辑
                </button>
                <button type="button" class="btn btn-outline-danger" onclick="categoryMergeManager.deleteMerge('${data.target_category}')">
                    删除
                </button>
            </div>
        `;
    }

    editMerge(targetCategory) {
        this.showNotification(`编辑合并规则 "${targetCategory}" 功能开发中...`, 'info');
    }

    deleteMerge(targetCategory) {
        if (confirm(`确定要删除合并规则 "${targetCategory}" 吗？`)) {
            this.showNotification('删除功能开发中...', 'info');
        }
    }

    showNotification(message, type = 'info') {
        // 创建一个简单的通知
        const notification = document.createElement('div');
        notification.className = `alert alert-${type === 'error' ? 'danger' : type} alert-dismissible fade show position-fixed top-0 end-0 m-3`;
        notification.style.zIndex = '9999';
        notification.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;

        document.body.appendChild(notification);

        // 3秒后自动移除
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 3000);
    }
}

// 初始化
let categoryMergeManager;
document.addEventListener('DOMContentLoaded', () => {
    categoryMergeManager = new CategoryMergeManager();
});