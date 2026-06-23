// mocks/handlers.ts - MSW Mock API handlers
import { http, HttpResponse } from 'msw'

// Mock 用户数据
const MOCK_USER = {
  userId: 1,
  name: '张三',
  avatar: '',
  phone: '138****5678',
  email: 'zhangsan@example.com',
  role: 'student' as const,
  token: 'mock-jwt-token-xxxxx'
}

// Mock 仪表盘数据
const MOCK_DASHBOARD = {
  profile: {
    name: '张三',
    phone: '138****5678',
    carType: 'C1 小型汽车',
    school: '安达驾校',
    registerDate: '2026-03-15',
    avatar: '',
    progress: 60
  },
  abilityScores: [82, 65, 78, 55],
  abilityBaseline: [60, 60, 60, 60],
  todayTasks: [
    { id: 1, title: '交通标志专项练习', description: '完成20道交通标志题', completed: false, type: 'practice' as const },
    { id: 2, title: 'AI知识点讲解 - 交通法规', description: '学习关键法规条目', completed: false, type: 'ai_lesson' as const },
    { id: 3, title: '模拟考试复盘', description: '回顾上次考试错题', completed: true, type: 'exam_review' as const },
    { id: 4, title: '错题回顾 - 易错题集', description: '重新练习近期错题', completed: false, type: 'error_review' as const }
  ],
  knowledgeTree: {
    name: '交通知识树',
    value: 100,
    children: [
      { name: '交通标志', value: 40 },
      { name: '交通法规', value: 30 },
      { name: '安全常识', value: 20 },
      { name: '驾驶理论', value: 10 }
    ]
  },
  completedQuestions: 320,
  totalQuestions: 530,
  streakDays: 7,
  todayStudyMinutes: 45,
  daysUntilExam: 14,
  subject1Progress: 75,
  subject4Progress: 40,
  transportProgress: 20,
  totalStudents: 35,
  quickActions: [
    { label: '开始练习', icon: '✏️', route: '/student/practice', color: '#1677FF' },
    { label: '模拟考试', icon: '📝', route: '/student/exam', color: '#52C41A' },
    { label: 'AI问答', icon: '🤖', route: '/student/ai-qa', color: '#722ED1' },
    { label: '错题本', icon: '📕', route: '/student/error-book', color: '#FA8C16' }
  ]
}

