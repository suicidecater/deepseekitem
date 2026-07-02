<script setup lang="ts">
// src/views/student/PracticeView.vue - 智能题库顺序刷题
import { ref, computed, watch, onMounted } from 'vue'
import { useAppStore } from '@/stores/app'
import request from '@/api/request'

const appStore = useAppStore()

// ===== 题库选择 =====
const banks = [
  { key: 'subject1', label: '科目一', icon: '🚗', desc: '道路交通安全法律、法规', count: '...' },
  { key: 'subject4', label: '科目四', icon: '🛣️', desc: '安全文明驾驶常识', count: '...' },
  { key: 'professional', label: '专业人员', icon: '🚛', desc: '客货运/危险品从业资格', count: '...' },
]

type Phase = 'select' | 'practicing'
const phase = ref<Phase>('select')
const currentBank = ref<typeof banks[0] | null>(null)

// ===== 题目数据 =====
interface Question {
  id: number; questionNumber: number; questionType: string
  questionText: string; optionA: string; optionB: string; optionC: string; optionD: string
  imageFile: string | null; category: string | null; difficulty: number
}
const questions = ref<Question[]>([])
const currentIndex = ref(0)
const selectedAnswer = ref('')
const submitting = ref(false)
const loading = ref(false)

// 答题记录: { [questionId]: { userAnswer: string, correctAnswer: string, correct: boolean } }
const answers = ref<Record<number, { userAnswer: string; correctAnswer: string; correct: boolean }>>({})
// 已提交记录: { [questionId]: bool }
const submittedSet = ref<Record<number, boolean>>({})

// ===== 统计 =====
const totalQuestions = computed(() => questions.value.length)
const answeredCount = computed(() => Object.keys(submittedSet.value).length)
const correctCount = computed(() => Object.values(answers.value).filter(a => a.correct).length)
const progressPercent = computed(() =>
  totalQuestions.value > 0 ? Math.round((answeredCount.value / totalQuestions.value) * 100) : 0
)
const accuracyPercent = computed(() =>
  answeredCount.value > 0 ? Math.round((correctCount.value / answeredCount.value) * 100) : 0
)

const currentQuestion = computed(() => questions.value[currentIndex.value] || null)
const isCurrentSubmitted = computed(() => {
  const q = currentQuestion.value
  return q ? !!submittedSet.value[q.id] : false
})
const currentSavedAnswer = computed(() => {
  const q = currentQuestion.value
  return q ? answers.value[q.id] : null
})

// SVG 圆环参数
const circleR = 54
const circleC = 2 * Math.PI * circleR
function dashOffset(pct: number) { return circleC * (1 - pct / 100) }

// ===== 图片路径兼容 =====
function getImageSrc(imageFile: string | null): string | null {
  if (!imageFile) return null
  // 直接使用数据库中的文件名（如 1_1.jpg）
  return `/images/${imageFile}`
}
const hideImage = ref(false)  // 只有 jpg/png 都失败才隐藏
const imageRetried = ref(false)
function onImageError(e: Event) {
  const img = e.target as HTMLImageElement
  if (imageRetried.value) {
    // 第二次也失败了，隐藏图片区域
    hideImage.value = true
    return
  }
  // 第一次失败：如果是 .jpg 则尝试 .png
  if (/\.jpg$/i.test(img.src) && !/\.png$/i.test(img.src)) {
    imageRetried.value = true
    img.src = img.src.replace(/\.jpg$/i, '.png')
  } else {
    // 第一次就是 .png 或其他格式失败，直接隐藏
    hideImage.value = true
  }
}
// 切换题目时重置状态
function resetImageState() {
  hideImage.value = false
  imageRetried.value = false
}

// ===== 选项相关 =====
const optionLabels = ['A', 'B', 'C', 'D']

function getCategoryClass(cat: string): string {
  const map: Record<string, string> = {
    '交通标志': 'sign', '交通法规': 'law', '安全常识': 'safe', '驾驶理论': 'theory',
  }
  return map[cat] || ''
}

function getStorageKey(bankKey: string) {
  return `seq_practice_${bankKey}`
}

/** 保存当前进度到 localStorage */
function saveProgress() {
  if (!currentBank.value) return
  const key = getStorageKey(currentBank.value.key)
  const data = {
    currentIndex: currentIndex.value,
    answers: answers.value,
    submittedSet: submittedSet.value,
    questionIds: questions.value.map(q => q.id), // 校验题库是否变化
    total: totalQuestions.value,
  }
  localStorage.setItem(key, JSON.stringify(data))
}

