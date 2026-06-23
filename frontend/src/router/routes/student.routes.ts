// src/router/routes/student.routes.ts
import type { RouteRecordRaw } from 'vue-router'

export const studentRoutes: RouteRecordRaw = {
  path: '/student',
  component: () => import('@/components/layout/StudentLayout.vue'),
  meta: { role: 'student' },
  children: [
    {
      path: 'home',
      name: 'StudentHome',
      component: () => import('@/views/student/HomeView.vue'),
      meta: { title: '学习首页' }
    },
    {
      path: 'evaluation',
      name: 'StudentEvaluation',
      component: () => import('@/views/student/EvaluationView.vue'),
      meta: { title: '能力基线测评' }
    },
    {
      path: 'study-plan',
      name: 'StudentStudyPlan',
      component: () => import('@/views/student/StudyPlanView.vue'),
      meta: { title: 'AI学习路径' }
    },
    {
      path: 'practice',
      name: 'StudentPractice',
      component: () => import('@/views/student/PracticeView.vue'),
      meta: { title: '智能题库练习' }
    },
    {
      path: 'exam',
      name: 'StudentExam',
      component: () => import('@/views/student/ExamView.vue'),
      meta: { title: '全真模拟考试', fullscreen: true }
    },
    {
      path: 'ai-qa',
      name: 'StudentAiQA',
      component: () => import('@/views/student/AiQAView.vue'),
      meta: { title: 'AI交规问答' }
    },
    {
      path: 'error-book',
      name: 'StudentErrorBook',
      component: () => import('@/views/student/ErrorBookView.vue'),
      meta: { title: '错题本' }
    },
    {
      path: 'confusing',
      name: 'StudentConfusing',
      component: () => import('@/views/student/ConfusingView.vue'),
      meta: { title: '易混淆专项训练' }
    },
    {
      path: 'scene-sim',
      name: 'StudentSceneSim',
      component: () => import('@/views/student/SceneSimView.vue'),
      meta: { title: '交通场景模拟' }
    },
    {
      path: 'sprint',
      name: 'StudentSprint',
      component: () => import('@/views/student/SprintView.vue'),
      meta: { title: '考前冲刺与押题' }
    },
    {
      path: 'progress',
      name: 'StudentProgress',
      component: () => import('@/views/student/ProgressView.vue'),
      meta: { title: '学习进度可视化' }
    },
    {
      path: 'rewards',
      name: 'StudentRewards',
      component: () => import('@/views/student/RewardsView.vue'),
      meta: { title: '学习激励' }
    },
    {
      path: 'report',
      name: 'StudentReport',
      component: () => import('@/views/student/ReportView.vue'),
      meta: { title: '学习评估报告' }
    },
    {
      path: 'transport',
      name: 'StudentTransport',
      component: () => import('@/views/student/TransportView.vue'),
      meta: { title: '运输从业人员培训' }
    },
    {
      path: 'messages',
      name: 'StudentMessages',
      component: () => import('@/views/student/MessagesView.vue'),
      meta: { title: '消息通知' }
    },
  ]
}
