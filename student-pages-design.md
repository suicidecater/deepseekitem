# 学员端核心页面设计文档

> **版本**: V1.0 | **技术栈**: Vue 3 + Pinia + ECharts 5

---

## 1. 学习首页 (StudentHomeView) - 数据仪表盘

### 页面布局
```
┌──────────────────────────────────────────────────────┐
│  Header: 欢迎回来，张三！          [消息] [头像▼]      │
├─────────────┬────────────────────────────────────────┤
│  Sidebar    │  ┌──────────┐ ┌──────────────────┐    │
│  学习首页   │  │ 个人档案  │ │   能力雷达图      │    │
│  能力测评   │  │ 姓名/车型 │ │   ECharts Radar  │    │
│  AI学习路径 │  │ 驾校/注册 │ │                  │    │
│  AI交规问答 │  └──────────┘ └──────────────────┘    │
│  智能题库   │  ┌──────────────────────┐             │
│  模拟考试   │  │   今日学习任务清单    │             │
│  错题本     │  │ □ 交通标志专项练习   │             │
│  ...        │  │ □ AI知识点讲解       │             │
│             │  │ ☑ 模拟考试复盘       │             │
│             │  └──────────────────────┘             │
│             │  ┌──────────┐ ┌──────────────────┐    │
│             │  │ 学习地图  │ │ 快捷入口         │    │
│             │  │ 知识树    │ │ [开始练习][模拟考]│    │
│             │  │ 完成度60% │ │ [AI问答][错题本] │    │
│             │  └──────────┘ └──────────────────┘    │
└─────────────┴────────────────────────────────────────┘
```

### 核心代码结构

```vue
<!-- src/views/student/HomeView.vue -->
<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useStudentStore } from '@/stores/student'
import { useAuthStore } from '@/stores/auth'
import RadarChart from '@/components/business/RadarChart.vue'
import KnowledgeTreeMap from '@/components/business/KnowledgeTreeMap.vue'
import ProfileCard from '@/components/business/ProfileCard.vue'
import TaskList from '@/components/business/TaskList.vue'

const authStore = useAuthStore()
const studentStore = useStudentStore()

// 加载数据
onMounted(async () => {
  await Promise.all([
    studentStore.fetchProfile(),
    studentStore.fetchDashboard(),
    studentStore.fetchTodayTasks()
  ])
})

// 快捷入口跳转
const quickActions = [
  { label: '开始练习', icon: '✏️', route: '/student/practice' },
  { label: '模拟考试', icon: '📝', route: '/student/exam' },
  { label: 'AI问答', icon: '🤖', route: '/student/ai-qa' },
  { label: '错题本', icon: '📕', route: '/student/error-book' },
]

const radarData = computed(() => ({
  dimensions: ['交通标志', '交通法规', '安全常识', '驾驶理论'],
  current: studentStore.abilityScores,
  baseline: [60, 60, 60, 60]
}))
</script>

<template>
  <div class="home-page">
    <div class="home-grid">
      <!-- 左侧：个人档案 + 今日任务 -->
      <div class="home-left">
        <ProfileCard :profile="studentStore.profile" />
        <TaskList :tasks="studentStore.todayTasks" />
      </div>

      <!-- 中间：雷达图 + 学习地图 -->
      <div class="home-center">
        <section class="card">
          <h3>能力雷达图</h3>
          <RadarChart :data="radarData" />
        </section>
        <section class="card">
          <h3>学习地图</h3>
          <KnowledgeTreeMap :data="studentStore.knowledgeTree" />
        </section>
      </div>

      <!-- 右侧：快捷入口 + 考前冲刺 -->
      <div class="home-right">
        <section class="card">
          <h3>快捷入口</h3>
          <div class="quick-actions">
            <router-link v-for="action in quickActions" :key="action.route"
              :to="action.route" class="quick-btn">
              <span class="quick-icon">{{ action.icon }}</span>
              <span>{{ action.label }}</span>
            </router-link>
          </div>
        </section>
        <section v-if="studentStore.isSprintMode" class="card sprint-card">
          <h3>🔥 考前冲刺</h3>
          <p>距考试还有 {{ studentStore.daysUntilExam }} 天</p>
          <router-link to="/student/sprint" class="btn btn-primary">进入冲刺</router-link>
        </section>
      </div>
    </div>
  </div>
</template>

<style scoped>
.home-page { padding: 24px; max-width: var(--content-max-width); margin: 0 auto; }
.home-grid {
  display: grid;
  grid-template-columns: 280px 1fr 260px;
  gap: 20px;
}
.card {
  background: #fff; border-radius: var(--radius-lg);
  padding: 20px; border: 1px solid var(--color-border);
  margin-bottom: 20px;
}
.card h3 { font-size: 16px; margin-bottom: 16px; }

.quick-actions { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.quick-btn {
  display: flex; flex-direction: column; align-items: center; gap: 6px;
  padding: 16px 12px; border-radius: var(--radius-md);
  background: #FAFAFA; text-decoration: none; color: var(--color-text-primary);
  transition: all 0.2s;
}
.quick-btn:hover { background: var(--color-primary-light); color: var(--color-primary); }
.quick-icon { font-size: 24px; }

.sprint-card { background: linear-gradient(135deg, #FFF7E6, #FFF1CC); border-color: #FFD666; }

@media (max-width: 1400px) {
  .home-grid { grid-template-columns: 1fr 1fr; }
}
</style>
```

