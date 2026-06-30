// src/stores/exam.ts - 考试/练习/测评状态管理（已与后端端点对齐）
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { get, post } from '@/api/request'
import type { ApiResponse } from '@/types/common'

interface ExamQuestion {
  id: number
  type: string
  content: string
  options: string[]
  image?: string
  difficulty?: number
}

interface AnswerItem {
  userAnswer: string
  correctAnswer: string
  isCorrect: boolean
}

interface ExamResult {
  score: number
  correctRate: number
  correctCount: number
  wrongCount: number
  totalCount: number
  passed: boolean
  categoryStats: { name: string; rate: number; correct: number; total: number }[]
  radarData: { dimensions: string[]; current: number[]; baseline: number[] }
  weakPoints: { name: string; rate: number }[]
  advices: string[]
  answerMap?: Record<string, AnswerItem>
}

export const useExamStore = defineStore('exam', () => {
  const questions = ref<ExamQuestion[]>([])
  const currentIndex = ref(0)
  const answers = ref<Map<number, string>>(new Map())
  const timeSpent = ref(0)
  const isFinished = ref(false)
  const examResult = ref<ExamResult | null>(null)
  const mode = ref<'practice' | 'exam' | 'evaluation'>('practice')
  const loading = ref(false)
  // 当前会话ID（练习返回practice_id，考试返回exam_id）
  const sessionId = ref<number | null>(null)

  // 交卷后答案映射（后端只返回判题结果，前端已有完整题目数据）
  const answerMap = ref<Record<string, AnswerItem>>({})

  const totalCount = computed(() => questions.value.length)
  const currentQuestion = computed(() => questions.value[currentIndex.value] || null)
  const answeredCount = computed(() => answers.value.size)
  const progress = computed(() => totalCount.value > 0 ? ((currentIndex.value + 1) / totalCount.value) * 100 : 0)
  const correctRate = computed(() => examResult.value?.correctRate ?? 0)

  // 答卷回顾用：前端题目数据 + 后端判题结果合并
  const reviewQuestions = computed(() => {
    return questions.value.map(q => {
      const item = answerMap.value[q.id]
      return {
        id: q.id,
        type: q.type,
        content: q.content,
        options: q.options,
        image: q.image,
        answer: item?.correctAnswer || '',
        userAnswer: item?.userAnswer || '',
        isCorrect: item?.isCorrect ?? false,
      }
    })
  })

  // 自动切换端点
  function _apiPath(endpoint: string) {
    if (mode.value === 'exam') {
      return `/api/question/exam/${endpoint}`
    }
    if (mode.value === 'evaluation') {
      return `/api/student/evaluation/${endpoint}`
    }
    return `/api/question/practice/${endpoint}`
  }

  // 加载题目
  async function loadQuestions(params: {
    mode: 'practice' | 'exam' | 'evaluation'
    subject: number
    count: number
    difficulty?: number
    types?: string[]
  }) {
    loading.value = true
    mode.value = params.mode
    reset()

    try {
      const path = params.mode === 'exam'
        ? '/api/question/exam/start'
        : params.mode === 'evaluation'
          ? '/api/student/evaluation/start'
          : '/api/question/practice/start'

      const res = await post<ApiResponse<{
        exam_id?: number
        practice_id?: number
        questions: ExamQuestion[]
        total: number
        subject: number
        duration: number
      }>>(path, {
        subject: params.subject,
        count: params.count,
        difficulty: params.difficulty,
        types: params.types
      })

      const raw = (res as any).data
      const data = raw?.data ?? raw
      if (data && data.questions) {
        questions.value = data.questions
        sessionId.value = data.exam_id || data.practice_id || null
      }
    } finally {
      loading.value = false
    }
  }

  function recordAnswer(questionId: number, answer: string) {
    answers.value.set(questionId, answer)
  }

  function nextQuestion() {
    if (currentIndex.value < totalCount.value - 1) currentIndex.value++
  }

  function prevQuestion() {
    if (currentIndex.value > 0) currentIndex.value--
  }

  function jumpTo(index: number) {
    if (index >= 0 && index < totalCount.value) currentIndex.value = index
  }

  // 提交考试/测评（发送 examId + totalTime，答案已在答题缓存中）
  async function submit(totalTime: number) {
    if (!sessionId.value && mode.value !== 'evaluation') {
      throw new Error('考试会话无效，请重新开始考试')
    }
    loading.value = true

    try {
      let res: any

      if (mode.value === 'evaluation') {
        // 测评：提交答案数组
        const answerList = Array.from(answers.value.entries()).map(([qid, ans]) => ({
          questionId: qid,
          answer: ans,
          correct: false // 后端判断
        }))
        res = await post('/api/student/evaluation/submit', { answers: answerList, totalTime })
      } else {
        // 考试/练习：提交答案
        const path = mode.value === 'exam'
          ? '/api/question/exam/submit'
          : '/api/question/practice/submit'

        // 将前端 Map 转为普通对象传给后端
        const answersObj: Record<string, string> = {}
        answers.value.forEach((val, key) => { answersObj[String(key)] = val })

        res = await post(path, {
          examId: sessionId.value,
          practiceId: sessionId.value,
          totalTime,
          answers: answersObj
        })
      }

      // 检查业务错误码
      const raw = (res as any).data
      if (raw && raw.code && raw.code !== 0) {
        throw new Error(raw.message || '提交失败')
      }

      const data = raw?.data ?? raw
      if (!data || data.score === undefined) {
        throw new Error('服务器返回数据异常')
      }

      examResult.value = data
      if (data.answerMap) {
        answerMap.value = data.answerMap
      }
      isFinished.value = true
      return data
    } catch (e: any) {
      // 重新抛出，让调用方处理UI恢复
      throw e
    } finally {
      loading.value = false
    }
  }

  // 单题提交答案（练习/考试模式）
  async function submitAnswer(questionId: number, answer: string) {
    recordAnswer(questionId, answer)

    if (mode.value === 'exam') {
      // 考试模式：缓存答案到后端
      const res = await post('/api/question/exam/answer', {
        examId: sessionId.value,
        questionId,
        answer
      })
      const raw = (res as any).data
      return raw?.data ?? raw
    }

    // 练习模式：提交单题
    const res = await post('/api/question/practice/answer', {
      practiceId: sessionId.value,
      questionId,
      answer
    })
    const raw2 = (res as any).data
    return raw2?.data ?? raw2
  }

  function reset() {
    questions.value = []
    currentIndex.value = 0
    answers.value = new Map()
    timeSpent.value = 0
    isFinished.value = false
    examResult.value = null
    sessionId.value = null
    answerMap.value = {}
  }

  return {
    questions, currentIndex, answers, timeSpent,
    isFinished, examResult, mode, loading, sessionId,
    totalCount, currentQuestion, answeredCount, progress, correctRate,
    reviewQuestions, answerMap,
    loadQuestions, recordAnswer, nextQuestion, prevQuestion,
    jumpTo, submit, submitAnswer, reset
  }
})
