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
      path: '',
      redirect: '/coach/students'
    }
  ]
}
