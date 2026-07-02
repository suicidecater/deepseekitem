<script setup lang="ts">
// src/views/student/SpecialTrainingView.vue - 专项训练（四分类20题×4）
import { ref, computed } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { post } from '@/api/request'
import QuestionCard from '@/components/business/QuestionCard.vue'

const authStore = useAuthStore()

type Phase = 'home' | 'loading' | 'quiz' | 'result'
const phase = ref<Phase>('home')
const loading = ref(false)

const cards = [
  { key: '交通标志', icon: '🚦', color: '#1677FF', bg: '#E6F4FF' },
  { key: '交通法规', icon: '📜', color: '#FA8C16', bg: '#FFF7E6' },
  { key: '安全常识', icon: '🛡️', color: '#52C41A', bg: '#F6FFED' },
  { key: '驾驶理论', icon: '📖', color: '#722ED1', bg: '#F9F0FF' },
] as const

const directionNames: Record<number, string> = { 1: '科目一', 4: '科目四', 5: '专业人员' }
const directionName = computed(() => directionNames[authStore.studySubject] || '科目一')

// 当前选中分类
const activeCategory = ref('')
const activeCard = computed(() => cards.find(c => c.key === activeCategory.value))

// 题目列表
interface TrainQuestion {
  id: number
  type: string
  content: string
  options: string[]
  image?: string
  difficulty?: number
}
const questions = ref<TrainQuestion[]>([])
const currentIndex = ref(0)
const answers = ref<Map<number, string>>(new Map())
const currentQuestion = computed(() => questions.value[currentIndex.value] || null)
const totalCount = computed(() => questions.value.length)
const answeredCount = computed(() => answers.value.size)

// 结果
interface AnswerItem {
  userAnswer: string
  correctAnswer: string
  isCorrect: boolean
}
const submitted = ref(false)
const answerMap = ref<Record<string, AnswerItem>>({})
const resultCorrectRate = ref(0)
const resultCorrectCount = ref(0)
const resultTotalCount = ref(0)

// 选择分类 → 加载题目
async function selectCategory(key: string) {
  activeCategory.value = key
  phase.value = 'loading'
  try {
    const res = await post<{ data: { questions: TrainQuestion[]; total: number } }>(
      '/api/question/special-training/start',
      { category: key }
    )
    const data = (res as any).data?.data || (res as any).data
    if (data?.questions?.length) {
      questions.value = data.questions
      currentIndex.value = 0
      answers.value = new Map()
      submitted.value = false
      answerMap.value = {}
      phase.value = 'quiz'
    } else {
      phase.value = 'home'
      alert('该分类暂无题目')
    }
  } catch {
    phase.value = 'home'
    alert('加载失败，请重试')
  }
}

// 答题
function handleAnswer(questionId: number, answer: string) {
  answers.value.set(questionId, answer)
}

// 导航
function goNext() {
  if (currentIndex.value < totalCount.value - 1) currentIndex.value++
}
function goPrev() {
  if (currentIndex.value > 0) currentIndex.value--
}
function jumpTo(idx: number) {
  if (idx >= 0 && idx < totalCount.value) currentIndex.value = idx
}

// 提交
async function handleSubmit() {
  if (answers.value.size < totalCount.value) {
    const confirm = window.confirm(`还有 ${totalCount.value - answers.value.size} 题未作答，确定提交吗？`)
    if (!confirm) return
  }
  loading.value = true
  try {
    const answerList = Array.from(answers.value.entries()).map(([qid, ans]) => ({
      questionId: qid,
      answer: ans,
    }))
    const res = await post('/api/question/special-training/submit', {
      answers: answerList,
      category: activeCategory.value,
    })
    const data = (res as any).data?.data || (res as any).data
    answerMap.value = data?.answerMap || {}
    resultCorrectRate.value = data?.correctRate || 0
    resultCorrectCount.value = data?.correctCount || 0
    resultTotalCount.value = data?.totalCount || totalCount.value
    submitted.value = true
    currentIndex.value = 0
    phase.value = 'result'
  } catch {
    alert('提交失败，请重试')
  } finally {
    loading.value = false
  }
}

// 带判题结果的题目（合并前端题目 + 后端判题）
const reviewQuestions = computed(() => {
  return questions.value.map(q => {
    const item = answerMap.value[q.id]
    return {
      ...q,
      answer: item?.correctAnswer || '',
      userAnswer: item?.userAnswer || '',
      isCorrect: item?.isCorrect ?? false,
    }
  })
})

function goHome() {
  phase.value = 'home'
  questions.value = []
  answers.value = new Map()
  submitted.value = false
  answerMap.value = {}
  currentIndex.value = 0
}