/** 从 localStorage 恢复进度，返回是否成功恢复 */
function restoreProgress(): boolean {
  if (!currentBank.value) return false
  const key = getStorageKey(currentBank.value.key)
  const raw = localStorage.getItem(key)
  if (!raw) return false
  try {
    const data = JSON.parse(raw)
    // 校验题库未变化（题数相同且第一题ID一致）
    if (data.total === totalQuestions.value && data.questionIds && data.questionIds[0] === questions.value[0]?.id) {
      answers.value = data.answers || {}
      submittedSet.value = data.submittedSet || {}
      // 从上次位置开始，如果该题已提交则前进到第一道未提交的题
      let idx = Math.min(data.currentIndex || 0, totalQuestions.value - 1)
      while (idx < totalQuestions.value - 1) {
        const qid = questions.value[idx]?.id
        if (qid && !submittedSet.value[qid]) break
        idx++
      }
      currentIndex.value = idx
      return true
    }
  } catch { /* ignore */ }
  return false
}

/** 清除进度并从头开始 */
function resetProgress() {
  answers.value = {}
  submittedSet.value = {}
  currentIndex.value = 0
  selectedAnswer.value = ''
  if (currentBank.value) {
    localStorage.removeItem(getStorageKey(currentBank.value.key))
  }
  selectAnswerFromHistory()
}

/** 检查某题库是否有保存的进度（选择页用） */
function hasProgress(bankKey: string): boolean {
  return !!localStorage.getItem(getStorageKey(bankKey))
}

function getOptions(q: Question): { letter: string; text: string; value: string }[] {
  const opts: { letter: string; text: string; value: string }[] = []
  const fields = ['A', 'B', 'C', 'D'] as const
  for (const f of fields) {
    const text = q[`option${f}` as keyof Question] as string
    if (text) {
      let value = f
      if (q.questionType === '判断题') {
        if (f === 'A' && (text === '√' || text === '对' || text === '正确')) value = '√'
        else if (f === 'B' && (text === '×' || text === '错' || text === '错误')) value = '×'
        else if (text === '√' || text === '对' || text === '正确') value = '√'
        else if (text === '×' || text === '错' || text === '错误') value = '×'
      }
      opts.push({ letter: f, text, value })
    }
  }
  return opts
}

function getOptionClass(opt: { letter: string; value: string }): Record<string, boolean> {
  const isSelected = selectedAnswer.value === opt.value
  if (!isCurrentSubmitted.value) return { selected: isSelected }

  const saved = currentSavedAnswer.value
  if (!saved) return {}

  const correctAnswer = saved.correctAnswer
  const userAnswer = saved.userAnswer
  const isCorrectOpt = opt.value === correctAnswer || opt.letter === correctAnswer
  const isUserSelected = opt.value === userAnswer || opt.letter === userAnswer

  // 正确答案始终标绿
  if (isCorrectOpt) return { 'is-correct': true }
  // 用户选错且这是用户选的 → 标红
  if (isUserSelected && !saved.correct) return { 'is-wrong': true }
  // 用户选对 → 标绿（已被 isCorrectOpt 覆盖，这里是兜底）
  if (isUserSelected && saved.correct) return { 'is-correct': true }

  return {}
}

function selectOption(value: string) {
  if (isCurrentSubmitted.value || submitting.value) return
  selectedAnswer.value = value
}

// ===== API =====
async function loadBankQuestions(source: string, resume = false) {
  loading.value = true
  answers.value = {}
  submittedSet.value = {}
  currentIndex.value = 0
  selectedAnswer.value = ''
  try {
    const res = await request.get(`/api/question/sequential?source=${source}`)
    const d = res.data
    if (d.code === 0 && d.data) {
      questions.value = d.data.questions || []
      banks.find(b => b.key === source)!.count = String(d.data.total || questions.value.length)
      // 尝试恢复上次进度
      if (resume && restoreProgress()) {
        // 已恢复：选中历史答案
        selectAnswerFromHistory()
      }
    } else {
      appStore.showToast(d.message || '加载失败', 'error')
    }
  } catch {
    appStore.showToast('加载题库失败', 'error')
  } finally {
    loading.value = false
  }
}