export const handlers = [
  // POST /api/auth/login
  http.post('/api/auth/login', async ({ request }) => {
    const body = await request.json() as any
    if (!body.account || (!body.password && !body.code)) {
      return HttpResponse.json({ code: 1001, message: '参数不完整' })
    }
    return HttpResponse.json({
      code: 0,
      message: '登录成功',
      data: {
        token: MOCK_USER.token,
        refresh_token: 'mock-refresh-token-xxxxx',
        user: MOCK_USER
      }
    })
  }),

  // POST /api/auth/register
  http.post('/api/auth/register', async ({ request }) => {
    const body = await request.json() as any
    if (!body.name || !body.account || !body.password) {
      return HttpResponse.json({ code: 1001, message: '参数不完整' })
    }
    return HttpResponse.json({
      code: 0,
      message: '注册成功',
      data: {
        token: MOCK_USER.token,
        refresh_token: 'mock-refresh-token-xxxxx',
        user: { ...MOCK_USER, name: body.name }
      }
    })
  }),

  // POST /api/auth/refresh
  http.post('/api/auth/refresh', async ({ request }) => {
    const body = await request.json() as any
    if (!body.refresh_token) {
      return HttpResponse.json({ code: 1401, message: 'refresh_token 无效' })
    }
    return HttpResponse.json({
      code: 0,
      message: 'token 刷新成功',
      data: {
        token: 'mock-jwt-token-refreshed-' + Date.now(),
        refresh_token: body.refresh_token
      }
    })
  }),

  // GET /api/student/dashboard
  http.get('/api/student/dashboard', () => {
    return HttpResponse.json({
      code: 0,
      message: 'success',
      data: MOCK_DASHBOARD
    })
  }),

  // POST /api/auth/send-code
  http.post('/api/auth/send-code', async ({ request }) => {
    return HttpResponse.json({
      code: 0,
      message: '验证码已发送'
    })
  }),

  // ======================== 题库/考试相关 ========================

  // POST /api/question/start - 加载题目（练习/考试/测评通用）
  http.post('/api/question/start', async ({ request }) => {
    const body = await request.json() as any
    const count = body.count || 20
    const subject = body.subject || 1
    const types = body.types || ['single', 'multiple', 'judge']

    const allQuestions = generateMockQuestions(subject as number, count, types)
    return HttpResponse.json({
      code: 0,
      message: 'success',
      data: { questions: allQuestions }
    })
  }),

  // POST /api/question/answer - 单题提交答案
  http.post('/api/question/answer', async ({ request }) => {
    const body = await request.json() as any
    const q = ALL_MOCK_QUESTIONS.find(x => x.id === body.questionId)
    if (!q) return HttpResponse.json({ code: 2001, message: '题目不存在' })
    return HttpResponse.json({
      code: 0,
      data: { correct: q.answer === body.answer, correctAnswer: q.answer, explanation: q.explanation }
    })
  }),

  // POST /api/question/submit - 提交整套题
  http.post('/api/question/submit', async ({ request }) => {
    const body = await request.json() as any
    const answers: any[] = body.answers || []
    const correctCount = answers.filter((a: any) => a.correct).length
    const total = answers.length
    const score = total > 0 ? Math.round((correctCount / total) * 100) : 0

    // Mock 知识点统计
    const categoryStats = [
      { name: '交通标志', rate: Math.floor(Math.random() * 40 + 50) },
      { name: '交通法规', rate: Math.floor(Math.random() * 30 + 55) },
      { name: '安全常识', rate: Math.floor(Math.random() * 35 + 50) },
      { name: '驾驶理论', rate: Math.floor(Math.random() * 30 + 45) }
    ]

    return HttpResponse.json({
      code: 0,
      data: {
        score,
        correctRate: score,
        correctCount,
        wrongCount: total - correctCount,
        totalCount: total,
        passed: score >= 90,
        categoryStats,
        radarData: {
          dimensions: categoryStats.map(c => c.name),
          current: categoryStats.map(c => c.rate),
          baseline: [60, 60, 60, 60]
        },
        weakPoints: categoryStats.filter(c => c.rate < 60).map(c => ({ name: c.name, rate: c.rate })),
        advices: ['建议重点复习薄弱知识点', '每天坚持练习，巩固记忆', '多做全真模拟考试提升应试能力']
      }
    })
  }),

  // POST /api/student/evaluation/start - 测评开始（复用 question/start）
  http.post('/api/student/evaluation/start', async () => {
    const questions = generateMockQuestions(1, 40, ['single'])
    return HttpResponse.json({ code: 0, data: { questions } })
  }),

  // POST /api/student/evaluation/submit - 测评提交（复用 question/submit）
  http.post('/api/student/evaluation/submit', async ({ request }) => {
    const body = await request.json() as any
    const answers: any[] = body.answers || []
    const correctCount = answers.filter((a: any) => a.correct).length
    const score = answers.length > 0 ? Math.round((correctCount / answers.length) * 100) : 0

    const dimensions = ['交通标志', '交通法规', '安全常识', '驾驶理论']
    const scores = dimensions.map(() => Math.floor(Math.random() * 40 + 40))
    const weakPoints = scores
      .map((s, i) => ({ name: dimensions[i], rate: s }))
      .filter(p => p.rate < 60)

    return HttpResponse.json({
      code: 0,
      data: {
        score,
        correctRate: score,
        correctCount,
        wrongCount: answers.length - correctCount,
        radarData: { dimensions, current: scores, baseline: [60, 60, 60, 60] },
        weakPoints,
        advices: [
          weakPoints.length > 0 ? `重点加强${weakPoints.map(p => p.name).join('、')}的学习` : '基础扎实，继续保持！',
          '建议每天完成20道练习，巩固知识点',
          '可查看AI学习路径获取个性化建议'
        ]
      }
    })
  }),

  // GET /api/student/study-plan - 学习计划
  http.get('/api/student/study-plan', () => {
    const days = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
    const todayIdx = 2 // 假设今天是周三
    const weekDays = days.map((name, i) => ({
      date: `06/${String(i + 2).padStart(2, '0')}`,
      dayOfWeek: name,
      isToday: i === todayIdx,
      tasks: [
        { id: i * 10 + 1, title: '交通标志专项练习', description: '完成15道交通标志题', timeSlot: 'morning' as const, type: 'practice', completed: i < todayIdx, knowledgePoint: '交通标志' },
        { id: i * 10 + 2, title: 'AI知识点讲解', description: '学习关键法规条目', timeSlot: 'afternoon' as const, type: 'ai_lesson', completed: i < todayIdx, knowledgePoint: '交通法规' },
        { id: i * 10 + 3, title: i % 2 === 0 ? '错题复习' : '模拟考试', description: '复习近期错题', timeSlot: 'evening' as const, type: i % 2 === 0 ? 'error' : 'exam', completed: i < todayIdx }
      ]
    }))

    const allTasks = weekDays.flatMap(d => d.tasks)
    const completedTasks = allTasks.filter(t => t.completed).length

    return HttpResponse.json({
      code: 0,
      data: {
        weekStart: '06/02', weekEnd: '06/08',
        days: weekDays,
        totalTasks: allTasks.length,
        completedTasks
      }
    })
  }),

  // ======================== AI 问答（SSE模拟） ========================

  // POST /api/ai/chat/stream
  http.post('/api/ai/chat/stream', async ({ request }) => {
    const body = await request.json() as any
    const question = body.question || ''
    const mockResponse = {
      knowledgePoint: '根据《道路交通安全法》相关规定，高速公路行驶需注意保持安全车距。',
      lawRef: '《道路交通安全法实施条例》第八十条：机动车在高速公路上行驶，车速超过100km/h时，应与前车保持100米以上距离。',
      caseStudy: '2024年某高速追尾事故中，后车因未保持安全距离导致追尾，负全责。'
    }
    return HttpResponse.json({
      code: 0,
      data: {
        reply: `关于"${question}"的问题：\n\n📚 知识点：${mockResponse.knowledgePoint}\n\n📜 法规引用：${mockResponse.lawRef}\n\n📋 案例分析：${mockResponse.caseStudy}`,
        structured: mockResponse
      }
    })
  }),

  // ======================== 错题本 / 冲刺 / 易混淆 / 进度 / 报告 ========================

  http.get('/api/question/error-book', () => {
    return HttpResponse.json({ code: 0, data: { list: [], total: 5, toReview: 3, reviewed: 1, mastered: 1 } })
  }),

  http.get('/api/question/sprint', () => {
    return HttpResponse.json({ code: 0, data: { daysUntilExam: 10, highFreqPoints: [], mockExams: [] } })
  }),

  http.get('/api/question/confusing', () => {
    return HttpResponse.json({ code: 0, data: { categories: ['交警手势', '扣分罚款', '交通标志', '综合'] } })
  }),

  http.get('/api/student/progress', () => {
    const heatmapCells = Array.from({ length: 52 }, (_, i) => ({
      date: `W${i + 1}`, minutes: Math.floor(Math.random() * 120),
      level: Math.floor(Math.random() * 5) as 0 | 1 | 2 | 3 | 4
    }))
    return HttpResponse.json({
      code: 0,
      data: {
        stats: { totalDays: 45, totalHours: 32, totalQuestions: 520, accuracy: 82 },
        knowledgeTree: [
          { name: '交通标志', value: 100, completed: 80, color: '#52C41A' },
          { name: '交通法规', value: 100, completed: 60, color: '#1677FF' },
          { name: '安全常识', value: 100, completed: 70, color: '#722ED1' },
          { name: '驾驶理论', value: 100, completed: 45, color: '#FA8C16' }
        ],
        radarData: {
          dimensions: ['交通标志', '交通法规', '安全常识', '驾驶理论'],
          current: [80, 60, 70, 45], baseline: [60, 60, 60, 60]
        },
        heatmapCells
      }
    })
  }),

  http.get('/api/student/report', () => {
    return HttpResponse.json({
      code: 0,
      data: {
        overallScore: 78, overallLevel: '进阶水平',
        growthCurve: [
          { date: '03月', scores: [55, 45, 50, 35] },
          { date: '04月', scores: [65, 55, 60, 42] },
          { date: '05月', scores: [75, 62, 68, 48] },
          { date: '06月', scores: [82, 65, 78, 55] },
        ],
        knowledgeMatrix: [],
        examHistory: [
          { date: '03-15', score: 62, passed: false },
          { date: '04-10', score: 75, passed: false },
          { date: '05-05', score: 84, passed: false },
          { date: '05-25', score: 92, passed: true },
        ],
        aiAdvices: ['驾驶理论是薄弱维度，每天花30分钟专项学习', '每周进行2次全真模拟考试']
      }
    })
  }),

  http.post('/api/ai/generate-scene', () => {
    return HttpResponse.json({ code: 0, data: { scene: { title: '场景', description: '', image: '' }, question: { content: '?', options: ['A','B','C','D'], answer: 'A' } } })
  }),

  http.get('/api/student/rewards', () => {
    return HttpResponse.json({ code: 0, data: { streakDays: 12 } })
  }),

  http.get('/api/student/transport', () => {
    return HttpResponse.json({ code: 0, data: { courses: [] } })
  }),

  http.get('/api/student/messages', () => {
    return HttpResponse.json({ code: 0, data: { list: [] } })
  }),

  // ======================== 教练端 ========================

  http.get('/api/coach/students', () => {
    return HttpResponse.json({
      code: 0,
      data: {
        stats: { total: 35, active: 28, avgScore: 82, avgAccuracy: 78 },
        list: [
          { id: 1, name: '张三', phone: '138****5678', carType: 'C1', score: 88, accuracy: 85, studyDays: 45, lastActive: '2026-06-01' },
          { id: 2, name: '李四', phone: '139****1234', carType: 'C2', score: 72, accuracy: 68, studyDays: 30, lastActive: '2026-05-30' },
        ]
      }
    })
  }),

  http.get('/api/coach/ai-advice', () => {
    return HttpResponse.json({
      code: 0,
      data: {
        weaknesses: ['驾驶理论薄弱', '扣分标准混淆'],
        aiSuggestions: [
          { type: '重点', content: '本周重点攻克驾驶理论' },
          { type: '方法', content: '使用对比记忆法' },
          { type: '方案', content: '制定5天专项辅导计划' },
        ],
        plan: [
          { day: '第1天', task: '驾驶理论精讲', duration: '45分钟' },
          { day: '第2天', task: '理论精讲续', duration: '45分钟' },
        ]
      }
    })
  }),

  // ======================== 管理端 ========================

  http.get('/api/admin/school/dashboard', () => {
    return HttpResponse.json({
      code: 0,
      data: { totalStudents: 128, avgScore: 82, passRate: 78, activeRate: 85 }
    })
  }),

  http.get('/api/admin/school/tasks', () => {
    return HttpResponse.json({
      code: 0,
      data: { list: [{ id: 1, title: '新增科目一题库', assignee: '管理员A', status: '进行中', dueDate: '2026-06-15' }] }
    })
  }),

  http.get('/api/admin/operation/dashboard', () => {
    return HttpResponse.json({
      code: 0,
      data: { totalUsers: 2560, dau: 420, mau: 1850, retention: 68 }
    })
  }),

  http.get('/api/admin/cms/questions', () => {
    return HttpResponse.json({
      code: 0,
      data: { list: [{ id: 1, content: '题目内容...', subject: 1, type: 'single', status: 'online', author: '管理员A' }] }
    })
  }),

  http.get('/api/admin/cms/review', () => {
    return HttpResponse.json({
      code: 0,
      data: { list: [{ id: 1, content: '新增题目', submitter: '编辑A', time: '2026-06-01', status: 'reviewing' }] }
    })
  }),

  http.get('/api/admin/cms/knowledge', () => {
    return HttpResponse.json({
      code: 0,
      data: { list: [{ id: 1, name: '交通标志', questionCount: 120, status: 'online', editor: '管理员A' }] }
    })
  }),
]