// 未作答数量提示
const unansweredCount = computed(() => totalCount.value - answeredCount.value)
</script>

<template>
  <div class="sp-page">
    <!-- ========== 首页：4张卡片 ========== -->
    <template v-if="phase === 'home'">
      <div class="sp-home">
        <h2>{{ directionName }} · 专项训练</h2>
        <p class="sp-sub">选择分类，每组 20 道题，无时间限制，可自由浏览作答</p>
        <div class="sp-cards">
          <div
            v-for="card in cards" :key="card.key"
            class="sp-card"
            :style="{ borderColor: card.color }"
            @click="selectCategory(card.key)"
          >
            <span class="sp-card-icon">{{ card.icon }}</span>
            <strong class="sp-card-title" :style="{ color: card.color }">{{ card.key }}</strong>
            <span class="sp-card-desc">20 道精选题</span>
          </div>
        </div>
      </div>
    </template>

    <!-- ========== 加载中 ========== -->
    <div v-if="phase === 'loading'" class="sp-loading">
      <div class="spinner"></div>
      <p>正在准备 {{ activeCard?.key }} 题目...</p>
    </div>

    <!-- ========== 答题阶段 ========== -->
    <template v-if="phase === 'quiz' && currentQuestion">
      <div class="sp-header">
        <div class="sp-header-top">
          <button class="btn btn-outline btn-sm" @click="goHome">← 返回</button>
          <h2>{{ activeCard?.icon }} {{ activeCard?.key }} · 专项训练</h2>
          <span class="sp-badge">{{ answeredCount }} / {{ totalCount }}</span>
        </div>
        <!-- 题号导航 -->
        <div class="sp-question-nav">
          <button
            v-for="(q, idx) in questions" :key="q.id"
            class="qn-dot"
            :class="{
              active: idx === currentIndex,
              answered: answers.has(q.id),
            }"
            :title="'第' + (idx + 1) + '题' + (answers.has(q.id) ? ' ✓' : '')"
            @click="jumpTo(idx)"
          >{{ idx + 1 }}</button>
        </div>
      </div>

      <div class="sp-body">
        <QuestionCard
          :question="currentQuestion"
          :question-index="currentIndex + 1"
          :selected-answer="answers.get(currentQuestion.id) || ''"
          :show-result="false"
          @answer="handleAnswer"
        />

        <div class="sp-nav">
          <button class="btn btn-outline" :disabled="currentIndex === 0" @click="goPrev">上一题</button>
          <span class="sp-nav-info">
            {{ unansweredCount > 0 ? `剩 ${unansweredCount} 题未答` : '已全部作答' }}
          </span>
          <button
            v-if="currentIndex < totalCount - 1"
            class="btn btn-outline"
            @click="goNext"
          >下一题</button>
          <button
            v-else
            class="btn btn-primary"
            :disabled="loading"
            @click="handleSubmit"
          >{{ loading ? '提交中...' : '提交答卷' }}</button>
        </div>
      </div>
    </template>

    <!-- ========== 结果阶段 ========== -->
    <template v-if="phase === 'result'">
      <div class="sp-result-header">
        <h2>{{ activeCard?.icon }} {{ activeCard?.key }} · 训练结果</h2>
        <div class="sp-result-score">
          <div class="score-circle" :style="{ '--pct': resultCorrectRate }">
            <span class="score-num">{{ resultCorrectRate }}%</span>
          </div>
          <p>正确 {{ resultCorrectCount }} / {{ resultTotalCount }} 题</p>
        </div>
        <button class="btn btn-outline" @click="goHome">返回分类</button>
      </div>

      <div class="sp-review">
        <div
          v-for="(q, idx) in reviewQuestions" :key="q.id"
          class="sp-review-item"
        >
          <div class="review-header">
            <span class="review-idx">第 {{ idx + 1 }} 题</span>
            <span class="review-tag" :class="q.isCorrect ? 'correct' : 'wrong'">
              {{ q.isCorrect ? '✓ 正确' : '✗ 错误' }}
            </span>
          </div>
          <QuestionCard
            :question="q"
            :question-index="idx + 1"
            :selected-answer="q.userAnswer"
            :show-result="true"
          />
        </div>
      </div>

      <div class="sp-result-footer">
        <button class="btn btn-primary" @click="goHome">返回分类列表</button>
      </div>
    </template>
  </div>
</template>

<style scoped>
.sp-page { max-width: 800px; margin: 0 auto; padding: 24px; }

