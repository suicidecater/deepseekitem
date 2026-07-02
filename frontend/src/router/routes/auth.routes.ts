// src/router/routes/auth.routes.ts
import type { RouteRecordRaw } from 'vue-router'

export const authRoutes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/auth/LoginView.vue'),
    meta: { title: '登录', guest: true }
  },
  {
    path: '/register/student',
    name: 'RegisterStudent',
    component: () => import('@/views/auth/RegisterStudent.vue'),
    meta: { title: '学员注册', guest: true }
  },
  {
    path: '/register/coach',
    name: 'RegisterCoach',
    component: () => import('@/views/auth/RegisterCoach.vue'),
    meta: { title: '教练注册', guest: true }
  },
  {
    path: '/register/admin',
    name: 'RegisterAdmin',
    component: () => import('@/views/auth/RegisterAdmin.vue'),
    meta: { title: '管理员注册', guest: true }
  }
]
