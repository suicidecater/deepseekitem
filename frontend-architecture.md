# 基于DeepSeek大模型的交通知识培训平台 - 前端架构设计文档

> **版本**: V1.0 | **日期**: 2026-06-01 | **作者**: 前端开发工程师  
> **技术栈**: Vue 3.x + TypeScript + Vite + Pinia + Vue Router 4 + ECharts 5

---

## 1. 项目目录结构

```
traffic-training-platform/
├── public/
│   ├── favicon.ico
│   └── logo.svg
├── src/
│   ├── assets/                    # 静态资源
│   │   ├── images/                # 图片资源
│   │   │   ├── medals/            # 勋章图标
│   │   │   └── icons/             # 通用图标
│   │   └── styles/                # 全局样式
│   │       ├── variables.css      # CSS变量（颜色/间距/字号）
│   │       ├── reset.css          # 浏览器默认样式重置
│   │       ├── global.css         # 全局样式
│   │       └── transitions.css    # 全局过渡动画
│   │
│   ├── api/                       # API 接口层
│   │   ├── index.ts               # Axios 实例封装（拦截器/JWT）
│   │   ├── modules/               # 按业务模块拆分
│   │   │   ├── auth.ts            # 登录注册相关
│   │   │   ├── student.ts         # 学员相关
│   │   │   ├── coach.ts           # 教练相关
│   │   │   ├── admin.ts           # 管理端相关
│   │   │   ├── exam.ts            # 考试/练习相关
│   │   │   ├── question.ts        # 题库相关
│   │   │   ├── ai.ts              # AI问答（SSE）
│   │   │   └── message.ts         # 消息通知
│   │   └── types/                 # API 响应类型
│   │       └── response.ts        # 统一响应格式
│   │
│   ├── components/                # 组件
│   │   ├── common/                # 通用基础组件
│   │   │   ├── FormInput.vue      # 表单输入
│   │   │   ├── CountdownTimer.vue # 倒计时器
│   │   │   ├── LoadingSpinner.vue # 加载动画
│   │   │   ├── ProgressBar.vue    # 进度条
│   │   │   ├── ModalDialog.vue    # 弹窗
│   │   │   ├── Toast.vue          # 消息提示
│   │   │   ├── EmptyState.vue     # 空状态
│   │   │   ├── FileUpload.vue     # 文件上传
│   │   │   ├── DataTable.vue      # 数据表格
│   │   │   └── SearchFilter.vue   # 搜索筛选
│   │   │
│   │   ├── business/              # 业务组件
│   │   │   ├── RadarChart.vue     # 能力雷达图
│   │   │   ├── KnowledgeTreeMap.vue # 知识树地图
│   │   │   ├── HeatmapCalendar.vue  # 学习热力图
│   │   │   ├── QuestionCard.vue   # 答题卡片
│   │   │   ├── ChatBubble.vue     # AI对话气泡
│   │   │   ├── ExamNavigator.vue  # 题号导航面板
│   │   │   ├── MedalWall.vue      # 勋章墙
│   │   │   ├── Leaderboard.vue    # 排行榜
│   │   │   ├── ContrastCard.vue   # 易混淆对比卡片
│   │   │   ├── DashboardChart.vue # 数据看板图表
│   │   │   ├── ProfileCard.vue    # 个人档案卡
│   │   │   ├── TaskList.vue       # 任务清单
│   │   │   └── VoiceRecorder.vue  # 语音录音
│   │   │
│   │   └── layout/                # 布局组件
│   │       ├── AppHeader.vue      # 顶部导航
│   │       ├── AppSidebar.vue     # 侧边导航
│   │       ├── AppFooter.vue      # 底部
│   │       └── AuthLayout.vue     # 登录注册布局
│   │
│   ├── composables/               # 组合式函数（逻辑复用）
│   │   ├── useAuth.ts             # 认证相关
│   │   ├── useTimer.ts            # 倒计时逻辑
│   │   ├── useExam.ts             # 考试/答题逻辑
│   │   ├── usePagination.ts       # 分页逻辑
│   │   ├── useSSE.ts              # SSE流式响应
│   │   ├── useFullscreen.ts       # 全屏/防切窗
│   │   ├── useVoice.ts            # 语音录音
│   │   ├── useDebounce.ts         # 防抖
│   │   └── useChart.ts            # 图表初始化
│   │
│   ├── router/                    # 路由配置
│   │   ├── index.ts               # 路由实例 + 全局守卫
│   │   ├── routes/                # 路由模块
│   │   │   ├── auth.routes.ts     # 登录注册
│   │   │   ├── student.routes.ts  # 学员端
│   │   │   ├── coach.routes.ts    # 教练端
│   │   │   └── admin.routes.ts    # 管理端
│   │   └── guards.ts              # 导航守卫（RBAC）
│   │
│   ├── stores/                    # Pinia 状态管理
│   │   ├── index.ts               # Pinia 实例
│   │   ├── auth.ts                # 用户认证状态
│   │   ├── student.ts             # 学员数据状态
│   │   ├── exam.ts                # 考试/练习状态
│   │   ├── chat.ts                # AI对话状态
│   │   └── app.ts                 # 全局应用状态
│   │
│   ├── views/                     # 页面视图
│   │   ├── auth/                  # 登录注册
│   │   │   └── LoginView.vue
│   │   ├── student/               # 学员端（14个页面）
│   │   │   ├── HomeView.vue              # 学习首页（仪表盘）
│   │   │   ├── EvaluationView.vue        # 能力基线测评
│   │   │   ├── StudyPlanView.vue         # AI学习路径规划
│   │   │   ├── AiQAView.vue              # AI交规问答
│   │   │   ├── PracticeView.vue          # 智能题库练习
│   │   │   ├── ExamView.vue              # 全真模拟考试（全屏）
│   │   │   ├── ErrorBookView.vue         # 错题本
│   │   │   ├── ConfusingView.vue         # 易混淆专项训练
│   │   │   ├── SceneSimView.vue          # 交通场景模拟
│   │   │   ├── SprintView.vue            # 考前冲刺与押题
│   │   │   ├── ProgressView.vue          # 学习进度可视化
│   │   │   ├── RewardsView.vue           # 学习提醒与激励
│   │   │   ├── ReportView.vue            # 学习评估报告
│   │   │   ├── TransportView.vue         # 运输从业人员培训
│   │   │   └── MessagesView.vue          # 消息通知
│   │   ├── coach/                 # 教练端（2个页面）
│   │   │   ├── StudentsView.vue          # 学情管理
│   │   │   └── AiAdviceView.vue          # AI教学辅导建议
│   │   └── admin/                 # 管理端（3个页面）
│   │       ├── SchoolView.vue            # 驾校管理后台
│   │       ├── OperationView.vue         # 运营管理平台
│   │       └── CMSView.vue               # 内容管理系统
│   │
│   ├── types/                     # TypeScript 类型定义
│   │   ├── user.ts                # 用户相关类型
│   │   ├── exam.ts                # 考试/题目类型
│   │   ├── ai.ts                  # AI对话类型
│   │   ├── chart.ts               # 图表数据类型
│   │   └── common.ts              # 通用类型
│   │
│   ├── utils/                     # 工具函数
│   │   ├── request.ts             # Axios封装
│   │   ├── storage.ts             # localStorage封装
│   │   ├── validators.ts          # 表单校验规则
│   │   ├── format.ts              # 格式化工具
│   │   └── constants.ts           # 常量定义
│   │
│   ├── App.vue                    # 根组件
│   └── main.ts                    # 入口文件
│
├── .env.development               # 开发环境变量
├── .env.production                # 生产环境变量
├── .eslintrc.cjs                  # ESLint配置
├── .prettierrc                    # Prettier配置
├── index.html
├── package.json
├── tsconfig.json
└── vite.config.ts
```

