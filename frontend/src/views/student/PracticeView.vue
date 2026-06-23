<script setup lang="ts">
// src/views/student/PracticeView.vue - 智能题库练习页
import { ref, reactive, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useExamStore } from '@/stores/exam'
import QuestionCard from '@/components/business/QuestionCard.vue'

const route = useRoute()
const router = useRouter()
const examStore = useExamStore()

type Phase = 'config' | 'practicing' | 'finished'
const phase = ref<Phase>('config')

// 筛选条件
const filters = reactive({
  subject: Number(route.query.subject) || 1,
  types: [] as string[],
  difficulty: 0,
  count: 20
})

const subjectOptions = [
  { label: '科目一', value: 1 },
  { label: '科目四', value: 4 }
]
const typeOptions = [
  { label: '单选题', value: 'single' },
  { label: '多选题', value: 'multiple' },
  { label: '判断题', value: 'judge' }
]
const countOptions = [10, 20, 50]

// 答题状态
const selectedAnswer = ref('')
const showResult = ref(false)
const currentResult = ref<any>(null)
const startTime = ref(0)
const totalTimeSpent = ref(0)

// 统计
const answerHistory = ref<{ correct: boolean; timeSpent: number }[]>([])
const correctCount = computed(() => answerHistory.value.filter(a => a.correct).length)
const accuracy = computed(() =>
  answerHistory.value.length > 0
    ? Math.round((correctCount.value / answerHistory.value.length) * 100)
    : 0
)

async function startPractice() {
  await examStore.loadQuestions({
    mode: 'practice',
    subject: filters.subject,
    count: filters.count,
    difficulty: filters.difficulty,
    types: filters.types.length > 0 ? filters.types : undefined
  })
  phase.value = 'practicing'
  startTime.value = Date.now()
  selectedAnswer.value = ''
  showResult.value = false
  answerHistory.value = []
}

function handleAnswer(questionId: number, answer: string) {
  if (showResult.value) return
  selectedAnswer.value = answer
  examStore.recordAnswer(questionId, answer)

  // 即时判题
  const q = examStore.currentQuestion
  if (q) {
    const correct = q.answer === answer
    const timeSpent = Math.round((Date.now() - startTime.value) / 1000)
    answerHistory.value.push({ correct, timeSpent })
    totalTimeSpent.value += timeSpent
    showResult.value = true

    // Mock 获取解析
    currentResult.value = {
      correct,
      correctAnswer: q.answer,
      explanation: q.explanation
    }
  }
}

function nextQuestion() {
  if (examStore.currentIndex < examStore.totalCount - 1) {
    examStore.nextQuestion()
    selectedAnswer.value = ''
    showResult.value = false
    currentResult.value = null
    startTime.value = Date.now()
  } else {
    finishPractice()
  }
}

function prevQuestion() {
  if (examStore.currentIndex > 0) {
    examStore.prevQuestion()
    const prevAnswer = examStore.answers.get(examStore.questions[examStore.currentIndex]?.id || 0)
    selectedAnswer.value = prevAnswer || ''
    showResult.value = !!prevAnswer
    currentResult.value = prevAnswer ? {
      correct: examStore.questions[examStore.currentIndex]?.answer === prevAnswer,
      correctAnswer: examStore.questions[examStore.currentIndex]?.answer,
      explanation: examStore.questions[examStore.currentIndex]?.explanation
    } : null
  }
}

function finishPractice() {
  phase.value = 'finished'
}

function restart() {
  examStore.reset()
  phase.value = 'config'
}

onMounted(() => {
  // 如果 URL 带 subject 参数，自动开始
  if (route.query.subject) {
    startPractice()
  }
})
</script>

