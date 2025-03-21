# 个人收支管理系统UI组件文档

## 1. 组件概述

本文档描述了个人收支管理系统中使用的UI组件、样式规范和交互设计。系统采用模块化的组件设计，确保界面风格统一和用户体验的一致性。

## 2. 布局组件

### 2.1 导航栏（NavBar）

```html
<nav class="nav-bar">
    <div class="nav-brand">
        <i class="fas fa-chart-line"></i>
        <span>个人收支管理</span>
    </div>
    <div class="nav-actions">
        <button class="btn-icon"><i class="fas fa-bell"></i></button>
        <button class="btn-icon"><i class="fas fa-user"></i></button>
    </div>
</nav>
```

#### 属性说明
- nav-bar: 顶部导航栏容器
- nav-brand: 品牌标识区域
- nav-actions: 导航操作区域
- btn-icon: 图标按钮

### 2.2 侧边栏（Sidebar）

```html
<nav class="sidebar">
    <div class="nav-menu">
        <h3><i class="fas fa-chart-pie"></i> 财务仪表盘</h3>
        <ul>
            <li><a href="dashboard.html"><i class="fas fa-home"></i> 仪表盘</a></li>
            <li><a href="transactions.html"><i class="fas fa-list"></i> 收支记录</a></li>
            
            <li><a href="accounts.html"><i class="fas fa-credit-card"></i> 账户管理</a></li>
            <li><a href="analysis.html"><i class="fas fa-chart-bar"></i> 账单分析</a></li>
        </ul>
    </div>
</nav>
```

#### 属性说明
- sidebar: 侧边导航容器
- nav-menu: 导航菜单
- active: 当前选中菜单项

### 2.3 页面布局（Layout）

```html
<div class="app-layout">
    <nav class="sidebar">...</nav>
    <main class="container">...</main>
</div>
```

#### 属性说明
- app-layout: 应用主布局
- container: 内容区域容器

## 3. 通用组件

### 3.1 按钮（Button）

```html
<!-- 主要按钮 -->
<button class="btn btn-primary">新增记录</button>

<!-- 次要按钮 -->
<button class="btn btn-outline">筛选</button>

<!-- 文本按钮 -->
<button class="btn btn-text">清除全部</button>

<!-- 图标按钮 -->
<button class="btn-icon"><i class="fas fa-bell"></i></button>
```

#### 属性说明
- btn: 基础按钮样式
- btn-primary: 主要按钮
- btn-outline: 描边按钮
- btn-text: 文本按钮
- btn-icon: 图标按钮

### 3.2 卡片（Card）

```html
<div class="card stat-card">
    <div class="stat-icon">
        <i class="fas fa-wallet"></i>
    </div>
    <div class="stat-content">
        <h3>总资产</h3>
        <p class="stat-value">¥152,360</p>
        <span class="stat-change positive">+5.2% 较上月</span>
    </div>
</div>
```

#### 属性说明
- card: 基础卡片样式
- stat-card: 统计卡片
- stat-icon: 统计图标
- stat-content: 统计内容
- stat-value: 统计数值
- stat-change: 变化指标

### 3.3 标签（Tag）

```html
<span class="filter-tag">
    <i class="fas fa-calendar"></i> 本月
    <button class="tag-remove"><i class="fas fa-times"></i></button>
</span>
```

#### 属性说明
- filter-tag: 筛选标签
- tag-remove: 删除按钮

## 4. 页面组件

### 4.1 页面标题（PageHeader）

```html
<div class="page-header">
    <h1>账户管理</h1>
    <div class="header-actions">
        <button class="btn btn-primary">
            <i class="fas fa-plus"></i> 添加账户
        </button>
    </div>
</div>
```

#### 属性说明
- page-header: 页面标题容器
- header-actions: 标题操作区

### 4.2 统计网格（StatsGrid）

```html
<div class="stats-grid">
    <div class="card stat-card">...</div>
    <div class="card stat-card">...</div>
</div>
```