---

## 2. 路由架构设计

### 2.1 完整路由表

```typescript
// src/router/routes/auth.routes.ts
export const authRoutes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/auth/LoginView.vue'),
    meta: { title: '登录注册', guest: true }
  }
]

// src/router/routes/student.routes.ts
export const studentRoutes: RouteRecordRaw = {
  path: '/student',
  component: () => import('@/components/layout/AppSidebar.vue'), // 学员端布局
  meta: { role: 'student' },
  children: [
    { path: 'home',      name: 'StudentHome',      component: () => import('@/views/student/HomeView.vue'),      meta: { title: '学习首页' } },
    { path: 'evaluation',name: 'StudentEvaluation', component: () => import('@/views/student/EvaluationView.vue'),meta: { title: '能力基线测评' } },
    { path: 'study-plan',name: 'StudentStudyPlan',  component: () => import('@/views/student/StudyPlanView.vue'), meta: { title: 'AI学习路径' } },
    { path: 'ai-qa',     name: 'StudentAiQA',       component: () => import('@/views/student/AiQAView.vue'),      meta: { title: 'AI交规问答' } },
    { path: 'practice',  name: 'StudentPractice',   component: () => import('@/views/student/PracticeView.vue'),   meta: { title: '智能题库练习' } },
    { path: 'exam',      name: 'StudentExam',       component: () => import('@/views/student/ExamView.vue'),       meta: { title: '全真模拟考试', fullscreen: true } },
    { path: 'error-book',name: 'StudentErrorBook',  component: () => import('@/views/student/ErrorBookView.vue'),  meta: { title: '错题本' } },
    { path: 'confusing', name: 'StudentConfusing',  component: () => import('@/views/student/ConfusingView.vue'),  meta: { title: '易混淆专项训练' } },
    { path: 'scene-sim', name: 'StudentSceneSim',   component: () => import('@/views/student/SceneSimView.vue'),   meta: { title: '交通场景模拟' } },
    { path: 'sprint',    name: 'StudentSprint',     component: () => import('@/views/student/SprintView.vue'),     meta: { title: '考前冲刺与押题' } },
    { path: 'progress',  name: 'StudentProgress',   component: () => import('@/views/student/ProgressView.vue'),   meta: { title: '学习进度可视化' } },
    { path: 'rewards',   name: 'StudentRewards',    component: () => import('@/views/student/RewardsView.vue'),    meta: { title: '学习提醒与激励' } },
    { path: 'report',    name: 'StudentReport',     component: () => import('@/views/student/ReportView.vue'),     meta: { title: '学习评估报告' } },
    { path: 'transport', name: 'StudentTransport',  component: () => import('@/views/student/TransportView.vue'),  meta: { title: '运输从业人员培训' } },
    { path: 'messages',  name: 'StudentMessages',   component: () => import('@/views/student/MessagesView.vue'),   meta: { title: '消息通知' } },
  ]
}

// src/router/routes/coach.routes.ts
export const coachRoutes: RouteRecordRaw = {
  path: '/coach',
  component: () => import('@/components/layout/AppSidebar.vue'),
  meta: { role: 'coach' },
  children: [
    { path: 'students',  name: 'CoachStudents',  component: () => import('@/views/coach/StudentsView.vue'),  meta: { title: '学情管理' } },
    { path: 'ai-advice', name: 'CoachAiAdvice',  component: () => import('@/views/coach/AiAdviceView.vue'),  meta: { title: 'AI教学辅导建议' } },
  ]
}

// src/router/routes/admin.routes.ts
export const adminRoutes: RouteRecordRaw = {
  path: '/admin',
  component: () => import('@/components/layout/AppSidebar.vue'),
  meta: { role: 'admin' },
  children: [
    { path: 'school',    name: 'AdminSchool',    component: () => import('@/views/admin/SchoolView.vue'),    meta: { title: '驾校管理后台', roles: ['admin'] } },
    { path: 'operation', name: 'AdminOperation', component: () => import('@/views/admin/OperationView.vue'), meta: { title: '运营管理平台', roles: ['admin', 'operator'] } },
    { path: 'cms',       name: 'AdminCMS',       component: () => import('@/views/admin/CMSView.vue'),       meta: { title: '内容管理系统', roles: ['admin', 'editor'] } },
  ]
}
```