---

## 2. 能力基线测评页 (EvaluationView) - 测评模式

### 交互流程
```
注册完成 → 自动引导进入测评
  ├── 40题逐题展示（不可回退）
  ├── 每题45秒倒计时
  ├── 进度条实时更新
  └── 提交 → 展示测评结果
       ├── 能力雷达图（四维度）
       ├── 薄弱点清单（<60分维度）
       ├── 能力等级（入门/基础/进阶/冲刺）
       └── 学习建议
```

### 核心逻辑

```vue
<!-- src/views/student/EvaluationView.vue -->
<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useExamStore } from '@/stores/exam'
import CountdownTimer from '@/components/common/CountdownTimer.vue'
import QuestionCard from '@/components/business/QuestionCard.vue'
import ProgressBar from '@/components/common/ProgressBar.vue'
import RadarChart from '@/components/business/RadarChart.vue'

const router = useRouter()
const examStore = useExamStore()

// 测评状态：'loading' | 'testing' | 'result'
const phase = ref<'loading' | 'testing' | 'result'>('loading')
const evaluationResult = ref<any>(null)

// 加载测评题目（四维度各10题，共40题）
onMounted(async () => {
  await examStore.loadQuestions({
    mode: 'exam',     // 测评使用考试模式（不可回退）
    subject: 1,
    count: 40,        // 固定40题
    difficulty: 0
  })
  phase.value = 'testing'
})

// 当前题目（不可回退，只能向前）
const currentQuestion = computed(() => examStore.currentQuestion)

function handleAnswer(questionId: number, answer: string) {
  examStore.answerQuestion(questionId, answer)
}

function handleTimeout() {
  // 45秒超时自动进入下一题
  if (examStore.currentIndex < examStore.totalCount - 1) {
    examStore.nextQuestion()
  } else {
    handleSubmit()
  }
}

async function handleSubmit() {
  const result = await examStore.submitExam(examStore.timeSpent)
  evaluationResult.value = result
  phase.value = 'result'
}

// 能力等级判定
const abilityLevel = computed(() => {
  const avg = examStore.correctRate
  if (avg >= 90) return { level: '冲刺', color: '#52C41A', desc: '基础扎实，可以直接冲刺考试！' }
  if (avg >= 75) return { level: '进阶', color: '#1677FF', desc: '有一定基础，重点突破薄弱环节' }
  if (avg >= 60) return { level: '基础', color: '#FAAD14', desc: '需要系统学习交通法规知识' }
  return { level: '入门', color: '#FF4D4F', desc: '建议从头系统学习，打好基础' }
})
</script>

<template>
  <div class="evaluation-page">
    <!-- 测评阶段 -->
    <template v-if="phase === 'testing'">
      <div class="eval-header">
        <h2>能力基线测评</h2>
        <div class="eval-info">
          <CountdownTimer :seconds="45" @timeout="handleTimeout" />
          <ProgressBar :percent="examStore.progress" />
          <span>第 {{ examStore.currentIndex + 1 }} / {{ examStore.totalCount }} 题</span>
        </div>
      </div>
      <QuestionCard
        :question="currentQuestion!"
        :disabled="false"
        @answer="handleAnswer"
      />
      <button class="btn btn-primary" @click="handleSubmit">提交测评</button>
    </template>

    <!-- 结果阶段 -->
    <template v-if="phase === 'result'">
      <div class="eval-result">
        <h2>测评结果</h2>
        <div class="level-badge" :style="{ background: abilityLevel.color }">
          {{ abilityLevel.level }}
        </div>
        <p>{{ abilityLevel.desc }}</p>

        <RadarChart :data="evaluationResult.radarData" />

        <div class="weak-list">
          <h3>薄弱知识点（正确率 < 60%）</h3>
          <ul>
            <li v-for="item in evaluationResult.weakPoints" :key="item.name">
              {{ item.name }}：正确率 {{ item.rate }}%
            </li>
          </ul>
        </div>

        <button class="btn btn-primary" @click="router.push('/student/study-plan')">
          查看AI学习计划
        </button>
      </div>
    </template>
  </div>
</template>
```

