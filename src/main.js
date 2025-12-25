import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import Notification from './components/common/Notification.vue'
import { registerGlobalErrorHandler } from './utils/errorHandler.js'
import { useNotificationStore } from './stores/notificationStore.js'
import './style.css'

const app = createApp(App)

// 安装 Pinia (必须在使用 store 之前)
const pinia = createPinia()
app.use(pinia)

// 安装 Router
app.use(router)

// ⚠️ 在 Pinia 初始化后,获取 notificationStore 传给错误处理器
const notificationStore = useNotificationStore()
registerGlobalErrorHandler(app, notificationStore)

// 注册全局通知组件
app.component('Notification', Notification)

app.mount('#app')