### 2.2 路由导航守卫（RBAC）

```typescript
// src/router/guards.ts
import type { Router } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

export function setupGuards(router: Router) {
  router.beforeEach((to, from, next) => {
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
    const userRole = authStore.role // 'student' | 'coach' | 'admin'
    const requiredRole = to.meta.role as string

    if (requiredRole && userRole !== requiredRole) {
      // 检查管理端子角色（adminType 细粒度校验）
      const allowedRoles = (to.meta.roles as string[]) || []
      if (userRole === 'admin' && allowedRoles.length > 0) {
        const userAdminType = authStore.userInfo?.adminType as number
        const adminTypeMap: Record<number, string[]> = {
          1: ['admin'],           // 超级管理员可访问所有
          2: ['editor'],          // 内容编辑 → 仅CMS
          3: ['operator'],        // 运营管理 → 仅运营面板
        }
        const allowed = adminTypeMap[userAdminType || 0] || []
        if (allowed.some(r => allowedRoles.includes(r))) {
          return next()
        }
        return next({ name: 'Forbidden' }) // 403
      }
      if (allowedRoles.length > 0 && allowedRoles.includes(userRole)) {
        return next()
      }
      return next({ name: 'Forbidden' }) // 403
    }

    // 4. 全屏考试页特殊处理
    if (to.meta.fullscreen) {
      document.documentElement.requestFullscreen()
    }

    next()
  })
}
```