---

## 3. 全真模拟考试页 (ExamView) - 全屏考试

### 页面布局
```
┌──────────────────────────────────────────────────────────┐
│  科目一 · 全真模拟考试                    剩余 42:15 ⏱   │
├─────────────┬────────────────────────────────────────────┤
│ 答题卡      │                                            │
│ ┌─┬─┬─┬─┐  │  第 15 题（单选题）                         │
│ │1│2│3│4│  │                                            │
│ ├─┼─┼─┼─┤  │  在高速公路上遇到紧急情况时，以下做法正确的   │
│ │5│6│7│8│  │  是？                                       │
│ └─┴─┴─┴─┘  │                                            │
│             │  ○ A. 立即紧急制动                          │
│ 已答: 14    │  ○ B. 先避人后避物                          │
│ 未答: 86    │  ● C. 先制动减速，后转向避让               │
│ 标记: 3     │  ○ D. 立即转向避让                          │
│             │                                            │
│ [交卷]      │  [上一题] [下一题] [标记]                   │
└─────────────┴────────────────────────────────────────────┘
```

### 防切窗实现

```typescript
// src/composables/useFullscreen.ts
import { ref, onMounted, onUnmounted } from 'vue'

export function useFullscreen() {
  const isFullscreen = ref(false)
  const warningCount = ref(0)
  const MAX_WARNINGS = 3  // 最多警告3次，超时强制交卷

  async function enterFullscreen() {
    try {
      await document.documentElement.requestFullscreen()
      isFullscreen.value = true
    } catch {
      console.warn('浏览器不支持全屏模式')
    }
  }

  function exitFullscreen() {
    if (document.fullscreenElement) {
      document.exitFullscreen()
    }
    isFullscreen.value = false
  }

  // 监听切窗/退出全屏
  function onFullscreenChange() {
    if (!document.fullscreenElement && isFullscreen.value) {
      warningCount.value++
      isFullscreen.value = false
      // 弹窗警告，超次数强制交卷
      if (warningCount.value >= MAX_WARNINGS) {
        return { forceSubmit: true }
      }
      return { warning: true, remaining: MAX_WARNINGS - warningCount.value }
    }
    return null
  }

  // 阻止右键、F12、Ctrl+S等
  function preventCheat(e: KeyboardEvent) {
    const blockedKeys = ['F12', 'F5']
    const blockedCombos = [
      e.ctrlKey && e.key === 's',
      e.ctrlKey && e.shiftKey && e.key === 'I',
      e.ctrlKey && e.key === 'u',
    ]
    if (blockedKeys.includes(e.key) || blockedCombos.some(Boolean)) {
      e.preventDefault()
      return false
    }
  }

  // 阻止切窗口
  function onVisibilityChange() {
    if (document.hidden) {
      warningCount.value++
      if (warningCount.value >= MAX_WARNINGS) {
        return { forceSubmit: true }
      }
      return { warning: true }
    }
    return null
  }

  onMounted(() => {
    document.addEventListener('fullscreenchange', onFullscreenChange)
    document.addEventListener('keydown', preventCheat)
    document.addEventListener('visibilitychange', onVisibilityChange)
  })

  onUnmounted(() => {
    document.removeEventListener('fullscreenchange', onFullscreenChange)
    document.removeEventListener('keydown', preventCheat)
    document.removeEventListener('visibilitychange', onVisibilityChange)
    exitFullscreen()
  })

  return { isFullscreen, enterFullscreen, exitFullscreen, warningCount }
}
```

