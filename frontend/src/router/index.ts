// src/router/index.ts
import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'
import { authRoutes } from './routes/auth.routes'
import { studentRoutes } from './routes/student.routes'
import { coachRoutes } from './routes/coach.routes'
import { adminRoutes } from './routes/admin.routes'
// import { setupGuards } from './guards'  // 预览模式：关闭权限校验

const routes: RouteRecordRaw[] = [
  ...authRoutes,
  studentRoutes,
  coachRoutes,
  adminRoutes,
  {
    path: '/',
    redirect: '/student/home'
  },
  {
    path: '/forbidden',
    name: 'Forbidden',
    component: () => import('@/views/auth/ForbiddenView.vue'),
    meta: { title: '403 无权限' }
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('@/views/auth/NotFoundView.vue'),
    meta: { title: '404 未找到' }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// setupGuards(router)  // 预览模式：关闭权限校验

export default router
