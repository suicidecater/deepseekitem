/**
 * src/api/modules/question.ts
 * 题库/考试/练习 API
 */
import { get, post, del } from '@/api/request'

// ======================== 请求/响应类型 ========================

export interface QuestionParams {
  mode?: 'practice' | 'exam' | 'evaluation'
  subject?: number        // 科目1/4
  count?: number          // 题目数量
  difficulty?: number     // 难度
  types?: string[]        // ['single', 'multiple', 'judge']
}

export interface ExamQuestion {
  id: number
  type: 'single' | 'multiple' | 'judge'
  subject: number
  content: string
  options: string[]
  answer: string
  explanation?: string
  category?: string
  difficulty?: number
}

export interface AnswerResult {
  correct: boolean
  correctAnswer: string
  explanation: string
}

export interface SubmitResult {
  score: number
  correctRate: number
  correctCount: number
  wrongCount: number
  totalCount: number
  passed: boolean
  categoryStats: Array<{ name: string; rate: number }>
  radarData: {
    dimensions: string[]
    current: number[]
    baseline: number[]
  }
  weakPoints: Array<{ name: string; rate: number }>
  advices: string[]
}

export interface ErrorBookItem {
  id: number
  questionId: number
  source: string
  type: 'single' | 'multiple' | 'judge'
  content: string
  answer: string
  options: string[]
  errorType: string
  errorCount: number
  difficulty: number
  image: string | null
  updateTime: string
}

export interface ErrorBookData {
  list: ErrorBookItem[]
  total: number
  toReview: number
  reviewed: number
  mastered: number
}

// ======================== API 方法 ========================

/** 加载题目（练习/测评） */
export function startQuestions(params: QuestionParams) {
  return post<{ questions: ExamQuestion[] }>('/api/question/practice/start', params)
}

/** 单题提交答案（练习模式） */
export function submitAnswer(params: { questionId: number; answer: string }) {
  return post<AnswerResult>('/api/question/practice/answer', params)
}

/** 提交整套题（考试模式） */
export function submitQuestions(params: { answers: any[]; timeSpent?: number }) {
  return post<SubmitResult>('/api/question/exam/submit', params)
}

/** 获取错题本 */
export function getErrorBook(params?: { page?: number; pageSize?: number; subject?: number }) {
  return get<ErrorBookData>('/api/question/error-book', params)
}

/** 删除错题记录 */
export function deleteErrorBook(errorId: number) {
  return del(`/api/question/error-book/${errorId}`)
}

/** 错题复习（提交答案） */
export function reviewError(params: { errorId: number; answer: string }) {
  return post<{ correct: boolean; correctAnswer: string; removed?: boolean }>('/api/question/error-book/review', params)
}