### 2.3 路由懒加载与代码分割

```typescript
// vite.config.ts - 手动分包策略
export default defineConfig({
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          'vendor': ['vue', 'vue-router', 'pinia'],
          'echarts': ['echarts'],
          'ui-common': ['@/components/common/FormInput.vue', /*...*/],
          'student-pages': ['./src/views/student/*.vue'],
          'coach-pages': ['./src/views/coach/*.vue'],
          'admin-pages': ['./src/views/admin/*.vue'],
        }
      }
    }
  }
})
```

---

## 3. Pinia 状态管理设计

### 3.1 认证状态 Store

```typescript
// src/stores/auth.ts
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { UserInfo, LoginForm, RegisterForm } from '@/types/user'
import { authApi } from '@/api/modules/auth'
import { storage } from '@/utils/storage'

export const useAuthStore = defineStore('auth', () => {
  // State
  const token = ref<string>(storage.get('token') || '')
  const userInfo = ref<UserInfo | null>(null)
  const refreshTimer = ref<number | null>(null)

  // Getters
  const isAuthenticated = computed(() => !!token.value)
  const role = computed(() => userInfo.value?.role || '')
  const userId = computed(() => userInfo.value?.id || 0)

  // Actions
  async function login(form: LoginForm) {
    const res = await authApi.login(form)
    token.value = res.data.access_token
    userInfo.value = res.data.user
    storage.set('token', res.data.access_token)
    storage.set('refresh_token', res.data.refresh_token)
    startRefreshTimer()
  }

  async function register(form: RegisterForm) {
    const res = await authApi.register(form)
    token.value = res.data.access_token
    userInfo.value = res.data.user
    storage.set('token', res.data.access_token)
  }

  async function logout() {
    await authApi.logout()
    token.value = ''
    userInfo.value = null
    storage.clear()
    clearRefreshTimer()
    window.location.href = '/login'
  }

  // 自动刷新 Token
  function startRefreshTimer() {
    clearRefreshTimer()
    refreshTimer.value = window.setInterval(async () => {
      try {
        const res = await authApi.refreshToken()
        token.value = res.data.access_token
        storage.set('token', res.data.access_token)
      } catch {
        logout()
      }
    }, 25 * 60 * 1000) // 每25分钟刷新
  }

  function clearRefreshTimer() {
    if (refreshTimer.value) {
      clearInterval(refreshTimer.value)
      refreshTimer.value = null
    }
  }

  return { token, userInfo, isAuthenticated, role, userId, login, register, logout }
})
```

### 3.2 考试/练习状态 Store