---

## 4. AI交规问答页 (AiQAView) - 对话式布局

### SSE 流式响应实现

```typescript
// src/composables/useSSE.ts
export function useSSE() {
  const isStreaming = ref(false)
  let abortController: AbortController | null = null

  async function sendMessage(question: string, history: ChatMessage[]) {
    isStreaming.value = true
    abortController = new AbortController()

    const token = useAuthStore().token
    const response = await fetch(`${API_BASE}/ai/chat/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({ question, history }),
      signal: abortController.signal
    })

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
          const data = JSON.parse(line.slice(6))
          if (data.done) {
            isStreaming.value = false
            return
          }
          // data.content 为增量文本
          yield data.content
        }
      }
    }
  }

  function abort() {
    abortController?.abort()
    isStreaming.value = false
  }

  return { isStreaming, sendMessage, abort }
}
```

### 语音录音实现

```typescript
// src/composables/useVoice.ts
export function useVoice() {
  const isRecording = ref(false)
  const mediaRecorder = ref<MediaRecorder | null>(null)
  const audioChunks = ref<Blob[]>([])

  async function startRecording() {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
    mediaRecorder.value = new MediaRecorder(stream, { mimeType: 'audio/webm' })

    mediaRecorder.value.ondataavailable = (e) => {
      audioChunks.value.push(e.data)
    }

    mediaRecorder.value.onstop = async () => {
      const audioBlob = new Blob(audioChunks.value, { type: 'audio/webm' })
      const formData = new FormData()
      formData.append('audio', audioBlob, 'recording.webm')

      // 上传到后端转文字
      const res = await fetch(`${API_BASE}/ai/speech-to-text`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${useAuthStore().token}` },
        body: formData
      })
      const data = await res.json()
      return data.text  // 返回识别的文字
    }

    mediaRecorder.value.start()
    isRecording.value = true
  }

  function stopRecording(): Promise<string> {
    return new Promise((resolve) => {
      if (mediaRecorder.value) {
        mediaRecorder.value.onstop = async () => {
          const text = await processAudio()
          resolve(text)
        }
        mediaRecorder.value.stop()
        isRecording.value = false
      }
    })
  }

  return { isRecording, startRecording, stopRecording }
}
```

---

## 5. 智能题库练习页 (PracticeView)

```vue
<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useExamStore } from '@/stores/exam'
import QuestionCard from '@/components/business/QuestionCard.vue'
import ProgressBar from '@/components/common/ProgressBar.vue'

const examStore = useExamStore()

const filter = reactive({
  knowledgeIds: [] as number[],
  type: 0,           // 0=全部, 1=单选, 2=多选, 3=判断
  difficulty: 0,     // 0=全部, 1-3
  count: 20          // 10/20/50
})

async function startPractice() {
  await examStore.loadQuestions({
    mode: 'practice',
    subject: 1,
    ...filter
  })
}

const showResult = ref(false)
function toggleResult() { showResult.value = !showResult.value }

// 实时统计
const stats = computed(() => {
  const correct = examStore.questions.filter(q => {
    const ans = examStore.answers.get(q.id)
    return ans && ans === q.answer
  }).length
  return { correct, total: examStore.questions.length }
})
</script>
```

---

## 6. 错题本页 (ErrorBookView)

```vue
<script setup lang="ts">
import { ref, onMounted } from 'vue'
import DataTable from '@/components/common/DataTable.vue'

interface ErrorQuestion {
  id: number
  questionContent: string
  errorType: '知识盲区' | '粗心' | '理解偏差'
  errorCount: number
  status: '待复习' | '已复习' | '已掌握'
  lastErrorTime: string
}

const errorList = ref<ErrorQuestion[]>([])
const filterType = ref('')

const columns = [
  { key: 'questionContent', title: '题目', width: 300 },
  { key: 'errorType', title: '错因', width: 100,
    render: (v: string) => {
      const colors: Record<string, string> = {
        '知识盲区': '#FF4D4F', '粗心': '#FAAD14', '理解偏差': '#1677FF'
      }
      return `<span style="color:${colors[v]}">${v}</span>`
    }
  },
  { key: 'errorCount', title: '错误次数', width: 80, sortable: true },
  { key: 'status', title: '复习状态', width: 100 },
  { key: 'lastErrorTime', title: '最后错误时间', width: 160 }
]

onMounted(async () => {
  // GET /api/student/error-book
  const res = await fetch('/api/student/error-book')
  errorList.value = await res.json()
})
</script>
```

---

## 7. 交通场景模拟页 (SceneSimView)

```vue
<script setup lang="ts">
import { ref } from 'vue'

const sceneTypes = ['城市道路', '高速公路', '夜间驾驶', '恶劣天气']
const currentScene = ref('')
const sceneImage = ref('')
const sceneQuestion = ref<any>(null)
const loading = ref(false)

async function generateScene(type: string) {
  loading.value = true
  currentScene.value = type
  // POST /api/ai/generate-scene
  const res = await fetch('/api/ai/generate-scene', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ sceneType: type })
  })
  const data = await res.json()
  sceneImage.value = data.image_url  // 文生图URL（5秒内返回）
  sceneQuestion.value = data.question
  loading.value = false
}
</script>
```

---

## 8. 学习评估报告页 (ReportView)

```vue
<script setup lang="ts">
import DashboardChart from '@/components/business/DashboardChart.vue'
import RadarChart from '@/components/business/RadarChart.vue'

// 能力成长曲线 - 折线图
const growthOption = {
  xAxis: { type: 'category', data: ['第1周', '第2周', '第3周', '第4周'] },
  yAxis: { type: 'value', max: 100 },
  series: [
    { name: '交通标志', type: 'line', data: [45, 60, 75, 85] },
    { name: '交通法规', type: 'line', data: [50, 55, 68, 72] },
    { name: '安全常识', type: 'line', data: [60, 72, 82, 90] },
    { name: '驾驶理论', type: 'line', data: [40, 50, 62, 65] }
  ]
}

// 成绩趋势 - 折线图
const scoreTrendOption = {
  xAxis: { type: 'category', data: ['模拟考1', '模拟考2', '模拟考3', '模拟考4'] },
  yAxis: { type: 'value', min: 0, max: 100 },
  series: [{
    type: 'line', data: [72, 78, 85, 92],
    markLine: { data: [{ yAxis: 90, label: { formatter: '及格线' } }] }
  }]
}

async function exportPDF() {
  // 调用后端生成PDF
  const res = await fetch('/api/student/report/pdf', {
    headers: { Authorization: `Bearer ${useAuthStore().token}` }
  })
  const blob = await res.blob()
  const url = URL.createObjectURL(blob)
  window.open(url)
}
</script>
```

---

*本文档基于 SRS V1.0 学员端 14 项功能需求编写*
