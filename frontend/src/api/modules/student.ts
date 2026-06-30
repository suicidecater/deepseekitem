/**
 * src/api/modules/student.ts
 * 学员端 API
 */
import { get, post } from '@/api/request'

// ======================== 请求/响应类型 ========================

export interface StudyTask {
  id: number
  title: string
  description: string
  completed: boolean
  type: 'practice' | 'ai_lesson' | 'exam_review' | 'error_review'
  route?: string
}

export interface KnowledgeTreeNode {
  name: string
  value: number
  children?: KnowledgeTreeNode[]
}

export interface QuickAction {
  label: string
  icon: string
  route: string
  color: string
}

export interface StudentProfile {
  name: string
  phone: string
  carType: string
  school: string
  registerDate: string
  avatar: string
  progress: number
}

export interface DashboardData {
  profile: StudentProfile
  abilityScores: number[]
  abilityBaseline: number[]
  todayTasks: StudyTask[]
  knowledgeTree: KnowledgeTreeNode
  completedQuestions: number
  totalQuestions: number
  streakDays: number
  todayStudyMinutes: number
  daysUntilExam: number
  subject1Progress: number
  subject4Progress: number
  transportProgress: number
  totalStudents: number
  quickActions: QuickAction[]
}

export interface ProgressData {
  stats: {
    totalDays: number
    totalHours: number
    totalQuestions: number
    accuracy: number
  }
  knowledgeTree: Array<{ name: string; value: number; completed: number; color: string }>
  radarData: {
    dimensions: string[]
    current: number[]
    baseline: number[]
  }
  heatmapCells: Array<{ date: string; minutes: number; level: 0 | 1 | 2 | 3 | 4 }>
}

export interface ReportData {
  overallScore: number
  overallLevel: string
  growthCurve: Array<{ date: string; scores: number[] }>
  knowledgeMatrix: any[]
  examHistory: Array<{ date: string; score: number; passed: boolean }>
  aiAdvices: string[]
}

export interface StudyPlanData {
  weekStart: string
  weekEnd: string
  days: Array<{
    date: string
    dayOfWeek: string
    isToday: boolean
    tasks: StudyTask[]
  }>
  totalTasks: number
  completedTasks: number
}

export interface EvaluationResult {
  score: number
  correctRate: number
  correctCount: number
  wrongCount: number
  radarData: {
    dimensions: string[]
    current: number[]
    baseline: number[]
  }
  weakPoints: Array<{ name: string; rate: number }>
  advices: string[]
}

// ======================== API 方法 ========================

/** 获取学员仪表盘数据 */
export function getDashboard() {
  return get<DashboardData>('/api/student/dashboard')
}

/** 获取学习进度 */
export function getProgress() {
  return get<ProgressData>('/api/student/progress')
}

/** 获取学习报告 */
export function getReport() {
  return get<ReportData>('/api/student/report')
}

/** 获取学习计划 */
export function getStudyPlan(direction?: number) {
  const params = direction ? `?direction=${direction}` : ''
  return get<StudyPlanData>(`/api/student/study-plan${params}`)
}

/** 生成学习计划 */
export function generateStudyPlan(params?: { study_subject?: number; exam_date?: string }) {
  return post<StudyPlanData>('/api/student/study-plan/generate', params || {})
}

/** 开始测评 */
export function startEvaluation() {
  return post<{ questions: any[] }>('/api/student/evaluation/start')
}

/** 提交测评 */
export function submitEvaluation(params: { answers: any[]; timeSpent?: number }) {
  return post<EvaluationResult>('/api/student/evaluation/submit', params)
}

/** 获取驾考课程 */
export function getTransportCourses() {
  return get<{ courses: any[] }>('/api/student/transport')
}

/** 获取消息列表 */
export function getMessages() {
  return get<{ list: any[] }>('/api/student/messages')
}