```typescript
// src/stores/exam.ts
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { Question, ExamConfig, AnswerRecord } from '@/types/exam'
import { examApi } from '@/api/modules/exam'

export const useExamStore = defineStore('exam', () => {
  // State
  const questions = ref<Question[]>([])
  const currentIndex = ref(0)
  const answers = ref<Map<number, string>>(new Map()) // questionId -> answer
  const config = ref<ExamConfig>({
    mode: 'practice',  // 'practice' | 'exam'
    subject: 1,        // 1: 科目一, 4: 科目四
    count: 50,
    difficulty: 0,     // 0: 全部, 1-3
    knowledgeIds: []
  })
  const isSubmitted = ref(false)
  const score = ref(0)
  const correctRate = ref(0)
  const timeSpent = ref(0) // 秒

  // Getters
  const currentQuestion = computed(() => questions.value[currentIndex.value])
  const totalCount = computed(() => questions.value.length)
  const answeredCount = computed(() => answers.value.size)
  const progress = computed(() => totalCount.value ? (answeredCount.value / totalCount.value) * 100 : 0)
  const wrongQuestions = computed(() => {
    return questions.value.filter(q => {
      const userAnswer = answers.value.get(q.id)
      return userAnswer && userAnswer !== q.answer
    })
  })

  // Actions
  async function loadQuestions(params: ExamConfig) {
    config.value = { ...params }
    const res = await examApi.getQuestions(params)
    questions.value = res.data.questions
    answers.value.clear()
    currentIndex.value = 0
    isSubmitted.value = false
  }

  function answerQuestion(questionId: number, answer: string) {
    answers.value.set(questionId, answer)
  }

  function nextQuestion() {
    if (currentIndex.value < totalCount.value - 1) {
      currentIndex.value++
    }
  }

  function prevQuestion() {
    if (currentIndex.value > 0) {
      currentIndex.value--
    }
  }

  function jumpTo(index: number) {
    if (index >= 0 && index < totalCount.value) {
      currentIndex.value = index
    }
  }

  async function submitExam(totalTime: number) {
    timeSpent.value = totalTime
    const answerList: AnswerRecord[] = Array.from(answers.value.entries()).map(([qid, ans]) => ({
      question_id: qid,
      user_answer: ans
    }))
    const res = await examApi.submitExam({
      mode: config.value.mode,
      subject: config.value.subject,
      answers: answerList,
      total_time: totalTime
    })
    score.value = res.data.score
    correctRate.value = res.data.correct_rate
    isSubmitted.value = true
    return res.data
  }

  function reset() {
    questions.value = []
    answers.value.clear()
    currentIndex.value = 0
    isSubmitted.value = false
    score.value = 0
    correctRate.value = 0
    timeSpent.value = 0
  }

  return {
    questions, currentIndex, answers, config, isSubmitted, score, correctRate, timeSpent,
    currentQuestion, totalCount, answeredCount, progress, wrongQuestions,
    loadQuestions, answerQuestion, nextQuestion, prevQuestion, jumpTo, submitExam, reset
  }
})
```

### 3.3 AI 对话状态 Store

```typescript
// src/stores/chat.ts
import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { ChatMessage } from '@/types/ai'

export const useChatStore = defineStore('chat', () => {
  const messages = ref<ChatMessage[]>([])
  const isStreaming = ref(false)
  const currentReply = ref('')

  function addUserMessage(content: string) {
    messages.value.push({
      id: Date.now(),
      role: 'user',
      content,
      timestamp: new Date().toISOString()
    })
  }

  function startAIResponse() {
    isStreaming.value = true
    currentReply.value = ''
    messages.value.push({
      id: Date.now(),
      role: 'assistant',
      content: '',
      timestamp: new Date().toISOString(),
      isStreaming: true
    })
  }

  function appendAIChunk(chunk: string) {
    currentReply.value += chunk
    const lastMsg = messages.value[messages.value.length - 1]
    if (lastMsg) lastMsg.content = currentReply.value
  }

  function finishAIResponse() {
    isStreaming.value = false
    const lastMsg = messages.value[messages.value.length - 1]
    if (lastMsg) {
      lastMsg.isStreaming = false
      lastMsg.content = currentReply.value
    }
  }

  function clearChat() {
    messages.value = []
    currentReply.value = ''
    isStreaming.value = false
  }

  return {
    messages, isStreaming, currentReply,
    addUserMessage, startAIResponse, appendAIChunk, finishAIResponse, clearChat
  }
})
```

---

## 4. API 接口层设计

### 4.1 Axios 实例封装

```typescript
// src/api/index.ts
import axios from 'axios'
import type { AxiosInstance, InternalAxiosRequestConfig, AxiosResponse } from 'axios'
import { useAuthStore } from '@/stores/auth'
import { ElMessage } from 'element-plus' // 假设使用 Element Plus
import router from '@/router'

const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'https://api.traffic-train.com'

const http: AxiosInstance = axios.create({
  baseURL: BASE_URL,
  timeout: 15000,
  headers: { 'Content-Type': 'application/json' }
})

// 请求拦截器 - JWT 注入
http.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const authStore = useAuthStore()
  if (authStore.token) {
    config.headers.Authorization = `Bearer ${authStore.token}`
  }
  return config
})

// 响应拦截器 - 统一错误处理
http.interceptors.response.use(
  (response: AxiosResponse) => {
    const { code, message, data } = response.data
    if (code === 0) return data
    if (code === 401) {
      useAuthStore().logout()
      return Promise.reject(new Error('登录已过期'))
    }
    ElMessage.error(message || '请求失败')
    return Promise.reject(new Error(message))
  },
  (error) => {
    if (error.response?.status === 401) {
      useAuthStore().logout()
    } else if (error.response?.status === 403) {
      router.push('/403')
    } else {
      ElMessage.error(error.message || '网络错误')
    }
    return Promise.reject(error)
  }
)

export default http
```

