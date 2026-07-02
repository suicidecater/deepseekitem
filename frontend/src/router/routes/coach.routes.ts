// src/router/routes/coach.routes.ts
import type { RouteRecordRaw } from 'vue-router'

export const coachRoutes: RouteRecordRaw = {
  path: '/coach',
  component: () => import('@/components/layout/CoachLayout.vue'),
  meta: { role: 'coach' },
  children: [
    {
      path: 'students',
      name: 'CoachStudents',
      component: () => import('@/views/coach/StudentsView.vue'),
      meta: { title: '学情管理' }
    },
    {
      path: 'ai-advice',
      name: 'CoachAiAdvice',
      component: () => import('@/views/coach/AiAdviceView.vue'),
      meta: { title: 'AI教学辅导建议' }
    },
    {
      path: 'chat',
      name: 'CoachChat',
      component: () => import('@/views/coach/ChatView.vue'),
      meta: { title: '学员对话' }
    },
    {
      path: 'notifications',
      name: 'CoachNotifications',
      component: () => import('@/views/coach/NotificationsView.vue'),
      meta: { title: '通知中心' }
    },
    {
      path: '',
      redirect: '/coach/students'
    }
  ]
}
