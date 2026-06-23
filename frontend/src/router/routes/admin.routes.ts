// src/router/routes/admin.routes.ts
import type { RouteRecordRaw } from 'vue-router'

export const adminRoutes: RouteRecordRaw = {
  path: '/admin',
  component: () => import('@/components/layout/AdminLayout.vue'),
  meta: { role: 'admin' },
  children: [
    {
      path: 'school',
      name: 'AdminSchool',
      component: () => import('@/views/admin/SchoolView.vue'),
      meta: { title: '驾校管理后台', roles: ['admin'] }
    },
    {
      path: 'operation',
      name: 'AdminOperation',
      component: () => import('@/views/admin/OperationView.vue'),
      meta: { title: '运营管理平台', roles: ['admin', 'operator'] }
    },
    {
      path: 'cms',
      name: 'AdminCMS',
      component: () => import('@/views/admin/CMSView.vue'),
      meta: { title: '内容管理系统', roles: ['admin', 'editor'] }
    },
    {
      path: '',
      redirect: '/admin/school'
    }
  ]
}
