import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import LoginView from '../views/LoginView.vue'
import DashboardView from '../views/DashboardView.vue'
import ExpensesView from '../views/ExpensesView.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/login', component: LoginView, meta: { public: true } },
    { path: '/', component: DashboardView, meta: { permission: 'rbac:user:read' } },
    { path: '/expenses', component: ExpensesView, meta: { permission: 'expense:read' } },
    { path: '/:pathMatch(.*)*', redirect: '/' },
  ],
})

router.beforeEach(async (to) => {
  const auth = useAuthStore()
  await auth.hydrate()
  if (to.meta.public) {
    if (auth.isAuthenticated) return '/'
    return true
  }
  if (!auth.isAuthenticated) return '/login'
  const permission = to.meta.permission as string | undefined
  if (permission && !auth.hasPermission(permission)) return '/'
  return true
})

export default router