function startPractice(bank: typeof banks[0], resume = true) {
  currentBank.value = bank
  phase.value = 'practicing'
  loadBankQuestions(bank.key, resume)
}

async function submitAnswer() {
  const q = currentQuestion.value
  if (!q || !selectedAnswer.value || submitting.value) return
  if (isCurrentSubmitted.value) { appStore.showToast('本题已提交过', 'info'); return }

  submitting.value = true
  try {
    const res = await request.post('/api/question/check-answer', {
      questionId: q.id,
      source: currentBank.value!.key,
      answer: selectedAnswer.value,
    })
    const d = res.data
    if (d.code === 0 && d.data) {
      const { correct, correctAnswer } = d.data
      answers.value[q.id] = { userAnswer: selectedAnswer.value, correctAnswer, correct }
      submittedSet.value[q.id] = true
      saveProgress()
    } else {
      appStore.showToast(d.message || '校验失败', 'error')
    }
  } catch {
    appStore.showToast('提交失败', 'error')
  } finally {
    submitting.value = false
  }
}

function goPrev() {
  if (currentIndex.value > 0) {
    currentIndex.value--
  }
}

function goNext() {
  if (currentIndex.value < totalQuestions.value - 1) {
    currentIndex.value++
  }
}

function selectAnswerFromHistory() {
  const q = questions.value[currentIndex.value]
  selectedAnswer.value = answers.value[q?.id]?.userAnswer || ''
  resetImageState()
}

function goBack() {
  saveProgress() // 保存进度再返回
  phase.value = 'select'
  currentBank.value = null
  questions.value = []
  answers.value = {}
  submittedSet.value = {}
}

watch(currentIndex, () => {
  selectAnswerFromHistory()
})
</script>