// Mock 题库数据生成
const ALL_MOCK_QUESTIONS = [
  { id: 1, type: 'single' as const, subject: 1 as const, content: '在高速公路上遇到紧急情况时，以下做法正确的是？', options: ['A. 立即紧急制动', 'B. 先避人后避物', 'C. 先制动减速，后转向避让', 'D. 立即转向避让'], answer: 'C', explanation: '高速行驶时应先制动减速再转向避让，避免急打方向导致侧翻。', category: '安全常识', difficulty: 2 },
  { id: 2, type: 'single' as const, subject: 1 as const, content: '这个标志表示什么含义？', options: ['A. 禁止通行', 'B. 禁止驶入', 'C. 禁止机动车通行', 'D. 禁止小型汽车通行'], answer: 'B', explanation: '红色圆圈加白色横杠表示"禁止驶入"。', category: '交通标志', difficulty: 1 },
  { id: 3, type: 'judge' as const, subject: 1 as const, content: '在道路上发生交通事故，仅造成轻微财产损失，并且基本事实清楚的，当事人应当先撤离现场再进行协商处理。', options: ['A. 正确', 'B. 错误'], answer: 'A', explanation: '根据《道路交通安全法》规定，轻微事故应先撤离再协商。', category: '交通法规', difficulty: 1 },
  { id: 4, type: 'single' as const, subject: 4 as const, content: '驾驶人进入驾驶室前，首先应做什么？', options: ['A. 观察车辆周围情况', 'B. 检查轮胎气压', 'C. 打开车门', 'D. 调整座椅'], answer: 'A', explanation: '安全驾驶的首要原则是观察周围环境。', category: '驾驶理论', difficulty: 1 },
  { id: 5, type: 'multiple' as const, subject: 1 as const, content: '以下哪些属于危险驾驶行为？', options: ['A. 酒后驾驶', 'B. 疲劳驾驶', 'C. 超速行驶', 'D. 系安全带'], answer: 'A,B,C', explanation: '酒后驾驶、疲劳驾驶、超速行驶均属危险驾驶行为。', category: '安全常识', difficulty: 2 },
  { id: 6, type: 'single' as const, subject: 1 as const, content: '夜间会车应当在距对方来车多少米以外改用近光灯？', options: ['A. 50米', 'B. 100米', 'C. 150米', 'D. 200米'], answer: 'C', explanation: '《道路交通安全法实施条例》规定夜间会车应在150米以外改用近光灯。', category: '交通法规', difficulty: 2 },
  { id: 7, type: 'judge' as const, subject: 4 as const, content: '在冰雪路面上行车时，应降低车速，增大安全距离。', options: ['A. 正确', 'B. 错误'], answer: 'A', explanation: '冰雪路面附着力降低，需要降低车速并增大跟车距离。', category: '驾驶理论', difficulty: 1 },
  { id: 8, type: 'single' as const, subject: 1 as const, content: '这个导向箭头表示什么？', options: ['A. 直行', 'B. 左转', 'C. 直行或左转', 'D. 右转'], answer: 'C', explanation: '该箭头表示直行或左转。', category: '交通标志', difficulty: 1 },
]

function generateMockQuestions(subject: number, count: number, types: string[]) {
  const filtered = ALL_MOCK_QUESTIONS.filter(q => q.subject === subject && (types.length === 0 || types.includes(q.type)))
  // 循环填充到指定数量
  const result: typeof ALL_MOCK_QUESTIONS = []
  for (let i = 0; i < count; i++) {
    const base = filtered[i % filtered.length]
    result.push({ ...base, id: i + 1, content: `[${i + 1}] ${base.content}` })
  }
  return result
}