### 4.2 SSE 流式响应（AI 问答）

```typescript
// src/composables/useSSE.ts
import { ref } from 'vue'
import { useAuthStore } from '@/stores/auth'
import type { ChatMessage } from '@/types/ai'

export function useSSE() {
  const isStreaming = ref(false)
  const error = ref<string | null>(null)
  let abortController: AbortController | null = null

  async function* streamChat(question: string, history: ChatMessage[] = []) {
    const authStore = useAuthStore()
    isStreaming.value = true
    error.value = null
    abortController = new AbortController()

    const response = await fetch(`${import.meta.env.VITE_API_BASE_URL}/api/ai/chat/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${authStore.token}`
      },
      body: JSON.stringify({ question, history }),
      signal: abortController.signal
    })

    if (!response.ok) {
      const retryAfter = response.status === 429
      error.value = retryAfter ? '请求过于频繁，请稍后重试' : `服务错误 (${response.status})`
      isStreaming.value = false
      throw new Error(error.value)
    }

    const reader = response.body!.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const event = JSON.parse(line.slice(6))
          switch (event.type) {
            case 'end':
              isStreaming.value = false
              return event.structured  // 返回结构化数据
            case 'error':
              error.value = event.message
              isStreaming.value = false
              throw new Error(event.message)
            case 'chunk':
              yield event.content
              break
          }
        }
      }
    }
    isStreaming.value = false
  }

  function abort() {
    abortController?.abort()
    isStreaming.value = false
  }

  function clearError() {
    error.value = null
  }

  return { isStreaming, error, streamChat, abort, clearError }
}
```

---

## 5. TypeScript 类型定义

```typescript
// src/types/user.ts
export interface UserInfo {
  id: number
  email: string
  phone?: string
  role: 'student' | 'coach' | 'admin'
  name?: string
  avatar?: string
  // 学员特有
  carType?: string       // 报考车型 C1/C2/A1/A2
  schoolName?: string    // 驾校名称
  registerTime?: string  // 注册时间
  trainType?: number     // 1驾考 2客运 3货运 4危化品
  // 教练特有
  coachSchoolName?: string
  // 管理特有
  adminType?: number     // 1超级 2内容 3运营
}

export interface LoginForm {
  email: string
  password: string
  type: 'password' | 'code'  // 密码登录 / 验证码登录
  code?: string
}

export interface RegisterForm {
  email: string
  phone?: string
  password: string
  code: string              // 验证码
  carType?: string
  schoolName?: string
}

// src/types/exam.ts
export interface Question {
  id: number
  knowId: number
  type: 1 | 2 | 3 | 4 | 5   // 1单选 2多选 3判断 4图片 5情景
  difficulty: 1 | 2 | 3
  subject: 1 | 4            // 科目一/科目四
  content: string           // 题干
  image?: string            // 题目图片
  options: QuestionOption[] // 选项
  answer: string            // 正确答案
  analysis?: string         // 解析
  law?: string              // 法规原文
  tags?: string[]
}

export interface QuestionOption {
  key: string   // A/B/C/D
  content: string
}

export interface ExamConfig {
  mode: 'practice' | 'exam'
  subject: 1 | 4
  count: number             // 10/20/50/100
  difficulty?: 0 | 1 | 2 | 3  // 0=全部
  knowledgeIds?: number[]
}

export interface AnswerRecord {
  question_id: number
  user_answer: string
}

// src/types/ai.ts
export interface ChatMessage {
  id: number
  role: 'user' | 'assistant'
  content: string
  timestamp: string
  isStreaming?: boolean
  // AI回复结构化数据
  structured?: {
    knowledge?: string       // 知识点解析
    lawText?: string         // 法规原文
    caseAnalysis?: string    // 案例分析
  }
}
```

---

## 6. 设计规范

### 6.1 CSS 变量体系