<template>
  <div class="seq-practice">
    <!-- ========== 题库选择页 ========== -->
    <template v-if="phase === 'select'">
      <div class="select-page">
        <h1 class="select-title">📚 智能题库</h1>
        <p class="select-subtitle">选择一个题库，按顺序逐题精刷，打牢基础</p>
        <div class="bank-cards">
          <div
            v-for="b in banks" :key="b.key"
            class="bank-card"
            @click="startPractice(b)"
          >
            <span class="bank-icon">{{ b.icon }}</span>
            <h3 class="bank-label">{{ b.label }}</h3>
            <p class="bank-desc">{{ b.desc }}</p>
            <span class="bank-count" v-if="b.count !== '...'">{{ b.count }} 题</span>
            <span class="bank-resume" v-if="hasProgress(b.key)">📌 继续上次</span>
          </div>
        </div>
      </div>
    </template>

    <!-- ========== 刷题页 ========== -->
    <template v-if="phase === 'practicing'">
      <!-- 加载中 -->
      <div v-if="loading" class="loading-wrap">
        <div class="spinner"></div>
        <p>加载题库中...</p>
      </div>

      <template v-else-if="questions.length > 0 && currentQuestion">
        <!-- 顶部：返回 + 圆环统计 -->
        <div class="top-bar">
          <button class="btn-back" @click="goBack">← 返回</button>
          <h2 class="top-title">{{ currentBank?.label }} · 顺序刷题</h2>
          <button class="btn-reset" @click="resetProgress" title="清空进度，从头开始">🔄 重新开始</button>
        </div>
        <div class="charts-row">
          <!-- 进度圆环 -->
          <div class="chart-item">
            <svg class="chart-svg" viewBox="0 0 130 130">
              <circle cx="65" cy="65" :r="circleR" fill="none" stroke="#e8e8e8" stroke-width="10" />
              <circle cx="65" cy="65" :r="circleR" fill="none" stroke="#1677FF" stroke-width="10"
                stroke-linecap="round"
                :stroke-dasharray="circleC"
                :stroke-dashoffset="dashOffset(progressPercent)"
                transform="rotate(-90 65 65)"
                style="transition: stroke-dashoffset 0.5s ease"
              />
            </svg>
            <div class="chart-text">
              <span class="chart-val">{{ progressPercent }}%</span>
              <span class="chart-label">已完成</span>
            </div>
          </div>
          <!-- 正确率圆环 -->
          <div class="chart-item">
            <svg class="chart-svg" viewBox="0 0 130 130">
              <circle cx="65" cy="65" :r="circleR" fill="none" stroke="#e8e8e8" stroke-width="10" />
              <circle cx="65" cy="65" :r="circleR" fill="none" :stroke="accuracyPercent >= 90 ? '#52C41A' : '#FA8C16'" stroke-width="10"
                stroke-linecap="round"
                :stroke-dasharray="circleC"
                :stroke-dashoffset="dashOffset(accuracyPercent)"
                transform="rotate(-90 65 65)"
                style="transition: stroke-dashoffset 0.5s ease"
              />
            </svg>
            <div class="chart-text">
              <span class="chart-val" :class="{ 'text-green': accuracyPercent >= 90, 'text-orange': accuracyPercent < 90 && answeredCount > 0 }">{{ accuracyPercent }}%</span>
              <span class="chart-label">正确率</span>
            </div>
          </div>
          <!-- 数字统计 -->
          <div class="chart-stats">
            <div class="stat-line">{{ currentIndex + 1 }} / {{ totalQuestions }} 题</div>
            <div class="stat-line stat-green">✅ {{ correctCount }}</div>
            <div class="stat-line stat-red">❌ {{ answeredCount - correctCount }}</div>
          </div>
        </div>

        <!-- 题目卡片 -->
        <div class="question-card">
          <!-- 题头 -->
          <div class="q-header">
            <span class="q-badge" :class="{
              'type-single': currentQuestion.questionType === '单选题',
              'type-multi': currentQuestion.questionType === '多选题',
              'type-judge': currentQuestion.questionType === '判断题',
            }">{{ currentQuestion.questionType }}</span>
            <span class="q-category" v-if="currentQuestion.category" :class="'cat-' + getCategoryClass(currentQuestion.category)">{{ currentQuestion.category }}</span>
            <span class="q-number">第 {{ currentQuestion.questionNumber }} 题</span>
            <span class="q-diff" v-if="currentQuestion.difficulty">{{ '⭐'.repeat(currentQuestion.difficulty) }}</span>
          </div>

          <!-- 图片 -->
          <div v-if="currentQuestion.imageFile && !hideImage" class="q-image-area">
            <img
              :src="getImageSrc(currentQuestion.imageFile)"
              class="q-image"
              alt="题目配图"
              @error="onImageError"
            />
          </div>

          <!-- 题干 -->
          <p class="q-content">{{ currentQuestion.questionText }}</p>

          <!-- 选项 -->
          <div class="q-options">
            <div
              v-for="opt in getOptions(currentQuestion)" :key="opt.letter"
              class="q-option"
              :class="getOptionClass(opt)"
              @click="selectOption(opt.value)"
            >
              <span class="opt-dot">{{ selectedAnswer === opt.value ? '●' : '○' }}</span>
              <span class="opt-letter">{{ opt.letter }}</span>
              <span class="opt-text">{{ opt.text }}</span>
            </div>
          </div>

          <!-- 判断题特殊按钮 -->
          <div v-if="currentQuestion.questionType === '判断题'" class="judge-row">
            <button class="judge-btn judge-true" :class="{ active: selectedAnswer === '√' }"
              :disabled="isCurrentSubmitted" @click="selectOption('√')">✅ 正确</button>
            <button class="judge-btn judge-false" :class="{ active: selectedAnswer === '×' }"
              :disabled="isCurrentSubmitted" @click="selectOption('×')">❌ 错误</button>
          </div>

          <!-- 提交后结果提示 -->
          <div v-if="isCurrentSubmitted" class="q-result" :class="currentSavedAnswer?.correct ? 'result-ok' : 'result-fail'">
            <template v-if="currentSavedAnswer?.correct">✔ 回答正确！</template>
            <template v-else>✘ 回答错误，正确答案是 <strong>{{ currentSavedAnswer?.correctAnswer }}</strong></template>
          </div>
        </div>

        <!-- 底部按钮 -->
        <div class="bottom-bar">
          <button class="btn-nav" :disabled="currentIndex <= 0" @click="goPrev">上一题</button>
          <button
            class="btn-submit"
            :disabled="!selectedAnswer || isCurrentSubmitted || submitting"
            @click="submitAnswer"
          >{{ submitting ? '提交中...' : '提 交' }}</button>
          <button class="btn-nav" :disabled="currentIndex >= totalQuestions - 1 || !isCurrentSubmitted" @click="goNext">下一题</button>
        </div>
      </template>

      <!-- 全部完成 -->
      <div v-else-if="questions.length > 0 && !currentQuestion" class="finish-wrap">
        <h2>🎉 全部题目已完成！</h2>
        <div class="finish-stats">
          <p>总题数：{{ totalQuestions }}</p>
          <p>正确数：{{ correctCount }}</p>
          <p>正确率：{{ accuracyPercent }}%</p>
        </div>
        <button class="btn btn-primary" @click="goBack">返回选择</button>
      </div>
    </template>
  </div>
