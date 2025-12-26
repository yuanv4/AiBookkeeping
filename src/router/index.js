import { createRouter, createWebHistory } from 'vue-router'
import { authApi } from '../api/index.js'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/LoginView.vue'),
    meta: { title: '登录', public: true }
  },
  {
    path: '/',
    redirect: '/dashboard'
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: () => import('../views/DashboardView.vue'),
    meta: { title: '仪表板', requiresAuth: true }
  },
  {
    path: '/analysis',
    name: 'Analysis',
    component: () => import('../views/AnalysisView.vue'),
    meta: { title: '数据分析', requiresAuth: true }
  },
  {
    path: '/transactions',
    name: 'Transactions',
    component: () => import('../views/TransactionsView.vue'),
    meta: { title: '账单明细', requiresAuth: true }
  },
  {
    path: '/settings',
    name: 'Settings',
    component: () => import('../views/SettingsView.vue'),
    meta: { title: '设置', requiresAuth: true },
    redirect: '/settings/ai',
    children: [
      {
        path: 'ai',
        name: 'AISettings',
        component: () => import('../components/settings/AIConfig.vue'),
        meta: { title: 'AI 配置', requiresAuth: true }
      },
      {
        path: 'data',
        name: 'DataSettings',
        component: () => import('../views/settings/DataSettings.vue'),
        meta: { title: '数据管理', requiresAuth: true }
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫:检查认证状态
router.beforeEach((to, from, next) => {
  // 设置页面标题
  document.title = to.meta.title ? `${to.meta.title} - AI 账单汇集工具` : 'AI 账单汇集工具'

  // 公开路由(如登录页)不需要认证
  if (to.meta.public) {
    // 如果已登录,访问登录页时重定向到首页
    if (authApi.isAuthenticated() && to.name === 'Login') {
      next('/')
      return
    }
    next()
    return
  }

  // 需要认证的路由
  if (to.meta.requiresAuth || !to.meta.public) {
    if (authApi.isAuthenticated()) {
      next()
    } else {
      // 未登录,重定向到登录页
      next({
        name: 'Login',
        query: { redirect: to.fullPath } // 保存原始目标路径
      })
    }
    return
  }

  next()
})

export default router
