// src/router/guards.ts
import type { Router } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

export function setupGuards(router: Router) {
  router.beforeEach((to, _from, next) => {
    const authStore = useAuthStore()

    // 1. 无需登录的页面（登录/注册）
    if (to.meta.guest) {
      if (authStore.isAuthenticated) return next('/student/home')
      return next()
    }

    // 2. 需要登录的页面
    if (!authStore.isAuthenticated) {
      return next({ name: 'Login', query: { redirect: to.fullPath } })
    }

    // 3. RBAC 角色校验
    const userRole = authStore.role
    const requiredRole = to.meta.role as string

    if (requiredRole && userRole !== requiredRole) {
      const allowedRoles = (to.meta.roles as string[]) || []
      if (userRole === 'admin' && allowedRoles.length > 0) {
        const userAdminType = authStore.userInfo?.adminType as number
        const adminTypeMap: Record<number, string[]> = {
          1: ['admin'],
          2: ['editor'],
          3: ['operator'],
        }
        const allowed = adminTypeMap[userAdminType || 0] || []
        if (allowed.some(r => allowedRoles.includes(r))) {
          return next()
        }
        return next({ name: 'Forbidden' })
      }
      if (allowedRoles.length > 0 && allowedRoles.includes(userRole)) {
        return next()
      }
      return next({ name: 'Forbidden' })
    }

    // 4. 学员未完成测评 → 强制跳转测评页
    if (userRole === 'student' && authStore.needsEvaluation && to.name !== 'StudentEvaluation') {
      return next({ name: 'StudentEvaluation', query: { required: '1' } })
    }

    next()
  })
}
