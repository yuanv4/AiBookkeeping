import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    redirect: '/dashboard'
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: () => import('../views/DashboardView.vue'),
    meta: { title: '仪表板' }
  },
  {
    path: '/analysis',
    name: 'Analysis',
    component: () => import('../views/AnalysisView.vue'),
    meta: { title: '数据分析' }
  },
  {
    path: '/transactions',
    name: 'Transactions',
    component: () => import('../views/TransactionsView.vue'),
    meta: { title: '账单明细' }
  },
  {
    path: '/settings',
    name: 'Settings',
    component: () => import('../views/SettingsView.vue'),
    meta: { title: '设置' },
    redirect: '/settings/ai',
    children: [
      {
        path: 'ai',
        name: 'AISettings',
        component: () => import('../components/settings/AIConfig.vue'),
        meta: { title: 'AI 配置' }
      },
      {
        path: 'data',
        name: 'DataSettings',
        component: () => import('../views/settings/DataSettings.vue'),
        meta: { title: '数据管理' }
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