#### 属性说明
- stats-grid: 统计卡片网格

### 4.3 筛选标签组（FilterTags）

```html
<div class="filter-tags">
    <span class="filter-tag">...</span>
    <span class="filter-tag">...</span>
    <button class="btn btn-text">清除全部</button>
</div>
```

#### 属性说明
- filter-tags: 筛选标签容器

## 5. 样式规范

### 5.1 颜色系统

```css
:root {
    --primary-color: #3498db;
    --success-color: #27ae60;
    --warning-color: #f1c40f;
    --danger-color: #e74c3c;
    --text-color: #2c3e50;
    --text-light: #7f8c8d;
    --border-color: #ecf0f1;
    --background-color: #f8f9fa;
}
```

### 5.2 字体规范

```css
body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    font-size: 14px;
    line-height: 1.5;
}

h1 { font-size: 24px; }
h2 { font-size: 20px; }
h3 { font-size: 16px; }
```

### 5.3 间距规范

```css
:root {
    --spacing-xs: 4px;
    --spacing-sm: 8px;
    --spacing-md: 16px;
    --spacing-lg: 24px;
    --spacing-xl: 32px;
}
```

### 5.4 阴影效果

```css
:root {
    --shadow-sm: 0 1px 3px rgba(0,0,0,0.12);
    --shadow-md: 0 4px 6px rgba(0,0,0,0.1);
    --shadow-lg: 0 10px 15px rgba(0,0,0,0.1);
}
```

## 6. 响应式设计

### 6.1 断点定义

```css
/* 移动端 */
@media (max-width: 767px) { ... }

/* 平板 */
@media (min-width: 768px) and (max-width: 1023px) { ... }

/* 桌面 */
@media (min-width: 1024px) { ... }
```

### 6.2 响应式布局

```css
/* 侧边栏响应式 */
@media (max-width: 767px) {
    .sidebar {
        position: fixed;
        transform: translateX(-100%);
    }
    
    .sidebar.active {
        transform: translateX(0);
    }
}

/* 统计网格响应式 */
@media (max-width: 767px) {
    .stats-grid {
        grid-template-columns: 1fr;
    }
}
```

## 7. 交互规范

### 7.1 状态反馈

- 按钮悬停效果
- 输入框焦点状态
- 加载状态指示
- 错误状态提示

### 7.2 动画效果

```css
/* 过渡动画 */
.btn {
    transition: all 0.3s ease;
}

/* 侧边栏切换动画 */
.sidebar {
    transition: transform 0.3s ease;
}

/* 卡片悬停效果 */
.card {
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.card:hover {
    transform: translateY(-2px);
    box-shadow: var(--shadow-lg);
}
```

## 8. 图标系统

### 8.1 图标库

使用Font Awesome图标库：
```html
<link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
```

### 8.2 常用图标

- 导航图标
  - fa-chart-line: 系统logo
  - fa-home: 仪表盘
  - fa-list: 收支记录
  - fa-wallet: 预算规划
  - fa-credit-card: 账户管理
  - fa-chart-bar: 账单分析

- 操作图标
  - fa-plus: 新增
  - fa-edit: 编辑
  - fa-trash: 删除
  - fa-filter: 筛选
  - fa-search: 搜索

- 状态图标
  - fa-check: 成功
  - fa-times: 错误
  - fa-exclamation: 警告
  - fa-spinner: 加载中

## 9. 可访问性

### 9.1 键盘导航

- 所有可交互元素可通过Tab键访问
- 使用适当的键盘快捷键
- 焦点状态清晰可见

### 9.2 ARIA属性

```html
<!-- 导航标记 -->
<nav aria-label="主导航">

<!-- 按钮状态 -->
<button aria-pressed="true">筛选</button>

<!-- 加载状态 -->
<div aria-busy="true">加载中...</div>
```

### 9.3 颜色对比度

- 确保文本与背景色的对比度符合WCAG标准
- 不仅依赖颜色传达信息
- 提供适当的文本替代方案