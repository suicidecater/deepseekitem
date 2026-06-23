// src/stores/exam.ts - 考试/练习状态管理
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { ExamQuestion } from '@/types/exam'

interface AnswerRecord {
  questionId: number
  answer: string
  correct: boolean
  timeSpent: number
}

export const useExamStore = defineStore('exam', () => {
  const questions = ref<ExamQuestion[]>([])
  const currentIndex = ref(0)
  const answers = ref<Map<number, string>>(new Map())
  const markedQuestions = ref<Set<number>>(new Set())
  const timeSpent = ref(0)
  const isFinished = ref(false)
  const examResult = ref<any>(null)
  const mode = ref<'practice' | 'exam' | 'evaluation'>('practice')
  const loading = ref(false)

  const totalCount = computed(() => questions.value.length)
  const currentQuestion = computed(() => questions.value[currentIndex.value] || null)
  const answeredCount = computed(() => answers.value.size)
  const progress = computed(() => totalCount.value > 0 ? (currentIndex.value / totalCount.value) * 100 : 0)
  const correctRate = computed(() => {
    if (!examResult.value) return 0
    return examResult.value.correctRate || 0
  })

  // 加载题目
  async function loadQuestions(params: { mode: string; subject: number; count: number; difficulty?: number; types?: string[] }) {
    loading.value = true
    try {
      const res = await fetch('/api/question/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(params)
      })
      const json = await res.json()
      if (json.code === 0) {
        questions.value = json.data.questions
        currentIndex.value = 0
        answers.value = new Map()
        markedQuestions.value = new Set()
        timeSpent.value = 0
        isFinished.value = false
        examResult.value = null
        mode.value = params.mode as any
      }
    } finally {
      loading.value = false
    }
  }

  // 记录答案
  function recordAnswer(questionId: number, answer: string) {
    answers.value.set(questionId, answer)
  }

  // 下一题
  function nextQuestion() {
    if (currentIndex.value < totalCount.value - 1) {
      currentIndex.value++
    }
  }

  // 上一题
  function prevQuestion() {
    if (currentIndex.value > 0) {
      currentIndex.value--
    }
  }

  // 跳转指定题号
  function jumpTo(index: number) {
    if (index >= 0 && index < totalCount.value) {
      currentIndex.value = index
    }
  }

  // 标记/取消标记
  function toggleMark(questionId: number) {
    if (markedQuestions.value.has(questionId)) {
      markedQuestions.value.delete(questionId)
    } else {
      markedQuestions.value.add(questionId)
    }
  }

  // 提交
  async function submit(answersData: AnswerRecord[]) {
    loading.value = true
    try {
      const res = await fetch('/api/question/submit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ answers: answersData, timeSpent: timeSpent.value })
      })
      const json = await res.json()
      if (json.code === 0) {
        examResult.value = json.data
        isFinished.value = true
      }
      return json.data
    } finally {
      loading.value = false
    }
  }

  // 单题提交答案（练习模式）
  async function submitAnswer(questionId: number, answer: string) {
    recordAnswer(questionId, answer)
    const res = await fetch('/api/question/answer', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ questionId, answer })
    })
    const json = await res.json()
    return json.data
  }

  function reset() {
    questions.value = []
    currentIndex.value = 0
    answers.value = new Map()
    markedQuestions.value = new Set()
    timeSpent.value = 0
    isFinished.value = false
    examResult.value = null
  }

  return {
    questions, currentIndex, answers, markedQuestions, timeSpent,
    isFinished, examResult, mode, loading,
    totalCount, currentQuestion, answeredCount, progress, correctRate,
    loadQuestions, recordAnswer, nextQuestion, prevQuestion,
    jumpTo, toggleMark, submit, submitAnswer, reset
  }
})