```css
/* src/assets/styles/variables.css */
:root {
  /* 主色调 */
  --color-primary: #1677FF;
  --color-primary-light: #E6F4FF;
  --color-primary-dark: #0958D9;

  /* 功能色（SRS规范） */
  --color-success: #52C41A;   /* 正确=绿色 */
  --color-error: #FF4D4F;     /* 错误=红色 */
  --color-warning: #FAAD14;   /* 警告=黄色 */

  /* 中性色 */
  --color-text-primary: #262626;
  --color-text-secondary: #595959;
  --color-text-tertiary: #8C8C8C;
  --color-border: #D9D9D9;
  --color-bg: #F5F5F5;
  --color-bg-white: #FFFFFF;

  /* 布局 */
  --sidebar-width: 240px;
  --header-height: 64px;
  --content-max-width: 1440px;

  /* 字号 */
  --font-size-xs: 12px;
  --font-size-sm: 14px;
  --font-size-base: 16px;
  --font-size-lg: 18px;
  --font-size-xl: 20px;
  --font-size-2xl: 24px;
  --font-size-3xl: 30px;

  /* 圆角 */
  --radius-sm: 4px;
  --radius-md: 8px;
  --radius-lg: 12px;

  /* 阴影 */
  --shadow-sm: 0 1px 2px rgba(0,0,0,0.06);
  --shadow-md: 0 4px 12px rgba(0,0,0,0.08);
  --shadow-lg: 0 8px 24px rgba(0,0,0,0.12);
}
```

### 6.2 组件命名规范
- **通用组件**: `Base{Name}` 如 `BaseModal`, `BaseTable`
- **业务组件**: `{Domain}{Name}` 如 `ExamTimer`, `ChatBubble`
- **单文件组件**: `<template>` + `<script setup lang="ts">` + `<style scoped>`
- **Props**: 使用 `defineProps<T>()` 类型推导
- **Emits**: 使用 `defineEmits<{ (e: 'name', value: T): void }>()`

---

## 7. 性能优化策略

| 优化项 | 策略 | 目标 |
|--------|------|------|
| 路由懒加载 | `() => import()` 动态导入 | 首屏 JS 体积降低 60% |
| 代码分割 | Vite manualChunks 分包 | vendor < 200KB |
| 图片懒加载 | `loading="lazy"` + IntersectionObserver | 减少首屏图片请求 |
| 虚拟列表 | 错题本/题库列表使用 `vue-virtual-scroller` | 万级数据流畅滚动 |
| 图表按需 | ECharts 按需引入 `echarts/core` | 减少 300KB+ 体积 |
| 防抖节流 | 搜索/滚动事件 | 减少不必要的请求 |
| 缓存策略 | Pinia 持久化 + API 缓存 | 减少重复请求 |
| CDN 加速 | 静态资源上传 CDN | 首页加载 ≤ 2s |

---

---

## 7. API 缓存策略 (useSWR)

```typescript
// src/composables/useSWR.ts
import { ref } from 'vue'

interface CacheEntry<T> {
  data: T
  timestamp: number
}

const cache = new Map<string, CacheEntry<any>>()

export function useSWR<T>(key: string, fetcher: () => Promise<T>, ttl = 30_000) {
  const data = ref<T | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function fetch() {
    // 检查缓存
    const cached = cache.get(key)
    if (cached && Date.now() - cached.timestamp < ttl) {
      data.value = cached.data
      return
    }

    loading.value = true
    error.value = null

    try {
      const result = await fetcher()
      data.value = result
      cache.set(key, { data: result, timestamp: Date.now() })
    } catch (e: any) {
      error.value = e.message || '请求失败'
    } finally {
      loading.value = false
    }
  }

  function invalidate() {
    cache.delete(key)
  }

  // 全局清缓存（如退出登录时）
  function clearAll() {
    cache.clear()
  }

  return { data, loading, error, fetch, invalidate, clearAll }
}
```

**应用场景说明：**
| 页面 | 缓存 Key | TTL | 说明 |
|------|---------|-----|------|
| HomeView 仪表盘 | `dashboard-{userId}` | 30s | 学习首页聚合数据，短TTL保证时效 |
| ProgressView 进度 | `progress-{userId}` | 60s | 每日零点更新，较长TTL |
| CoachStudentsView 学员列表 | `coach-students` | 60s | 教练端数据变化频率低 |
| ErrorBookView 错题统计 | `error-stats-{userId}` | 30s | 练习后可能变化 |

---

*本文档基于 SRS V1.0 编写，后续将根据实际开发进展持续更新*