<template>
  <div class="practice-page">
    <!-- 配置页 -->
    <template v-if="phase === 'config'">
      <div class="config-panel card">
        <h2>智能题库练习</h2>
        <p class="config-desc">选择科目和题型，开始针对性练习</p>

        <div class="filter-group">
          <label>科目</label>
          <div class="filter-options">
            <button
              v-for="opt in subjectOptions" :key="opt.value"
              class="filter-btn" :class="{ active: filters.subject === opt.value }"
              @click="filters.subject = opt.value"
            >{{ opt.label }}</button>
          </div>
        </div>

        <div class="filter-group">
          <label>题型（可多选，不选则全部）</label>
          <div class="filter-options">
            <button
              v-for="opt in typeOptions" :key="opt.value"
              class="filter-btn" :class="{ active: filters.types.includes(opt.value) }"
              @click="filters.types.includes(opt.value)
                ? filters.types = filters.types.filter(t => t !== opt.value)
                : filters.types.push(opt.value)"
            >{{ opt.label }}</button>
          </div>
        </div>

        <div class="filter-group">
          <label>题目数量</label>
          <div class="filter-options">
            <button
              v-for="n in countOptions" :key="n"
              class="filter-btn" :class="{ active: filters.count === n }"
              @click="filters.count = n"
            >{{ n }}题</button>
          </div>
        </div>

        <button class="btn btn-primary btn-lg btn-block" @click="startPractice">开始练习</button>
      </div>
    </template>

    <!-- 练习中 -->
    <template v-if="phase === 'practicing' && examStore.currentQuestion">
      <div class="practice-header">
        <h2>智能题库练习</h2>
        <div class="practice-stats">
          <span>进度：{{ examStore.currentIndex + 1 }}/{{ examStore.totalCount }}</span>
          <span>正确率：{{ accuracy }}%</span>
        </div>
        <div class="progress-bar">
          <div class="progress-fill" :style="{ width: ((examStore.currentIndex + 1) / examStore.totalCount) * 100 + '%' }"></div>
        </div>
      </div>

      <QuestionCard
        :question="examStore.currentQuestion"
        :selected-answer="selectedAnswer"
        :show-result="showResult"
        @answer="handleAnswer"
      />

      <div class="practice-footer">
        <button class="btn btn-outline" :disabled="examStore.currentIndex === 0" @click="prevQuestion">
          上一题
        </button>
        <button class="btn btn-primary" @click="nextQuestion">
          {{ examStore.currentIndex < examStore.totalCount - 1 ? '下一题' : '完成练习' }}
        </button>
      </div>
    </template>

    <!-- 完成 -->
    <template v-if="phase === 'finished'">
      <div class="finish-panel card">
        <h2>练习完成！</h2>
        <div class="finish-stats">
          <div class="finish-stat">
            <span class="stat-num">{{ examStore.totalCount }}</span>
            <span class="stat-label">总题数</span>
          </div>
          <div class="finish-stat">
            <span class="stat-num correct">{{ correctCount }}</span>
            <span class="stat-label">正确</span>
          </div>
          <div class="finish-stat">
            <span class="stat-num wrong">{{ examStore.totalCount - correctCount }}</span>
            <span class="stat-label">错误</span>
          </div>
          <div class="finish-stat">
            <span class="stat-num">{{ accuracy }}%</span>
            <span class="stat-label">正确率</span>
          </div>
        </div>
        <p class="finish-time">总用时：{{ Math.floor(totalTimeSpent / 60) }}分{{ totalTimeSpent % 60 }}秒</p>
        <div class="finish-actions">
          <button class="btn btn-primary" @click="restart">再来一组</button>
          <button class="btn btn-outline" @click="router.push('/student/error-book')">查看错题</button>
        </div>
      </div>
    </template>
  </div>
</template>

<style scoped>
.practice-page { max-width: 800px; margin: 0 auto; padding: 24px; }

.config-panel { padding: 32px; }
.config-panel h2 { font-size: var(--font-size-2xl); margin-bottom: 4px; }
.config-desc { font-size: var(--font-size-sm); color: var(--color-text-tertiary); margin-bottom: 24px; }

.filter-group { margin-bottom: 20px; }
.filter-group label { display: block; font-size: var(--font-size-sm); color: var(--color-text-secondary); margin-bottom: 8px; }
.filter-options { display: flex; gap: 8px; flex-wrap: wrap; }
.filter-btn {
  padding: 8px 18px; border-radius: var(--radius-md); border: 1px solid var(--color-border);
  font-size: var(--font-size-sm); transition: all var(--transition-fast);
}
.filter-btn.active { border-color: var(--color-primary); background: var(--color-primary-light); color: var(--color-primary); font-weight: 500; }

.card { background: #fff; border-radius: var(--radius-lg); padding: 20px; border: 1px solid var(--color-border-light); }

.practice-header { margin-bottom: 20px; }
.practice-header h2 { font-size: var(--font-size-xl); margin-bottom: 8px; }
.practice-stats { display: flex; gap: 20px; font-size: var(--font-size-sm); color: var(--color-text-secondary); margin-bottom: 10px; }
.progress-bar { height: 6px; background: #F0F0F0; border-radius: 3px; overflow: hidden; }
.progress-fill { height: 100%; background: var(--color-primary); border-radius: 3px; transition: width 0.3s; }

.practice-footer {
  display: flex; justify-content: space-between; margin-top: 24px; padding-top: 16px;
  border-top: 1px solid var(--color-border-light);
}

/* 完成页 */
.finish-panel { text-align: center; padding: 40px; }
.finish-panel h2 { font-size: var(--font-size-2xl); margin-bottom: 24px; color: var(--color-success); }

.finish-stats { display: flex; justify-content: center; gap: 32px; margin-bottom: 16px; }
.finish-stat { text-align: center; }
.stat-num { display: block; font-size: 36px; font-weight: 700; color: var(--color-primary); }
.stat-num.correct { color: var(--color-success); }
.stat-num.wrong { color: var(--color-error); }
.stat-label { font-size: var(--font-size-xs); color: var(--color-text-tertiary); }

.finish-time { font-size: var(--font-size-sm); color: var(--color-text-secondary); margin-bottom: 24px; }
.finish-actions { display: flex; gap: 12px; justify-content: center; }
</style>
