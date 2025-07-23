/**
 * 核心通用工具函数
 * 提供基础的辅助函数和工具方法
 *
 * 注意：专门功能已拆分到独立模块：
 * - 格式化函数 → formatters.js
 * - 验证函数 → validators.js
 * - 通知系统 → notifications.js
 * - API请求 → api-helpers.js
 * - DOM操作 → dom-utils.js
 */

import { formatCurrency } from './formatters.js';
import { getCSSColor } from './dom-utils.js';

/**
 * 防抖函数
 * @param {Function} func - 要防抖的函数
 * @param {number} wait - 等待时间（毫秒）
 * @returns {Function} 防抖后的函数
 */
export function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

/**
 * 节流函数
 * @param {Function} func - 要节流的函数
 * @param {number} limit - 时间间隔（毫秒）
 * @returns {Function} 节流后的函数
 */
export function throttle(func, limit) {
    let inThrottle;
    return function(...args) {
        if (!inThrottle) {
            func.apply(this, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

/**
 * URL 处理工具
 */
export const urlHandler = {
    /**
     * 获取URL查询参数值
     * @param {string} param - 参数名
     * @returns {string|null} 参数值
     */
    get(param) {
        const urlParams = new URLSearchParams(window.location.search);
        return urlParams.get(param);
    },

    /**
     * 设置URL查询参数
     * @param {string} param - 参数名
     * @param {string} value - 参数值
     * @param {boolean} reload - 是否重新加载页面，默认true
     */
    set(param, value, reload = true) {
        const url = new URL(window.location);
        url.searchParams.set(param, value);
        
        if (reload) {
            window.location.href = url.toString();
        } else {
            window.history.pushState({}, '', url.toString());
        }
    },

    /**
     * 移除URL查询参数
     * @param {string} param - 参数名
     * @param {boolean} reload - 是否重新加载页面，默认true
     */
    remove(param, reload = true) {
        const url = new URL(window.location);
        url.searchParams.delete(param);
        
        if (reload) {
            window.location.href = url.toString();
        } else {
            window.history.pushState({}, '', url.toString());
        }
    },

    /**
     * 批量设置URL查询参数
     * @param {Object} params - 参数对象
     * @param {boolean} reload - 是否重新加载页面，默认true
     */
    setMultiple(params, reload = true) {
        const url = new URL(window.location);
        
        Object.entries(params).forEach(([key, value]) => {
            if (value !== null && value !== undefined && value !== '') {
                url.searchParams.set(key, value);
            } else {
                url.searchParams.delete(key);
            }
        });
        
        if (reload) {
            window.location.href = url.toString();
        } else {
            window.history.pushState({}, '', url.toString());
        }
    },

    /**
     * 获取当前所有查询参数
     * @returns {Object} 参数对象
     */
    getAll() {
        const urlParams = new URLSearchParams(window.location.search);
        const params = {};
        for (const [key, value] of urlParams) {
            params[key] = value;
        }
        return params;
    }
};

// API服务已迁移到 api-helpers.js

// UI组件已迁移到 dom-utils.js

/**
 * ECharts 轻量级工具函数
 * 提供项目统一的图表配置和工具函数，不封装ECharts API
 */

/**
 * 获取项目颜色配置
 * @returns {Object} 颜色配置对象
 */
/**
 * 从CSS变量动态获取颜色值
 * @param {string} colorName - Bootstrap颜色名称（如 'primary', 'success'）
 * @returns {string} 颜色值
 */
export function getCSSColorValue(colorName) {
    const value = getComputedStyle(document.documentElement)
        .getPropertyValue(`--bs-${colorName}`)?.trim();
    return value || '#6c757d'; // 默认为secondary颜色
}

/**
 * 获取通用的图表样式配置
 * @returns {Object} 样式配置对象
 */
export function getChartStyles() {
    return {
        tooltip: {
            backgroundColor: getCSSColor('--bs-card-bg') || '#ffffff',
            borderColor: getCSSColor('--bs-border-color') || '#dee2e6',
            borderWidth: 1,
            textStyle: {
                color: getCSSColor('--bs-body-color') || '#212529',
                fontSize: 12
            }
        },
        grid: {
            left: '3%',
            right: '4%',
            bottom: '3%',
            containLabel: true
        },
        axisStyle: {
            axisLine: {
                lineStyle: { color: getCSSColor('--bs-border-color') || '#dee2e6' }
            },
            axisLabel: {
                color: getCSSColor('--bs-secondary') || '#6c757d',
                fontSize: 11
            },
            splitLine: {
                lineStyle: { color: getCSSColor('--bs-border-color-translucent') || 'rgba(0,0,0,.125)' }
            }
        }
    };
}

/**
 * 简单的图表实例管理器（防止内存泄漏）
 */
export const ChartRegistry = {
    charts: new Map(),

    /**
     * 注册图表实例
     * @param {string} id - 图表ID
     * @param {Object} chart - ECharts实例
     */
    register(id, chart) {
        // 先销毁现有实例
        this.destroy(id);

        // 注册新实例
        this.charts.set(id, chart);

        // 添加响应式支持
        const resizeHandler = () => {
            if (chart && !chart.isDisposed()) {
                chart.resize();
            }
        };
        window.addEventListener('resize', resizeHandler);
        chart._resizeHandler = resizeHandler;
    },

    /**
     * 销毁图表实例
     * @param {string} id - 图表ID
     */
    destroy(id) {
        const chart = this.charts.get(id);
        if (chart && !chart.isDisposed()) {
            // 移除resize监听器
            if (chart._resizeHandler) {
                window.removeEventListener('resize', chart._resizeHandler);
            }
            chart.dispose();
            this.charts.delete(id);
        }
    },

    /**
     * 获取图表实例
     * @param {string} id - 图表ID
     * @returns {Object|null} ECharts实例
     */
    get(id) {
        return this.charts.get(id) || null;
    },

    /**
     * 销毁所有图表实例
     */
    destroyAll() {
        this.charts.forEach((_, id) => {
            this.destroy(id);
        });
    }
};

// 页面卸载时清理所有图表实例
window.addEventListener('beforeunload', () => {
    ChartRegistry.destroyAll();
});

/**
 * Tabulator 表格工具函数
 * 提供项目统一的表格配置和工具函数
 */

/**
 * 获取Tabulator中文本地化配置
 * @returns {Object} 中文本地化配置
 */
export function getTabulatorLocale() {
    return {
        "zh-cn": {
            "pagination": {
                "page_size": "每页显示",
                "page_title": "显示页面",
                "first": "首页",
                "first_title": "首页",
                "last": "末页",
                "last_title": "末页",
                "prev": "上一页",
                "prev_title": "上一页",
                "next": "下一页",
                "next_title": "下一页",
                "all": "全部"
            },
            "headerFilters": {
                "default": "筛选...",
                "columns": {
                    "name": "按名称筛选..."
                }
            },
            "groups": {
                "item": "项目",
                "items": "项目"
            },
            "sort": {
                "sortAsc": "升序排列",
                "sortDesc": "降序排列"
            },
            "columns": {
                "name": "名称"
            },
            "data": {
                "loading": "加载中...",
                "error": "错误"
            }
        }
    };
}

/**
 * 获取Tabulator通用配置
 * @returns {Object} 通用配置对象
 */
export function getTabulatorCommonConfig() {
    return {
        layout: "fitColumns",
        responsiveLayout: "hide",
        pagination: "local",
        paginationSize: 20,
        paginationSizeSelector: [10, 20, 50, 100],
        movableColumns: true,
        resizableRows: true,
        selectable: true,
        locale: "zh-cn",
        langs: getTabulatorLocale(),
        headerFilterPlaceholder: "筛选...",
        placeholder: "没有找到匹配的记录",
        // 样式配置
        rowHeight: 45,
        headerHeight: 50,
        // 主题样式
        cssClass: "table-bootstrap5"
    };
}

/**
 * 获取财务数据专用的列格式化器
 * @returns {Object} 格式化器对象
 */
export function getTabulatorFormatters() {
    return {
        // 货币格式化器
        currency: function(cell) {
            const value = cell.getValue();
            if (value === null || value === undefined || value === '') return '';

            const formatted = formatCurrency(Math.abs(value));

            if (value > 0) {
                return `<span class="text-success fw-semibold">+${formatted}</span>`;
            } else if (value < 0) {
                return `<span class="text-danger fw-semibold">-${formatted}</span>`;
            } else {
                return `<span class="text-muted">${formatted}</span>`;
            }
        },

        // 余额格式化器
        balance: function(cell) {
            const value = cell.getValue();
            if (value === null || value === undefined || value === '') return '';

            return `<span class="fw-semibold">${formatCurrency(value)}</span>`;
        },

        // 日期格式化器
        dateFormat: function(cell) {
            const value = cell.getValue();
            if (!value) return '';

            const date = new Date(value);
            return date.toLocaleDateString('zh-CN', {
                year: 'numeric',
                month: '2-digit',
                day: '2-digit'
            });
        },

        // 文本截断格式化器
        textTruncate: function(cell, formatterParams) {
            const value = cell.getValue();
            if (!value) return '';

            const maxLength = formatterParams.maxLength || 20;
            const truncated = value.length > maxLength
                ? value.substring(0, maxLength) + '...'
                : value;

            return `<span title="${value}" class="text-truncate d-inline-block" style="max-width: 100%;">${truncated}</span>`;
        }
    };
}

// ==================== 分类相关工具函数 ====================



/**
 * 创建分类列的格式化器
 * @param {Object} categoriesConfig - 分类配置信息
 * @returns {Function} 格式化器函数
 */
function createCategoryFormatter(categoriesConfig) {
    return function(cell) {
        const category = cell.getValue();

        // 使用传入的分类配置
        let categoryInfo;
        if (categoriesConfig && categoriesConfig[category]) {
            categoryInfo = categoriesConfig[category];
        } else {
            // 配置缺失时使用最小化的通用默认值
            categoryInfo = {
                name: '未知分类',
                icon: 'help-circle',
                color: 'secondary'
            };
        }

        return `<span class="category-badge d-flex align-items-center">
            <i data-lucide="${categoryInfo.icon}" class="text-${categoryInfo.color}" style="width: 1rem; height: 1rem;"></i>
            <span class="ms-2 small">${categoryInfo.name}</span>
        </span>`;
    };
}

/**
 * 创建分类筛选器选项
 * @param {Object} categoriesConfig - 分类配置信息
 * @returns {Object} 筛选器参数
 */
function createCategoryFilterParams(categoriesConfig) {
    const filterOptions = { '': '全部分类' };

    // 使用分类配置构建筛选选项
    if (categoriesConfig && Object.keys(categoriesConfig).length > 0) {
        for (const [code, info] of Object.entries(categoriesConfig)) {
            filterOptions[code] = info.name;
        }
    }
    // 如果没有配置，筛选器将只有"全部分类"选项

    return {
        values: filterOptions,
        clearable: true,
        placeholder: "选择分类"
    };
}

/**
 * 获取财务表格专用的列配置
 * @param {Object} categoriesConfig - 分类配置信息
 * @returns {Object} 列配置对象
 */
export function getFinancialTableColumns(categoriesConfig = {}) {
    const formatters = getTabulatorFormatters();

    return {
        // 交易记录表格列配置（优化后的列顺序）
        transactions: [
            {
                title: "日期",
                field: "date",
                sorter: "string",
                headerFilter: "input",
                headerFilterPlaceholder: "YYYY-MM-DD 或 YYYY-MM",
                headerFilterFunc: function(headerValue, rowValue) {
                    if (!headerValue) return true;

                    const searchValue = headerValue.trim();
                    const dateValue = rowValue || '';

                    // 支持完整日期匹配和年月筛选
                    if (searchValue.length === 10) { // YYYY-MM-DD
                        return dateValue === searchValue;
                    } else if (searchValue.length === 7) { // YYYY-MM
                        return dateValue.startsWith(searchValue);
                    } else {
                        return dateValue.startsWith(searchValue);
                    }
                },
                width: 120,
                formatter: formatters.dateFormat,
                responsive: 0 // 最高优先级，始终显示
            },
            {
                title: "分类",
                field: "category",
                headerFilter: "list",
                headerFilterParams: createCategoryFilterParams(categoriesConfig),
                width: 100,
                formatter: createCategoryFormatter(categoriesConfig),
                sorter: "string",
                responsive: 1 // 高优先级
            },
            {
                title: "对手信息",
                field: "counterparty",
                headerFilter: "list",
                headerFilterParams: {
                    valuesLookup: true, // 从表格数据中查找唯一值
                    valuesLookupField: "counterparty", // 指定查找的字段
                    multiselect: true,
                    clearable: true,
                    placeholder: "选择对手信息",
                    maxHeight: 200
                },
                width: 150,
                formatter: formatters.textTruncate,
                formatterParams: { maxLength: 15 },
                responsive: 2 // 中等优先级
            },
            {
                title: "金额",
                field: "amount",
                sorter: "number",
                headerFilter: "input",
                headerFilterPlaceholder: "如: 100-1000, >500, <100",
                headerFilterFunc: createAmountRangeFilter(),
                width: 120,
                formatter: formatters.currency,
                hozAlign: "right",
                responsive: 0 // 最高优先级，始终显示
            },
            {
                title: "账户",
                field: "account",
                headerFilter: "list",
                headerFilterParams: {
                    valuesLookup: true, // 从表格数据中查找唯一值
                    valuesLookupField: "account", // 指定查找的字段
                    multiselect: true,
                    clearable: true,
                    placeholder: "选择账户",
                    maxHeight: 200
                },
                width: 150,
                formatter: formatters.textTruncate,
                formatterParams: { maxLength: 15 },
                responsive: 4 // 较低优先级
            },
            {
                title: "摘要",
                field: "description",
                headerFilter: "input",
                headerFilterPlaceholder: "筛选摘要",
                minWidth: 200,
                formatter: formatters.textTruncate,
                formatterParams: { maxLength: 25 },
                responsive: 5 // 最低优先级，小屏幕隐藏
            }
        ]
    };
}

/**
 * Tabulator实例管理器（类似ChartRegistry）
 */
export const TableRegistry = {
    tables: new Map(),

    /**
     * 注册表格实例
     * @param {string} id - 表格ID
     * @param {Object} table - Tabulator实例
     */
    register(id, table) {
        // 先销毁现有实例
        this.destroy(id);

        // 注册新实例
        this.tables.set(id, table);

        // 添加响应式支持
        const resizeHandler = () => {
            if (table && !table.destroyed) {
                table.redraw();
            }
        };
        window.addEventListener('resize', resizeHandler);
        table._resizeHandler = resizeHandler;
    },

    /**
     * 销毁表格实例
     * @param {string} id - 表格ID
     */
    destroy(id) {
        const table = this.tables.get(id);
        if (table && !table.destroyed) {
            // 移除resize监听器
            if (table._resizeHandler) {
                window.removeEventListener('resize', table._resizeHandler);
            }
            table.destroy();
            this.tables.delete(id);
        }
    },

    /**
     * 获取表格实例
     * @param {string} id - 表格ID
     * @returns {Object|null} Tabulator实例
     */
    get(id) {
        return this.tables.get(id) || null;
    },

    /**
     * 销毁所有表格实例
     */
    destroyAll() {
        this.tables.forEach((_, id) => {
            this.destroy(id);
        });
    }
};

/**
 * 创建交易记录表格
 * @param {string} containerId - 容器ID
 * @param {Array} data - 表格数据
 * @param {Object} options - 额外配置选项
 * @param {Object} categoriesConfig - 分类配置信息
 * @returns {Object} Tabulator实例
 */
export function createTransactionsTable(containerId, data = [], options = {}, categoriesConfig = {}) {
    const commonConfig = getTabulatorCommonConfig();
    const columns = getFinancialTableColumns(categoriesConfig).transactions;

    // 合并配置
    const config = {
        ...commonConfig,
        data: data,
        columns: columns,
        // 交易记录特定配置
        initialSort: [
            { column: "date", dir: "desc" }
        ],
        // 行样式配置
        rowFormatter: function(row) {
            const data = row.getData();
            const element = row.getElement();

            // 根据金额大小添加样式
            if (data.amount > 1000) {
                element.style.backgroundColor = "#e8f5e8";
            } else if (data.amount < -1000) {
                element.style.backgroundColor = "#ffeaea";
            }
        },
        ...options
    };

    // 创建表格实例
    const table = new window.Tabulator(`#${containerId}`, config);

    // 添加表格渲染完成后的回调，初始化图标
    table.on("tableBuilt", function(){
        // 初始化Lucide图标
        if (typeof lucide !== 'undefined' && lucide.createIcons) {
            lucide.createIcons();
        }
    });

    table.on("renderComplete", function(){
        // 每次重新渲染后都初始化图标
        if (typeof lucide !== 'undefined' && lucide.createIcons) {
            lucide.createIcons();
        }
    });

    // 注册到管理器
    TableRegistry.register(containerId, table);

    return table;
}

/**
 * 更新表格汇总信息（用于交易记录）
 * @param {Object} table - Tabulator实例
 * @param {Object} summaryElements - 汇总元素对象
 */
export function updateTransactionsSummary(table, summaryElements) {
    if (!table || !summaryElements) return;

    try {
        const data = table.getData();

        let totalIncome = 0;
        let totalExpense = 0;
        let incomeCount = 0;
        let expenseCount = 0;
        let latestBalance = 0;

        data.forEach(row => {
            const amount = parseFloat(row.amount) || 0;
            const balance = parseFloat(row.balance) || 0;

            if (amount > 0) {
                totalIncome += amount;
                incomeCount++;
            } else if (amount < 0) {
                totalExpense += Math.abs(amount);
                expenseCount++;
            }

            // 假设数据按日期排序，取最新的余额
            latestBalance = balance;
        });

        // 更新DOM元素
        if (summaryElements.totalIncome) {
            summaryElements.totalIncome.textContent = formatCurrency(totalIncome);
        }
        if (summaryElements.totalExpense) {
            summaryElements.totalExpense.textContent = formatCurrency(totalExpense);
        }
        if (summaryElements.incomeCount) {
            summaryElements.incomeCount.textContent = incomeCount;
        }
        if (summaryElements.expenseCount) {
            summaryElements.expenseCount.textContent = expenseCount;
        }
        if (summaryElements.latestBalance) {
            summaryElements.latestBalance.textContent = formatCurrency(latestBalance);
        }

    } catch (error) {
        console.error('更新交易汇总信息失败:', error);
    }
}

/**
 * 创建金额范围筛选器
 * @returns {Function} 自定义筛选器函数
 */
function createAmountRangeFilter() {
    return function(headerValue, rowValue) {
        if (!headerValue) return true;

        const amount = parseFloat(rowValue) || 0;
        const input = headerValue.trim();

        // 支持多种格式：
        // "100-1000" - 范围
        // ">500" - 大于
        // "<100" - 小于
        // "=50" - 等于

        if (input.includes('-')) {
            const [min, max] = input.split('-').map(v => parseFloat(v.trim()));
            return amount >= (min || 0) && amount <= (max || Infinity);
        } else if (input.startsWith('>')) {
            const threshold = parseFloat(input.substring(1));
            return amount > threshold;
        } else if (input.startsWith('<')) {
            const threshold = parseFloat(input.substring(1));
            return amount < threshold;
        } else if (input.startsWith('=')) {
            const target = parseFloat(input.substring(1));
            return Math.abs(amount - target) < 0.01;
        } else {
            // 直接数字，按等于处理
            const target = parseFloat(input);
            return !isNaN(target) && Math.abs(amount - target) < 0.01;
        }
    };
}

// 页面卸载时清理所有表格实例
window.addEventListener('beforeunload', () => {
    TableRegistry.destroyAll();
});

