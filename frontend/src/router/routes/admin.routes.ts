// src/router/routes/admin.routes.ts
import type { RouteRecordRaw } from 'vue-router'

export const adminRoutes: RouteRecordRaw = {
  path: '/admin',
  component: () => import('@/components/layout/AdminLayout.vue'),
  meta: { role: 'admin' },
  children: [
    {
      path: 'users',
      name: 'AdminUsers',
      component: () => import('@/views/admin/AdminUsers.vue'),
      meta: { title: '人员管理', roles: ['admin'] }
    },
    {
      path: 'questions',
      name: 'AdminQuestions',
      component: () => import('@/views/admin/AdminQuestions.vue'),
      meta: { title: '题库管理', roles: ['admin', 'editor'] }
    },
    {
      path: 'api-config',
      name: 'AdminApiConfig',
      component: () => import('@/views/admin/AdminApiConfig.vue'),
      meta: { title: 'API 配置', roles: ['admin'] }
    },
    {
      path: 'cms',
      redirect: '/admin/questions'
    },
    {
      path: 'coach-assignment',
      name: 'AdminCoachAssignment',
      component: () => import('@/views/admin/StudentCoachAssignment.vue'),
      meta: { title: '教练分配', roles: ['admin'] }
    },
    {
      path: 'notifications',
      name: 'AdminNotifications',
      component: () => import('@/views/admin/AdminNotifications.vue'),
      meta: { title: '通知管理', roles: ['admin'] }
    },
    {
      path: '',
      redirect: '/admin/users'
    }
  ]
}