/* ====== 首页 ====== */
.sp-home { text-align: center; padding: 40px 0; }
.sp-home h2 { font-size: var(--font-size-2xl); margin-bottom: 8px; }
.sp-sub { color: var(--color-text-tertiary); font-size: var(--font-size-sm); margin-bottom: 40px; }
.sp-cards { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; max-width: 560px; margin: 0 auto; }
.sp-card {
  background: #fff; border-radius: var(--radius-lg); padding: 32px 20px;
  border: 2px solid; cursor: pointer; transition: all 0.2s; text-align: center;
}
.sp-card:hover { transform: translateY(-4px); box-shadow: 0 8px 24px rgba(0,0,0,0.1); }
.sp-card-icon { display: block; font-size: 40px; margin-bottom: 12px; }
.sp-card-title { display: block; font-size: var(--font-size-lg); font-weight: 700; margin-bottom: 4px; }
.sp-card-desc { font-size: var(--font-size-xs); color: var(--color-text-tertiary); }

/* ====== 加载 ====== */
.sp-loading { display: flex; flex-direction: column; align-items: center; justify-content: center; height: 50vh; gap: 16px; color: var(--color-text-tertiary); }
.spinner { width: 40px; height: 40px; border: 3px solid var(--color-border); border-top-color: var(--color-primary); border-radius: 50%; animation: spin 0.8s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }

/* ====== 答题 ====== */
.sp-header { margin-bottom: 20px; }
.sp-header-top { display: flex; align-items: center; gap: 12px; }
.sp-header-top h2 { font-size: var(--font-size-xl); flex: 1; }
.sp-badge { font-size: var(--font-size-sm); font-weight: 600; color: var(--color-primary); white-space: nowrap; }

.sp-nav { display: flex; align-items: center; justify-content: space-between; margin-top: 24px; padding-top: 16px; border-top: 1px solid var(--color-border-light); }
.sp-nav-info { font-size: var(--font-size-xs); color: var(--color-text-tertiary); }

/* 题号导航 */
.sp-question-nav { display: flex; flex-wrap: nowrap; gap: 4px; margin-top: 12px; padding: 8px 12px; background: #fff; border-radius: var(--radius-md); border: 1px solid var(--color-border-light); overflow-x: auto; }
.sp-question-nav::-webkit-scrollbar { height: 4px; }
.sp-question-nav::-webkit-scrollbar-thumb { background: #ccc; border-radius: 2px; }
.qn-dot {
  width: 32px; height: 32px; border-radius: var(--radius-sm); border: 1px solid var(--color-border);
  font-size: 12px; font-weight: 600; display: flex; align-items: center; justify-content: center;
  transition: all 0.15s; background: #fff; color: var(--color-text-secondary);
}
.qn-dot:hover:not(.active) { border-color: var(--color-primary); }
.qn-dot.active { background: var(--color-primary); color: #fff; border-color: var(--color-primary); }
.qn-dot.answered { background: var(--color-primary-light); border-color: var(--color-primary); color: var(--color-primary); }

/* ====== 结果 ====== */
.sp-result-header { text-align: center; margin-bottom: 24px; }
.sp-result-header h2 { font-size: var(--font-size-2xl); margin-bottom: 20px; }
.sp-result-score { display: flex; flex-direction: column; align-items: center; gap: 8px; margin-bottom: 20px; }
.score-circle {
  width: 100px; height: 100px; border-radius: 50%;
  background: conic-gradient(#52C41A calc(var(--pct) * 1%), #F0F0F0 0);
  display: flex; align-items: center; justify-content: center; position: relative;
}
.score-circle::after {
  content: ''; width: 80px; height: 80px; border-radius: 50%; background: #fff; position: absolute;
}
.score-num { position: relative; z-index: 1; font-size: 24px; font-weight: 700; color: var(--color-text-primary); }
.sp-result-header p { color: var(--color-text-secondary); font-size: var(--font-size-sm); }

.sp-review { display: flex; flex-direction: column; gap: 24px; }
.sp-review-item { background: #fff; border-radius: var(--radius-lg); border: 1px solid var(--color-border-light); overflow: hidden; }
.review-header { display: flex; align-items: center; justify-content: space-between; padding: 12px 24px; background: #FAFAFA; border-bottom: 1px solid var(--color-border-light); }
.review-idx { font-size: var(--font-size-sm); font-weight: 600; }
.review-tag { font-size: var(--font-size-xs); padding: 2px 10px; border-radius: var(--radius-sm); font-weight: 600; }
.review-tag.correct { background: #F6FFED; color: #52C41A; }
.review-tag.wrong { background: #FFF1F0; color: #FF4D4F; }

.sp-result-footer { text-align: center; margin-top: 24px; padding-bottom: 40px; }
</style>
