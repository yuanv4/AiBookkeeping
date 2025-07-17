/**
 * 页面基类
 * 提供通用的页面初始化逻辑和生命周期管理
 */
export default class BasePage {
    constructor() {
        this.elements = {};
    }
    
    /**
     * 页面初始化入口
     * 子类可以重写此方法来定制初始化流程
     */
    init() {
        this.bindElements();
        this.setupEventListeners();
        this.renderPage();
    }
    
    /**
     * 绑定页面元素
     * 子类必须重写此方法来定义页面元素的绑定逻辑
     */
    bindElements() {
        // 子类实现
    }
    
    /**
     * 设置事件监听器
     * 子类可以重写此方法来添加事件监听逻辑
     */
    setupEventListeners() {
        // 子类实现
    }
    
    /**
     * 渲染页面内容
     * 子类可以重写此方法来定义页面渲染逻辑
     */
    renderPage() {
        // 子类实现
    }
    
    /**
     * 初始化Lucide图标
     * 统一的图标初始化方法，避免重复调用
     */
    initializeIcons() {
        try {
            if (typeof lucide !== 'undefined' && lucide.createIcons) {
                lucide.createIcons();
                console.log('Lucide图标初始化成功');
            } else {
                console.warn('Lucide图标库未加载');
            }
        } catch (error) {
            console.error('初始化Lucide图标失败:', error);
        }
    }

    /**
     * 页面销毁清理
     * 子类可以重写此方法来定义清理逻辑
     */
    destroy() {
        // 移除事件监听器等清理工作
        // 子类实现
    }
}