</template>

<style scoped>
.seq-practice { max-width: 780px; margin: 0 auto; padding: 24px 16px; min-height: 100vh; }

/* ---- 选择页 ---- */
.select-page { text-align: center; padding-top: 60px; }
.select-title { font-size: 28px; margin-bottom: 8px; }
.select-subtitle { color: var(--color-text-tertiary); margin-bottom: 40px; font-size: 15px; }
.bank-cards { display: flex; gap: 16px; justify-content: center; flex-wrap: wrap; }
.bank-card {
  width: 210px; padding: 28px 20px; background: #fff; border-radius: 16px;
  border: 2px solid var(--color-border-light); cursor: pointer;
  transition: all 0.2s; text-align: center;
}
.bank-card:hover { border-color: var(--color-primary); transform: translateY(-3px); box-shadow: 0 8px 24px rgba(24,144,255,0.12); }
.bank-icon { font-size: 40px; display: block; margin-bottom: 12px; }
.bank-label { font-size: 20px; margin-bottom: 6px; }
.bank-desc { font-size: 13px; color: var(--color-text-tertiary); margin-bottom: 12px; }
.bank-count { font-size: 13px; color: var(--color-primary); font-weight: 600; }
.bank-resume { display: block; margin-top: 8px; font-size: 12px; color: #FA8C16; font-weight: 500; }

/* ---- 加载 ---- */
.loading-wrap { text-align: center; padding: 100px 0; }
.spinner { width: 36px; height: 36px; border: 3px solid var(--color-border); border-top-color: var(--color-primary); border-radius: 50%; animation: spin 0.8s linear infinite; margin: 0 auto 16px; }
@keyframes spin { to { transform: rotate(360deg); } }

/* ---- 顶部 ---- */
.top-bar { display: flex; align-items: center; gap: 16px; margin-bottom: 20px; }
.btn-back { padding: 6px 14px; border: 1px solid var(--color-border); border-radius: 8px; background: #fff; font-size: 14px; cursor: pointer; }
.top-title { font-size: 18px; flex: 1; }
.btn-reset { padding: 6px 14px; border: 1px solid #FFCCC7; border-radius: 8px; background: #FFF1F0; color: #CF1322; font-size: 13px; cursor: pointer; transition: all 0.15s; }
.btn-reset:hover { border-color: #FF4D4F; }

/* ---- 统计圆环 ---- */
.charts-row { display: flex; align-items: center; justify-content: center; gap: 32px; margin-bottom: 24px; flex-wrap: wrap; }
.chart-item { position: relative; width: 130px; height: 130px; }
.chart-svg { width: 130px; height: 130px; }
.chart-text { position: absolute; inset: 0; display: flex; flex-direction: column; align-items: center; justify-content: center; }
.chart-val { font-size: 24px; font-weight: 700; color: var(--color-primary); }
.chart-val.text-green { color: #52C41A; }
.chart-val.text-orange { color: #FA8C16; }
.chart-label { font-size: 12px; color: var(--color-text-tertiary); margin-top: 2px; }
.chart-stats { display: flex; flex-direction: column; gap: 6px; }
.stat-line { font-size: 16px; font-weight: 600; }
.stat-green { color: #52C41A; }
.stat-red { color: #FF4D4F; }

/* ---- 题目卡片 ---- */
.question-card { background: #fff; border-radius: 16px; padding: 24px; border: 1px solid var(--color-border-light); margin-bottom: 20px; }
.q-header { display: flex; align-items: center; gap: 12px; margin-bottom: 20px; padding-bottom: 12px; border-bottom: 1px solid var(--color-border-light); }
.q-badge { font-size: 12px; padding: 2px 10px; border-radius: 6px; font-weight: 500; }
.type-single { background: #E6F4FF; color: #1677FF; }
.type-multi { background: #F6FFED; color: #52C41A; }
.type-judge { background: #FFF7E6; color: #FA8C16; }
.q-category { font-size: 11px; padding: 2px 8px; border-radius: 4px; font-weight: 500; }
.cat-sign { background: #F0F5FF; color: #2F54EB; }
.cat-law { background: #FFF2E8; color: #D4380D; }
.cat-safe { background: #F6FFED; color: #389E0D; }
.cat-theory { background: #F9F0FF; color: #722ED1; }
.q-number { font-size: 14px; color: var(--color-text-secondary); }
.q-diff { margin-left: auto; font-size: 12px; }
.q-image-area { margin-bottom: 16px; text-align: center; }
.q-image { max-width: 100%; max-height: 300px; border-radius: 8px; display: block; margin: 0 auto; }
.q-content { font-size: 18px; line-height: 1.8; color: var(--color-text-primary); margin-bottom: 20px; }

.q-options { display: flex; flex-direction: column; gap: 10px; }
.q-option {
  display: flex; align-items: center; gap: 12px; padding: 14px 16px;
  border: 2px solid var(--color-border); border-radius: 12px;
  cursor: pointer; transition: all 0.15s;
  font-size: 16px;
}
.q-option:hover:not(.is-correct):not(.is-wrong) { border-color: var(--color-primary); background: var(--color-primary-light); }
.q-option.selected { border-color: var(--color-primary); background: var(--color-primary-light); }
.q-option.is-correct { border-color: #52C41A; background: #F6FFED; }
.q-option.is-wrong { border-color: #FF4D4F; background: #FFF1F0; }
.opt-dot { font-size: 14px; width: 20px; text-align: center; }
.opt-letter {
  width: 30px; height: 30px; border-radius: 50%; background: #F5F5F5;
  display: flex; align-items: center; justify-content: center;
  font-weight: 600; font-size: 14px; flex-shrink: 0;
}
.q-option.selected .opt-letter { background: var(--color-primary); color: #fff; }
.q-option.is-correct .opt-letter { background: #52C41A; color: #fff; }
.q-option.is-wrong .opt-letter { background: #FF4D4F; color: #fff; }
.opt-text { flex: 1; }

/* 判断题 */
.judge-row { display: flex; gap: 16px; margin-top: 16px; }
.judge-btn {
  flex: 1; padding: 16px; border: 2px solid var(--color-border); border-radius: 12px;
  font-size: 18px; font-weight: 600; cursor: pointer; transition: all 0.2s;
  text-align: center; background: #fff;
}
.judge-btn:disabled { cursor: default; opacity: 0.6; }
.judge-btn:hover:not(:disabled) { border-color: var(--color-primary); }
.judge-true.active { border-color: #52C41A; background: #F6FFED; }
.judge-false.active { border-color: #FF4D4F; background: #FFF1F0; }

/* 结果提示 */
.q-result { margin-top: 16px; padding: 12px 16px; border-radius: 10px; font-size: 15px; font-weight: 500; }
.result-ok { background: #F6FFED; color: #389E0D; }
.result-fail { background: #FFF1F0; color: #CF1322; }

/* ---- 底部 ---- */
.bottom-bar {
  display: flex; justify-content: space-between; align-items: center;
  padding: 16px; background: #fff; border-radius: 16px;
  border: 1px solid var(--color-border-light); gap: 12px;
}
.btn-nav {
  padding: 12px 28px; border-radius: 10px; border: 1px solid var(--color-border);
  background: #fff; font-size: 15px; cursor: pointer; min-width: 100px;
  transition: all 0.15s;
}
.btn-nav:disabled { opacity: 0.4; cursor: not-allowed; }
.btn-nav:hover:not(:disabled) { border-color: var(--color-primary); color: var(--color-primary); }
.btn-submit {
  padding: 12px 40px; border-radius: 10px; border: none;
  background: var(--color-primary); color: #fff; font-size: 16px; font-weight: 600;
  cursor: pointer; min-width: 120px; transition: all 0.15s;
}
.btn-submit:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-submit:hover:not(:disabled) { opacity: 0.9; }

/* ---- 完成页 ---- */
.finish-wrap { text-align: center; padding: 80px 20px; }
.finish-wrap h2 { font-size: 24px; margin-bottom: 20px; }
.finish-stats { margin-bottom: 24px; font-size: 16px; color: var(--color-text-secondary); }
.finish-stats p { margin: 6px 0; }
</style>
